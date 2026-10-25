"""„Chycení kapitulace“ – long na dně po panice, malé riziko, velký potenciál (stanoveno PŘEDEM, 25. 10. 2026).

Signál na denní svíčce i (8 mincí, denní data yfinance, Fear & Greed z alternative.me od 2/2018):
  1. Low_i ≤ 0,70 × max(High za předchozích 60 svíček)       (cena ≥ 30 % pod 60denním maximem)
  2. pořadí ATR % za 365 svíček ≥ 0,90                        (volatilita v horních 10 % roku – panika)
  3. min. Fear & Greed za dny i-2..i < 20                      (extrémní strach)
  4. Low_i < min(Low předchozích 20 svíček) a Close_i > toto minimum   (sweep nového minima a reclaim)
Vstup: Close_i. Stop: Low_i − 0,1 ATR, min. 1,5 % od vstupu. Celá pozice; po +2R stop na vstup, pak trailing 3 ATR,
max. 60 dní. Max. 1 signál na minci za 10 dní. Náklady 0,15 % na stranu.
Varianty pro srovnání (ne pro výběr): K-bez F&G (bez podmínky 3, data od 2016), náhodné vstupy (stejná mince, long,
stejný stop v ATR, stejný výstup, 20 opakování).
Měří se: počet, úspěšnost, Ø a medián R, podíl obchodů ≥ 5R / ≥ 10R, největší obchod, kolik celku dělají 3 nejlepší,
IS/OOS 70/30, roky.

    python3 research/experiments/capitulation.py [cache_dir]      # potřebuje alternative.me → GitHub Actions
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, setups as st  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
COST, HOLD, TRAIL, T1_R = 0.15, 60, 3.0, 2.0


def fear_greed():
    d = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=30).json()["data"]
    s = pd.Series({pd.Timestamp(int(x["timestamp"]), unit="s", tz="UTC").normalize(): int(x["value"]) for x in d})
    return s.sort_index()


def signals(df, fng=None):
    x = st.Ctx(df)
    hi60 = df["High"].rolling(60).max().shift(1).values
    lo20 = x.roll_min(20)
    rank = x.vol_rank(365)
    fmin = None
    if fng is not None:
        f = fng.reindex(df.index.normalize()).values
        fmin = pd.Series(f, index=df.index).rolling(3, min_periods=1).min().values
    out, last = [], -99
    for i in range(400, len(df) - 1):
        lo, cl = df["Low"].iat[i], df["Close"].iat[i]
        if np.isnan(hi60[i]) or np.isnan(lo20[i]) or np.isnan(rank[i]):
            continue
        if not (lo <= 0.70 * hi60[i] and rank[i] >= 0.90 and lo < lo20[i] and cl > lo20[i]):
            continue
        if fmin is not None and not (fmin[i] < 20):
            continue
        if i - last < 10:
            continue
        atr = x.atr[i]
        stop = min(lo - 0.1 * atr, cl * (1 - 0.015))
        risk = cl - stop
        out.append({"i": i, "time": df.index[i], "entry": cl, "stop": stop, "atr": atr, "stop_atr": risk / atr})
        last = i
    return out


def run(df, s):
    risk = s["entry"] - s["stop"]
    setup = {"direction": "long", "entry": s["entry"], "stop": s["stop"],
             "targets": [s["entry"] + T1_R * risk, s["entry"] + 50 * risk], "meta": {"atr": s["atr"]}}
    return ev.simulate(setup, df.iloc[s["i"] + 1:], HOLD, 0.0, COST, TRAIL)


def random_r(frames, trades, k=20, seed=7):
    rng = np.random.default_rng(seed)
    rs = []
    for t in trades:
        df = frames[t["coin"]]
        atr = st.Ctx(df).atr
        for _ in range(k):
            i = int(rng.integers(400, len(df) - 2))
            e, a = float(df["Close"].iat[i]), atr[i]
            res = run(df, {"i": i, "entry": e, "stop": e - t["stop_atr"] * a, "atr": a})
            if res["result"] != "open":
                rs.append(res["r"])
    return np.array(rs)


def describe(name, trades, rnd=None):
    if not trades:
        print(f"\n{name}: žádné obchody")
        return
    df = pd.DataFrame(trades).sort_values("time")
    r = df["r"]
    top3 = r.nlargest(3).sum()
    cut = df["time"].iloc[int(len(df) * 0.7)] if len(df) >= 5 else df["time"].iloc[-1]
    print(f"\n{name}: {len(df)} obchodů ({df['time'].min():%Y-%m} – {df['time'].max():%Y-%m})")
    print(f"  úspěšnost {(r > 0).mean() * 100:.0f} %, Ø {r.mean():+.2f} R ± {1.96 * r.std(ddof=1) / np.sqrt(len(r)):.2f}, "
          f"medián {r.median():+.2f} R, Σ {r.sum():+.1f} R")
    print(f"  ≥ 5R: {(r >= 5).mean() * 100:.0f} %, ≥ 10R: {(r >= 10).mean() * 100:.0f} %, největší {r.max():+.1f} R, "
          f"3 nejlepší = {top3:+.1f} R ({top3 / r.sum() * 100 if r.sum() > 0 else float('nan'):.0f} % celku)")
    print(f"  IS Ø {df[df['time'] < cut]['r'].mean():+.2f} R / OOS Ø {df[df['time'] >= cut]['r'].mean():+.2f} R "
          f"(OOS od {cut:%Y-%m-%d}, n={int((df['time'] >= cut).sum())})")
    print(f"  po letech: {df.groupby(df['time'].dt.year)['r'].sum().round(1).to_dict()}")
    print(f"  mince: {df.groupby('coin')['r'].agg(['count', 'sum']).round(1).to_dict('index')}")
    if rnd is not None and len(rnd):
        print(f"  náhodné vstupy (stejný stop a výstup): Ø {rnd.mean():+.2f} R, úspěšnost {(rnd > 0).mean() * 100:.0f} %, "
              f"≥ 5R {(rnd >= 5).mean() * 100:.0f} %")
    print("  obchody: " + "; ".join(f"{t.coin} {t.time:%Y-%m-%d} {t.r:+.1f}R" for t in df.itertuples()))


def main():
    fng = fear_greed()
    print(f"Fear & Greed: {len(fng)} dní od {fng.index[0]:%Y-%m-%d}")
    frames = {}
    for c in COINS:
        df = ev.load_history(f"{c}/USDT", "crypto", "1d", 3650, cache_dir=SP)
        frames[c] = df[["Open", "High", "Low", "Close", "Volume"]].dropna().iloc[:-1]
    for name, f in (("K – kapitulace (s Fear & Greed)", fng), ("K-bez F&G", None)):
        trades = []
        for c, df in frames.items():
            for s in signals(df, f):
                res = run(df, s)
                if res["result"] != "open":
                    trades.append({"coin": c, "time": s["time"], "r": res["r"], "stop_atr": s["stop_atr"],
                                   "stop_pct": (s["entry"] - s["stop"]) / s["entry"] * 100, "bars": res["bars"]})
        describe(name, trades, random_r(frames, trades) if trades else None)
        if trades:
            sp = pd.Series([t["stop_pct"] for t in trades])
            print(f"  stop od vstupu: medián {sp.median():.1f} %, rozsah {sp.min():.1f}–{sp.max():.1f} %")


if __name__ == "__main__":
    main()
