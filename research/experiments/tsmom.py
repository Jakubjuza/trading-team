"""Předem stanovená klasika: každá mince rovným dílem, ale jen když je týdenní close nad SMA 200 dní, jinak hotovost."""
import sys
from pathlib import Path
exec(open(Path(__file__).with_name("rotation.py")).read().split('print("Benchmarky')[0])
SMA = P.rolling(200, min_periods=200).mean()
def run_ts():
    w_old, rets, dates = pd.Series(0.0, index=COINS), [], []
    for t0, t1 in zip(reb[:-1], reb[1:]):
        p0, p1 = P.loc[t0], P.loc[t1]
        elig = p0.notna() & p1.notna() & SMA.loc[t0].notna()
        if elig.sum() == 0:
            continue
        w = pd.Series(0.0, index=COINS)
        on = elig & (p0 > SMA.loc[t0])
        w[on] = 1.0 / elig.sum()                         # slot mince pod SMA = hotovost
        turnover = (w - w_old).abs().sum()
        r = float((w * (p1 / p0 - 1)).fillna(0).sum()) - turnover * COST
        grow = (w * (p1 / p0)).fillna(0)
        w_old = grow / (grow.sum() + (1 - w.sum()))
        rets.append(r); dates.append(t1)
    return pd.Series(rets, index=dates)
def summary(s):
    e = (1 + s).cumprod(); yr = (1 + s).groupby(s.index.year).prod() - 1
    cagr = lambda x: ((1 + x).prod() ** (52 / len(x)) - 1) * 100
    roll26 = (1 + s).rolling(26).apply(np.prod, raw=True) - 1
    return {"CAGR %": round(cagr(s), 1), "maxDD %": round(float((e / e.cummax() - 1).min()) * 100, 1), "Sharpe": round(s.mean() / s.std() * np.sqrt(52), 2),
            "nejhorších 26 t %": round(float(roll26.min()) * 100, 1), "CAGR <2022": round(cagr(s[s.index < "2022-01-01"]), 1),
            "CAGR ≥2022": round(cagr(s[s.index >= "2022-01-01"]), 1), "roky": {int(k): round(v * 100) for k, v in yr.items()}}
ts = run_ts()
print("trendový filtr SMA200:", summary(ts))
# stejné období pro benchmark rovným dílem
ew = []
for t0, t1 in zip(reb[:-1], reb[1:]):
    if t1 < ts.index[0] or t1 > ts.index[-1]:
        continue
    p0, p1 = P.loc[t0], P.loc[t1]; elig = p0.notna() & p1.notna() & SMA.loc[t0].notna()
    ew.append((t1, float(((p1 / p0 - 1)[elig]).mean())))
ew = pd.Series(dict(ew))
print("rovným dílem (stejné období):", summary(ew))
print("podíl týdnů v hotovosti (celý fond):", round(float((ts == 0).mean()) * 100), "%")
