"""Předem stanovený test: mean reversion (RSI 2) na denních datech – po mincích, IS/OOS, náhodné vstupy, portfolio."""
import sys
from pathlib import Path
exec(open(Path(__file__).with_name("adaptive_variants.py")).read().split("base = {name")[0])
MR = {"name": "mr_1d", "setup": "mean_reversion", "timeframe": "1d",
      "params": {"rsi_len": 2, "rsi_low": 10, "rsi_high": 90, "stop_atr": 2.5, "trend_ema": 200, "min_stop_pct": 1.5,
                 "target_multiples": [1.0, 2.0]},
      "exit": {"split": 0.5, "trail_atr": 0.0, "max_hold_bars": 7}, "min_rr": 1.0, "max_open_per_direction": 2}
STRATS["mr_1d"] = MR
p = strategy_params(MR)
print("Po mincích (celá historie / IS 70 % / OOS 30 % / náhodné OOS):")
tot = {"all": [], "is": [], "oos": []}; rnd = []
for c, df in frames.items():
    cut = int(len(df) * 0.7)
    a = ev.backtest(df, p, "both", COST, 0, None, setup="mean_reversion")
    i = ev.backtest(df, p, "both", COST, 0, cut, setup="mean_reversion")
    o = ev.backtest(df, p, "both", COST, cut, None, setup="mean_reversion")
    r = ev.random_baseline(df.iloc[cut:], o, p, COST) if o else float("nan")
    tot["all"] += a; tot["is"] += i; tot["oos"] += o; rnd.append((len(o), r))
    s = lambda tr: f"{np.mean([t['r'] for t in tr]):+.3f} (n={len(tr)})" if tr else "–"
    print(f"  {c:5} {s(a):>16} {s(i):>16} {s(o):>16} {r:+.3f}")
for k, v in tot.items():
    st_ = ev.stats(v); print(f"  {k:5} n={st_['n']} Ø {st_['avg_r']:+.3f} ± {st_['ci']:.3f} DD {st_['max_dd_r']}")
w = sum(n for n, _ in rnd); print("  náhodné OOS Ø", round(sum(n * r for n, r in rnd if not np.isnan(r)) / w, 3))
longs = [t["r"] for t in tot["all"] if t["direction"] == "long"]; shorts = [t["r"] for t in tot["all"] if t["direction"] == "short"]
print(f"  long Ø {np.mean(longs):+.3f} (n={len(longs)}) · short Ø {np.mean(shorts):+.3f} (n={len(shorts)})")
# portfolio: přidá to něco k trendovým strategiím?
trend = candidates("donchian_1d", strategy_params(STRATS["donchian_1d"])) + candidates("pullback_1d", strategy_params(STRATS["pullback_1d"]))
mr = candidates("mr_1d", p)
for lab, cs in (("trend (donchian + pullback)", trend), ("jen mean reversion", mr), ("trend + mean reversion", trend + mr)):
    m = metrics(portfolio(cs))
    print(f"{lab:28} n={m['n']} Ø {m['avg_r']:+.3f} Σ {m['sum_r']:+.1f} DD {m['max_dd_r']} neg6m {m['neg_6m_pct']}% nejh6m {m['worst_6m_r']:+.1f} <2022 {m['pre2022_avg']:+.3f} ≥2022 {m['post2022_avg']:+.3f} roky {m['years']}")
tm = pd.DataFrame(portfolio(trend)).set_index("exit")["rs"].resample("ME").sum()
mm = pd.DataFrame(portfolio(mr)).set_index("exit")["rs"].resample("ME").sum()
j = pd.concat([tm, mm], axis=1).fillna(0)
print("korelace měsíčních výsledků trend × MR:", round(j.corr().iloc[0, 1], 2))
