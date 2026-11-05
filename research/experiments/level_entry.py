"""Vstup v okamžiku průrazu úrovně místo čekání na zavření denní svíčky – stanoveno PŘEDEM, 5. 11. 2026.

Podnět (Jakub): „Proč vstupovat na denní svíčce? Když BTC znovu prolomí 80k a na nižších TF dělá nižší high a nižší
low, je ideální vstup u 79,9k – ne až na 76k, kde hrozí odraz a vyplachování.“

Strategie: donchian_1d (průraz 20denního minima/maxima ve směru EMA200, bez vstupu v panice, stop 2 ATR, min 1,5 %).
Data: 8 mincí, denní svíčky (indikátory) + 1H (~2 roky, provedení). Náklady 0,15 % na stranu, 1 pozice na minci
a variantu. Výstupy pro všechny stejné: 50 % na 2R, zbytek trailing 3 denní ATR, max 20 dní.

  A  dnes: zavření denní svíčky za kanálem → vstup na close (další hodina po půlnoci UTC).
  E  stop příkaz NA ÚROVNI: na začátku dne d je známá úroveň (20denní min/max z předchozích dní), trend (close d−1 vs.
     EMA200) a panika (d−1). První hodina dne, která úroveň protne → vstup na úrovni + 0,05 % skluz. Stop 2 denní ATR
     (d−1) od vstupu, min 1,5 %. Bere i falešné průrazy, které se do večera vrátí – ty se počítají.
  E2 jako E, ale jen když je 1H v trendu ve směru (EMA20 < EMA50 na 1H pro short, zrcadlově long) = „nižší high a low“.
  E3 jako E2, ale stop nad posledním 1H swingem (max high 6 svíček + 0,1 denního ATR, min 1,5 %) = těsnější stop.

PROJDE varianta X, když proti A: Ø R na obchod ≥ A + 0,05 R a R za rok vyšší, v OBOU polovinách období, n ≥ 100.
Pak jde papírově souběžně (jako vstup z nižších TF), pravidla skeneru se mění až po živém ověření.

    python3 research/experiments/level_entry.py /tmp/cache      → reports/level_entry.md
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, setups as st  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
OUT = ROOT / "reports" / "level_entry.md"
COST, SLIP = 0.15, 0.0005
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
STRAT = next(s for s in cfg["strategies"] if s["name"] == "donchian_1d")
P = strategy_params(STRAT)
RULE, EX, MIN_RR = ev.split_params(P, STRAT["setup"])


def load(c, tf, days):
    df = ev.load_history(f"{c}/USDT", "crypto", tf, days, cache_dir=SP)
    if df is None or df.empty:
        raise SystemExit(f"DATA_UNAVAILABLE {c} {tf}")
    return df[["Open", "High", "Low", "Close", "Volume"]].astype(float).dropna().iloc[:-1]


def sim(direction, entry, stop, atr, path):
    risk = abs(entry - stop)
    sg = 1 if direction == "long" else -1
    s = {"direction": direction, "entry": entry, "stop": stop, "targets": [entry + sg * 2 * risk, entry + sg * 4 * risk],
         "meta": {"atr": atr}}
    return ev.simulate(s, path, EX["max_hold_bars"] * 24, EX["split"], COST, EX["trail_atr"])


def run_coin(c):
    d1, h1 = load(c, "1d", 3650), load(c, "1h", 730)
    x = st.Ctx(d1)
    n = RULE["channel"]
    hi, lo, e200 = x.roll_max(n), x.roll_min(n), x.ema(RULE["trend_ema"])
    rank = x.vol_rank(RULE.get("panic_window", 365))
    e20h, e50h = st.ema(h1["Close"], 20).values, st.ema(h1["Close"], 50).values
    hh, hl, hc = h1["High"].values, h1["Low"].values, h1["Close"].values
    hidx = h1.index
    start = hidx[0] + pd.Timedelta(days=3)
    end = hidx[-1] - pd.Timedelta(days=21)
    rows, busy = [], {k: hidx[0] for k in ("A", "E", "E2", "E3")}

    def take(var, t_entry_i, direction, entry, stop, atr, day):
        if hidx[t_entry_i] < busy[var]:
            return
        res = sim(direction, entry, stop, atr, h1.iloc[t_entry_i + 1:])
        if res["result"] == "open":
            return
        busy[var] = hidx[min(t_entry_i + res["bars"], len(hidx) - 1)]
        rows.append({"coin": c, "var": var, "time": day, "dir": direction, "r": res["r"]})

    # A – dnešní signály (stejný kód jako skener)
    for s in st.find(STRAT["setup"], d1, "both", RULE):
        if s.rr[0] < MIN_RR or not (start <= s.hold_time <= end):
            continue
        t0 = s.hold_time + pd.Timedelta(days=1)
        i = hidx.searchsorted(t0)
        if i >= len(hidx) - 2:
            continue
        take("A", i, s.direction, float(s.entry), float(s.stop), float(s.meta["atr"]), s.hold_time)

    # E/E2/E3 – stop příkaz na úrovni během dne
    for d in range(n + 2, len(d1)):
        day = d1.index[d]
        if not (start <= day <= end):
            continue
        p = d - 1                                             # vše známé z předchozího uzavřeného dne
        if np.isnan(hi[d]) or np.isnan(e200[p]) or (not np.isnan(rank[p]) and rank[p] >= RULE["panic_vol_rank"]):
            continue
        a = float(x.atr[p])
        a0, a1 = hidx.searchsorted(day), hidx.searchsorted(day + pd.Timedelta(days=1))
        for direction in ("long", "short"):
            long = direction == "long"
            if long and not (x.c[p] > e200[p] and x.c[p] <= hi[d]):
                continue
            if not long and not (x.c[p] < e200[p] and x.c[p] >= lo[d]):
                continue
            level = hi[d] if long else lo[d]
            hit = next((j for j in range(a0, a1) if (hh[j] >= level if long else hl[j] <= level)), None)
            if hit is None:
                continue
            sg = 1 if long else -1
            entry = level * (1 + sg * SLIP)
            entry = max(entry, h1["Open"].iat[hit]) if long else min(entry, h1["Open"].iat[hit])   # gap přes úroveň
            mind = entry * P["min_stop_pct"] / 100
            stop = entry - sg * max(P["stop_atr"] * a, mind)
            # vstup uvnitř hodiny `hit`: simulace od další hodiny (stop v té samé hodině se nepočítá – viz zpráva)
            take("E", hit, direction, entry, stop, a, day)
            trend_ok = (e20h[hit - 1] > e50h[hit - 1]) if long else (e20h[hit - 1] < e50h[hit - 1])
            if hit >= 7 and trend_ok:
                take("E2", hit, direction, entry, stop, a, day)
                sw = (hl[hit - 6:hit].min() - 0.1 * a) if long else (hh[hit - 6:hit].max() + 0.1 * a)
                stop3 = min(sw, entry - mind) if long else max(sw, entry + mind)
                take("E3", hit, direction, entry, stop3, a, day)
    return rows


def fmt(v, d=3):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:+.{d}f}".replace(".", ",")


def main():
    rows = []
    for c in COINS:
        rows += run_coin(c)
    df = pd.DataFrame(rows)
    t_min, t_max = df.time.min(), df.time.max()
    mid = t_min + (t_max - t_min) / 2
    yrs = (t_max - t_min).days / 365.25
    L = ["# 🎯 Vstup na průrazu úrovně vs. zavření denní svíčky – výsledky testu", "",
         f"Spuštěno {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. Pravidla předem (hlavička "
         "`research/experiments/level_entry.py`). donchian_1d, 8 mincí, 1H provedení "
         f"{t_min:%Y-%m} – {t_max:%Y-%m}, náklady 0,15 %/stranu + 0,05 % skluz na úrovni.", "",
         "| varianta | obchodů | výhry | Ø R ± CI | R/rok | 1. pol. Ø R (n) | 2. pol. Ø R (n) | long Ø R | short Ø R |",
         "|---|---|---|---|---|---|---|---|---|"]
    names = {"A": "A dnes – zavření denní svíčky", "E": "E stop příkaz na úrovni", "E2": "E2 + 1H trend ve směru",
             "E3": "E3 + 1H trend, stop za 1H swingem"}
    st_ = {}
    for k, lab in names.items():
        x = df[df["var"] == k]
        if x.empty:
            L.append(f"| {lab} | 0 | – | – | – | – | – | – | – |")
            continue
        h1, h2 = x[x.time < mid], x[x.time >= mid]
        ci = 1.96 * x.r.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0
        st_[k] = {"n": len(x), "m": x.r.mean(), "m1": h1.r.mean(), "m2": h2.r.mean(),
                  "y1": h1.r.sum() / (yrs / 2), "y2": h2.r.sum() / (yrs / 2)}
        L.append(f"| {lab} | {len(x)} | {(x.r > 0).mean() * 100:.0f} % | {fmt(x.r.mean())} ± {ci:.2f} | "
                 f"{x.r.sum() / yrs:+.0f} | {fmt(h1.r.mean())} ({len(h1)}) | {fmt(h2.r.mean())} ({len(h2)}) | "
                 f"{fmt(x[x.dir == 'long'].r.mean())} | {fmt(x[x.dir == 'short'].r.mean())} |")
    L += ["", "## Verdikt", ""]
    a = st_.get("A")
    for k in ("E", "E2", "E3"):
        v = st_.get(k)
        if not v or not a:
            L.append(f"- {names[k]}: bez dat")
            continue
        ok = (v["n"] >= 100 and v["m1"] >= a["m1"] + 0.05 and v["m2"] >= a["m2"] + 0.05
              and v["y1"] > a["y1"] and v["y2"] > a["y2"])
        L.append(f"- {names[k]}: **{'PROŠLO ✅' if ok else 'NEPROŠLO ❌'}** – Ø R {fmt(v['m1'])} / {fmt(v['m2'])} vs. A "
                 f"{fmt(a['m1'])} / {fmt(a['m2'])}; R/rok {v['y1']:+.0f} / {v['y2']:+.0f} vs. A {a['y1']:+.0f} / {a['y2']:+.0f}")
    L += ["", "Po mincích (Ø R):", "", "| mince | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for c in COINS:
        L.append(f"| {c} | " + " | ".join(f"{fmt(df[(df.coin == c) & (df['var'] == k)].r.mean())} "
                                          f"({((df.coin == c) & (df['var'] == k)).sum()})" for k in names) + " |")
    L += ["", "Pozn.: u E se stop ve stejné hodině jako vstup nepočítá (hodinová data neříkají pořadí) – to E mírně "
          "zvýhodňuje; proto je laťka +0,05 R v obou polovinách.", "",
          "Rozhodnutí: co PROŠLO, jde papírově souběžně s dnešním vstupem; jinak beze změny. Nejde o finanční poradenství."]
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
