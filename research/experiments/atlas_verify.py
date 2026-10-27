"""Nezávislé ověření kandidáta z atlasu: long 12H MACD (19, 39, 9), vstup při protnutí signální linie zespodu,
výstup při opačném protnutí (na open další svíčky), bez stopu, max. 300 svíček, poplatky 0,05 % na stranu.

Samostatný kód (prostá smyčka v pandas, žádné sdílené funkce s atlasem), stejná data OKX 1H od 2019.
Kontroly:
  1. výsledek na stejných pravidlech (musí se shodovat s atlasem: IS +0,78 / OOS +0,65 / HOLDOUT +0,19 R),
  2. vstup o 1 svíčku později (pohled do budoucnosti by se projevil prudkým zhoršením),
  3. účet: riziko 0,5 % účtu na obchod (2 ATR), všech 8 mincí souběžně – výnos a max. propad v %,
  4. výsledek po letech a po mincích, buy & hold pro srovnání.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.experiments.strategy_atlas import COINS, fetch, resample  # noqa: E402  (jen stažení dat)

CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cache")
COST = 0.0005
OOS, HOLD = pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")


def trades_for(df, delay=0):
    c = df["Close"]
    line = c.ewm(span=19, adjust=False, min_periods=39).mean() - c.ewm(span=39, adjust=False, min_periods=39).mean()
    sig = line.ewm(span=9, adjust=False, min_periods=9).mean()
    above = line > sig
    cross_up = above & ~above.shift(1, fill_value=False) & line.shift(1).notna() & sig.shift(1).notna()
    cross_dn = ~above & above.shift(1, fill_value=False) & line.notna() & sig.notna()
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - c.shift()).abs(), (df["Low"] - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    o = df["Open"].to_numpy(); cl = c.to_numpy(); idx = df.index
    ups, dns, a = cross_up.to_numpy(), cross_dn.to_numpy(), atr.to_numpy()
    out, busy_until = [], -1
    for i in np.flatnonzero(ups):
        e = i + 1 + delay
        if e >= len(o) or e <= busy_until or not (a[i] > 0):
            continue
        x = None
        for t in range(e, min(len(o), e + 300)):
            if dns[t]:
                x = (t + 1, o[t + 1]) if t + 1 < len(o) else (t, cl[t])
                break
        if x is None:
            t = min(len(o), e + 300) - 1
            x = (t, cl[t])
        g = x[1] / o[e] - 1 - 2 * COST
        rf = 2 * a[i] / o[e]
        out.append({"entry": idx[e], "exit": idx[x[0]], "ret": g, "r": g / rf, "rf": rf})
        busy_until = x[0]
    return pd.DataFrame(out)


def split(t):
    return {"IS": t[t.entry < OOS], "OOS": t[(t.entry >= OOS) & (t.entry < HOLD)], "HOLDOUT": t[t.entry >= HOLD]}


def account(all_trades, risk=0.005):
    """Riziko 0,5 % účtu na obchod (velikost pozice = risk / vzdálenost 2 ATR), výsledky připsány při výstupu."""
    t = all_trades.sort_values("exit")
    eq, peak, dd, path = 1.0, 1.0, 0.0, []
    for _, r in t.iterrows():
        eq *= 1 + risk * r["r"]
        peak = max(peak, eq)
        dd = max(dd, 1 - eq / peak)
        path.append((r["exit"], eq))
    return eq, dd, pd.Series(dict(path))


def main():
    rows, late, bh = [], [], {}
    for coin in COINS:
        df = resample(fetch(coin, "1h", "2019-01-01", CACHE), "12h")
        t = trades_for(df); t["coin"] = coin; rows.append(t)
        tl = trades_for(df, delay=1); tl["coin"] = coin; late.append(tl)
        bh[coin] = df["Close"].iloc[-1] / df["Close"].iloc[0] - 1
    T, TL = pd.concat(rows, ignore_index=True), pd.concat(late, ignore_index=True)
    print("== 1. Stejná pravidla (Ø R / n / Ø % na obchod / úspěšnost)")
    for k, s in split(T).items():
        print(f"{k:8s} n={len(s):4d}  Ø R={s.r.mean():+.3f}  t={s.r.mean() / (s.r.std(ddof=1) / np.sqrt(len(s))):+.2f}  "
              f"Ø %={s.ret.mean() * 100:+.2f}  win={(s.r > 0).mean():.0%}")
    print("== 2. Vstup o svíčku později")
    for k, s in split(TL).items():
        print(f"{k:8s} n={len(s):4d}  Ø R={s.r.mean():+.3f}")
    print("== 3. Účet, riziko 0,5 % na obchod, 8 mincí souběžně")
    for k, s in split(T).items():
        eq, dd, _ = account(s)
        years = max((s.exit.max() - s.entry.min()).days / 365.25, .1)
        print(f"{k:8s} konečný účet {eq:.2f}×  ročně {eq ** (1 / years) - 1:+.1%}  max. propad {dd:.1%}")
    eq, dd, path = account(T)
    years = (T.exit.max() - T.entry.min()).days / 365.25
    print(f"CELKEM   {eq:.2f}×  ročně {eq ** (1 / years) - 1:+.1%}  max. propad {dd:.1%}  ({years:.1f} let)")
    for risk in (0.0025, 0.01):
        e2, d2, _ = account(T, risk)
        print(f"  riziko {risk:.2%}: {e2:.2f}×, ročně {e2 ** (1 / years) - 1:+.1%}, max. propad {d2:.1%}")
    print("== 4. Po letech (Σ R, n) a po mincích (Ø R)")
    print(T.groupby(T.entry.dt.year).r.agg(["sum", "count", "mean"]).round(2).to_string())
    print(T.groupby("coin").r.agg(["mean", "count", "sum"]).round(2).to_string())
    print("Buy & hold za celé období:", {c: f"{v:+.0%}" for c, v in bh.items()})
    print("Nejdelší obchody (svíčky 12H):", ((T.exit - T.entry).dt.total_seconds() / 43200).describe().round(1).to_dict())


if __name__ == "__main__":
    main()
