#!/usr/bin/env python3
"""Vyhodnocení skeneru: jak dopadly odeslané signály a jak by pravidla fungovala na historii.

Použití:
    python3 scanner/evaluate.py                     # signály ze signals.jsonl + backtest aktuálních pravidel
    python3 scanner/evaluate.py --grid              # navíc mřížka parametrů (in-sample / out-of-sample)
    python3 scanner/evaluate.py --out reports/scanner_review.md

Simulace obchodu (konzervativně): stop se kontroluje dřív než cíle ve stejné svíčce,
50 % pozice na T1, zbytek na T2, po T1 stop na break-even, max. `max_hold_bars` svíček,
pak výstup na close. Výsledek v R (bez poplatků).
"""
import argparse
import itertools
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import rules  # noqa: E402
from scanner.data import TF_MINUTES, YF_BASE, resample  # noqa: E402

GRID = {
    "tolerance_pct": [0.2, 0.3, 0.5],
    "retest_window": [3, 6, 10],
    "min_stop_atr": [0.5, 1.0],
    "target_multiples": [[1.0, 2.0], [0.5, 1.0]],
}


def simulate(setup, after, max_hold_bars=48, split=0.5):
    """setup: dict (Setup.to_dict) nebo Setup; after: svíčky PO hold svíčce."""
    s = setup if isinstance(setup, dict) else setup.to_dict()
    long = s["direction"] == "long"
    entry, stop, t1, t2 = s["entry"], s["stop"], s["targets"][0], s["targets"][1]
    risk = abs(entry - stop)
    r_of = (lambda p: (p - entry) / risk) if long else (lambda p: (entry - p) / risk)
    got1, realized, cur_stop = False, 0.0, stop
    for i, (_, c) in enumerate(after.head(max_hold_bars).iterrows()):
        hit_stop = c["Low"] <= cur_stop if long else c["High"] >= cur_stop
        if hit_stop:
            rem = (1 - split) if got1 else 1.0
            return {"result": "T1+BE" if got1 else "stop", "r": round(realized + rem * r_of(cur_stop), 3), "bars": i + 1}
        if not got1 and (c["High"] >= t1 if long else c["Low"] <= t1):
            got1, realized, cur_stop = True, split * r_of(t1), entry
        if got1 and (c["High"] >= t2 if long else c["Low"] <= t2):
            return {"result": "T2", "r": round(realized + (1 - split) * r_of(t2), 3), "bars": i + 1}
    n = min(len(after), max_hold_bars)
    if n == 0:
        return {"result": "open", "r": 0.0, "bars": 0}
    last = after["Close"].iloc[n - 1]
    rem = (1 - split) if got1 else 1.0
    res = "time" if n >= max_hold_bars else "open"
    return {"result": res, "r": round(realized + rem * r_of(last), 3), "bars": n}


def yf_symbol(symbol, source):
    if source == "crypto":
        base = symbol.split("/")[0]
        return f"{base}-USD"
    return symbol


def load_history(symbol, source, tf, days, exchange="kraken"):
    """Historie pro vyhodnocení: ccxt (krypto), při chybě yfinance."""
    if source == "crypto":
        try:
            import ccxt
            ex = getattr(ccxt, exchange)({"enableRateLimit": True})
            since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
            rows, step = [], TF_MINUTES[tf] * 60_000
            while True:
                batch = ex.fetch_ohlcv(symbol, timeframe=tf, since=since, limit=720)
                if not batch:
                    break
                rows += batch
                since = batch[-1][0] + step
                if len(batch) < 2 or since > datetime.now(timezone.utc).timestamp() * 1000:
                    break
            df = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("ts")
            df.index = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
            if len(df):
                return df
        except Exception as exc:
            print(f"[{symbol}] ccxt nedostupné ({exc.__class__.__name__}), zkouším yfinance", file=sys.stderr)
    import yfinance as yf
    interval = YF_BASE[tf]
    period = f"{min(days, 729 if interval == '60m' else 59 if interval.endswith('m') else 3650)}d"
    df = yf.download(yf_symbol(symbol, source), period=period, interval=interval, progress=False, auto_adjust=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return resample(df, tf) if tf == "4h" else df


def backtest(df, params, direction, min_rr, max_hold_bars):
    trades = []
    for s in rules.find_setups(df, direction, params):
        if s.rr[0] < min_rr:
            continue
        h = s.meta["hold_index"]
        res = simulate(s, df.iloc[h + 1:], max_hold_bars)
        if res["result"] != "open":
            trades.append({"time": s.hold_time, "direction": s.direction, **res})
    return trades


def stats(trades):
    if not trades:
        return {"n": 0, "win": 0.0, "avg_r": 0.0, "sum_r": 0.0, "max_dd_r": 0.0}
    r = pd.Series([t["r"] for t in trades])
    eq = r.cumsum()
    return {"n": len(r), "win": round((r > 0).mean() * 100, 1), "avg_r": round(r.mean(), 3),
            "sum_r": round(r.sum(), 2), "max_dd_r": round((eq.cummax() - eq).max(), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=HERE / "config.yaml")
    ap.add_argument("--signals", type=Path, default=HERE / "signals.jsonl")
    ap.add_argument("--days", type=int, default=180, help="délka historie pro backtest")
    ap.add_argument("--grid", action="store_true", help="otestovat mřížku parametrů")
    ap.add_argument("--max-hold", type=int, default=48)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    out = [f"# Vyhodnocení skeneru {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", ""]

    # 1) skutečné signály
    sigs = [json.loads(line) for line in args.signals.read_text().splitlines() if line.strip()] if args.signals.exists() else []
    out += [f"## Odeslané signály ({len(sigs)})", ""]
    live = []
    for sg in sigs:
        df = load_history(sg["symbol"], sg["source"], sg["timeframe"], 30, cfg.get("exchange", "kraken"))
        if df is None:
            out.append(f"- {sg['id']}: data nedostupná")
            continue
        after = df[df.index > pd.Timestamp(sg["setup"]["hold_time"])]
        res = simulate(sg["setup"], after, args.max_hold)
        live.append(res)
        out.append(f"- {sg['symbol']} {sg['timeframe']} {sg['setup']['direction']} {sg['setup']['hold_time'][:16]}: "
                   f"{res['result']}, {res['r']:+.2f} R za {res['bars']} svíček")
    closed = [r for r in live if r["result"] != "open"]
    out += ["", f"Uzavřené: {stats(closed)}", ""]

    # 2) backtest aktuálních pravidel (+ mřížka)
    hist = {}
    for t in cfg["tickers"]:
        tf = t.get("timeframe", cfg["timeframe"])
        df = load_history(t["symbol"], t["source"], tf, args.days, cfg.get("exchange", "kraken"))
        if df is not None and len(df) > 100:
            hist[t["symbol"]] = (df, t.get("direction", cfg["direction"]))
    out += [f"## Backtest aktuálních pravidel ({args.days} dní, {', '.join(hist)})", "",
            "| Ticker | Obchody | Win % | Ø R | Σ R | Max DD (R) |", "|---|---|---|---|---|---|"]
    allt = []
    for sym, (df, d) in hist.items():
        tr = backtest(df, cfg["rules"], d, cfg["min_rr"], args.max_hold)
        allt += tr
        st = stats(tr)
        out.append(f"| {sym} | {st['n']} | {st['win']} | {st['avg_r']} | {st['sum_r']} | {st['max_dd_r']} |")
    st = stats(allt)
    out += [f"| **celkem** | {st['n']} | {st['win']} | {st['avg_r']} | {st['sum_r']} | {st['max_dd_r']} |", ""]

    if args.grid and hist:
        out += ["## Mřížka parametrů (in-sample = prvních 70 %, out-of-sample = posledních 30 %)", "",
                "| Parametry | IS n | IS Ø R | OOS n | OOS Ø R | OOS win % |", "|---|---|---|---|---|---|"]
        rows = []
        keys = list(GRID)
        for combo in itertools.product(*(GRID[k] for k in keys)):
            p = {**cfg["rules"], **dict(zip(keys, combo))}
            is_t, oos_t = [], []
            for df, d in hist.values():
                cut = int(len(df) * 0.7)
                is_t += backtest(df.iloc[:cut], p, d, cfg["min_rr"], args.max_hold)
                oos_t += backtest(df.iloc[cut - p["range_lookback"]:], p, d, cfg["min_rr"], args.max_hold)
            rows.append((dict(zip(keys, combo)), stats(is_t), stats(oos_t)))
        rows.sort(key=lambda x: x[1]["avg_r"], reverse=True)
        for p, a, b in rows[:15]:
            out.append(f"| {p} | {a['n']} | {a['avg_r']} | {b['n']} | {b['avg_r']} | {b['win']} |")
        out.append("")

    text = "\n".join(out)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
