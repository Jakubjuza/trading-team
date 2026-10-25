import sys
from pathlib import Path
exec(open(Path(__file__).with_name("adaptive_variants.py")).read().split("base = {name")[0])
base = {name: candidates(name, strategy_params(s)) for name, s in STRATS.items()}
allc = base["donchian_1d"] + base["pullback_1d"]
def wk_up_series(df, n):
    w = df["Close"].resample("W-SUN", label="right", closed="right").last().dropna()
    e = w.ewm(span=n, adjust=False).mean()
    up = (w > e).where(np.arange(len(w)) >= n)
    up.index = up.index + pd.Timedelta(days=1)
    return up.reindex(df.index, method="ffill")
print(f"{'EMA týdnů':>9} {'n':>5} {'ØR':>7} {'ΣR':>7} {'DD':>6} {'nejh6m':>7} {'<2022':>7} {'≥2022':>7} {'2026':>6}")
m = metrics(portfolio(allc)); print(f"{'bez':>9} {m['n']:>5} {m['avg_r']:>+7.3f} {m['sum_r']:>+7.1f} {m['max_dd_r']:>6.1f} {m['worst_6m_r']:>+7.1f} {m['pre2022_avg']:>+7.3f} {m['post2022_avg']:>+7.3f} {m['years'].get(2026,0):>+6.1f}")
for n in (10, 15, 21, 30, 40):
    ups = {c: wk_up_series(df, n) for c, df in frames.items()}
    def f(t, ups=ups):
        u = at(ups[t["coin"]], t["time"])
        return True if pd.isna(u) else bool(u) == (t["dir"] == "long")
    m = metrics(portfolio(allc, accept_fn=f))
    print(f"{n:>9} {m['n']:>5} {m['avg_r']:>+7.3f} {m['sum_r']:>+7.1f} {m['max_dd_r']:>6.1f} {m['worst_6m_r']:>+7.1f} {m['pre2022_avg']:>+7.3f} {m['post2022_avg']:>+7.3f} {m['years'].get(2026,0):>+6.1f}")
ups = {c: wk_up_series(df, 21) for c, df in frames.items()}
print("\nPo strategiích (všichni kandidáti, bez limitů portfolia) – Ø R ve směru týdne vs. proti:")
for name, cs in base.items():
    w = [t["r"] for t in cs if not pd.isna(at(ups[t["coin"]], t["time"])) and bool(at(ups[t["coin"]], t["time"])) == (t["dir"] == "long")]
    a = [t["r"] for t in cs if not pd.isna(at(ups[t["coin"]], t["time"])) and bool(at(ups[t["coin"]], t["time"])) != (t["dir"] == "long")]
    print(f"  {name}: ve směru n={len(w)} Ø {np.mean(w):+.3f} | proti n={len(a)} Ø {np.mean(a):+.3f} ± {1.96*np.std(a, ddof=1)/np.sqrt(len(a)):.3f}")
print("\nPo mincích (Ø R ve směru − proti):")
for c in COINS:
    w = [t["r"] for t in allc if t["coin"] == c and not pd.isna(at(ups[c], t["time"])) and bool(at(ups[c], t["time"])) == (t["dir"] == "long")]
    a = [t["r"] for t in allc if t["coin"] == c and not pd.isna(at(ups[c], t["time"])) and bool(at(ups[c], t["time"])) != (t["dir"] == "long")]
    print(f"  {c}: {np.mean(w) - np.mean(a):+.3f} (proti n={len(a)})")
