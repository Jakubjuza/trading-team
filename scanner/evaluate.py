#!/usr/bin/env python3
"""Vyhodnocení skeneru: jak dopadly odeslané signály a jak by pravidla fungovala na historii.

Použití:
    python3 scanner/evaluate.py                     # signály + backtest aktuálního nastavení
    python3 scanner/evaluate.py --grid              # navíc mřížka parametrů (in-sample / out-of-sample)
    python3 scanner/evaluate.py --days 730 --out reports/scanner_review.md

Simulace obchodu (konzervativně):
  - stop se kontroluje dřív než cíle ve stejné svíčce,
  - `split` pozice na T1, zbytek na T2 (nebo trailing stop `trail_atr` × ATR po T1),
  - po T1 stop na break-even, max. `max_hold_bars` svíček, pak výstup na close,
  - náklady = (poplatek + skluz) v % na každou stranu, započtené v R.
Benchmark: stejné stopy/cíle (v ATR a R) na náhodných vstupech – strategie má smysl, jen když ho poráží.
"""
import argparse
import itertools
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import rules  # noqa: E402
from scanner.data import TF_MINUTES, YF_BASE, resample  # noqa: E402

DEFAULT_EXIT = {"split": 0.5, "trail_atr": 0.0, "max_hold_bars": 48}
DEFAULT_COSTS = {"fee_pct": 0.1, "slippage_pct": 0.05}

GRID = {
    "trend_ema": [0, 200],
    "breakout_volume_mult": [0.0, 1.5],
    "min_stop_atr": [0.5, 1.0, 1.5],
    "min_stop_pct": [0.0, 0.75, 1.5],
    "skip_weekends": [False, True],
    "target_multiples": [[1.0, 2.0], [0.5, 1.0]],
    "trail_atr": [0.0, 2.0],
    "min_rr": [1.0, 2.0],
}


# --- simulace jednoho obchodu ------------------------------------------------
def simulate(setup, after, max_hold_bars=48, split=0.5, cost_pct=0.0, trail_atr=0.0):
    """setup: dict/Setup (direction, entry, stop, targets[, meta.atr]); after: svíčky PO vstupu.

    cost_pct = poplatek + skluz v % na jednu stranu. Výsledek v R po nákladech.
    """
    s = setup if isinstance(setup, dict) else setup.to_dict()
    long = s["direction"] == "long"
    entry, stop, t1, t2 = s["entry"], s["stop"], s["targets"][0], s["targets"][1]
    risk = abs(entry - stop)
    atr = (s.get("meta") or {}).get("atr") or risk
    sign = 1 if long else -1
    cost = cost_pct / 100

    def leg(frac, exit_price):  # R z části pozice po nákladech na vstup i výstup
        return frac * (sign * (exit_price - entry) - cost * (entry + exit_price)) / risk

    hi, lo, cl = after["High"].values, after["Low"].values, after["Close"].values
    n = min(len(cl), max_hold_bars)
    got1, realized, cur_stop, rem = False, 0.0, stop, 1.0
    best = entry
    for i in range(n):
        if (lo[i] <= cur_stop) if long else (hi[i] >= cur_stop):
            return {"result": "T1+BE" if got1 else "stop", "r": round(realized + leg(rem, cur_stop), 3), "bars": i + 1,
                    "t1": got1}
        if not got1 and ((hi[i] >= t1) if long else (lo[i] <= t1)):
            got1, realized, rem, cur_stop = True, leg(split, t1), 1 - split, entry
        if got1:
            if trail_atr:
                best = max(best, cl[i]) if long else min(best, cl[i])
                trail = best - sign * trail_atr * atr
                cur_stop = max(cur_stop, trail) if long else min(cur_stop, trail)
            elif (hi[i] >= t2) if long else (lo[i] <= t2):
                return {"result": "T2", "r": round(realized + leg(rem, t2), 3), "bars": i + 1, "t1": True}
    if n == 0:
        return {"result": "open", "r": 0.0, "bars": 0, "t1": False}
    res = "time" if n >= max_hold_bars else "open"
    return {"result": res, "r": round(realized + leg(rem, cl[n - 1]), 3), "bars": n, "t1": got1}


# --- data ---------------------------------------------------------------------
def yf_symbol(symbol, source):
    return f"{symbol.split('/')[0]}-USD" if source == "crypto" else symbol


def load_history(symbol, source, tf, days, exchange="kraken", cache_dir=None):
    """Historie pro vyhodnocení. yfinance první (u krypta delší historie než Kraken API), pak ccxt."""
    cache = Path(cache_dir) / f"eval_{source}_{symbol.replace('/', '-')}_{tf}_{days}d.csv" if cache_dir else None
    if cache and cache.exists() and datetime.now().timestamp() - cache.stat().st_mtime < 6 * 3600:
        df = pd.read_csv(cache, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    df = None
    try:
        import yfinance as yf
        interval = YF_BASE[tf]
        lim = 729 if interval == "60m" else 59 if interval.endswith("m") else 3650
        df = yf.download(yf_symbol(symbol, source), period=f"{min(days, lim)}d", interval=interval,
                         progress=False, auto_adjust=False)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index = pd.to_datetime(df.index, utc=True)
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            df = resample(df, tf) if tf == "4h" else df
    except Exception as exc:
        print(f"[{symbol}] yfinance selhal ({exc.__class__.__name__})", file=sys.stderr)
    if (df is None or df.empty) and source == "crypto":
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
        except Exception as exc:
            print(f"[{symbol}] ccxt selhal ({exc.__class__.__name__})", file=sys.stderr)
            return None
    if cache is not None and df is not None and len(df):
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache)
    return df


# --- backtest -----------------------------------------------------------------
def split_params(p, setup="breakout_retest_hold"):
    """Rozdělí slovník na pravidla setupu, výstupy a min_rr."""
    from scanner import setups as st
    keys = set(rules.DEFAULTS) if setup == "breakout_retest_hold" else set(st.COMMON) | set(st.DEFAULTS[setup])
    rule_p = {k: v for k, v in p.items() if k in keys}
    exit_p = {**DEFAULT_EXIT, **{k: v for k, v in p.items() if k in DEFAULT_EXIT}}
    return rule_p, exit_p, p.get("min_rr", 2.0)


def backtest(df, params, direction, cost_pct, start=0, end=None, setup="breakout_retest_hold", with_features=False):
    """Obchody, jejichž hold svíčka leží v [start, end). Výstup může pokračovat za end."""
    from scanner import setups as st
    rule_p, exit_p, min_rr = split_params(params, setup)
    end = len(df) if end is None else end
    x = st.Ctx(df) if with_features else None
    trades, busy_until = [], -1
    for s in sorted(st.find(setup, df, direction, rule_p), key=lambda s: s.meta["hold_index"]):
        h = s.meta["hold_index"]
        if not (start <= h < end) or s.rr[0] < min_rr or h <= busy_until:
            continue  # jedna pozice na ticker naráz
        res = simulate(s, df.iloc[h + 1:], exit_p["max_hold_bars"], exit_p["split"], cost_pct, exit_p["trail_atr"])
        if res["result"] == "open":
            continue
        busy_until = h + res["bars"]
        t = {"time": s.hold_time, "direction": s.direction, "hold_index": h, "setup": setup,
             "risk_atr": abs(s.entry - s.stop) / s.meta["atr"], "rr": s.rr, **res}
        if with_features:
            t.update(st.features(x, h, s.direction))
        trades.append(t)
    return trades


def random_baseline(df, trades, params, cost_pct, k=30, seed=7):
    """Ø R náhodných vstupů se stejným rozložením stopu (v ATR), cílů (v R) a směrem."""
    if not trades:
        return float("nan")
    _, exit_p, _ = split_params(params)
    rng = np.random.default_rng(seed)
    a = rules.atr(df).values
    c = df["Close"].values
    lo_i, hi_i = 15, len(df) - exit_p["max_hold_bars"] - 1   # 15 = rozjezd ATR(14)
    if hi_i <= lo_i:
        return float("nan")
    out = []
    for t in trades:
        for j in rng.integers(lo_i, hi_i, size=k):
            sign = 1 if t["direction"] == "long" else -1
            risk = t["risk_atr"] * a[j]
            fake = {"direction": t["direction"], "entry": c[j], "stop": c[j] - sign * risk,
                    "targets": [c[j] + sign * r * risk for r in t["rr"]], "meta": {"atr": a[j]}}
            out.append(simulate(fake, df.iloc[j + 1:], exit_p["max_hold_bars"], exit_p["split"],
                                cost_pct, exit_p["trail_atr"])["r"])
    return float(np.mean(out))


def load_verdicts(path):
    if not path or not Path(path).exists():
        return {}
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            v = json.loads(line)
            out[v["signal_id"]] = v
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def verdict_groups(sigs, results, verdicts):
    """Uzavřené výsledky signálů rozdělené podle stupně verdiktu."""
    groups = {"schváleno (A/B)": [], "zamítnuto (C/NO_TRADE)": [], "bez verdiktu": []}
    for sg, res in zip(sigs, results):
        if res["result"] == "open":
            continue
        v = verdicts.get(sg["id"])
        key = "bez verdiktu" if not v else "schváleno (A/B)" if v.get("grade") in ("A", "B") else "zamítnuto (C/NO_TRADE)"
        groups[key].append(res)
    return groups


def stats(trades):
    if not trades:
        return {"n": 0, "win": 0.0, "avg_r": 0.0, "ci": 0.0, "sum_r": 0.0, "max_dd_r": 0.0}
    if all("time" in t for t in trades):           # drawdown chronologicky přes všechny tickery
        trades = sorted(trades, key=lambda t: pd.Timestamp(t["time"]))
    r = pd.Series([t["r"] for t in trades])
    eq = r.cumsum()
    ci = 1.96 * r.std(ddof=1) / math.sqrt(len(r)) if len(r) > 1 else 0.0
    return {"n": len(r), "win": float(round((r > 0).mean() * 100, 1)), "avg_r": float(round(r.mean(), 3)),
            "ci": float(round(ci, 3)), "sum_r": float(round(r.sum(), 2)), "max_dd_r": float(round((eq.cummax() - eq).max(), 2))}


def evaluate_params(hist, params, cost_pct, split_at=None, with_random=False):
    """Souhrn přes všechny tickery; split_at = podíl dat pro in-sample (zbytek out-of-sample)."""
    parts = {"all": []} if split_at is None else {"is": [], "oos": []}
    rand = {k: [] for k in parts}
    for df, d in hist.values():
        cut = len(df) if split_at is None else int(len(df) * split_at)
        ranges = {"all": (0, len(df))} if split_at is None else {"is": (0, cut), "oos": (cut, len(df))}
        for k, (a, b) in ranges.items():
            tr = backtest(df, params, d, cost_pct, a, b, setup=params.get("_setup", "breakout_retest_hold"))
            parts[k] += tr
            if with_random and tr:
                rand[k].append((len(tr), random_baseline(df.iloc[a:b] if k != "all" else df, tr, params, cost_pct)))
    res = {k: stats(v) for k, v in parts.items()}
    if with_random:
        for k, lst in rand.items():
            w = sum(n for n, _ in lst)
            res[k]["random_r"] = round(sum(n * r for n, r in lst) / w, 3) if w else float("nan")
    return res


# --- report -------------------------------------------------------------------
def current_params(cfg):
    return {**rules.DEFAULTS, **cfg["rules"], **{**DEFAULT_EXIT, **cfg.get("exit", {})}, "min_rr": cfg["min_rr"]}


def fmt_row(name, st):
    rnd = st.get("random_r")
    edge = f"{st['avg_r'] - rnd:+.3f}" if rnd is not None and not math.isnan(rnd) else "–"
    rnd_s = f"{rnd:+.3f}" if rnd is not None and not math.isnan(rnd) else "–"
    return (f"| {name} | {st['n']} | {st['win']} | {st['avg_r']:+.3f} ± {st['ci']:.3f} | {st['sum_r']:+.1f} | "
            f"{st['max_dd_r']} | {rnd_s} | {edge} |")


HDR = ["| | Obchody | Win % | Ø R (95% CI) | Σ R | Max DD (R) | Náhodné Ø R | Výhoda |",
       "|---|---|---|---|---|---|---|---|"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=HERE / "config.yaml")
    ap.add_argument("--signals", type=Path, default=HERE / "signals.jsonl")
    ap.add_argument("--verdicts", type=Path, default=HERE.parent / "research" / "verdicts.jsonl")
    ap.add_argument("--days", type=int, default=730, help="délka historie pro backtest")
    ap.add_argument("--grid", action="store_true", help="otestovat mřížku parametrů")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--cache-dir", type=Path, default=HERE / "cache")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--json-out", type=Path, help="strojově čitelný výsledek (pro naplánovanou kontrolu)")
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    costs = {**DEFAULT_COSTS, **cfg.get("costs", {})}
    cost_pct = costs["fee_pct"] + costs["slippage_pct"]
    cur = current_params(cfg)
    out = [f"# Vyhodnocení skeneru {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", "",
           f"Náklady: poplatek {costs['fee_pct']} % + skluz {costs['slippage_pct']} % na stranu "
           f"(≈ {2 * cost_pct:.2f} % ceny za celý obchod). Výsledky v R po nákladech.", ""]
    result = {"costs": costs}

    # 1) skutečné signály
    sigs = [json.loads(x) for x in args.signals.read_text().splitlines() if x.strip()] if args.signals.exists() else []
    out += [f"## Odeslané signály ({len(sigs)})", ""]
    live, evaluated = [], []
    for sg in sigs:
        df = load_history(sg["symbol"], sg["source"], sg["timeframe"], 30 if sg["timeframe"] != "1d" else 120,
                          cfg.get("exchange", "kraken"))
        if df is None:
            out.append(f"- {sg['id']}: data nedostupná")
            continue
        after = df[df.index > pd.Timestamp(sg["setup"]["hold_time"])]
        ex = {**cur, **sg.get("exit", {})}
        res = simulate(sg["setup"], after, ex["max_hold_bars"], ex["split"], cost_pct, ex["trail_atr"])
        live.append(res)
        evaluated.append(sg)
        stop_pct = abs(sg["setup"]["entry"] - sg["setup"]["stop"]) / sg["setup"]["entry"] * 100
        out.append(f"- {sg['symbol']} {sg['timeframe']} {sg['setup']['direction']} {sg['setup']['hold_time'][:16]} "
                   f"(stop {stop_pct:.2f} %): {res['result']}, {res['r']:+.2f} R za {res['bars']} svíček")
    closed = [r for r in live if r["result"] != "open"]
    result["signals"] = stats(closed)
    out += ["", f"Uzavřené: {stats(closed)}", ""]

    # 1b) přidává AI desk hodnotu? výsledek signálů podle verdiktu head-tradera
    verdicts = load_verdicts(args.verdicts)
    if verdicts:
        groups = verdict_groups(evaluated, live, verdicts)
        out += ["## Verdikty desku vs. výsledek", "",
                "| Skupina | Uzavřené obchody | Win % | Ø R | Σ R |", "|---|---|---|---|---|"]
        for name, rs in groups.items():
            st = stats(rs)
            out.append(f"| {name} | {st['n']} | {st['win']} | {st['avg_r']:+.3f} | {st['sum_r']:+.2f} |")
        out += ["", "Desk přidává hodnotu, jen když „schváleno (A/B)“ dlouhodobě vychází lépe než „zamítnuto“.", ""]
        result["verdicts"] = {k: stats(v) for k, v in groups.items()}

    # 2) historie
    hist = {}
    for t in cfg["tickers"]:
        tf = t.get("timeframe", cfg["timeframe"])
        df = load_history(t["symbol"], t["source"], tf, args.days, cfg.get("exchange", "kraken"), args.cache_dir)
        if df is not None and len(df) > 200:
            hist[t["symbol"]] = (df, t.get("direction", cfg["direction"]))
    span = ", ".join(f"{s} {len(d)} svíček" for s, (d, _) in hist.items())
    out += [f"## Backtest aktuálního nastavení ({span})", "", *HDR]
    per = {}
    for sym, h in hist.items():
        per[sym] = evaluate_params({sym: h}, cur, cost_pct, with_random=True)["all"]
        out.append(fmt_row(sym, per[sym]))
    tot = evaluate_params(hist, cur, cost_pct, split_at=0.7, with_random=True)
    allst = evaluate_params(hist, cur, cost_pct, with_random=True)["all"]
    out += [fmt_row("**celkem**", allst), fmt_row("in-sample 70 %", tot["is"]), fmt_row("out-of-sample 30 %", tot["oos"]), ""]
    result["current"] = {"all": allst, **tot, "per_ticker": per}

    # 2b) všechny zapnuté strategie (setup + časový rámec)
    from scanner.calibrate import HISTORY_DAYS, strategies, strategy_params
    out += ["## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)", "",
            "| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |", "|---|---|---|---|---|---|"]
    result["strategies"] = {}
    for strat in strategies(cfg):
        sh = {}
        for t in cfg["tickers"]:
            d = load_history(t["symbol"], t["source"], strat["timeframe"], HISTORY_DAYS.get(strat["timeframe"], 730),
                             cfg.get("exchange", "kraken"), args.cache_dir)
            if d is not None and len(d) > 300:
                sh[t["symbol"]] = (d, t.get("direction", cfg["direction"]))
        sp = {**strategy_params(strat), "_setup": strat["setup"]}
        r_all = evaluate_params(sh, sp, cost_pct)["all"]
        r_split = evaluate_params(sh, sp, cost_pct, split_at=0.7, with_random=True)
        o = r_split["oos"]
        out.append(f"| {strat['name']} | {r_all['n']} | {r_all['avg_r']:+.3f} | {r_split['is']['avg_r']:+.3f} | "
                   f"{o['avg_r']:+.3f} ± {o['ci']:.3f} | {o.get('random_r', float('nan')):+.3f} |")
        result["strategies"][strat["name"]] = {"all": r_all, **r_split}
    out.append("")

    # 3) mřížka
    if args.grid and hist:
        keys = list(GRID)
        rows = []
        for combo in itertools.product(*(GRID[k] for k in keys)):
            p = {**cur, **dict(zip(keys, combo))}
            r = evaluate_params(hist, p, cost_pct, split_at=0.7)
            rows.append((dict(zip(keys, combo)), r))
        # výběr podle in-sample (min. 30 obchodů), posouzení out-of-sample + náhodným benchmarkem
        cands = [x for x in rows if x[1]["is"]["n"] >= 30]
        cands.sort(key=lambda x: x[1]["is"]["avg_r"], reverse=True)
        out += [f"## Mřížka parametrů ({len(rows)} kombinací) – top {args.top} podle in-sample", "",
                "| # | Parametry | IS n | IS Ø R | OOS n | OOS Ø R (95% CI) | OOS win % | OOS náhodné | OOS výhoda |",
                "|---|---|---|---|---|---|---|---|---|"]
        top = []
        for i, (p, r) in enumerate(cands[:args.top], 1):
            full = evaluate_params(hist, {**cur, **p}, cost_pct, split_at=0.7, with_random=True)
            o = full["oos"]
            top.append({"params": p, "is": full["is"], "oos": o})
            short = ", ".join(f"{k}={v}" for k, v in p.items())
            out.append(f"| {i} | {short} | {full['is']['n']} | {full['is']['avg_r']:+.3f} | {o['n']} | "
                       f"{o['avg_r']:+.3f} ± {o['ci']:.3f} | {o['win']} | {o['random_r']:+.3f} | {o['avg_r'] - o['random_r']:+.3f} |")
        out.append("")
        result["grid_top"] = top

    text = "\n".join(out)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    if args.json_out:
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
