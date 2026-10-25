"""Vstup na 15M při začínajícím uptrendu po velkém propadu a panice (stanoveno PŘEDEM, 25. 10. 2026).

Data: 15M svíčky OKX (spot USDT, s objemem), 8 mincí, ~2 roky; 1H, 4H a 1D se skládají z 15M (jen uzavřené svíčky).
Kontext (vše k poslední UZAVŘENÉ svíčce):
  1. propad: min. Low za posledních 30 dní ≤ 0,75 × max. High za 60 dní před tím (≥ 25 % pod maximem)
  2. panika pak klid: pořadí ATR % na 4H (okno 1 080 svíček ≈ 180 dní) bylo za posledních 180 svíček 4H (30 dní)
     ≥ 0,90 a teď je ≤ 0,50
  3. uptrend na 1H: fraktály (5 svíček, potvrzené 2 svíčky po vrcholu): poslední 2 maxima rostou a poslední 2 minima rostou
  4. malé svíčky: Ø rozsah posledních 8 svíček 15M ≤ 0,7 × Ø rozsah posledních 96 svíček
Vstup: 15M svíčka zavře nad posledním fraktálovým maximem 1H (předchozí 15M zavřela pod ním) → long na zavření.
Stop: poslední fraktálové minimum 1H − 0,1 × ATR14 15M, min. 0,3 % od vstupu. Max. 1 vstup na minci za 3 dny.
Výstupy (všechny reportované): po +2R stop na vstup + trailing 3 × ATR 1H; cíl 10R; cíl 20R; max. 14 dní;
  stop i cíl ve stejné svíčce = stop. Náklady 0,07 % (futures) a 0,15 % (spot) na stranu.
Rozdělení podle objemu průrazové 15M svíčky vs. průměr 20 svíček: nízký (< 1×) / vysoký (≥ 1×).
Srovnání: náhodný long (stejná mince, stejný stop v %, stejný výstup, 20 opakování); výzva 100 USD s reinvesticí.

    python3 research/experiments/recovery.py [cache_dir]          # stahuje 15M z OKX (GitHub Actions)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mtf15 import okx_15m, OHLC  # noqa: E402
from reversal import atr, challenge  # noqa: E402

COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
EXITS = ["T2R+trail", "cíl 10R", "cíl 20R"]
MAX_BARS = 14 * 96


def last_closed(series, times, bar):
    """Hodnota série k poslední svíčce uzavřené do času t (index = začátek svíčky)."""
    pos = np.searchsorted(series.index.values, (times - bar).values, side="right") - 1
    vals = series.values
    return np.where(pos >= 0, vals[np.clip(pos, 0, None)], np.nan)


def pivots(h1):
    """Fraktály 5 svíček; hodnota platí až od uzavření 2. svíčky po vrcholu (kauzálně)."""
    hi, lo = h1["High"].values, h1["Low"].values
    ph, pl = [], []
    for j in range(2, len(h1) - 2):
        t = h1.index[j + 2] + pd.Timedelta(hours=1)                      # čas potvrzení
        if hi[j] > max(hi[j - 2:j]) and hi[j] > max(hi[j + 1:j + 3]):
            ph.append((t, hi[j]))
        if lo[j] < min(lo[j - 2:j]) and lo[j] < min(lo[j + 1:j + 3]):
            pl.append((t, lo[j]))
    return ph, pl


def find_setups(m15):
    idx = m15.index
    d1 = m15.resample("1D").agg(OHLC).dropna()
    h4 = m15.resample("4h").agg(OHLC).dropna()
    h1 = m15.resample("1h").agg(OHLC).dropna()
    # 1. propad (denní)
    low30 = d1["Low"].rolling(30).min()
    high60 = d1["High"].shift(30).rolling(60).max()
    crash = (low30 <= 0.75 * high60).astype(float)
    crash_ok = last_closed(crash, idx, pd.Timedelta(days=1)) == 1
    # 2. panika → klid (4H)
    ap = atr(h4) / h4["Close"]
    rank = ap.rolling(1080, min_periods=300).apply(lambda w: (w[-1] >= w).mean(), raw=True)
    panic_recent = rank.rolling(180).max()
    rank_now = last_closed(rank, idx, pd.Timedelta(hours=4))
    panic_ok = (last_closed(panic_recent, idx, pd.Timedelta(hours=4)) >= 0.90) & (rank_now <= 0.50)
    # 4. malé svíčky (15M, jen předchozí svíčky)
    rngs = (m15["High"] - m15["Low"])
    small = (rngs.shift(1).rolling(8).mean() <= 0.7 * rngs.shift(1).rolling(96).mean()).values
    a15 = atr(m15).values
    a1 = atr(h1)
    vol_ratio = (m15["Volume"] / m15["Volume"].shift(1).rolling(20).mean()).values
    # 3. struktura 1H
    ph, pl = pivots(h1)
    ph_t = np.array([p[0] for p in ph], dtype="datetime64[ns]")
    pl_t = np.array([p[0] for p in pl], dtype="datetime64[ns]")
    ph_v, pl_v = np.array([p[1] for p in ph]), np.array([p[1] for p in pl])
    out, last = [], None
    close = m15["Close"].values
    end_times = (idx + pd.Timedelta(minutes=15)).values                      # čas uzavření 15M svíčky
    for i in range(100, len(m15)):
        if not (crash_ok[i] and panic_ok[i] and small[i]):
            continue
        t_end = end_times[i]
        kh = np.searchsorted(ph_t, idx.values[i], side="right")            # potvrzené před otevřením svíčky
        kl = np.searchsorted(pl_t, idx.values[i], side="right")
        if kh < 2 or kl < 2:
            continue
        if not (ph_v[kh - 1] > ph_v[kh - 2] and pl_v[kl - 1] > pl_v[kl - 2]):
            continue
        level = ph_v[kh - 1]
        if not (close[i] > level and close[i - 1] <= level):
            continue
        if last is not None and idx[i] < last + pd.Timedelta(days=3):
            continue
        entry = float(close[i])
        stop = pl_v[kl - 1] - 0.1 * a15[i]
        if entry - stop < entry * 0.003:
            stop = entry * (1 - 0.003)
        if stop >= entry:
            continue
        a1h = float(last_closed(a1, pd.DatetimeIndex([idx[i]]), pd.Timedelta(hours=1))[0])
        out.append({"time": idx[i], "dir": "long", "entry": entry, "stop": float(stop), "atr1h": a1h,
                    "vol": "vysoký" if vol_ratio[i] >= 1 else "nízký", "t_end": t_end})
        last = idx[i]
    return out


def simulate(path, s, exit_kind, cost_pct):
    e, stop0 = s["entry"], s["stop"]
    risk = e - stop0
    c = cost_pct / 100
    r_at = lambda px: ((px - e) - c * (e + px)) / risk                       # noqa: E731
    hi, lo, cl = path["High"].values[:MAX_BARS], path["Low"].values[:MAX_BARS], path["Close"].values[:MAX_BARS]
    if not len(cl):
        return None
    if exit_kind == "T2R+trail":
        stop, armed, best = stop0, False, e
        for i in range(len(cl)):
            if lo[i] <= stop:
                return r_at(stop)
            if not armed and hi[i] >= e + 2 * risk:
                armed, stop = True, e
            if armed:
                best = max(best, cl[i])
                stop = max(stop, best - 3 * s["atr1h"])
        return r_at(cl[-1])
    tgt = e + float(exit_kind.split()[1].rstrip("R")) * risk
    for i in range(len(cl)):
        if lo[i] <= stop0:
            return r_at(stop0)
        if hi[i] >= tgt:
            return r_at(tgt)
    return r_at(cl[-1])


def main():
    data, trades = {}, []
    for c in COINS:
        m15 = okx_15m(c)
        data[c] = m15
        n0 = len(trades)
        for s in find_setups(m15):
            s["coin"] = c
            trades.append(s)
        print(f"{c}: {len(m15)} svíček, vstupů {len(trades) - n0}", flush=True)
    trades.sort(key=lambda t: t["time"])
    if not trades:
        print("žádné vstupy")
        return
    print(f"\nVstupů celkem: {len(trades)} ({trades[0]['time']:%Y-%m-%d} – {trades[-1]['time']:%Y-%m-%d}); "
          f"nízký objem {sum(t['vol'] == 'nízký' for t in trades)}, vysoký {sum(t['vol'] == 'vysoký' for t in trades)}")
    sp = pd.Series([(t["entry"] - t["stop"]) / t["entry"] * 100 for t in trades])
    print(f"stop od vstupu: medián {sp.median():.2f} %, 10.–90. percentil {sp.quantile(.1):.2f}–{sp.quantile(.9):.2f} %")
    print("vstupy: " + "; ".join(f"{t['coin']} {t['time']:%Y-%m-%d %H:%M}" for t in trades[:60]))
    rng = np.random.default_rng(7)
    res = {}
    for cost in (0.07, 0.15):
        print(f"\n=== náklady {cost} % na stranu ===")
        print("| Výstup | Skupina | n | Úspěšnost | Ø R ± CI | Medián | ≥ 10R | Největší | Σ R | Náhoda Ø R |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for ex in EXITS:
            rows = []
            for t in trades:
                m15 = data[t["coin"]]
                r = simulate(m15[m15.index > t["time"]], t, ex, cost)
                if r is not None:
                    rows.append((t, r))
            rnd = []
            for t, _ in rows:
                m15 = data[t["coin"]]
                pct = (t["entry"] - t["stop"]) / t["entry"]
                for _ in range(20):
                    i = int(rng.integers(200, len(m15) - 10))
                    e = float(m15["Close"].iat[i])
                    r = simulate(m15.iloc[i + 1:], {"entry": e, "stop": e * (1 - pct), "atr1h": t["atr1h"] * e / t["entry"]}, ex, cost)
                    if r is not None:
                        rnd.append(r)
            res[(cost, ex)] = np.array([r for _, r in rows])
            for grp in ("vše", "nízký", "vysoký"):
                rs = np.array([r for t, r in rows if grp == "vše" or t["vol"] == grp])
                if not len(rs):
                    continue
                ci = 1.96 * rs.std(ddof=1) / np.sqrt(len(rs)) if len(rs) > 1 else float("nan")
                print(f"| {ex} | {grp} objem | {len(rs)} | {(rs > 0).mean() * 100:.0f} % | {rs.mean():+.2f} ± {ci:.2f} | "
                      f"{np.median(rs):+.2f} | {(rs >= 10).mean() * 100:.1f} % | {rs.max():+.1f} | {rs.sum():+.1f} | "
                      f"{np.mean(rnd):+.2f} |")
        half = len(res[(cost, EXITS[0])]) // 2
        print("Poloviny období (Ø R): " + ", ".join(
            f"{ex}: {res[(cost, ex)][:half].mean():+.2f} / {res[(cost, ex)][half:].mean():+.2f}" for ex in EXITS))
    print("\n=== Výzva: 100 USD, náklady 0,07 %, reinvestice, 10 000 náhodných pořadí ===")
    print("| Výstup | Riziko/pokus | Konec (skutečné pořadí) | P(≥ 1 000 USD) | P(< 10 USD) | Medián konce |")
    print("|---|---|---|---|---|---|")
    for ex in EXITS:
        rs = res[(0.07, ex)]
        for f in (0.02, 0.05, 0.10):
            end, _, _ = challenge(rs, f)
            sims = np.array([challenge(rng.permutation(rs), f) for _ in range(10000)])
            print(f"| {ex} | {f * 100:.0f} % | {end:,.0f} | {(sims[:, 1] >= 1000).mean() * 100:.1f} % | "
                  f"{(sims[:, 2] < 10).mean() * 100:.1f} % | {np.median(sims[:, 0]):,.0f} |")


if __name__ == "__main__":
    main()
