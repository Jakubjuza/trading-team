"""Donchian ensemble s cílovou volatilitou (podle Zarattini, Pagani, Barbon: Catching Crypto Trends) a kombinace s jádrem.

Stanoveno PŘEDEM (26. 10. 2026), denní data 8 mincí, ~10 let, jen long (spot), náklady 0,15 % z obratu:
  • pro každou minci 5 modelů Donchian s okny N = 10, 20, 40, 80, 160 dní: model je long od zavření nad max. High
    předchozích N dní do zavření pod min. Low předchozích N/2 dní; signál mince = podíl modelů v longu (0–1),
  • váha mince = signál × min(1, 0,40 / roční volatilita za 30 dní) / 8 (cílová volatilita 40 % na minci),
  • rebalance denně na zavření, výnos následující den.
Srovnání: držení BTC, držení všech 8 mincí rovným dílem, jádro desku (donchian_1d + pullback_1d, limity portfolia,
riziko 0,5 % účtu na obchod, R připsané v den uzavření). Kombinace: jádro + ensemble (50 % kapitálu).
Měří se: roční výnos, volatilita, Sharpe, max. propad, výnos po letech, IS (do 10/2023) / OOS (10/2023–10/2025) /
odložený rok (od 25. 10. 2025), korelace denních výnosů jádra a ensemblu.

    python3 research/experiments/ensemble.py scanner/cache
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pyramid as P  # noqa: E402  (stejné signály a portfolio jádra)

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COINS = P.COINS
WINDOWS = [10, 20, 40, 80, 160]
COST = 0.0015
OOS, HOLD = pd.Timestamp("2023-10-25", tz="UTC"), pd.Timestamp("2025-10-25", tz="UTC")


def load(c):
    df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_1d_3650d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df[["Open", "High", "Low", "Close"]].dropna().iloc[:-1]


def coin_signal(df):
    sig = pd.DataFrame(index=df.index)
    for n in WINDOWS:
        up = df["Close"] > df["High"].rolling(n).max().shift(1)
        dn = df["Close"] < df["Low"].rolling(n // 2).min().shift(1)
        state, out = 0, []
        for u, d in zip(up.values, dn.values):
            state = 1 if u else (0 if d else state)
            out.append(state)
        sig[n] = out
    return sig.mean(axis=1)


def stats(r, start=None, end=None):
    r = r[(r.index >= (start or r.index[0])) & (r.index < (end or r.index[-1] + pd.Timedelta(days=1)))]
    eq = (1 + r).cumprod()
    yrs = len(r) / 365
    ann = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else np.nan
    vol = r.std() * np.sqrt(365)
    return {"výnos/rok": f"{ann * 100:+.1f} %", "volatilita": f"{vol * 100:.0f} %",
            "Sharpe": round(r.mean() * 365 / vol, 2) if vol else np.nan,
            "max propad": f"{(eq / eq.cummax() - 1).min() * 100:.0f} %"}


def main():
    frames = {c: load(c) for c in COINS}
    idx = frames["BTC"].index
    rets = pd.DataFrame({c: f["Close"].pct_change() for c, f in frames.items()}).reindex(idx)
    w = pd.DataFrame(0.0, index=idx, columns=COINS)
    for c, f in frames.items():
        s = coin_signal(f)
        vol = f["Close"].pct_change().rolling(30).std() * np.sqrt(365)
        w[c] = (s * np.minimum(1, 0.40 / vol) / len(COINS)).reindex(idx).fillna(0)
    turnover = w.diff().abs().sum(axis=1).fillna(0)
    ens = (w.shift(1) * rets.fillna(0)).sum(axis=1) - turnover * COST
    btc = rets["BTC"].fillna(0)
    ew = rets.mean(axis=1).fillna(0)
    # jádro: R uzavřených obchodů × 0,5 % účtu v den uzavření
    df = P.build()
    core_t = P.portfolio(df[df["var"] == "P0"])
    core = pd.Series(0.0, index=idx)
    for x in core_t.itertuples():
        d = x.exit.normalize()
        if d in core.index:
            core[d] += 0.005 * x.r
    start = idx[200]
    combo = core + 0.5 * ens
    series = {"BTC držení": btc, "8 mincí držení": ew, "Jádro (0,5 % riziko)": core, "Ensemble": ens,
              "Jádro + 50 % ensemble": combo}
    for name, r in series.items():
        r = r[r.index >= start]
        print(f"{name:24} celé: {stats(r)} | IS: {stats(r, end=OOS)['Sharpe']} · OOS: {stats(r, OOS, HOLD)['Sharpe']} · "
              f"odložený rok: {stats(r, HOLD)['výnos/rok']} (Sharpe {stats(r, HOLD)['Sharpe']})")
    print(f"\nkorelace denních výnosů jádro × ensemble: {core[core.index >= start].corr(ens[ens.index >= start]):+.2f}")
    print(f"Ø obrat ensemblu {turnover[turnover.index >= start].mean() * 365:.1f}× ročně, Ø expozice {w.sum(axis=1)[w.index >= start].mean() * 100:.0f} %")
    print("\nPo letech (výnos %):")
    for name, r in series.items():
        r = r[r.index >= start]
        print(f"  {name:24} " + str({int(y): round(((1 + g).prod() - 1) * 100) for y, g in r.groupby(r.index.year)}))


if __name__ == "__main__":
    main()
