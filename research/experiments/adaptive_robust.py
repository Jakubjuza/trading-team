"""Kontrola robustnosti V3 (sousední hodnoty, zvlášť strategie a mince) a opravená V5 (stínová equity)."""
from pathlib import Path
import sys
exec(open(Path(__file__).with_name("adaptive_variants.py")).read().split("base = {name")[0])          # načte data a funkce, bez spuštění variant
import pandas as pd, numpy as np
base = {name: candidates(name, strategy_params(s)) for name, s in STRATS.items()}
allc = base["donchian_1d"] + base["pullback_1d"]
v0 = portfolio(allc)

def rank_series(win):
    return {c: s.rolling(win, min_periods=min(200, win)).apply(lambda w: (w[-1] >= w).mean(), raw=True) for c, s in atr_pct.items()}
ranks = {w: rank_series(w) for w in (180, 365, 730)}
def calm_fn(win, top):
    return lambda t: not (at(ranks[win][t["coin"]], t["time"]) >= 1 - top)

print("V3 sousední hodnoty (okno dní × vynechat horních X % volatility):")
print(f"{'okno':>5} {'top':>4} {'n':>5} {'ØR':>7} {'ΣR':>7} {'DD':>6} {'<2022':>7} {'≥2022':>7} {'2026':>6}")
m0 = metrics(v0); print(f"{'—':>5} {'0%':>4} {m0['n']:>5} {m0['avg_r']:>+7.3f} {m0['sum_r']:>+7.1f} {m0['max_dd_r']:>6.1f} {m0['pre2022_avg']:>+7.3f} {m0['post2022_avg']:>+7.3f} {m0['years'].get(2026, 0):>+6.1f}")
for win in (180, 365, 730):
    for top in (0.1, 0.2, 0.3):
        m = metrics(portfolio(allc, accept_fn=calm_fn(win, top)))
        print(f"{win:>5} {int(top*100):>3}% {m['n']:>5} {m['avg_r']:>+7.3f} {m['sum_r']:>+7.1f} {m['max_dd_r']:>6.1f} {m['pre2022_avg']:>+7.3f} {m['post2022_avg']:>+7.3f} {m['years'].get(2026, 0):>+6.1f}")

print("\nV3 (365 d, 20 %) zvlášť strategie – Ø R obchodů s vysokou vs. normální volatilitou (všechny kandidáty, bez limitů):")
for name, cs in base.items():
    hi = [t["r"] for t in cs if at(ranks[365][t["coin"]], t["time"]) >= 0.8]
    lo = [t["r"] for t in cs if not (at(ranks[365][t["coin"]], t["time"]) >= 0.8)]
    ci = 1.96 * np.std(hi, ddof=1) / np.sqrt(len(hi))
    print(f"  {name}: vysoká vol n={len(hi)} Ø {np.mean(hi):+.3f} ± {ci:.3f} | normální n={len(lo)} Ø {np.mean(lo):+.3f}")
print("\nPo mincích (Ø R vysoká vol − normální):")
for c in COINS:
    hi = [t["r"] for t in allc if t["coin"] == c and at(ranks[365][c], t["time"]) >= 0.8]
    lo = [t["r"] for t in allc if t["coin"] == c and not (at(ranks[365][c], t["time"]) >= 0.8)]
    print(f"  {c}: {np.mean(hi) - np.mean(lo):+.3f} (n vysoká vol {len(hi)})")

# V5 opravená: rozhoduje stínová equity = obchody, které by vzal základ V0, uzavřené před signálem
v0s = sorted(v0, key=lambda o: o["exit"])
def shadow(t, closed, n=20, low=0.0):
    hist = [o for o in v0s if o["exit"] <= t["time"]][-n:]
    if len(hist) < n:
        return 1.0
    return 1.0 if sum(o["r"] for o in hist) >= 0 else low
print("\nEquity filtr se stínovou equity:")
for low, lab in ((0.0, "stop"), (0.5, "½")):
    m = metrics(portfolio(allc, size_fn=lambda t, c, low=low: shadow(t, c, low=low)))
    print(f"  {lab}: n={m['n']} Ø {m['avg_r']:+.3f} Σ {m['sum_r']:+.1f} DD {m['max_dd_r']} neg6m {m['neg_6m_pct']}% nejhorší6m {m['worst_6m_r']:+.1f} "
          f"<2022 {m['pre2022_avg']:+.3f} ≥2022 {m['post2022_avg']:+.3f} roky {m['years']}")
