"""Obrat po prudkém pohybu s těsným stopem + simulace „malý účet → velký“ (stanoveno PŘEDEM, 25. 10. 2026).

Data: 15M svíčky OKX (spot USDT), 8 mincí, ~2 roky. 1H svíčky z 15M.
Prudký pohyb: |Close_1H(t) − Close_1H(t−4)| ≥ 4 × ATR14 1H (ATR k času t−4). Propad → hledá se long, výstřel → short.
Vstup: do 12 h po uzavření 1H svíčky pohybu; 15M svíčka zavře nad max. High 2 předchozích 15M svíček (long),
  resp. pod min. Low (short). Extrém = nejnižší Low (nejvyšší High) od začátku pohybu do vstupu.
Stop: extrém − 0,1 × ATR14 15M (long; short zrcadlově), min. 0,3 % od vstupu. Jeden pokus na pohyb; další pohyb
  na téže minci nejdřív 24 h po předchozím.
Výstupy (každý zvlášť, všechny reportované): T2R+trail = po +2R stop na vstup, pak trailing 3 × ATR 1H;
  cíl 10R; cíl 20R; cíl 50R. Max. 7 dní. Stop i cíl ve stejné svíčce = stop (konzervativně).
Náklady: 0,07 %/stranu (futures taker + skluz) a 0,15 %/stranu (spot). R po nákladech.
Srovnání: náhodné vstupy (stejná mince, směr, stop v %, výstup; 20 opakování).
Výzva: obchody chronologicky (jen jedna pozice naráz), start 100 USD, riziko 2 / 5 / 10 % účtu na pokus, zisky se
  reinvestují; + 10 000 náhodných pořadí stejných obchodů: P(účet ≥ 10×), P(účet ≥ 100×), P(pád pod 10 USD), medián konce.

    python3 research/experiments/reversal.py [cache_dir]          # stahuje 15M z OKX (GitHub Actions)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scanner import setups as st  # noqa: E402
from mtf15 import okx_15m, OHLC  # noqa: E402

COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
EXITS = ["T2R+trail", "cíl 10R", "cíl 20R", "cíl 50R"]
MAX_BARS = 7 * 96


def atr(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def find_setups(m15):
    h1 = m15.resample("1h").agg(OHLC).dropna()
    a1, a15 = atr(h1), atr(m15)
    move = h1["Close"] - h1["Close"].shift(4)
    out, last = [], None
    idx15 = m15.index
    for k in range(20, len(h1)):
        t = h1.index[k]
        ref_atr = a1.iat[k - 4]
        if not ref_atr or abs(move.iat[k]) < 4 * ref_atr:
            continue
        if last is not None and t < last + pd.Timedelta(hours=24):
            continue
        long = move.iat[k] < 0
        start, ready = h1.index[k - 4], t + pd.Timedelta(hours=1)          # 1H svíčka t uzavřena v t+1h
        seg = m15[(idx15 >= start) & (idx15 < ready + pd.Timedelta(hours=12))]
        pos0 = int(np.searchsorted(seg.index, ready))
        for j in range(max(pos0, 2), len(seg)):
            bar = seg.iloc[j]
            prev = seg.iloc[j - 2:j]
            if (long and bar["Close"] > prev["High"].max()) or (not long and bar["Close"] < prev["Low"].min()):
                ext = seg["Low"].iloc[:j + 1].min() if long else seg["High"].iloc[:j + 1].max()
                a = a15.loc[seg.index[j]]
                entry = float(bar["Close"])
                stop = ext - 0.1 * a if long else ext + 0.1 * a
                if abs(entry - stop) < entry * 0.003:
                    stop = entry * (1 - 0.003) if long else entry * (1 + 0.003)
                out.append({"time": seg.index[j], "dir": "long" if long else "short", "entry": entry, "stop": float(stop),
                            "atr1h": float(a1.iat[k]), "shock": t})
                last = t
                break
    return out


def simulate(path, s, exit_kind, cost_pct):
    long = s["dir"] == "long"
    sign = 1 if long else -1
    e, stop0 = s["entry"], s["stop"]
    risk = abs(e - stop0)
    c = cost_pct / 100

    def r_at(px):
        return (sign * (px - e) - c * (e + px)) / risk
    hi, lo, cl = path["High"].values[:MAX_BARS], path["Low"].values[:MAX_BARS], path["Close"].values[:MAX_BARS]
    if not len(cl):
        return None
    if exit_kind == "T2R+trail":
        stop, armed, best = stop0, False, e
        for i in range(len(cl)):
            if (lo[i] <= stop) if long else (hi[i] >= stop):
                return r_at(stop)
            if not armed and ((hi[i] >= e + 2 * risk) if long else (lo[i] <= e - 2 * risk)):
                armed, stop = True, e
            if armed:
                best = max(best, cl[i]) if long else min(best, cl[i])
                tr = best - sign * 3 * s["atr1h"]
                stop = max(stop, tr) if long else min(stop, tr)
        return r_at(cl[-1])
    target_r = float(exit_kind.split()[1].rstrip("R"))
    tgt = e + sign * target_r * risk
    for i in range(len(cl)):
        if (lo[i] <= stop0) if long else (hi[i] >= stop0):
            return r_at(stop0)
        if (hi[i] >= tgt) if long else (lo[i] <= tgt):
            return r_at(tgt)
    return r_at(cl[-1])


def challenge(rs, f, start=100.0):
    eq, peak, low = start, start, start
    for r in rs:
        eq *= max(1 + f * r, 0.0)
        peak, low = max(peak, eq), min(low, eq)
    return eq, peak, low


def main():
    data, trades = {}, []
    for c in COINS:
        m15 = okx_15m(c)
        data[c] = m15
        for s in find_setups(m15):
            s["coin"] = c
            trades.append(s)
        print(f"{c}: {len(m15)} svíček, pokusů {sum(1 for t in trades if t['coin'] == c)}", flush=True)
    trades.sort(key=lambda t: t["time"])
    print(f"\nPokusů celkem: {len(trades)} ({trades[0]['time']:%Y-%m-%d} – {trades[-1]['time']:%Y-%m-%d}), "
          f"long {sum(t['dir'] == 'long' for t in trades)}, short {sum(t['dir'] == 'short' for t in trades)}")
    sp = pd.Series([abs(t["entry"] - t["stop"]) / t["entry"] * 100 for t in trades])
    print(f"stop od vstupu: medián {sp.median():.2f} %, 10.–90. percentil {sp.quantile(.1):.2f}–{sp.quantile(.9):.2f} %")
    rng = np.random.default_rng(7)
    results = {}
    for cost in (0.07, 0.15):
        print(f"\n=== náklady {cost} % na stranu ===")
        print("| Výstup | Úspěšnost | Ø R ± CI | Medián | ≥10R | ≥20R | ≥50R | Největší | Σ R | Náhoda Ø R |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for ex in EXITS:
            rs, ends = [], []
            for t in trades:
                m15 = data[t["coin"]]
                path = m15[m15.index > t["time"]]
                r = simulate(path, t, ex, cost)
                if r is not None:
                    rs.append(r)
                    ends.append(path.index[min(len(path) - 1, MAX_BARS - 1)])
            rs = np.array(rs)
            rnd = []
            for t in trades:
                m15 = data[t["coin"]]
                pct = abs(t["entry"] - t["stop"]) / t["entry"]
                for _ in range(20):
                    i = int(rng.integers(200, len(m15) - MAX_BARS))
                    e = float(m15["Close"].iat[i])
                    sign = 1 if t["dir"] == "long" else -1
                    s = {"dir": t["dir"], "entry": e, "stop": e * (1 - sign * pct), "atr1h": t["atr1h"] * e / t["entry"]}
                    r = simulate(m15.iloc[i + 1:], s, ex, cost)
                    if r is not None:
                        rnd.append(r)
            ci = 1.96 * rs.std(ddof=1) / np.sqrt(len(rs))
            print(f"| {ex} | {(rs > 0).mean() * 100:.0f} % | {rs.mean():+.2f} ± {ci:.2f} | {np.median(rs):+.2f} | "
                  f"{(rs >= 10).mean() * 100:.1f} % | {(rs >= 20).mean() * 100:.1f} % | {(rs >= 50).mean() * 100:.1f} % | "
                  f"{rs.max():+.1f} | {rs.sum():+.1f} | {np.mean(rnd):+.2f} |")
            results[(cost, ex)] = rs
        half = len(trades) // 2
        print("\nPoloviny období (Ø R): " + ", ".join(
            f"{ex}: {results[(cost, ex)][:half].mean():+.2f} / {results[(cost, ex)][half:].mean():+.2f}" for ex in EXITS))
    print("\n=== Výzva: 100 USD, náklady 0,07 %, skutečné pořadí obchodů (jedna pozice naráz zjednodušeně = všechny pokusy) ===")
    print("| Výstup | Riziko/pokus | Konec (skutečné pořadí) | Max | Min | P(≥ 1 000 USD) | P(≥ 10 000 USD) | P(< 10 USD) | Medián konce |")
    print("|---|---|---|---|---|---|---|---|---|")
    for ex in EXITS:
        rs = results[(0.07, ex)]
        for f in (0.02, 0.05, 0.10):
            end, peak, low = challenge(rs, f)
            sims = np.array([challenge(rng.permutation(rs), f) for _ in range(10000)])
            print(f"| {ex} | {f * 100:.0f} % | {end:,.0f} | {peak:,.0f} | {low:,.0f} | {(sims[:, 1] >= 1000).mean() * 100:.1f} % | "
                  f"{(sims[:, 1] >= 10000).mean() * 100:.1f} % | {(sims[:, 2] < 10).mean() * 100:.1f} % | {np.median(sims[:, 0]):,.0f} |")


if __name__ == "__main__":
    main()
