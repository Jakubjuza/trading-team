"""Předem stanovený test: denní strategie (už s filtrem paniky) jen ve směru týdenního / měsíčního trendu."""
import sys
from pathlib import Path
exec(open(Path(__file__).with_name("adaptive_variants.py")).read().split("base = {name")[0])
sys.path.insert(0, str(ROOT))
from research import scenarios as sc
base = {name: candidates(name, strategy_params(s)) for name, s in STRATS.items()}
allc = base["donchian_1d"] + base["pullback_1d"]
reg = {c: sc.regime_series(df) for c, df in frames.items()}
def aligned(kind):
    def f(t):
        r = at(reg[t["coin"]], t["time"])
        if not isinstance(r, str):
            return True
        w_up, m_up = "týden ↑" in r, "měsíc ↑" in r
        want = t["dir"] == "long"
        if kind == "week":
            return w_up == want
        if kind == "month":
            return m_up == want
        return w_up == want and m_up == want
    return f
rows = {"základ (s filtrem paniky)": portfolio(allc), "W1 ve směru týdne": portfolio(allc, accept_fn=aligned("week")),
        "W2 ve směru měsíce": portfolio(allc, accept_fn=aligned("month")), "W3 týden i měsíc": portfolio(allc, accept_fn=aligned("both"))}
print(f"{'varianta':28} {'n':>5} {'ØR':>7} {'ΣR':>7} {'DD':>6} {'neg6m%':>6} {'nejh6m':>7} {'<2022':>7} {'≥2022':>7} {'2026':>6}")
for k, tr in rows.items():
    m = metrics(tr)
    print(f"{k:28} {m['n']:>5} {m['avg_r']:>+7.3f} {m['sum_r']:>+7.1f} {m['max_dd_r']:>6.1f} {m['neg_6m_pct']:>6} {m['worst_6m_r']:>+7.1f} {m['pre2022_avg']:>+7.3f} {m['post2022_avg']:>+7.3f} {m['years'].get(2026, 0):>+6.1f}")
    print("   ", m["years"])
