"""Měřitelná pravidla setupů. Bez AI, jen kód.

Setup „breakout → retest → hold“ (BRH), vyhodnocuje se jen na UZAVŘENÝCH svíčkách.

LONG (index b = breakout, r = retest, h = hold):
  1. Range: RH = max(high[b-L .. b-1]), RL = min(low[b-L .. b-1]), L = range_lookback.
     Výška range (RH-RL)/RH musí být mezi min_range_pct a max_range_pct.
  2. Breakout: close[b] > RH a close[b-1] <= RH (první close nad range high).
  3. Retest: první svíčka r v (b, b+retest_window], jejíž low <= RH*(1+tol).
     Mezi b a r musí všechny close zůstat > RH (jinak je breakout neplatný).
     Retest svíčka nesmí zavřít pod RH*(1-tol).
  4. Hold: svíčka h = r+1 má close > RH a low >= RH*(1-tol).
  5. Signál platí, jen když h je poslední uzavřená svíčka (čerstvý setup).

SHORT je zrcadlo: breakdown pod RL, retest high >= RL*(1-tol), hold close < RL a high <= RL*(1+tol).

Plán obchodu:
  vstup  = close[h]
  stop   = long: min(low[r], low[h]) - stop_buffer_atr*ATR14 ; short: max(high[r], high[h]) + buffer,
           ale vždy aspoň min_stop_atr*ATR14 od vstupu
  cíle   = measured move: RH + k*(RH-RL) pro k v target_multiples (short: RL - k*(RH-RL)),
           nebo target_mode "r_multiple": vstup ± k*R
  R:R    = |cíl - vstup| / |vstup - stop| pro každý cíl; filtr min_rr se aplikuje na T1.
"""
from dataclasses import dataclass, field, asdict
import math

import pandas as pd

DEFAULTS = {
    "range_lookback": 20,
    "min_range_pct": 0.5,
    "max_range_pct": 8.0,
    "retest_window": 6,
    "tolerance_pct": 0.3,
    "stop_buffer_atr": 0.1,
    "min_stop_atr": 0.5,
    "target_mode": "measured_move",
    "target_multiples": [1.0, 2.0],
}


@dataclass
class Setup:
    kind: str
    direction: str
    breakout_time: pd.Timestamp
    retest_time: pd.Timestamp
    hold_time: pd.Timestamp
    level: float
    range_high: float
    range_low: float
    entry: float
    stop: float
    targets: list
    rr: list
    meta: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        for k in ("breakout_time", "retest_time", "hold_time"):
            d[k] = pd.Timestamp(d[k]).isoformat()
        return d


def atr(df, n=14):
    prev = df["Close"].shift(1)
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()


def _targets(direction, entry, stop, rh, rl, p):
    risk = abs(entry - stop)
    height = rh - rl
    sign = 1 if direction == "long" else -1
    if p["target_mode"] == "r_multiple":
        tg = [entry + sign * k * risk for k in p["target_multiples"]]
    else:
        base = rh if direction == "long" else rl
        tg = [base + sign * k * height for k in p["target_multiples"]]
    rr = [round(sign * (t - entry) / risk, 2) if risk > 0 else 0.0 for t in tg]
    return tg, rr


def _brh_at(df, b, direction, p, a):
    """Zkusí setup s breakoutem na indexu b. Vrátí Setup, nebo None."""
    L, W, tol = p["range_lookback"], p["retest_window"], p["tolerance_pct"] / 100
    if b < L:
        return None
    win = df.iloc[b - L:b]
    rh, rl = float(win["High"].max()), float(win["Low"].min())
    height_pct = (rh - rl) / rh * 100
    if not (p["min_range_pct"] <= height_pct <= p["max_range_pct"]):
        return None
    c, h, l = df["Close"].values, df["High"].values, df["Low"].values
    long = direction == "long"
    lvl = rh if long else rl

    # 2. breakout / breakdown
    if long and not (c[b] > lvl and c[b - 1] <= lvl):
        return None
    if not long and not (c[b] < lvl and c[b - 1] >= lvl):
        return None

    # 3. retest
    r = None
    for i in range(b + 1, min(b + W, len(df) - 1) + 1):
        touched = l[i] <= lvl * (1 + tol) if long else h[i] >= lvl * (1 - tol)
        if touched:
            r = i
            break
        stayed = c[i] > lvl if long else c[i] < lvl
        if not stayed:
            return None
    if r is None or r + 1 >= len(df):
        return None
    if long and c[r] < lvl * (1 - tol):
        return None
    if not long and c[r] > lvl * (1 + tol):
        return None

    # 4. hold
    hh = r + 1
    if long and not (c[hh] > lvl and l[hh] >= lvl * (1 - tol)):
        return None
    if not long and not (c[hh] < lvl and h[hh] <= lvl * (1 + tol)):
        return None

    entry = float(c[hh])
    buf = p["stop_buffer_atr"] * float(a.iloc[hh])
    stop = min(l[r], l[hh]) - buf if long else max(h[r], h[hh]) + buf
    # stop ne blíž než min_stop_atr*ATR od vstupu (jinak by R:R bylo uměle vysoké)
    min_dist = p["min_stop_atr"] * float(a.iloc[hh])
    stop = min(stop, entry - min_dist) if long else max(stop, entry + min_dist)
    if (long and stop >= entry) or (not long and stop <= entry):
        return None
    tg, rr = _targets(direction, entry, float(stop), rh, rl, p)
    return Setup(
        kind="breakout_retest_hold", direction=direction,
        breakout_time=df.index[b], retest_time=df.index[r], hold_time=df.index[hh],
        level=lvl, range_high=rh, range_low=rl, entry=entry, stop=float(stop),
        targets=[float(t) for t in tg], rr=rr,
        meta={"range_pct": round(height_pct, 2), "atr": float(a.iloc[hh]), "hold_index": hh},
    )


def find_setups(df, direction="both", params=None):
    """Všechny výskyty BRH v historii (pro testy a backtest)."""
    p = {**DEFAULTS, **(params or {})}
    dirs = ["long", "short"] if direction == "both" else [direction]
    a = atr(df)
    out = []
    for b in range(p["range_lookback"], len(df) - 2):
        for d in dirs:
            s = _brh_at(df, b, d, p, a)
            if s:
                out.append(s)
    return out


def latest_setup(df, direction="both", params=None):
    """Setupy, jejichž hold svíčka je poslední uzavřená svíčka v df."""
    p = {**DEFAULTS, **(params or {})}
    last = len(df) - 1
    dirs = ["long", "short"] if direction == "both" else [direction]
    a = atr(df)
    out = []
    # hold = last → retest = last-1 → breakout v [last-1-W, last-2]
    for b in range(max(p["range_lookback"], last - 1 - p["retest_window"]), last - 1):
        for d in dirs:
            s = _brh_at(df, b, d, p, a)
            if s and s.meta["hold_index"] == last:
                out.append(s)
    return out


def position_size(setup, account, risk_pct, fractional=True, cash_only=True):
    """Počet kusů tak, aby ztráta na stopu = risk_pct % účtu; u hotovosti omezeno velikostí účtu."""
    risk_usd = account * risk_pct / 100
    per_unit = abs(setup.entry - setup.stop)
    qty = risk_usd / per_unit
    if cash_only:
        qty = min(qty, account / setup.entry)
    qty = math.floor(qty * 1e6) / 1e6 if fractional else math.floor(qty)
    return {"qty": qty, "notional": round(qty * setup.entry, 2), "risk_usd": round(qty * per_unit, 2)}
