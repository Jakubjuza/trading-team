"""Křehkost trhu a pozdní vstup u denních strategií – stanoveno PŘEDEM, 5. 11. 2026 (před prvním spuštěním).

Podnět (Jakub): (1) v křehkém trhu špatné zprávy hýbou hodně a dobré málo, v býčím naopak – desk to nerozlišuje;
(2) pozice se otevírají pozdě, po hlavním pohybu dne, a pak je smaže vyplachovací svíčka.

Data: BTC 1H (~2 roky, yfinance) pro index K (research/fragility.py); denní svíčky 8 mincí ~10 let.
Signály: dnešní donchian_1d a pullback_1d (stejný kód jako skener, s filtrem paniky), vstup na close signální
svíčky, výstupy jako dnes (50 % na 2R, zbytek trailing 3 ATR, max 20 dní), náklady 0,15 % na stranu, 1 pozice na minci.
Pozn.: v context_gate (lab, intradenní TF) „přetažení od EMA20“ výhodu nedalo; tady se testují DENNÍ strategie skeneru.

T1 Křehkost (jen období s 1H daty BTC): K v čase signálu (zavření denní svíčky). Skupiny:
   „proti“      = long při K ≥ +0,25 (křehký) nebo short při K ≤ −0,25 (optimistický),
   „po směru“   = short při křehkém nebo long při optimistickém, „vyrovnaný“ = zbytek.
   PROJDE (→ kandidát na filtr, nejdřív papír), když Ø R „proti“ je o ≥ 0,10 R nižší než Ø R ostatních
   v OBOU polovinách období a „proti“ má ≥ 30 obchodů.
   Doplněk (popis): Ø výnos BTC za 7 dní po stavu křehký / vyrovnaný / optimistický, po polovinách.
T2 Pozdní vstup (celých ~10 let): přetažení = (close − EMA20) / ATR14 ve směru obchodu na signální svíčce,
   a pohyb dne = (close − open) / ATR14 ve směru obchodu. Skupiny přetažení < 1, 1–2, ≥ 2 ATR.
   PROJDE, když Ø R skupiny ≥ 2 ATR je o ≥ 0,10 R nižší než Ø R < 2 ATR v OBOU polovinách a má ≥ 30 obchodů.
   Doplněk: podíl obchodů, které šly nejdřív ≥ 0,5 R proti (vyplachování), po skupinách přetažení.

    python3 research/experiments/fragility_test.py /tmp/cache    → reports/fragility.md
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import fragility as fr  # noqa: E402
from research.events import FOMC_DECISIONS  # noqa: E402
from scanner import evaluate as ev, setups as st  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
OUT = ROOT / "reports" / "fragility.md"
COST = 0.15
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
STRATS = [s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")]


def load(c, tf, days):
    df = ev.load_history(f"{c}/USDT", "crypto", tf, days, cache_dir=SP)
    if df is None or df.empty:
        raise SystemExit(f"DATA_UNAVAILABLE {c} {tf}")
    df = df[["Open", "High", "Low", "Close"]].astype(float).dropna()
    return df.iloc[:-1]                                              # poslední (neuzavřená) svíčka pryč


def mae_r(path, s, bars):
    """Jak daleko (v R) šla cena proti před výstupem."""
    p = path.iloc[:max(bars, 1)]
    risk = abs(s.entry - s.stop)
    adv = (s.entry - p["Low"].min()) if s.direction == "long" else (p["High"].max() - s.entry)
    return float(adv / risk) if risk else np.nan


def trades_for(c, d1):
    e20 = st.ema(d1["Close"], 20)
    atr = pd.Series(st.Ctx(d1).atr, index=d1.index)
    rows = []
    for strat in STRATS:
        p = strategy_params(strat)
        rule_p, ex, min_rr = ev.split_params(p, strat["setup"])
        busy = -1
        for s in sorted(st.find(strat["setup"], d1, "both", rule_p), key=lambda s: s.meta["hold_index"]):
            h = s.meta["hold_index"]
            if s.rr[0] < min_rr or h <= busy:
                continue
            path = d1.iloc[h + 1:]
            res = ev.simulate(s, path, ex["max_hold_bars"], ex["split"], COST, ex["trail_atr"])
            if res["result"] == "open":
                continue
            busy = h + res["bars"]
            sg = 1 if s.direction == "long" else -1
            a = float(atr.iat[h]) or np.nan
            rows.append({"coin": c, "strategy": strat["name"], "time": d1.index[h], "dir": s.direction, "r": res["r"],
                         "ext": sg * (d1["Close"].iat[h] - e20.iat[h]) / a,
                         "day": sg * (d1["Close"].iat[h] - d1["Open"].iat[h]) / a,
                         "mae": mae_r(path, s, res["bars"])})
    return rows


def fmt(x, d=3):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.{d}f}".replace(".", ",")


def grp_table(df, col, order, title):
    lines = [f"| {title} | n | Ø R | 1. pol. Ø R (n) | 2. pol. Ø R (n) | výhry | vypláchnuto ≥ 0,5 R proti |",
             "|---|---|---|---|---|---|---|"]
    mid = df["time"].min() + (df["time"].max() - df["time"].min()) / 2
    for g in order:
        x = df[df[col] == g]
        h1, h2 = x[x.time < mid], x[x.time >= mid]
        lines.append(f"| {g} | {len(x)} | {fmt(x.r.mean())} | {fmt(h1.r.mean())} ({len(h1)}) | {fmt(h2.r.mean())} ({len(h2)}) | "
                     f"{(x.r > 0).mean() * 100 if len(x) else 0:.0f} % | {(x.mae >= 0.5).mean() * 100 if len(x) else 0:.0f} % |")
    return lines


def verdict(df, col, bad, label):
    mid = df["time"].min() + (df["time"].max() - df["time"].min()) / 2
    ok, parts = True, []
    for name, m in (("1. pol.", df.time < mid), ("2. pol.", df.time >= mid)):
        x = df[m]
        b, o = x[x[col] == bad].r.mean(), x[x[col] != bad].r.mean()
        d = o - b if not (np.isnan(b) or np.isnan(o)) else np.nan
        parts.append(f"{name}: {label} {fmt(b)} vs. ostatní {fmt(o)} (rozdíl {fmt(d)})")
        ok &= bool(not np.isnan(d) and d >= 0.10)
    n = int((df[col] == bad).sum())
    ok &= n >= 30
    return ok, "; ".join(parts) + f"; n = {n}"


def main():
    btc_h1 = load("BTC", "1h", 730)
    sh = fr.shocks(btc_h1)
    rows = []
    for c in COINS:
        rows += trades_for(c, load(c, "1d", 3650))
    df = pd.DataFrame(rows).sort_values("time")
    L = [f"# 🧊 Křehkost trhu a pozdní vstup – výsledky testu",
         "",
         f"Spuštěno {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. Pravidla stanovena předem "
         "(hlavička `research/experiments/fragility_test.py`). Index: `research/fragility.py`.",
         f"Denní strategie donchian_1d + pullback_1d, 8 mincí, {len(df)} obchodů "
         f"({df.time.min():%Y-%m} – {df.time.max():%Y-%m}), náklady 0,15 %/stranu. Šoků BTC (≥ 3σ za hodinu): {len(sh)} "
         f"({btc_h1.index[0]:%Y-%m} – {btc_h1.index[-1]:%Y-%m}).", ""]

    # --- T1
    t0 = btc_h1.index[0] + pd.Timedelta(days=fr.WINDOW_D + 30)
    d = df[df.time >= t0].copy()
    d["k"] = fr.series(btc_h1, d.time + pd.Timedelta(days=1), sh=sh).values      # stav při zavření signální svíčky
    d["st"] = d["k"].map(fr.state)
    d["grp"] = np.where((d.st == "křehký") & (d.dir == "long") | (d.st == "optimistický") & (d.dir == "short"), "proti",
               np.where((d.st == "křehký") & (d.dir == "short") | (d.st == "optimistický") & (d.dir == "long"),
                        "po směru", "vyrovnaný / málo dat"))
    ok1, why1 = verdict(d, "grp", "proti", "proti")
    L += [f"## T1 Křehkost: **{'PROŠLO ✅' if ok1 else 'NEPROŠLO ❌'}**", "", why1, ""]
    L += grp_table(d, "grp", ["proti", "po směru", "vyrovnaný / málo dat"], "obchod vůči stavu")
    L += ["", "Po směru a stavu (Ø R, n):", "", "| stav BTC | long | short |", "|---|---|---|"]
    for s_ in ("křehký", "vyrovnaný", "optimistický", "málo dat"):
        x = d[d.st == s_]
        L.append(f"| {s_} | {fmt(x[x.dir == 'long'].r.mean())} ({(x.dir == 'long').sum()}) | "
                 f"{fmt(x[x.dir == 'short'].r.mean())} ({(x.dir == 'short').sum()}) |")

    # BTC 7 dní po stavu (denní vzorky)
    days = pd.date_range(t0.normalize(), btc_h1.index[-1] - pd.Timedelta(days=8), freq="1D", tz="UTC")
    ks = fr.series(btc_h1, days, sh=sh)
    c = btc_h1["Close"]
    fwd = [(c.asof(t + pd.Timedelta(days=7)) / c.asof(t) - 1) * 100 for t in days]
    b = pd.DataFrame({"k": ks.values, "fwd": fwd}, index=days)
    b["st"] = b.k.map(fr.state)
    mid = days[len(days) // 2]
    L += ["", "BTC za 7 dní po stavu (denní vzorky, Ø %; vzorky se překrývají – jen popis):", "",
          "| stav | dní | Ø % | 1. pol. | 2. pol. | podíl dní |", "|---|---|---|---|---|---|"]
    for s_ in ("křehký", "vyrovnaný", "optimistický", "málo dat"):
        x = b[b.st == s_]
        L.append(f"| {s_} | {len(x)} | {fmt(x.fwd.mean(), 2)} | {fmt(x[x.index < mid].fwd.mean(), 2)} | "
                 f"{fmt(x[x.index >= mid].fwd.mean(), 2)} | {len(x) / len(b) * 100:.0f} % |")

    # FOMC – jak trh reagoval a jaký byl stav
    L += ["", "Rozhodnutí Fedu (FOMC, 14:00 New York) v datech: pohyb BTC 4 h a 24 h po prohlášení a K před ním:", "",
          "| datum | K před | stav | 4 h % | 24 h % |", "|---|---|---|---|---|"]
    for dstr in FOMC_DECISIONS:
        t = pd.Timestamp(dstr + " 14:00", tz="America/New_York").tz_convert("UTC")
        if t < t0 or t + pd.Timedelta(hours=24) > btc_h1.index[-1]:
            continue
        k = fr.series(btc_h1, [t], sh=sh).iat[0]
        p0 = c.asof(t)
        L.append(f"| {dstr} | {fmt(k, 2)} | {fr.state(k)} | {fmt((c.asof(t + pd.Timedelta(hours=4)) / p0 - 1) * 100, 2)} | "
                 f"{fmt((c.asof(t + pd.Timedelta(hours=24)) / p0 - 1) * 100, 2)} |")

    # --- T2
    df["xg"] = pd.cut(df.ext, [-np.inf, 1, 2, np.inf], labels=["< 1 ATR", "1–2 ATR", "≥ 2 ATR"], right=False).astype(str)
    df["bad"] = np.where(df.ext >= 2, "≥ 2 ATR", "< 2 ATR")
    ok2, why2 = verdict(df, "bad", "≥ 2 ATR", "≥ 2 ATR")
    L += ["", f"## T2 Pozdní vstup (přetažení od EMA20): **{'PROŠLO ✅' if ok2 else 'NEPROŠLO ❌'}**", "", why2, ""]
    L += grp_table(df, "xg", ["< 1 ATR", "1–2 ATR", "≥ 2 ATR"], "přetažení na signálu")
    df["dg"] = pd.cut(df.day, [-np.inf, 0.5, 1.5, np.inf], labels=["< 0,5 ATR", "0,5–1,5 ATR", "≥ 1,5 ATR"],
                      right=False).astype(str)
    L += ["", "Pohyb signálního dne ve směru obchodu (popis):", ""]
    L += grp_table(df, "dg", ["< 0,5 ATR", "0,5–1,5 ATR", "≥ 1,5 ATR"], "pohyb dne")
    L += ["", "Po strategiích (Ø R):", "", "| strategie | < 1 ATR | 1–2 ATR | ≥ 2 ATR |", "|---|---|---|---|"]
    for s_ in df.strategy.unique():
        x = df[df.strategy == s_]
        L.append(f"| {s_} | " + " | ".join(f"{fmt(x[x.xg == g].r.mean())} ({(x.xg == g).sum()})"
                                          for g in ("< 1 ATR", "1–2 ATR", "≥ 2 ATR")) + " |")

    cur = fr.current(btc_h1)
    L += ["", "## Stav teď", "", fr.line(cur), "",
          "Rozhodnutí: co PROŠLO, jde nejdřív papírově souběžně (jako vstup z nižších TF); co NEPROŠLO, zůstává jen popisem "
          "pro desk. Pravidla skeneru se mění jen po testu.", "", "Nejde o finanční poradenství."]
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
