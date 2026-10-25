"""Vstup z nižších timeframů pro denní signály (předem stanovené varianty, hodinová data ~2 roky).

Signál a směr vždy z denního grafu (donchian_1d, pullback_1d dle config.yaml, s filtrem paniky).
Varianty vstupu (okno 72 h po uzavření denní svíčky; nesplněno = obchod se neotevře = 0 R):
  A  zavření denní svíčky (dnešní stav), stop a cíle ze signálu
  B  limitní příkaz o 0,5 denního ATR lépe; stop a cíle stejné ceny
  C  4H ve směru (close vs EMA20 4H) + 1H návrat k EMA20 1H + 1H obratová svíčka (close za EMA20 i za high/low
     předchozí); stop za swingem 6 hodinových svíček (min. 1,5 %, nejvýš původní stop); cíle stejné ceny
  D  jako C, ale původní denní stop (jen lepší načasování, bez těsnějšího stopu)
Výstupy pro všechny varianty stejně na hodinových svíčkách: 50 % na T1, zbytek trailing 3 denní ATR, max. 20 dní.

    python3 research/experiments/mtf_entry.py <adresář s eval_crypto_*_1d_3650d.csv a *_1h_730d.csv>
"""
import sys
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
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
STRATS = [s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")]


def load(c, tf, days):
    df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_{tf}_{days}d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df[["Open", "High", "Low", "Close"]].astype(float)


def sim(direction, entry, stop, targets, atr, path, ex):
    s = {"direction": direction, "entry": entry, "stop": stop, "targets": targets, "meta": {"atr": atr}}
    return ev.simulate(s, path, ex["max_hold_bars"] * 24, ex["split"], COST, ex["trail_atr"])


def variants(sig, h1, h4, e1, e4, ex):
    long = sig.direction == "long"
    sign = 1 if long else -1
    t0 = sig.hold_time + pd.Timedelta(days=1)                       # denní svíčka uzavřena
    win = h1[(h1.index >= t0) & (h1.index < t0 + pd.Timedelta(hours=WAIT_H))]
    after = lambda t: h1[h1.index > t]                              # noqa: E731
    atr = sig.meta["atr"]
    out = {}
    out["A"] = sim(sig.direction, sig.entry, sig.stop, sig.targets, atr, h1[h1.index >= t0], ex)["r"]
    # B: limit o 0,5 ATR lépe
    lim = sig.entry - sign * 0.5 * atr
    out["B"] = None
    for t, row in win.iterrows():
        if (long and row["Low"] <= sig.stop) or (not long and row["High"] >= sig.stop):
            break
        if (long and row["Low"] <= lim) or (not long and row["High"] >= lim):
            out["B"] = sim(sig.direction, lim, sig.stop, sig.targets, atr, after(t), ex)["r"]
            break
    # C/D: sdílená logika se skenerem (scanner/mtf.py)
    out["C"] = out["D"] = None
    trg = mtf.find_trigger(sig.direction, h1, t0, sig.stop, sig.targets, atr, WAIT_H, ema1=e1, h4=h4, ema4=e4)
    if trg and trg["status"] == "entry":
        out["C"] = sim(sig.direction, trg["entry"], trg["stop"], sig.targets, atr, after(trg["time"]), ex)["r"]
        out["D"] = sim(sig.direction, trg["entry"], sig.stop, sig.targets, atr, after(trg["time"]), ex)["r"]
    return out


rows = []
for c in COINS:
    d1, h1 = load(c, "1d", 3650), load(c, "1h", 730)
    h4 = h1.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    e1 = st.ema(h1["Close"], 20)
    e4 = st.ema(h4["Close"], 20)
    for strat in STRATS:
        p = strategy_params(strat)
        rule_p, ex, min_rr = ev.split_params(p, strat["setup"])
        for sig in st.find(strat["setup"], d1, "both", rule_p):
            if sig.rr[0] < min_rr or sig.hold_time < h1.index[0] + pd.Timedelta(days=10):
                continue
            if sig.hold_time + pd.Timedelta(days=21) > h1.index[-1]:
                continue
            v = variants(sig, h1, h4, e1, e4, ex)
            rows.append({"coin": c, "strategy": strat["name"], "time": sig.hold_time, "dir": sig.direction, **v})

df = pd.DataFrame(rows)
print(f"denních signálů s hodinovými daty: {len(df)} ({df['time'].min():%Y-%m} – {df['time'].max():%Y-%m})\n")
print(f"{'varianta':44} {'otevřeno':>9} {'Ø R / obchod':>14} {'Ø R / signál':>13} {'Σ R':>7}")
names = {"A": "A zavření denní svíčky (dnes)", "B": "B limit o 0,5 ATR lépe", "C": "C 4H směr + 1H zóna + 1H spouštěč, těsný stop",
         "D": "D jako C, původní stop"}
for k, lab in names.items():
    r = df[k].dropna()
    per_sig = df[k].fillna(0)
    ci = 1.96 * r.std(ddof=1) / np.sqrt(len(r)) if len(r) > 1 else 0
    print(f"{lab:44} {len(r) / len(df) * 100:>8.0f} % {r.mean():>+8.3f} ± {ci:.2f} {per_sig.mean():>+13.3f} {per_sig.sum():>+7.1f}")
print()
for half, m in (("1. polovina", df["time"] < df["time"].median()), ("2. polovina", df["time"] >= df["time"].median())):
    print(half, {k: round(float(df.loc[m, k].fillna(0).mean()), 3) for k in names})
for s in df["strategy"].unique():
    m = df["strategy"] == s
    print(s, {k: round(float(df.loc[m, k].fillna(0).mean()), 3) for k in names})
print("mince (C − A, Ø R/signál):", {c: round(float(df.loc[df.coin == c, "C"].fillna(0).mean() - df.loc[df.coin == c, "A"].mean()), 2) for c in COINS})
missed = df[df["C"].isna()]
print(f"C neotevřeno: {len(missed)} signálů, jejich výsledek ve variantě A: Ø {missed['A'].mean():+.3f} R (ušlé / ušetřené)")
