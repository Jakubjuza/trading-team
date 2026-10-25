"""Knihovna setupů – každý je měřitelné pravidlo (kód, ne AI), zvlášť pro long a short.

Každý setup vrací `rules.Setup` se vstupem na close signální svíčky (hold_index), stopem a 2 cíli.
Společné pro všechny (parametry v configu):
  - stop aspoň `min_stop_atr` × ATR a `min_stop_pct` % od vstupu (jinak ho sežerou poplatky),
  - volitelný filtr trendu `trend_ema` (long nad EMA, short pod), `skip_weekends`,
  - cíle: `target_mode` "r_multiple" (vstup ± k×R) nebo strukturální (u range fade střed/hrana range).

Setupy (long; short je zrcadlo):
  breakout_retest_hold  – close nad range high, retest do 0,3 %, další svíčka hladinu udrží (rules.py)
  pullback              – trend (EMA50 > EMA200, EMA50 roste), pokles k EMA20 a obratová svíčka (close > high předchozí)
  sweep_reclaim         – knot pod swing low posledních N svíček a close zpět nad (vybrané stopy), objem nad průměrem
  squeeze_breakout      – Bollinger šířka u N-svíčkového minima, close nad horním pásmem s objemem
  donchian_breakout     – close nad maximem posledních N svíček (Turtle), stop k×ATR
  range_fade            – boční trh (ADX nízký), dotek dna range, RSI přeprodané, býčí svíčka → cíl střed a vrchol range
"""
import numpy as np
import pandas as pd

from scanner import rules
from scanner.rules import Setup

COMMON = {
    "min_stop_atr": 0.5,
    "min_stop_pct": 1.5,
    "stop_buffer_atr": 0.1,
    "trend_ema": 0,
    "skip_weekends": False,
    "target_mode": "r_multiple",
    "target_multiples": [1.5, 3.0],
}

DEFAULTS = {
    "breakout_retest_hold": {},  # parametry v rules.DEFAULTS
    "pullback": {"ema_fast": 20, "ema_mid": 50, "ema_slow": 200, "slope_bars": 10, "touch_tol_pct": 0.3, "lookback": 3},
    "sweep_reclaim": {"swing_bars": 20, "min_sweep_atr": 0.1, "volume_mult": 1.2},
    "squeeze_breakout": {"bb_len": 20, "bb_std": 2.0, "squeeze_lookback": 100, "squeeze_tol": 1.1, "volume_mult": 1.2},
    "donchian_breakout": {"channel": 20, "stop_atr": 2.0},
    "range_fade": {"range_bars": 40, "adx_max": 20, "rsi_low": 30, "rsi_high": 70, "touch_tol_pct": 0.3},
}

NAMES_CS = {
    "breakout_retest_hold": "breakout → retest → hold",
    "pullback": "pullback v trendu",
    "sweep_reclaim": "sweep likvidity a reclaim",
    "squeeze_breakout": "squeeze breakout",
    "donchian_breakout": "Donchian breakout",
    "range_fade": "range fade (odraz od hrany)",
}


# --- indikátory -------------------------------------------------------------------
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def adx(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    up, dn = h.diff(), -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr_ = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_
    mdi = 100 * pd.Series(minus, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


class Ctx:
    """Předpočítané řady pro jedno df (rychlé i na letech dat)."""

    def __init__(self, df):
        self.df = df
        self.idx = df.index
        self.o, self.c, self.h, self.l = (df[k].values for k in ("Open", "Close", "High", "Low"))
        vol = df["Volume"] if "Volume" in df else pd.Series(0.0, index=df.index)
        self.v = vol.values
        self.vavg = vol.rolling(20).mean().shift(1).values
        self.atr = rules.atr(df).values
        self.weekday = df.index.dayofweek
        self._cache = {}

    def get(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def ema(self, n):
        return self.get(("ema", n), lambda: ema(self.df["Close"], n).values)

    def rsi(self, n=14):
        return self.get(("rsi", n), lambda: rsi(self.df["Close"], n).values)

    def adx(self, n=14):
        return self.get(("adx", n), lambda: adx(self.df, n).values)

    def roll_max(self, n):  # max high[i-n .. i-1]
        return self.get(("hmax", n), lambda: self.df["High"].rolling(n).max().shift(1).values)

    def roll_min(self, n):
        return self.get(("lmin", n), lambda: self.df["Low"].rolling(n).min().shift(1).values)

    def bb(self, n, k):
        def calc():
            m = self.df["Close"].rolling(n).mean()
            sd = self.df["Close"].rolling(n).std()
            return m.values, (m + k * sd).values, (m - k * sd).values, ((2 * k * sd) / m).values
        return self.get(("bb", n, k), calc)


# --- společné dokončení setupu -------------------------------------------------------------
def finalize(x, i, direction, kind, p, entry, stop, level, rng=None, targets=None, b=None, r=None, meta=None):
    """Aplikuje filtry a minimální stop, spočítá cíle a R:R. Vrátí Setup, nebo None."""
    long = direction == "long"
    if p.get("skip_weekends") and x.weekday[i] >= 5:
        return None
    if p.get("trend_ema"):
        e = x.ema(p["trend_ema"])[i]
        if np.isnan(e) or (long and x.c[i] <= e) or (not long and x.c[i] >= e):
            return None
    a = float(x.atr[i])
    stop = stop - p["stop_buffer_atr"] * a if long else stop + p["stop_buffer_atr"] * a
    min_dist = max(p["min_stop_atr"] * a, entry * p["min_stop_pct"] / 100)
    stop = min(stop, entry - min_dist) if long else max(stop, entry + min_dist)
    risk = abs(entry - stop)
    if risk <= 0 or np.isnan(risk):
        return None
    sign = 1 if long else -1
    if targets is None:
        targets = [entry + sign * k * risk for k in p["target_multiples"]]
    if (long and targets[0] <= entry) or (not long and targets[0] >= entry):
        return None
    rr = [round(sign * (t - entry) / risk, 2) for t in targets]
    rh, rl = rng if rng else (level, level)
    return Setup(kind=kind, direction=direction,
                 breakout_time=x.idx[b if b is not None else i], retest_time=x.idx[r if r is not None else i],
                 hold_time=x.idx[i], level=float(level), range_high=float(rh), range_low=float(rl),
                 entry=float(entry), stop=float(stop), targets=[float(t) for t in targets], rr=rr,
                 meta={"atr": a, "hold_index": int(i), "range_pct": round((rh - rl) / rh * 100, 2) if rh else 0,
                       **(meta or {})})


def _dirs(direction):
    return ["long", "short"] if direction == "both" else [direction]


# --- setupy ----------------------------------------------------------------------------------
def pullback(x, p, direction, idxs):
    ef, em, es = x.ema(p["ema_fast"]), x.ema(p["ema_mid"]), x.ema(p["ema_slow"])
    sb, tol, lb = p["slope_bars"], p["touch_tol_pct"] / 100, p["lookback"]
    out = []
    for i in idxs:
        if i < max(p["ema_slow"], sb + lb + 1):
            continue
        for d in _dirs(direction):
            if d == "long":
                trend = em[i] > es[i] and em[i] > em[i - sb] and x.c[i] > es[i]
                touched = min(x.l[i - lb + 1:i + 1]) <= ef[i] * (1 + tol)
                trig = x.c[i] > x.h[i - 1] and x.c[i] > ef[i]
                if trend and touched and trig:
                    s = finalize(x, i, d, "pullback", p, x.c[i], min(x.l[i - lb + 1:i + 1]), ef[i])
                    out.append(s) if s else None
            else:
                trend = em[i] < es[i] and em[i] < em[i - sb] and x.c[i] < es[i]
                touched = max(x.h[i - lb + 1:i + 1]) >= ef[i] * (1 - tol)
                trig = x.c[i] < x.l[i - 1] and x.c[i] < ef[i]
                if trend and touched and trig:
                    s = finalize(x, i, d, "pullback", p, x.c[i], max(x.h[i - lb + 1:i + 1]), ef[i])
                    out.append(s) if s else None
    return out


def sweep_reclaim(x, p, direction, idxs):
    n = p["swing_bars"]
    lo, hi = x.roll_min(n), x.roll_max(n)
    out = []
    for i in idxs:
        if i < n + 1 or np.isnan(lo[i]):
            continue
        vol_ok = x.vavg[i] > 0 and x.v[i] >= p["volume_mult"] * x.vavg[i]
        a = x.atr[i]
        for d in _dirs(direction):
            if d == "long" and x.l[i] < lo[i] - p["min_sweep_atr"] * a and x.c[i] > lo[i] and vol_ok:
                s = finalize(x, i, d, "sweep_reclaim", p, x.c[i], x.l[i], lo[i], rng=(hi[i], lo[i]))
                out.append(s) if s else None
            if d == "short" and x.h[i] > hi[i] + p["min_sweep_atr"] * a and x.c[i] < hi[i] and vol_ok:
                s = finalize(x, i, d, "sweep_reclaim", p, x.c[i], x.h[i], hi[i], rng=(hi[i], lo[i]))
                out.append(s) if s else None
    return out


def squeeze_breakout(x, p, direction, idxs):
    mid, up, dn, w = x.bb(p["bb_len"], p["bb_std"])
    wmin = pd.Series(w).rolling(p["squeeze_lookback"]).min().shift(1).values
    out = []
    for i in idxs:
        if i < p["squeeze_lookback"] + p["bb_len"] or np.isnan(wmin[i]):
            continue
        squeezed = w[i - 1] <= wmin[i] * p["squeeze_tol"]
        vol_ok = x.vavg[i] > 0 and x.v[i] >= p["volume_mult"] * x.vavg[i]
        if not (squeezed and vol_ok):
            continue
        for d in _dirs(direction):
            if d == "long" and x.c[i] > up[i] and x.c[i - 1] <= up[i - 1]:
                s = finalize(x, i, d, "squeeze_breakout", p, x.c[i], mid[i], up[i], rng=(up[i], dn[i]))
                out.append(s) if s else None
            if d == "short" and x.c[i] < dn[i] and x.c[i - 1] >= dn[i - 1]:
                s = finalize(x, i, d, "squeeze_breakout", p, x.c[i], mid[i], dn[i], rng=(up[i], dn[i]))
                out.append(s) if s else None
    return out


def donchian_breakout(x, p, direction, idxs):
    n = p["channel"]
    hi, lo = x.roll_max(n), x.roll_min(n)
    out = []
    for i in idxs:
        if i < n + 1 or np.isnan(hi[i]):
            continue
        for d in _dirs(direction):
            if d == "long" and x.c[i] > hi[i] and x.c[i - 1] <= hi[i - 1]:
                s = finalize(x, i, d, "donchian_breakout", p, x.c[i], x.c[i] - p["stop_atr"] * x.atr[i], hi[i], rng=(hi[i], lo[i]))
                out.append(s) if s else None
            if d == "short" and x.c[i] < lo[i] and x.c[i - 1] >= lo[i - 1]:
                s = finalize(x, i, d, "donchian_breakout", p, x.c[i], x.c[i] + p["stop_atr"] * x.atr[i], lo[i], rng=(hi[i], lo[i]))
                out.append(s) if s else None
    return out


def range_fade(x, p, direction, idxs):
    n, tol = p["range_bars"], p["touch_tol_pct"] / 100
    hi, lo, ad, rs = x.roll_max(n), x.roll_min(n), x.adx(), x.rsi()
    out = []
    for i in idxs:
        if i < n + 30 or np.isnan(hi[i]) or np.isnan(ad[i]) or ad[i] > p["adx_max"]:
            continue
        mid = (hi[i] + lo[i]) / 2
        for d in _dirs(direction):
            if d == "long" and x.l[i] <= lo[i] * (1 + tol) and rs[i - 1] < p["rsi_low"] and x.c[i] > x.o[i] and x.c[i] > lo[i]:
                s = finalize(x, i, d, "range_fade", p, x.c[i], min(x.l[i], lo[i]), lo[i], rng=(hi[i], lo[i]),
                             targets=[mid, hi[i] * (1 - tol)])
                out.append(s) if s else None
            if d == "short" and x.h[i] >= hi[i] * (1 - tol) and rs[i - 1] > p["rsi_high"] and x.c[i] < x.o[i] and x.c[i] < hi[i]:
                s = finalize(x, i, d, "range_fade", p, x.c[i], max(x.h[i], hi[i]), hi[i], rng=(hi[i], lo[i]),
                             targets=[mid, lo[i] * (1 + tol)])
                out.append(s) if s else None
    return out


FUNCS = {"pullback": pullback, "sweep_reclaim": sweep_reclaim, "squeeze_breakout": squeeze_breakout,
         "donchian_breakout": donchian_breakout, "range_fade": range_fade}


def params_for(name, params=None):
    if name == "breakout_retest_hold":
        return {**rules.DEFAULTS, **(params or {})}
    return {**COMMON, **DEFAULTS[name], **(params or {})}


def find(name, df, direction="both", params=None, last_only=False):
    """Všechny výskyty setupu v historii, nebo jen ten na poslední uzavřené svíčce (last_only)."""
    p = params_for(name, params)
    if name == "breakout_retest_hold":
        return rules.latest_setup(df, direction, p) if last_only else rules.find_setups(df, direction, p)
    x = Ctx(df)
    idxs = [len(df) - 1] if last_only else range(1, len(df))
    return FUNCS[name](x, p, direction, idxs)


def features(x, i, direction):
    """Režim trhu na svíčce i (x = Ctx celého df; vše počítané jen z minulosti) – pro tabulku pravděpodobností."""
    e50, e200 = x.ema(50)[i], x.ema(200)[i]
    long = direction == "long"
    if np.isnan(e200) or i < 200:
        trend = "neutral"
    elif (long and x.c[i] > e200 and e50 > e200) or (not long and x.c[i] < e200 and e50 < e200):
        trend = "with"
    elif (long and x.c[i] < e200 and e50 < e200) or (not long and x.c[i] > e200 and e50 > e200):
        trend = "against"
    else:
        trend = "neutral"
    ap = x.get("atr_pct", lambda: pd.Series(x.atr / x.c * 100))
    q = x.get("atr_q", lambda: (ap.rolling(500, min_periods=50).quantile(0.33).values,
                                 ap.rolling(500, min_periods=50).quantile(0.67).values))
    a = ap.values[i]
    vol = "high" if a > q[1][i] else "low" if a < q[0][i] else "mid"
    relv = x.v[i] / x.vavg[i] if x.vavg[i] and not np.isnan(x.vavg[i]) else 1.0
    return {"trend": trend, "vol": vol, "volume": "high" if relv >= 1.5 else "normal"}
