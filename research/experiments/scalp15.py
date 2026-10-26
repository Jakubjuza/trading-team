"""Krátký timeframe s pákou: průraz VE SMĚRU pohybu na 15M, těsný stop, posouvaný stop (stanoveno PŘEDEM, 26. 10. 2026).

Navazuje na reports/reversal.md: obrat PROTI prudkému pohybu prohrál, protože pohyb v kryptu spíš pokračuje.
Tady se testuje opak – jít s pohybem, stop těsně a posouvat ho, když pozice jede.

Data: 15M svíčky OKX (spot USDT), 8 mincí, ~2 roky; 1H a 1D svíčky složené z 15M (jen uzavřené).
Spouštěč (long; short zrcadlově), vyhodnocuje se na zavření 15M svíčky:
  - close > max. High 20 předchozích 15M svíček,
  - objem svíčky ≥ 1,5 × průměr 20 předchozích,
  - poslední uzavřená 1H svíčka: close > EMA50 (1H).
  Filtr F1 (varianta): navíc poslední uzavřený den close > EMA50 (1D) – denní směr (reports/bias_entry.md).
Vstup: na zavření spouštěcí svíčky. Stop: min. Low 6 posledních 15M svíček − 0,1 × ATR14 (15M), nejméně 0,3 %
  od vstupu; stop širší než 1,5 % = obchod se nebere (není „těsný“). Na minci jen jedna pozice naráz.
Výstupy (každý zvlášť, všechny reportované; max. 2 dny = 192 svíček, pak na close):
  BE+trail  po +1R stop na vstup, pak trailing 2 × ATR14 (15M, k času vstupu) od nejlepšího close,
  schody    každý dosažený +kR posune stop na (k − 1)R (po +1R na vstup, po +2R na +1R …),
  chandelier od začátku stop = max(počáteční, nejlepší close − 3 × ATR14 15M),
  cíl 2R    pevný cíl bez posouvání (srovnání).
  Stop i cíl ve stejné svíčce = stop; stop se posouvá až po kontrole zásahu v dané svíčce (konzervativně).
Náklady: 0,07 %/stranu (futures taker + skluz) a 0,10 %/stranu (horší skluz na těsných stopech). Funding se nepočítá.
Srovnání: náhodné vstupy (stejná mince, směr, stop v %, ATR v %, výstup; 20 opakování na obchod).
Páka: potřebná páka = riziko účtu / vzdálenost stopu (celý účet jako marže, cross). Reportuje se rozdělení pro riziko
  1 % a podíl obchodů, kde by izolovaná pozice s pákou 20× / 50× byla likvidována dřív, než ji zavře stop
  (likvidace ≈ 1 / páka − 0,5 % udržovací marže).
Účet: 1 000 USD, riziko 1 / 2 / 5 / 10 % na obchod, chronologicky a jen jedna pozice naráz přes všechny mince,
  + 10 000 náhodných pořadí (konec na pořadí nezávisí, propad ano): medián max. propadu, P(propad ≥ 30 % / 50 %).
Kritérium (předem): výstup projde, jen když při 0,07 % je Ø R > 0 v obou polovinách i v OOS (posledních 30 %)
  a poráží náhodu o ≥ 0,05 R. Pak teprve papírově na nových datech, ne naostro.

    python3 research/experiments/scalp15.py [cache_dir]          # stahuje 15M z OKX (GitHub Actions)
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
from reversal import atr  # noqa: E402

COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
EXITS = ["BE+trail", "schody", "chandelier", "cíl 2R"]
FILTERS = {"F0": "1H trend", "F1": "1H trend + denní směr"}
MAX_BARS = 2 * 96
LOOKBACK, VOL_MULT, SWING = 20, 1.5, 6
MIN_STOP, MAX_STOP = 0.003, 0.015


def find_setups(m15):
    """Spouštěče na zavření 15M svíčky; 1H/1D filtr jen z uzavřených svíček (bez pohledu dopředu)."""
    a15 = atr(m15)
    hi_prev = m15["High"].shift(1).rolling(LOOKBACK).max()
    lo_prev = m15["Low"].shift(1).rolling(LOOKBACK).min()
    vol_ok = m15["Volume"] >= VOL_MULT * m15["Volume"].shift(1).rolling(LOOKBACK).mean()
    h1 = m15.resample("1h").agg(OHLC).dropna()
    d1 = m15.resample("1D").agg(OHLC).dropna()
    up1h = (h1["Close"] > st.ema(h1["Close"], 50)).astype(float)
    up1d = (d1["Close"] > st.ema(d1["Close"], 50)).astype(float)
    up1d[st.ema(d1["Close"], 50).index[:50]] = np.nan                     # EMA50 bez rozjezdu se nebere
    close_t = m15.index + pd.Timedelta(minutes=15)                         # svíčka je uzavřená v čase open + 15 min
    trend1h = up1h.set_axis(h1.index + pd.Timedelta(hours=1))             # 1H hodnota platí až po zavření
    trend1d = up1d.set_axis(d1.index + pd.Timedelta(days=1))
    t1h = trend1h.reindex(close_t, method="ffill").values
    t1d = trend1d.reindex(close_t, method="ffill").values
    out = []
    for i in range(max(LOOKBACK, SWING) + 1, len(m15)):
        if not vol_ok.iat[i] or np.isnan(t1h[i]):
            continue
        c = m15["Close"].iat[i]
        long = c > hi_prev.iat[i] and t1h[i] == 1
        short = c < lo_prev.iat[i] and t1h[i] == 0
        if not (long or short):
            continue
        a = float(a15.iat[i])
        seg = m15.iloc[i - SWING + 1:i + 1]
        stop = seg["Low"].min() - 0.1 * a if long else seg["High"].max() + 0.1 * a
        dist = abs(c - stop) / c
        if dist < MIN_STOP:
            stop, dist = (c * (1 - MIN_STOP) if long else c * (1 + MIN_STOP)), MIN_STOP
        if dist > MAX_STOP:
            continue
        day_ok = not np.isnan(t1d[i]) and (t1d[i] == 1) == long
        out.append({"i": i, "time": m15.index[i], "dir": "long" if long else "short", "entry": float(c),
                    "stop": float(stop), "atr": a, "f1": day_ok})
    return out


def simulate(hi, lo, cl, s, exit_kind, cost_pct):
    """R po nákladech a počet svíček v obchodu; hi/lo/cl = svíčky PO vstupu."""
    long = s["dir"] == "long"
    sign = 1 if long else -1
    e, stop = s["entry"], s["stop"]
    risk = abs(e - stop)
    c = cost_pct / 100
    n = min(len(cl), MAX_BARS)
    if not n:
        return None

    def r_at(px):
        return (sign * (px - e) - c * (e + px)) / risk

    tgt = e + sign * 2 * risk
    armed, best, step = False, e, 0
    for i in range(n):
        if (lo[i] <= stop) if long else (hi[i] >= stop):
            return r_at(stop), i + 1
        if exit_kind == "cíl 2R":
            if (hi[i] >= tgt) if long else (lo[i] <= tgt):
                return r_at(tgt), i + 1
            continue
        best = max(best, cl[i]) if long else min(best, cl[i])
        fav = (hi[i] - e) / risk if long else (e - lo[i]) / risk         # nejlepší pohyb v R v této svíčce
        if exit_kind == "BE+trail":
            if not armed and fav >= 1:
                armed, stop = True, max(stop, e) if long else min(stop, e)
            if armed:
                tr = best - sign * 2 * s["atr"]
                stop = max(stop, tr) if long else min(stop, tr)
        elif exit_kind == "schody":
            k = int(np.floor(fav))
            if k > step:
                step = k
                new = e + sign * (k - 1) * risk
                stop = max(stop, new) if long else min(stop, new)
        elif exit_kind == "chandelier":
            tr = best - sign * 3 * s["atr"]
            stop = max(stop, tr) if long else min(stop, tr)
    return r_at(cl[n - 1]), n


def run(trades, data, exit_kind, cost):
    """Jedna pozice na minci naráz: další spouštěč až po výstupu z předchozího obchodu."""
    out, busy = [], {}
    for t in trades:
        if t["i"] <= busy.get(t["coin"], -1):
            continue
        hi, lo, cl = data[t["coin"]]
        j = t["i"] + 1
        res = simulate(hi[j:], lo[j:], cl[j:], t, exit_kind, cost)
        if res is None:
            continue
        r, bars = res
        busy[t["coin"]] = t["i"] + bars
        out.append({**t, "r": r, "bars": bars})
    return out


def random_r(trades, data, exit_kind, cost, rng, reps=20):
    rs = []
    for t in trades:
        hi, lo, cl = data[t["coin"]]
        pct = abs(t["entry"] - t["stop"]) / t["entry"]
        sign = 1 if t["dir"] == "long" else -1
        for _ in range(reps):
            i = int(rng.integers(200, len(cl) - MAX_BARS - 1))
            e = float(cl[i])
            s = {"dir": t["dir"], "entry": e, "stop": e * (1 - sign * pct), "atr": t["atr"] * e / t["entry"]}
            res = simulate(hi[i + 1:], lo[i + 1:], cl[i + 1:], s, exit_kind, cost)
            if res:
                rs.append(res[0])
    return float(np.mean(rs)) if rs else float("nan")


def account(tr, f, start=1000.0):
    """Chronologicky, jen jedna pozice naráz přes všechny mince."""
    eq, peak, dd, free = start, start, 0.0, pd.Timestamp.min.tz_localize("UTC")
    for t in tr:
        if t["time"] < free:
            continue
        eq *= max(1 + f * t["r"], 0.0)
        peak = max(peak, eq)
        dd = max(dd, 1 - eq / peak)
        free = t["time"] + pd.Timedelta(minutes=15 * t["bars"])
    return eq, dd


def path_stats(rs, f, start=1000.0):
    eq = start * np.cumprod(np.maximum(1 + f * rs, 0.0))
    peak = np.maximum.accumulate(np.concatenate([[start], eq]))[1:]
    return eq[-1], (1 - eq / peak).max()


def ci(x):
    x = np.asarray(x)
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0.0


def main():
    data, trades = {}, []
    for c in COINS:
        m15 = okx_15m(c)
        data[c] = (m15["High"].values, m15["Low"].values, m15["Close"].values)
        found = find_setups(m15)
        for s in found:
            s["coin"] = c
        trades += found
        print(f"{c}: {len(m15)} svíček {m15.index[0]:%Y-%m-%d} – {m15.index[-1]:%Y-%m-%d}, spouštěčů {len(found)}", flush=True)
    trades.sort(key=lambda t: t["time"])
    print(f"\nSpouštěčů celkem: {len(trades)}, long {sum(t['dir'] == 'long' for t in trades)}, "
          f"short {sum(t['dir'] == 'short' for t in trades)}, s denním směrem (F1) {sum(t['f1'] for t in trades)}")
    sp = pd.Series([abs(t["entry"] - t["stop"]) / t["entry"] * 100 for t in trades])
    print(f"stop od vstupu: medián {sp.median():.2f} %, 10.–90. percentil {sp.quantile(.1):.2f}–{sp.quantile(.9):.2f} %")
    lev = 1.0 / sp                                                          # páka pro riziko 1 % účtu
    print(f"potřebná páka při riziku 1 % účtu (celý účet jako marže): medián {lev.median():.1f}×, "
          f"90. percentil {lev.quantile(.9):.1f}×, max {lev.max():.1f}×")
    for L in (20, 50):
        liq = (1 / L - 0.005) * 100
        print(f"izolovaná páka {L}×: likvidace ≈ {liq:.2f} % od vstupu → stop dál než likvidace u "
              f"{(sp > liq).mean() * 100:.0f} % obchodů (pozice by skončila likvidací, ne stopem)")

    rng = np.random.default_rng(11)
    keep = {}
    for fk, flabel in FILTERS.items():
        pool = trades if fk == "F0" else [t for t in trades if t["f1"]]
        for cost in (0.07, 0.10):
            print(f"\n=== {fk} {flabel} · náklady {cost} % na stranu ===")
            print("| Výstup | Obchodů | Úspěšnost | Ø R ± CI | Medián | Ø držení | 1. / 2. polovina | OOS ± CI | Náhoda Ø R | Σ R |")
            print("|---|---|---|---|---|---|---|---|---|---|")
            for ex in EXITS:
                tr = run(pool, data, ex, cost)
                if len(tr) < 2:
                    print(f"| {ex} | {len(tr)} | – | – | – | – | – | – | – | – |")
                    continue
                rs = np.array([t["r"] for t in tr])
                half, cut = len(rs) // 2, int(len(rs) * 0.7)
                rnd = random_r(tr, data, ex, cost, rng)
                hours = np.mean([t["bars"] for t in tr]) / 4
                print(f"| {ex} | {len(rs)} | {(rs > 0).mean() * 100:.0f} % | {rs.mean():+.3f} ± {ci(rs):.2f} | "
                      f"{np.median(rs):+.2f} | {hours:.1f} h | {rs[:half].mean():+.3f} / {rs[half:].mean():+.3f} | "
                      f"{rs[cut:].mean():+.3f} ± {ci(rs[cut:]):.2f} | {rnd:+.3f} | {rs.sum():+.1f} |")
                keep[(fk, cost, ex)] = (tr, rs, rnd)

    print("\n=== Kritérium (náklady 0,07 %): obě poloviny > 0, OOS > 0, náskok proti náhodě ≥ 0,05 R ===")
    for (fk, cost, ex), (tr, rs, rnd) in keep.items():
        if cost != 0.07:
            continue
        half, cut = len(rs) // 2, int(len(rs) * 0.7)
        ok = rs[:half].mean() > 0 and rs[half:].mean() > 0 and rs[cut:].mean() > 0 and rs.mean() - rnd >= 0.05
        print(f"  {fk} {ex}: {'✅ prošlo' if ok else '❌ neprošlo'} (Ø {rs.mean():+.3f}, náhoda {rnd:+.3f})")

    print("\n=== Účet 1 000 USD, náklady 0,07 %, jedna pozice naráz přes všechny mince ===")
    print("| Filtr | Výstup | Riziko | Obchodů | Konec | Max. propad (skutečné pořadí) | Medián max. propadu (10 000 pořadí) | P(propad ≥ 30 %) | P(propad ≥ 50 %) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for (fk, cost, ex), (tr, rs, rnd) in keep.items():
        if cost != 0.07:
            continue
        free, seq = pd.Timestamp.min.tz_localize("UTC"), []
        for t in tr:                                                        # stejné obchody, které vzal účet
            if t["time"] >= free:
                seq.append(t["r"])
                free = t["time"] + pd.Timedelta(minutes=15 * t["bars"])
        seq = np.array(seq)
        for f in (0.01, 0.02, 0.05, 0.10):
            end, dd = account(tr, f)
            sims = np.array([path_stats(rng.permutation(seq), f) for _ in range(10000)])
            print(f"| {fk} | {ex} | {f * 100:.0f} % | {len(seq)} | {end:,.0f} | {dd * 100:.0f} % | {np.median(sims[:, 1]) * 100:.0f} % | "
                  f"{(sims[:, 1] >= 0.3).mean() * 100:.1f} % | {(sims[:, 1] >= 0.5).mean() * 100:.1f} % |")

    print("\nmince (F0, BE+trail, 0,07 %, Ø R):")
    tr = keep.get(("F0", 0.07, "BE+trail"), ([], None, None))[0]
    for c in COINS:
        r = [t["r"] for t in tr if t["coin"] == c]
        print(f"  {c}: n={len(r)}, Ø {np.mean(r) if r else float('nan'):+.3f}")


if __name__ == "__main__":
    main()
