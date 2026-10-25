#!/usr/bin/env python3
"""Tabulka pravděpodobností pro každou strategii skeneru – z historie, po nákladech.

Pro každou strategii (setup + časový rámec z config.yaml → strategies) projde historii všech tickerů,
nasimuluje obchody a rozdělí je podle režimu trhu v okamžiku signálu:
  trend  – with / against / neutral (cena a EMA50 vůči EMA200 ve směru obchodu)
  vol    – low / mid / high (ATR % vůči posledním 500 svíčkám)
  volume – high (≥ 1,5× průměr) / normal
Pro každou skupinu: P(T1 před stopem), P(zisk), P(≥ 2R), Ø R, 95% interval. Skupina s < min_n obchody
se nepoužije a použije se hrubší (jen trend), případně celá strategie.

Kalibrace: tabulka postavená na prvních 70 % historie predikuje P(T1) pro posledních 30 % –
report ukazuje, jestli „předpovězených 45 %“ opravdu vyšlo kolem 45 %.

Použití:
    python3 scanner/calibrate.py [--out scanner/probabilities.json] [--report reports/probabilities.md]
"""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import evaluate as ev  # noqa: E402

MIN_N = 30
HISTORY_DAYS = {"1h": 730, "4h": 730, "1d": 3650}


def strategies(cfg):
    """Seznam strategií z configu (nebo jedna výchozí ze starého formátu rules/exit/min_rr)."""
    if cfg.get("strategies"):
        return [s for s in cfg["strategies"] if s.get("enabled", True)]
    return [{"name": "breakout_retest_hold_" + cfg.get("timeframe", "1h"), "setup": "breakout_retest_hold",
             "timeframe": cfg.get("timeframe", "1h"), "params": cfg.get("rules", {}),
             "exit": cfg.get("exit", {}), "min_rr": cfg.get("min_rr", 2.0)}]


def strategy_params(strat):
    return {**strat.get("params", {}), **ev.DEFAULT_EXIT, **strat.get("exit", {}), "min_rr": strat.get("min_rr", 1.0)}


def summarize(trades):
    n = len(trades)
    if not n:
        return {"n": 0}
    r = np.array([t["r"] for t in trades])
    out = {"n": n, "avg_r": round(float(r.mean()), 3),
           "avg_r_ci": round(float(1.96 * r.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0, 3)}
    for key, vals in (("p_t1", [t["t1"] for t in trades]), ("p_win", r > 0), ("p_2r", r >= 2.0)):
        p = float(np.mean(vals))
        out[key] = round(p, 3)
        out[key + "_ci"] = round(1.96 * math.sqrt(p * (1 - p) / n), 3)
    return out


def bucket_keys(f):
    return [f"{f['trend']}|{f['vol']}|{f['volume']}", f"{f['trend']}|*|*", "*|*|*"]


def build_table(trades):
    groups = {}
    for t in trades:
        for k in bucket_keys(t):
            groups.setdefault(k, []).append(t)
    table = {k: summarize(v) for k, v in groups.items()}
    after = [t for t in trades if t["t1"]]
    table["_after_t1"] = summarize(after)
    return table


def lookup(table, feats=None, min_n=MIN_N, detail=False):
    """Statistiky pro signál. Výchozí = celá strategie (jemné skupiny kalibraci nezlepšily, viz report).
    detail=True: nejjemnější skupina s dostatkem obchodů. Vrací (statistiky, klíč) nebo (None, None)."""
    keys = bucket_keys(feats) if (detail and feats) else ["*|*|*"]
    for k in keys:
        st = table.get(k)
        if st and st.get("n", 0) >= min_n:
            return st, k
    return None, None


def collect(strat, tickers, cost_pct, exchange="kraken", cache_dir=None, split=None):
    """Obchody strategie přes všechny tickery; split=0.7 vrátí (in-sample, out-of-sample)."""
    p = strategy_params(strat)
    tf = strat["timeframe"]
    is_t, oos_t = [], []
    for t in tickers:
        df = ev.load_history(t["symbol"], t["source"], tf, HISTORY_DAYS.get(tf, 730), exchange, cache_dir)
        if df is None or len(df) < 300:
            continue
        cut = int(len(df) * split) if split else len(df)
        is_t += ev.backtest(df, p, t.get("direction", "both"), cost_pct, 0, cut, setup=strat["setup"], with_features=True)
        if split:
            oos_t += ev.backtest(df, p, t.get("direction", "both"), cost_pct, cut, None, setup=strat["setup"],
                                 with_features=True)
    return (is_t, oos_t) if split else is_t


def calibration(is_trades, oos_trades):
    table = build_table(is_trades)
    rows = []
    for t in oos_trades:
        st, _ = lookup(table, t, detail=True)
        if st:
            rows.append((st["p_t1"], float(t["t1"]), st["avg_r"], t["r"]))
    if not rows:
        return {"n": 0}
    pred, act, ev_pred, r_act = map(np.array, zip(*rows))
    bins = []
    for lo, hi in ((0, 0.35), (0.35, 0.45), (0.45, 0.55), (0.55, 1.01)):
        m = (pred >= lo) & (pred < hi)
        if m.sum():
            bins.append({"pred": f"{lo:.0%}–{min(hi, 1):.0%}", "n": int(m.sum()),
                         "pred_avg": round(float(pred[m].mean()), 3), "actual": round(float(act[m].mean()), 3)})
    return {"n": len(rows), "brier": round(float(np.mean((pred - act) ** 2)), 4),
            "brier_naive": round(float(np.mean((act.mean() - act) ** 2)), 4),
            "pred_p_t1": round(float(pred.mean()), 3), "actual_p_t1": round(float(act.mean()), 3),
            "pred_avg_r": round(float(ev_pred.mean()), 3), "actual_avg_r": round(float(r_act.mean()), 3), "bins": bins}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=HERE / "config.yaml")
    ap.add_argument("--out", type=Path, default=HERE / "probabilities.json")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--cache-dir", type=Path, default=HERE / "cache")
    a = ap.parse_args()
    cfg = yaml.safe_load(a.config.read_text(encoding="utf-8"))
    costs = {**ev.DEFAULT_COSTS, **cfg.get("costs", {})}
    cost_pct = costs["fee_pct"] + costs["slippage_pct"]
    tickers = [t for t in cfg["tickers"] if t["source"] == "crypto"]
    out = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "costs_pct_per_side": cost_pct,
           "min_n": MIN_N, "strategies": {}}
    md = [f"# Pravděpodobnosti strategií ({out['generated'][:10]})", "",
          f"Po nákladech {round(cost_pct, 3)} % na stranu. P(T1) = cena došla na T1 dřív než na stop.", ""]
    for strat in strategies(cfg):
        is_t, oos_t = collect(strat, tickers, cost_pct, cfg.get("exchange", "kraken"), a.cache_dir, split=0.7)
        table = build_table(is_t + oos_t)
        cal = calibration(is_t, oos_t)
        out["strategies"][strat["name"]] = {"table": table, "calibration": cal, "recent": summarize(oos_t),
                                            "setup": strat["setup"], "timeframe": strat["timeframe"]}
        ov = table.get("*|*|*", {})
        md += [f"## {strat['name']} ({strat['setup']}, {strat['timeframe']})", "",
               f"Celkem {ov.get('n', 0)} obchodů: P(T1) {ov.get('p_t1', 0):.0%}, P(zisk) {ov.get('p_win', 0):.0%}, "
               f"P(≥2R) {ov.get('p_2r', 0):.0%}, Ø {ov.get('avg_r', 0):+.2f} R ± {ov.get('avg_r_ci', 0):.2f}", "",
               f"Kalibrace na posledních 30 % (n={cal.get('n', 0)}): předpověď P(T1) {cal.get('pred_p_t1', 0):.0%} → "
               f"skutečnost {cal.get('actual_p_t1', 0):.0%}; Ø R předpověď {cal.get('pred_avg_r', 0):+.2f} → "
               f"skutečnost {cal.get('actual_avg_r', 0):+.2f}; Brier {cal.get('brier', 0)} (bez modelu {cal.get('brier_naive', 0)})", "",
               "| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |", "|---|---|---|---|"]
        md += [f"| {b['pred']} | {b['n']} | {b['pred_avg']:.0%} | {b['actual']:.0%} |" for b in cal.get("bins", [])]
        md += ["", "| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |", "|---|---|---|---|---|"]
        for k, st in sorted(table.items(), key=lambda kv: -kv[1].get("n", 0)):
            if k.startswith("_") or st.get("n", 0) < MIN_N or k.endswith("|*|*"):
                continue
            md.append(f"| {k.replace('|', ' · ')} | {st['n']} | {st['p_t1']:.0%} | {st['p_win']:.0%} | {st['avg_r']:+.2f} |")
        md.append("")
        print("\n".join(md[-12:]))
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"OK: {a.out}")


if __name__ == "__main__":
    main()
