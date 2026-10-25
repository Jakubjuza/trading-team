"""Vstup pro denní signály: H4 (sweep & reclaim na 1H) a M15 (spouštěč o patro níž) – předem stanovený test.

Signál a směr vždy z denního grafu (donchian_1d, pullback_1d dle config.yaml, s filtrem paniky). Okno 72 h po
uzavření denní svíčky; nesplněno = obchod se neotevře (0 R). Všechny varianty se vyhodnocují na STEJNÝCH 15M
svíčkách z OKX (spot, USDT), cíle T1/T2 z denního signálu, polovina na T1, zbytek trailing 3 denní ATR, max. 20 dní.
  A    vstup na zavření denní svíčky, stop ze signálu
  C    dnešní vstup (scanner/mtf.py): 4H close vs EMA20 → 1H dotek EMA20 → 1H obratová svíčka; stop za swingem 6 svíček
  H4   sweep & reclaim na 1H (hypotéza H4, video „timeframe ladder“): 1H svíčka propíchne minimum (long) / maximum
       (short) posledních 12 hodin a nejpozději do 2 dalších hodin zavře zpět nad (pod) tou úrovní → vstup na zavření;
       stop za knotem sweepu − 0,1 denního ATR; bez 4H filtru
  M15  pravidlo C o patro níž: 1H close vs EMA20 → 15M dotek EMA20 → 15M obratová svíčka; stop za swingem 6 svíček
Společné: stop min. 1,5 % od vstupu a nikdy širší než denní stop; vstup za T1 se nebere; zásah denního stopu před
spouštěčem = signál propadá. Náklady 0,15 % na stranu.

    python3 research/experiments/mtf15.py [cache_dir]      # stahuje 15M z OKX (běží v GitHub Actions)
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, mtf, setups as st  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COST = 0.15
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
WAIT_H = 72
DAYS = 730
OHLC = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
STRATS = [s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")]


def okx_15m(coin, days=DAYS):
    """15M svíčky z OKX (veřejná data, bez klíče), cache v CSV."""
    path = SP / f"okx_{coin}_15m_{days}d.csv"
    if path.exists() and time.time() - path.stat().st_mtime < 12 * 3600:
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    import ccxt
    ex = ccxt.okx({"enableRateLimit": True})
    step = 15 * 60_000
    since = int(datetime.now(timezone.utc).timestamp() * 1000) - days * 86_400_000
    rows, end = [], int(datetime.now(timezone.utc).timestamp() * 1000)
    while since < end:
        batch = ex.fetch_ohlcv(f"{coin}/USDT", "15m", since=since, limit=100)
        if not batch:
            since += 100 * step                                  # díra v datech – posun dál
            continue
        rows += batch
        nxt = batch[-1][0] + step
        if nxt <= since:
            break
        since = nxt
    df = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("ts")
    df.index = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
    df = df.sort_index()[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    df = df[df.index < pd.Timestamp.now(tz="UTC").floor("15min")]          # jen uzavřené
    SP.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def sweep_trigger(direction, h1, t0, daily_stop, targets, atr, wait_hours=WAIT_H, lookback=12, reclaim_bars=2,
                  min_stop_pct=1.5):
    long = direction == "long"
    win = h1[(h1.index >= t0) & (h1.index < t0 + pd.Timedelta(hours=wait_hours))]
    pos = {t: k for k, t in enumerate(h1.index)}
    for t, row in win.iterrows():
        if (long and row["Low"] <= daily_stop) or (not long and row["High"] >= daily_stop):
            return {"status": "stopped", "time": t}
        k = pos[t]
        if k < lookback:
            continue
        prior = h1.iloc[k - lookback:k]
        level = prior["Low"].min() if long else prior["High"].max()
        if not ((long and row["Low"] < level) or (not long and row["High"] > level)):
            continue
        for j in range(k, min(k + reclaim_bars + 1, len(h1))):
            b = h1.iloc[j]
            if (long and b["Low"] <= daily_stop) or (not long and b["High"] >= daily_stop):
                return {"status": "stopped", "time": h1.index[j]}
            if (long and b["Close"] > level) or (not long and b["Close"] < level):
                entry = float(b["Close"])
                if (long and targets[0] <= entry) or (not long and targets[0] >= entry):
                    return {"status": "skipped", "time": h1.index[j]}
                seg = h1.iloc[k:j + 1]
                sw = seg["Low"].min() - 0.1 * atr if long else seg["High"].max() + 0.1 * atr
                min_d = entry * min_stop_pct / 100
                sw = min(sw, entry - min_d) if long else max(sw, entry + min_d)
                stop = max(sw, daily_stop) if long else min(sw, daily_stop)
                return {"status": "entry", "time": h1.index[j], "entry": entry, "stop": float(stop)}
        # bez reclaimu – hledá se další sweep
    return None


def sim(direction, entry, stop, targets, atr, path, ex):
    s = {"direction": direction, "entry": entry, "stop": stop, "targets": targets, "meta": {"atr": atr}}
    return ev.simulate(s, path, ex["max_hold_bars"] * 96, ex["split"], COST, ex["trail_atr"])


def main():
    rows = []
    for c in COINS:
        d1 = ev.load_history(f"{c}/USDT", "crypto", "1d", 3650, cache_dir=SP)
        d1 = d1[["Open", "High", "Low", "Close", "Volume"]].dropna().iloc[:-1]
        m15 = okx_15m(c)
        h1 = m15.resample("1h").agg(OHLC).dropna()
        h4 = m15.resample("4h").agg(OHLC).dropna()
        e15, e1, e4 = (st.ema(x["Close"], 20) for x in (m15, h1, h4))
        print(f"{c}: 15M {len(m15)} svíček {m15.index[0]:%Y-%m-%d} – {m15.index[-1]:%Y-%m-%d}", flush=True)
        after = lambda t, bar: m15[m15.index >= t + bar]                    # noqa: E731
        for strat in STRATS:
            p = strategy_params(strat)
            rule_p, ex, min_rr = ev.split_params(p, strat["setup"])
            for sig in st.find(strat["setup"], d1, "both", rule_p):
                if sig.rr[0] < min_rr:
                    continue
                t0 = sig.hold_time + pd.Timedelta(days=1)
                if t0 < m15.index[0] + pd.Timedelta(days=10) or t0 + pd.Timedelta(days=21) > m15.index[-1]:
                    continue
                atr, out = sig.meta["atr"], {}
                out["A"] = sim(sig.direction, sig.entry, sig.stop, sig.targets, atr, m15[m15.index >= t0], ex)["r"]
                for name, trg, bar in (
                        ("C", mtf.find_trigger(sig.direction, h1, t0, sig.stop, sig.targets, atr, WAIT_H, ema1=e1,
                                               h4=h4, ema4=e4), pd.Timedelta(hours=1)),
                        ("H4", sweep_trigger(sig.direction, h1, t0, sig.stop, sig.targets, atr), pd.Timedelta(hours=1)),
                        ("M15", mtf.find_trigger(sig.direction, m15, t0, sig.stop, sig.targets, atr, WAIT_H, ema1=e15,
                                                 h4=h1, ema4=e1, upper_hours=1), pd.Timedelta(minutes=15))):
                    out[name] = (sim(sig.direction, trg["entry"], trg["stop"], sig.targets, atr, after(trg["time"], bar), ex)["r"]
                                 if trg and trg["status"] == "entry" else None)
                rows.append({"coin": c, "strategy": strat["name"], "time": sig.hold_time, "dir": sig.direction, **out})
    df = pd.DataFrame(rows).sort_values("time")
    df.to_csv(SP / "mtf15_signals.csv")
    names = {"A": "A zavření denní svíčky", "C": "C dnes: 4H → 1H spouštěč", "H4": "H4 sweep & reclaim 1H",
             "M15": "M15 1H → 15M spouštěč"}
    cut = df["time"].iloc[int(len(df) * 0.7)]
    print(f"\ndenních signálů: {len(df)} ({df['time'].min():%Y-%m} – {df['time'].max():%Y-%m}); OOS od {cut:%Y-%m-%d}\n")
    print("| Varianta | Otevřeno | Ø R / obchod ± CI | Ø R / signál | IS Ø R / signál | OOS Ø R / signál ± CI | Σ R |")
    print("|---|---|---|---|---|---|---|")
    for k, lab in names.items():
        r = df[k].dropna()
        per = df[k].fillna(0)
        is_, oos = per[df["time"] < cut], per[df["time"] >= cut]
        ci = lambda x: 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0   # noqa: E731
        print(f"| {lab} | {len(r) / len(df) * 100:.0f} % | {r.mean():+.3f} ± {ci(r):.2f} | {per.mean():+.3f} | "
              f"{is_.mean():+.3f} | {oos.mean():+.3f} ± {ci(oos):.2f} | {per.sum():+.1f} |")
    print("\nPárově proti C (Ø rozdíl R/signál ± CI, celé období):")
    for k in ("A", "H4", "M15"):
        d = df[k].fillna(0) - df["C"].fillna(0)
        print(f"  {k} − C: {d.mean():+.3f} ± {1.96 * d.std(ddof=1) / np.sqrt(len(d)):.3f}")
    for s in df["strategy"].unique():
        m = df["strategy"] == s
        print(s, {k: round(float(df.loc[m, k].fillna(0).mean()), 3) for k in names})
    for half, m in (("1. polovina", df["time"] < df["time"].median()), ("2. polovina", df["time"] >= df["time"].median())):
        print(half, {k: round(float(df.loc[m, k].fillna(0).mean()), 3) for k in names})
    print("mince (Ø R/signál):")
    for c in COINS:
        m = df["coin"] == c
        print(f"  {c}", {k: round(float(df.loc[m, k].fillna(0).mean()), 2) for k in names})


if __name__ == "__main__":
    main()
