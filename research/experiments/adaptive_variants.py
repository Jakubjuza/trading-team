"""Test přizpůsobení strategií trhu – denní Donchian + pullback, 8 mincí, ~10 let, náklady 0,15 %/stranu.

Varianty jsou stanovené PŘEDEM se standardními hodnotami (žádné ladění na těchto datech):
  V0 základ        – jak běží teď (limity portfolia: max 2 otevřené na strategii a směr, max 3 nové za den)
  V1 BTC režim     – long jen když BTC > EMA200, short jen když BTC < EMA200
  V2 ADX ≥ 20      – jen když je mince v trendu (ADX14 ≥ 20)
  V3 bez paniky    – vynechat, když je ATR % mince v horních 20 % za poslední rok
  V4 equity ½      – poloviční velikost, když posledních 20 uzavřených obchodů portfolia je v součtu ve ztrátě
  V5 equity stop   – jako V4, ale místo poloviny vůbec neobchodovat
  V6 rotace        – V4 zvlášť pro každou strategii
  V7 walk-forward  – každých 6 měsíců vybrat parametry z mřížky podle předchozích 24 měsíců
  V8 V1 + V4       – kombinace (stanovená předem)
Vše kauzálně: filtr vidí jen data do okamžiku signálu, equity jen obchody uzavřené před signálem.
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, setups as st  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COST = 0.15
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
STRATS = {s["name"]: s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")}

frames = {}
for c in COINS:
    df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_1d_3650d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    frames[c] = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

btc = frames["BTC"]
btc_ema200 = st.ema(btc["Close"], 200)
ctxs = {c: st.Ctx(df) for c, df in frames.items()}
atr_pct = {c: pd.Series(ctxs[c].atr / frames[c]["Close"].values, index=frames[c].index) for c in COINS}
atr_rank = {c: s.rolling(365, min_periods=200).apply(lambda w: (w[-1] >= w).mean(), raw=True) for c, s in atr_pct.items()}
adx = {c: pd.Series(ctxs[c].adx(14), index=frames[c].index) for c in COINS}


def candidates(strat_name, params):
    setup = STRATS[strat_name]["setup"]
    rule_p, exit_p, min_rr = ev.split_params(params, setup)
    out = []
    for c, df in frames.items():
        for s in st.find(setup, df, "both", rule_p):
            h = s.meta["hold_index"]
            if s.rr[0] < min_rr:
                continue
            res = ev.simulate(s, df.iloc[h + 1:], exit_p["max_hold_bars"], exit_p["split"], COST, exit_p["trail_atr"])
            if res["result"] == "open":
                continue
            out.append({"coin": c, "strategy": strat_name, "time": s.hold_time, "dir": s.direction, "r": res["r"],
                        "rr": s.rr[0], "exit": df.index[min(h + res["bars"], len(df) - 1)]})
    return out


def portfolio(cands, size_fn=None, accept_fn=None):
    """Chronologicky: limity jako v živém skeneru. size_fn/accept_fn vidí jen minulost."""
    cands = sorted(cands, key=lambda t: (t["time"], -t["rr"]))
    open_, closed, taken, per_day = [], [], [], {}
    for t in cands:
        now = t["time"]
        still = []
        for o in open_:
            (closed if o["exit"] <= now else still).append(o)
        open_ = still
        closed.sort(key=lambda o: o["exit"])
        if any(o["coin"] == t["coin"] and o["strategy"] == t["strategy"] for o in open_):
            continue
        if sum(1 for o in open_ if o["strategy"] == t["strategy"] and o["dir"] == t["dir"]) >= 2:
            continue
        d = now.date()
        if per_day.get(d, 0) >= 3:
            continue
        if accept_fn and not accept_fn(t):
            continue
        size = size_fn(t, closed) if size_fn else 1.0
        if size <= 0:
            continue
        per_day[d] = per_day.get(d, 0) + 1
        x = {**t, "size": size, "rs": t["r"] * size}
        open_.append(x)
        taken.append(x)
    return taken


def at(series, ts):
    i = series.index.searchsorted(ts, side="right") - 1
    return series.iloc[i] if i >= 0 else np.nan


def btc_regime(t):
    up = at(btc["Close"], t["time"]) > at(btc_ema200, t["time"])
    return up if t["dir"] == "long" else not up


def adx_ok(t):
    return at(adx[t["coin"]], t["time"]) >= 20


def calm(t):
    r = at(atr_rank[t["coin"]], t["time"])
    return not (r >= 0.8)


def equity_size(t, closed, n=20, low=0.5, per_strategy=False):
    hist = [o for o in closed if (not per_strategy or o["strategy"] == t["strategy"])][-n:]
    if len(hist) < n:
        return 1.0
    return 1.0 if sum(o["rs"] for o in hist) >= 0 else low


def metrics(trades):
    if not trades:
        return {}
    df = pd.DataFrame(trades).sort_values("exit")
    eq = df.set_index("exit")["rs"].cumsum()
    dd = float((eq.cummax() - eq).max())
    yr = df.groupby(df["exit"].dt.year)["rs"].sum()
    m = df.set_index("exit")["rs"].resample("ME").sum()
    roll6 = m.rolling(6).sum().dropna()
    pre = df[df["exit"] < "2022-01-01"]["rs"]
    post = df[df["exit"] >= "2022-01-01"]["rs"]
    return {"n": len(df), "avg_r": round(df["rs"].mean(), 3), "sum_r": round(df["rs"].sum(), 1), "max_dd_r": round(dd, 1),
            "neg_6m_pct": round((roll6 < 0).mean() * 100), "worst_6m_r": round(roll6.min(), 1),
            "pre2022_avg": round(pre.mean(), 3), "post2022_avg": round(post.mean(), 3),
            "neg_years": int((yr < 0).sum()), "years": {int(k): round(v, 1) for k, v in yr.items()},
            "y2022": round(yr.get(2022, 0), 1), "last_5m": round(df[df["exit"] >= "2026-06-01"]["rs"].sum(), 1)}


base = {name: candidates(name, strategy_params(s)) for name, s in STRATS.items()}
allc = base["donchian_1d"] + base["pullback_1d"]

res = {}
res["V0 základ"] = metrics(portfolio(allc))
res["V1 BTC režim"] = metrics(portfolio(allc, accept_fn=btc_regime))
res["V2 ADX ≥ 20"] = metrics(portfolio(allc, accept_fn=adx_ok))
res["V3 bez paniky"] = metrics(portfolio(allc, accept_fn=calm))
res["V4 equity ½"] = metrics(portfolio(allc, size_fn=equity_size))
res["V5 equity stop"] = metrics(portfolio(allc, size_fn=lambda t, c: equity_size(t, c, low=0.0)))
res["V6 rotace"] = metrics(portfolio(allc, size_fn=lambda t, c: equity_size(t, c, per_strategy=True)))

# V7 walk-forward: mřížka parametrů, výběr podle předchozích 24 měsíců (jen obchody uzavřené před oknem)
grids = {
    "donchian_1d": [{"channel": ch, "stop_atr": sa} for ch, sa in itertools.product([10, 20, 55], [1.5, 2.0, 3.0])],
    "pullback_1d": [{"lookback": lb, "ema_fast": ef} for lb, ef in itertools.product([2, 3, 5], [10, 20, 30])],
}
grid_c = {}
for name, grid in grids.items():
    for g in grid:
        s = STRATS[name]
        p = strategy_params({**s, "params": {**s["params"], **g}})
        grid_c[(name, json.dumps(g, sort_keys=True))] = candidates(name, p)
wf, choices = [], []
starts = pd.date_range("2019-01-01", "2026-07-01", freq="6MS", tz="UTC")
for i, w0 in enumerate(starts):
    w1 = starts[i + 1] if i + 1 < len(starts) else pd.Timestamp("2027-01-01", tz="UTC")
    for name in grids:
        best, best_score = None, -9
        for (n2, key), cs in grid_c.items():
            if n2 != name:
                continue
            past = [t["r"] for t in cs if w0 - pd.DateOffset(months=24) <= t["time"] and t["exit"] < w0]
            if len(past) >= 30 and np.mean(past) > best_score:
                best, best_score = key, np.mean(past)
        default = {"donchian_1d": {"channel": 20, "stop_atr": 2.0}, "pullback_1d": {"lookback": 3, "ema_fast": 20}}[name]
        key = best or json.dumps(default, sort_keys=True)
        choices.append((str(w0.date()), name, key))
        wf += [t for t in grid_c[(name, key)] if w0 <= t["time"] < w1]
pre2019 = [t for t in allc if t["time"] < starts[0]]
res["V7 walk-forward"] = metrics(portfolio(pre2019 + wf))
res["V8 BTC režim + equity ½"] = metrics(portfolio(allc, size_fn=equity_size, accept_fn=btc_regime))

out = {"variants": res, "wf_choices": choices}
(SP / "adaptive_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
print(f"{'varianta':26} {'n':>5} {'ØR':>7} {'ΣR':>7} {'maxDD':>6} {'neg6m%':>6} {'nejhorší6m':>10} {'<2022':>7} {'≥2022':>7} {'ztr.roky':>8} {'2022':>6} {'VI-X 2026':>9}")
for k, m in res.items():
    print(f"{k:26} {m['n']:>5} {m['avg_r']:>+7.3f} {m['sum_r']:>+7.1f} {m['max_dd_r']:>6.1f} {m['neg_6m_pct']:>6} {m['worst_6m_r']:>+10.1f} "
          f"{m['pre2022_avg']:>+7.3f} {m['post2022_avg']:>+7.3f} {m['neg_years']:>8} {m['y2022']:>+6.1f} {m['last_5m']:>+9.1f}")
print()
for k, m in res.items():
    print(k, m["years"])
print()
print("walk-forward volby:", choices[-6:])
