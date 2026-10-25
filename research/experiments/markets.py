"""Stejné denní strategie na jiných trzích: krypto × měnové páry × technologické akcie (stanoveno PŘEDEM, 25. 10. 2026).

donchian_1d a pullback_1d s parametry ze scanner/config.yaml beze změny (vč. filtru paniky, okna v počtu svíček),
výstupy jako živě (polovina na T1, trailing 3 ATR, max. 20 svíček). Denní svíčky z yfinance, ~10 let.
  krypto:  BTC ETH SOL XRP ADA LINK AVAX DOGE           náklady 0,15 % na stranu
  měny:    EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURJPY   0,02 % (běžný spread hlavních párů)
  akcie:   AAPL MSFT NVDA AMZN GOOGL META TSLA AMD       0,05 % (spread + skluz, bez poplatku)
Navíc každý trh se stejnými náklady jako krypto (0,15 %) – čisté srovnání výhody strategie.
Měří se: Ø R/obchod ± CI, IS/OOS 70/30, náhodné vstupy (stejná mince, směr, stop v ATR, cíle v R), portfolio s limity
desku (max. 2 na strategii a směr, max. 3 nové za den): R za rok, max. propad R.
Pozor: akcie = dnešní vítězové (survivorship bias) – výsledek akcií je nadsazený.

    python3 research/experiments/markets.py scanner/cache
"""
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
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
LIVE = [s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")]
MARKETS = {
    "krypto": (0.15, [(f"{c}/USDT", "crypto") for c in ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]]),
    "měny": (0.02, [(f"{p}=X", "stock") for p in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY"]]),
    "akcie": (0.05, [(s, "stock") for s in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD"]]),
}


def load(sym, src):
    df = ev.load_history(sym, src, "1d", 3650, cache_dir=SP)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Open", "High", "Low", "Close"])
    return df.iloc[:-1]


def signals(frames):
    out = []
    for s in LIVE:
        rule_p, ex, min_rr = ev.split_params(strategy_params(s), s["setup"])
        for sym, df in frames.items():
            atr = st.Ctx(df).atr
            for g in st.find(s["setup"], df, "both", rule_p):
                if g.rr[0] >= min_rr:
                    out.append((s["name"], sym, g, ex, atr))
    return out


def trades(frames, sigs, cost):
    rows = []
    for name, sym, g, ex, atr in sigs:
        df, h = frames[sym], g.meta["hold_index"]
        res = ev.simulate(g, df.iloc[h + 1:], ex["max_hold_bars"], ex["split"], cost, ex["trail_atr"])
        if res["result"] == "open":
            continue
        risk = abs(g.entry - g.stop)
        rows.append({"strategy": name, "coin": sym, "time": g.hold_time, "dir": g.direction, "r": res["r"], "rr": g.rr[0],
                     "exit": df.index[min(h + res["bars"], len(df) - 1)], "stop_atr": risk / atr[h] if atr[h] else np.nan,
                     "t_r": [abs(t - g.entry) / risk for t in g.targets], "ex": ex})
    return pd.DataFrame(rows).sort_values("time").reset_index(drop=True)


def random_r(frames, t, cost, k=10, seed=7):
    rng = np.random.default_rng(seed)
    atrs = {s: st.Ctx(df).atr for s, df in frames.items()}
    rs = []
    for _, x in t.iterrows():
        df, atr, ex = frames[x["coin"]], atrs[x["coin"]], x["ex"]
        for _ in range(k):
            i = int(rng.integers(220, len(df) - 2))
            e, a = float(df["Close"].iloc[i]), atr[i]
            if not a or np.isnan(x["stop_atr"]):
                continue
            sign, risk = (1 if x["dir"] == "long" else -1), x["stop_atr"] * a
            s = {"direction": x["dir"], "entry": e, "stop": e - sign * risk,
                 "targets": [e + sign * m * risk for m in x["t_r"]], "meta": {"atr": a}}
            res = ev.simulate(s, df.iloc[i + 1:], ex["max_hold_bars"], ex["split"], cost, ex["trail_atr"])
            if res["result"] != "open":
                rs.append(res["r"])
    return float(np.mean(rs)) if rs else np.nan


def portfolio(t):
    open_, taken, per_day = [], [], {}
    for _, x in t.sort_values(["time", "rr"], ascending=[True, False]).iterrows():
        open_ = [o for o in open_ if o["exit"] > x["time"]]
        if any(o["coin"] == x["coin"] and o["strategy"] == x["strategy"] for o in open_):
            continue
        if sum(1 for o in open_ if o["strategy"] == x["strategy"] and o["dir"] == x["dir"]) >= 2:
            continue
        d = x["time"].date()
        if per_day.get(d, 0) >= 3:
            continue
        per_day[d] = per_day.get(d, 0) + 1
        open_.append(x)
        taken.append(x)
    return pd.DataFrame(taken)


def ci(x):
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan


def row(label, frames, t, cost):
    cut = t["time"].iloc[int(len(t) * 0.7)]
    is_, oos = t[t["time"] < cut]["r"], t[t["time"] >= cut]["r"]
    p = portfolio(t)
    eq = p.sort_values("exit")["r"].cumsum()
    yrs = (p["time"].max() - p["time"].min()).days / 365.25
    post = t[t["time"] >= "2022-01-01"]["r"]
    return {"trh": label, "obchodů": len(t), "Ø R ± CI": f"{t['r'].mean():+.3f} ± {ci(t['r']):.2f}",
            "IS": round(is_.mean(), 3), "OOS ± CI": f"{oos.mean():+.3f} ± {ci(oos):.2f}",
            "náhoda": round(random_r(frames, t, cost), 3), "od 2022": round(post.mean(), 3),
            "portfolio R/rok": round(p["r"].sum() / yrs, 1), "max propad R": round(float((eq.cummax().clip(lower=0) - eq).max()), 1),
            "P(zisk)": round((t["r"] > 0).mean(), 2)}


def main():
    res, detail = [], []
    for label, (cost, syms) in MARKETS.items():
        frames = {}
        for sym, src in syms:
            try:
                frames[sym] = load(sym, src)
            except Exception as exc:
                print(f"{sym}: data nedostupná ({exc.__class__.__name__})")
        print(f"{label}: {len(frames)} instrumentů, od {min(df.index[0] for df in frames.values()):%Y-%m}", flush=True)
        sigs = signals(frames)
        t = trades(frames, sigs, cost)
        res.append(row(f"{label} (náklady {cost:g} %)", frames, t, cost))
        if cost != 0.15:
            t15 = trades(frames, sigs, 0.15)
            res.append(row(f"{label} (náklady 0,15 %)", frames, t15, 0.15))
        for name in ("donchian_1d", "pullback_1d"):
            x = t[t["strategy"] == name]
            detail.append(f"  {label:7} {name:12} n={len(x):4}  Ø {x['r'].mean():+.3f} ± {ci(x['r']):.2f}")
        per = t.groupby("coin")["r"].agg(["count", "mean"]).round(2)
        detail.append(f"  {label:7} podle instrumentu: " + ", ".join(f"{k} {v['mean']:+.2f} ({int(v['count'])})" for k, v in per.iterrows()))
        yr = t.groupby(t["exit"].dt.year)["r"].sum().round(1).to_dict()
        detail.append(f"  {label:7} Σ R po letech: {yr}")
    print()
    print(pd.DataFrame(res).to_string(index=False))
    print("\n" + "\n".join(detail))


if __name__ == "__main__":
    main()
