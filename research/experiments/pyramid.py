"""Přikupování do vydělávající pozice (pyramiding) + delší držení na dnešních denních signálech (stanoveno PŘEDEM, 25. 10. 2026).

Signály: donchian_1d + pullback_1d z scanner/config.yaml (vč. filtru paniky), 8 mincí, denní svíčky ~10 let.
Varianty (stejné signály, vstup na zavření signální svíčky, náklady 0,15 % na stranu u každého kusu):
  P0  dnes: polovina na T1, zbytek trailing 3 ATR, max. 20 dní (scanner/evaluate.simulate)
  P1  přikupování: start 1 kus s rizikem 0,5 R (R = vzdálenost vstup–stop signálu); za každý pohyb o +1 ATR (ATR signálu)
      od vstupu přidat kus stejné velikosti, max. 4 kusy; po přidání stop všech kusů = cena přidání − 2 ATR (long),
      nikdy pod dosavadní stop; trailing: nejlepší zavírací cena − 3 ATR; max. 60 dní. Pořadí ve svíčce: stop, pak přidání.
  P2  jako P1, max. 20 dní (samotný efekt přikupování)
  P3  bez přikupování, celá pozice (1 R), trailing 3 ATR od začátku, max. 60 dní (samotný efekt delšího držení)
Výsledek obchodu v R (1 R = riziko plné pozice dneška). Portfolio s limity desku (max. 2 na strategii a směr, max. 3 nové
za den, 1 na minci a strategii). IS/OOS 70/30, odložený rok od 25. 10. 2025, roky, MAR, podíl ≥ 5 / 10 / 20 R,
výzva malého účtu (100 USD, riziko 1 / 2 / 5 % na obchod, chronologicky).

    python3 research/experiments/pyramid.py scanner/cache
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, setups as st  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COST = 0.15 / 100
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
HOLDOUT = pd.Timestamp("2025-10-25", tz="UTC")
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
LIVE = [s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")]


def pyramid(sig, after, max_hold, adds=True, unit_r=0.5, max_units=4, trail=3.0, add_stop=2.0):
    long = sig.direction == "long"
    sg = 1 if long else -1
    e0, stop = sig.entry, sig.stop
    risk, atr = abs(e0 - stop), sig.meta["atr"]
    unit = unit_r / risk if adds else 1.0 / risk                 # velikost kusu (R na jednotku ceny)
    units = [e0]
    best = e0
    hi, lo, cl = after["High"].values, after["Low"].values, after["Close"].values
    n = min(len(cl), max_hold)
    if n == 0:
        return None

    def close_all(px):
        return sum(unit * (sg * (px - e) - COST * (e + px)) for e in units)
    for i in range(n):
        if (lo[i] <= stop) if long else (hi[i] >= stop):
            return {"r": close_all(stop), "bars": i + 1, "units": len(units)}
        while adds and len(units) < max_units:
            lvl = e0 + sg * len(units) * atr
            if not ((hi[i] >= lvl) if long else (lo[i] <= lvl)):
                break
            units.append(lvl)
            ns = lvl - sg * add_stop * atr
            stop = max(stop, ns) if long else min(stop, ns)
        best = max(best, cl[i]) if long else min(best, cl[i])
        tr = best - sg * trail * atr
        stop = max(stop, tr) if long else min(stop, tr)
    if n < max_hold:
        return None                                              # obchod ještě běží na konci dat
    return {"r": close_all(cl[n - 1]), "bars": n, "units": len(units)}


def build():
    rows = []
    for c in COINS:
        df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_1d_3650d.csv", index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna().iloc[:-1]
        for s in LIVE:
            rule_p, ex, min_rr = ev.split_params(strategy_params(s), s["setup"])
            for g in st.find(s["setup"], df, "both", rule_p):
                if g.rr[0] < min_rr:
                    continue
                h = g.meta["hold_index"]
                after = df.iloc[h + 1:]
                p0 = ev.simulate(g, after, ex["max_hold_bars"], ex["split"], COST * 100, ex["trail_atr"])
                v = {"P0": None if p0["result"] == "open" else {"r": p0["r"], "bars": p0["bars"], "units": 1},
                     "P1": pyramid(g, after, 60), "P2": pyramid(g, after, 20), "P3": pyramid(g, after, 60, adds=False)}
                if any(x is None for x in v.values()):
                    continue
                base = {"coin": c, "strategy": s["name"], "time": g.hold_time, "dir": g.direction, "rr": g.rr[0]}
                for k, x in v.items():
                    rows.append({**base, "var": k, "r": x["r"], "units": x["units"],
                                 "exit": df.index[min(h + x["bars"], len(df) - 1)]})
    return pd.DataFrame(rows)


def portfolio(t):
    open_, taken, per_day = [], [], {}
    for x in t.sort_values(["time", "rr"], ascending=[True, False]).to_dict("records"):
        open_ = [o for o in open_ if o["exit"] > x["time"]]
        if any(o["coin"] == x["coin"] and o["strategy"] == x["strategy"] for o in open_):
            continue
        if sum(1 for o in open_ if o["strategy"] == x["strategy"] and o["dir"] == x["dir"]) >= 2:
            continue
        d = x["time"].date()
        if per_day.get(d, 0) >= 3:
            continue
        per_day[d] = per_day.get(d, 0) + 1
        open_.append(x)
        taken.append(x)
    return pd.DataFrame(taken)


def stats(p, start=None, end=None):
    q = p[(p["time"] >= (start or p["time"].min())) & (p["time"] < (end or p["time"].max() + pd.Timedelta(days=1)))]
    if q.empty:
        return {}
    eq = q.sort_values("exit")["r"].cumsum()
    dd = float((eq.cummax().clip(lower=0) - eq).max())
    yrs = max((q["time"].max() - q["time"].min()).days / 365.25, 0.5)
    r = q["r"]
    return {"n": len(q), "Ø R": round(r.mean(), 3), "± CI": round(1.96 * r.std(ddof=1) / np.sqrt(len(r)), 3),
            "R/rok": round(r.sum() / yrs, 1), "max DD": round(dd, 1), "MAR": round(r.sum() / yrs / max(dd, 3), 2),
            "úspěšnost": f"{(r > 0).mean() * 100:.0f} %", "≥5R": f"{(r >= 5).mean() * 100:.1f} %",
            "≥10R": f"{(r >= 10).mean() * 100:.1f} %", "≥20R": f"{(r >= 20).mean() * 100:.1f} %",
            "max R": round(r.max(), 1), "min R": round(r.min(), 2)}


def main():
    df = build()
    print(f"signálů: {df[df['var'] == 'P0'].shape[0]} ({df['time'].min():%Y-%m} – {df['time'].max():%Y-%m})\n")
    ports = {k: portfolio(df[df["var"] == k]) for k in ("P0", "P1", "P2", "P3")}
    names = {"P0": "P0 dnes", "P1": "P1 přikupování + 60 dní", "P2": "P2 přikupování, 20 dní", "P3": "P3 bez přikup., 60 dní"}
    rows = []
    for k, p in ports.items():
        cut = p["time"].iloc[int(len(p) * 0.7)]
        s_all, s_is, s_oos, s_h = stats(p), stats(p, end=cut), stats(p, start=cut, end=HOLDOUT), stats(p, start=HOLDOUT)
        rows.append({"varianta": names[k], **s_all, "IS Ø R": s_is.get("Ø R"), "OOS Ø R": s_oos.get("Ø R"),
                     "OOS MAR": s_oos.get("MAR"), "odložený rok Σ R": round(p[p["time"] >= HOLDOUT]["r"].sum(), 1),
                     "odl. max DD": s_h.get("max DD")})
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nPo letech (Σ R, portfolio):")
    for k, p in ports.items():
        print(f"  {names[k]:26} {p.groupby(p['time'].dt.year)['r'].sum().round(1).to_dict()}")
    print("\nPárově na stejných signálech (Ø rozdíl R/signál ± CI):")
    w = df.pivot_table(index=["coin", "strategy", "time", "dir"], columns="var", values="r")
    for k in ("P1", "P2", "P3"):
        d = w[k] - w["P0"]
        dh = d[d.index.get_level_values("time") >= HOLDOUT]
        print(f"  {k} − P0: {d.mean():+.3f} ± {1.96 * d.std(ddof=1) / np.sqrt(len(d)):.3f} (n={len(d)}); "
              f"odložený rok {dh.mean():+.3f} (n={len(dh)})")
    print("\nPočet kusů u P1 (podíl obchodů):", ports["P1"]["units"].value_counts(normalize=True).sort_index().round(2).to_dict())
    print("Strategie (Ø R portfolio):", {k: p.groupby("strategy")["r"].mean().round(3).to_dict() for k, p in ports.items()})
    print("\nVýzva: 100 USD, chronologicky, zisky reinvestované (riziko z aktuálního účtu):")
    for k, p in ports.items():
        rs = p.sort_values("exit")["r"].values
        out = []
        for f in (0.01, 0.02, 0.05):
            eq, low = 100.0, 100.0
            for r in rs:
                eq *= max(1 + f * r, 0)
                low = min(low, eq)
            out.append(f"{f * 100:.0f} %: konec {eq:,.0f} USD (min {low:,.0f})")
        print(f"  {names[k]:26} " + " · ".join(out))


if __name__ == "__main__":
    main()
