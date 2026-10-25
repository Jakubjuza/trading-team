"""Předem stanovený test: rotace dual momentum (long-only spot, hotovost když nic neroste).
Hlavní nastavení: lookback 28 dní, top 3, týdenní přeskupení (neděle close), náklady 0,15 % na stranu z obratu.
Robustnost: lookback 14/28/56/84 × top 2/3/4. Benchmarky: držet BTC, všechny mince rovným dílem."""
import sys
import numpy as np, pandas as pd
SP = sys.argv[1] if len(sys.argv) > 1 else "scanner/cache"
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
P = pd.concat({c: pd.read_csv(f"{SP}/eval_crypto_{c}-USDT_1d_3650d.csv", index_col=0, parse_dates=True)["Close"] for c in COINS}, axis=1)
P.index = pd.to_datetime(P.index, utc=True)
P = P[P.index < "2026-10-25"]
COST = 0.0015
reb = P.index[P.index.dayofweek == 6]                     # neděle

def run(L=28, K=3, abs_filter=True, mode="rot"):
    eq, w_old, rets, dates = 1.0, pd.Series(0.0, index=COINS), [], []
    for t0, t1 in zip(reb[:-1], reb[1:]):
        if t0 < P.index[0] + pd.Timedelta(days=L + 1):
            continue
        p0, p1 = P.loc[t0], P.loc[t1]
        past = P.loc[t0 - pd.Timedelta(days=L)] if (t0 - pd.Timedelta(days=L)) in P.index else None
        if past is None:
            continue
        elig = p0.notna() & past.notna() & p1.notna()
        w = pd.Series(0.0, index=COINS)
        if mode == "btc":
            w["BTC"] = 1.0
        elif mode == "ew":
            w[elig] = 1.0 / elig.sum()
        else:
            mom = (p0 / past - 1)[elig].sort_values(ascending=False)
            pick = [c for c in mom.index[:K] if (mom[c] > 0 or not abs_filter)]
            for c in pick:
                w[c] = 1.0 / K                             # neobsazený slot = hotovost
        turnover = (w - w_old).abs().sum()
        r = float((w * (p1 / p0 - 1)).fillna(0).sum()) - turnover * COST
        eq *= 1 + r
        grow = (w * (p1 / p0)).fillna(0)
        w_old = grow / (grow.sum() + (1 - w.sum())) if (grow.sum() + (1 - w.sum())) > 0 else w * 0
        rets.append(r); dates.append(t1)
    s = pd.Series(rets, index=dates)
    e = (1 + s).cumprod()
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    yr = (1 + s).groupby(s.index.year).prod() - 1
    pre, post = s[s.index < "2022-01-01"], s[s.index >= "2022-01-01"]
    cagr = lambda x: ((1 + x).prod() ** (52 / len(x)) - 1) * 100 if len(x) else np.nan
    roll26 = (1 + s).rolling(26).apply(np.prod, raw=True) - 1
    return {"CAGR %": round(cagr(s), 1), "maxDD %": round(float((e / e.cummax() - 1).min()) * 100, 1),
            "Sharpe": round(s.mean() / s.std() * np.sqrt(52), 2), "ztrátové roky": int((yr < 0).sum()), "roků": len(yr),
            "nejhorších 26 t %": round(float(roll26.min()) * 100, 1), "CAGR <2022": round(cagr(pre), 1), "CAGR ≥2022": round(cagr(post), 1),
            "v hotovosti %": None, "roky": {int(k): round(v * 100) for k, v in yr.items()}}

print("Benchmarky a hlavní nastavení (stejné období):")
for lab, kw in (("držet BTC", {"mode": "btc"}), ("všechny mince rovným dílem", {"mode": "ew"}),
                ("ROTACE 28 d, top 3, s filtrem", {}), ("rotace bez filtru (vždy investováno)", {"abs_filter": False})):
    m = run(**kw); yrs = m.pop("roky")
    print(f"  {lab:38}", {k: v for k, v in m.items() if v is not None}); print("     roky:", yrs)
print("\nRobustnost (CAGR % / maxDD % / Sharpe / CAGR ≥2022):")
for L in (14, 28, 56, 84):
    row = []
    for K in (2, 3, 4):
        m = run(L, K)
        row.append(f"top{K}: {m['CAGR %']:>6} / {m['maxDD %']:>6} / {m['Sharpe']:>4} / {m['CAGR ≥2022']:>6}")
    print(f"  L={L:>2}  " + "  |  ".join(row))
