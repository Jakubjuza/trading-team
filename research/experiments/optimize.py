"""Hledání lepšího nastavení denních strategií – walk-forward + odložený finální test (stanoveno PŘEDEM, 25. 10. 2026).

Prostor (pro donchian_1d i pullback_1d zvlášť; vstupní pravidla jinak jako v config.yaml):
  max_hold_bars 20 / 40 / 60 · trail_atr 2 / 3 / 4 · split (podíl na T1) 0,5 / 0 · skip_weekends ne / ano ·
  panic_vol_rank 0,8 / vypnuto  → 72 nastavení na strategii;  váhy rizika (Donchian : pullback)
  1:1, 1:0,5, 0,5:1, 1:0, 0:1.
Měřítko: MAR = R za rok / největší propad v R, v portfoliu s limity desku (max. 2 otevřené na strategii a směr,
max. 3 nové za den). Náklady 0,15 %/stranu. Nastavení s < 30 obchody v trénovacím okně se nevybírá.
Walk-forward: testovací roky začínají 25. 10. 2020, 2021, 2022, 2023, 2024; výběr vždy jen z dat před nimi.
Odložený test: 25. 10. 2025 – 25. 10. 2026 – do výběru nevstupuje, vyhodnotí se jednou na konci.
Rozhodnutí: kandidát = nastavení vybrané na všech datech před odloženým testem. Navrhne se jen když porazí dnešní
nastavení ve walk-forward (MAR i R) A na odloženém testu. Jinak zůstává dnešní nastavení.

    python3 research/experiments/optimize.py scanner/cache
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, setups as st  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COST = 0.15
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
HOLDOUT = pd.Timestamp("2025-10-25", tz="UTC")
FOLDS = [pd.Timestamp(f"{y}-10-25", tz="UTC") for y in range(2020, 2025)]
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
LIVE = {s["name"]: s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")}
GRID = list(itertools.product([20, 40, 60], [2.0, 3.0, 4.0], [0.5, 0.0], [False, True], [0.8, 0.0]))
WEIGHTS = [(1, 1), (1, 0.5), (0.5, 1), (1, 0), (0, 1)]

frames = {}
for c in COINS:
    df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_1d_3650d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    frames[c] = df[["Open", "High", "Low", "Close", "Volume"]].dropna().iloc[:-1]


def key_of(name, g):
    return (name,) + g


def current_key(name):
    s = LIVE[name]
    return (name, s["exit"]["max_hold_bars"], float(s["exit"]["trail_atr"]), s["exit"]["split"],
            bool(s["params"].get("skip_weekends", False)), float(s["params"].get("panic_vol_rank", 0.0)))


def trades_for(name):
    """Obchody pro všech 72 nastavení jedné strategie: {klíč: [obchody]}."""
    s = LIVE[name]
    out = {}
    for skip_w, panic in itertools.product([False, True], [0.8, 0.0]):
        params = {**s["params"], "skip_weekends": skip_w, "panic_vol_rank": panic}
        rule_p, _, _ = ev.split_params({**params, "min_rr": s["min_rr"]}, s["setup"])
        sigs = [(c, sg) for c, df in frames.items() for sg in st.find(s["setup"], df, "both", rule_p) if sg.rr[0] >= s["min_rr"]]
        for hold, trail, split in itertools.product([20, 40, 60], [2.0, 3.0, 4.0], [0.5, 0.0]):
            lst = []
            for c, sg in sigs:
                df, h = frames[c], sg.meta["hold_index"]
                res = ev.simulate(sg, df.iloc[h + 1:], hold, split, COST, trail)
                if res["result"] == "open":
                    continue
                lst.append({"coin": c, "strategy": name, "time": sg.hold_time, "dir": sg.direction, "r": res["r"],
                            "rr": sg.rr[0], "exit": df.index[min(h + res["bars"], len(df) - 1)]})
            out[(name, hold, trail, split, skip_w, panic)] = lst
    return out


def portfolio(cands, weights=None):
    """Chronologicky s limity živého skeneru (max 2 na strategii a směr, max 3 nové za den, 1 na minci a strategii)."""
    cands = sorted(cands, key=lambda t: (t["time"], -t["rr"]))
    open_, taken, per_day = [], [], {}
    for t in cands:
        w = (weights or {}).get(t["strategy"], 1.0)
        if w <= 0:
            continue
        open_ = [o for o in open_ if o["exit"] > t["time"]]
        if any(o["coin"] == t["coin"] and o["strategy"] == t["strategy"] for o in open_):
            continue
        if sum(1 for o in open_ if o["strategy"] == t["strategy"] and o["dir"] == t["dir"]) >= 2:
            continue
        d = t["time"].date()
        if per_day.get(d, 0) >= 3:
            continue
        per_day[d] = per_day.get(d, 0) + 1
        x = {**t, "rs": t["r"] * w}
        open_.append(x)
        taken.append(x)
    return taken


def metrics(trades, start, end):
    t = [x for x in trades if start <= x["time"] < end]
    if not t:
        return {"n": 0, "r_yr": 0.0, "dd": 0.0, "mar": -9.0, "avg": 0.0, "sum": 0.0}
    df = pd.DataFrame(t).sort_values("exit")
    eq = df["rs"].cumsum()
    dd = float((eq.cummax().clip(lower=0) - eq).max())
    yrs = max((end - start).days / 365.25, 0.5)
    r_yr = df["rs"].sum() / yrs
    return {"n": len(df), "r_yr": round(r_yr, 2), "dd": round(dd, 1), "mar": round(r_yr / max(dd, 3.0), 3),
            "avg": round(df["rs"].mean(), 3), "sum": round(df["rs"].sum(), 1)}


def pick(allt, name, start, end):
    """Nejlepší nastavení strategie podle MAR v okně [start, end) – jen z minulosti."""
    best, best_m = None, None
    for g in GRID:
        k = key_of(name, g)
        m = metrics(portfolio(allt[k]), start, end)
        if m["n"] < 30:
            continue
        if best_m is None or m["mar"] > best_m["mar"]:
            best, best_m = k, m
    return best, best_m


def combo(allt, kd, kp, w):
    return portfolio(allt[kd] + allt[kp], {"donchian_1d": w[0], "pullback_1d": w[1]})


def pick_weights(allt, kd, kp, start, end):
    return max(WEIGHTS, key=lambda w: metrics(combo(allt, kd, kp, w), start, end)["mar"])


def main():
    allt = {**trades_for("donchian_1d"), **trades_for("pullback_1d")}
    t0 = min(x["time"] for v in allt.values() for x in v)
    cur_d, cur_p = current_key("donchian_1d"), current_key("pullback_1d")
    print(f"data od {t0:%Y-%m-%d}, nastavení: {len(GRID)} na strategii, dnešní: {cur_d[1:]} / {cur_p[1:]}\n")

    # --- walk-forward (jen data před odloženým testem) ---
    wf_new, wf_cur, picks = [], [], []
    for i, f in enumerate(FOLDS):
        end = FOLDS[i + 1] if i + 1 < len(FOLDS) else HOLDOUT
        kd, _ = pick(allt, "donchian_1d", t0, f)
        kp, _ = pick(allt, "pullback_1d", t0, f)
        w = pick_weights(allt, kd, kp, t0, f)
        picks.append((f, kd, kp, w))
        wf_new += [x for x in combo(allt, kd, kp, w) if f <= x["time"] < end]
        wf_cur += [x for x in combo(allt, cur_d, cur_p, (1, 1)) if f <= x["time"] < end]
        print(f"krok {f:%Y}: Donchian {kd[1:]}, pullback {kp[1:]}, váhy {w}")
    a, b = FOLDS[0], HOLDOUT
    m_new, m_cur = metrics(wf_new, a, b), metrics(wf_cur, a, b)
    print(f"\nWalk-forward {a:%Y-%m}–{b:%Y-%m} (mimo vzorek výběru):")
    print(f"  vybírané: {m_new}\n  dnešní:   {m_cur}")
    yrs = lambda tr: pd.DataFrame(tr).groupby(pd.DataFrame(tr)["time"].dt.year)["rs"].sum().round(1).to_dict() if tr else {}  # noqa: E731
    print(f"  po letech – vybírané {yrs(wf_new)}\n  po letech – dnešní   {yrs(wf_cur)}")

    # --- kandidát: výběr na všech datech před odloženým testem ---
    kd, md = pick(allt, "donchian_1d", t0, HOLDOUT)
    kp, mp = pick(allt, "pullback_1d", t0, HOLDOUT)
    w = pick_weights(allt, kd, kp, t0, HOLDOUT)
    print(f"\nKandidát: Donchian {kd[1:]} {md}\n          pullback {kp[1:]} {mp}\n          váhy {w}")
    ins_new = metrics(combo(allt, kd, kp, w), t0, HOLDOUT)
    ins_cur = metrics(combo(allt, cur_d, cur_p, (1, 1)), t0, HOLDOUT)
    print(f"  in-sample kandidát {ins_new}\n  in-sample dnešní   {ins_cur}")

    # --- odložený test (jednou) ---
    end = pd.Timestamp.now(tz="UTC")
    h_new = metrics(combo(allt, kd, kp, w), HOLDOUT, end)
    h_cur = metrics(combo(allt, cur_d, cur_p, (1, 1)), HOLDOUT, end)
    print(f"\nODLOŽENÝ TEST {HOLDOUT:%Y-%m-%d} – {end:%Y-%m-%d}:\n  kandidát {h_new}\n  dnešní   {h_cur}")

    # měsíční bootstrap rozdílu (odložený test)
    def monthly(tr):
        t = [x for x in tr if x["time"] >= HOLDOUT]
        return pd.DataFrame(t).set_index("exit")["rs"].resample("ME").sum() if t else pd.Series(dtype=float)
    j = pd.concat([monthly(combo(allt, kd, kp, w)), monthly(combo(allt, cur_d, cur_p, (1, 1)))], axis=1).fillna(0)
    if len(j) > 3:
        d = (j.iloc[:, 0] - j.iloc[:, 1]).values
        rng = np.random.default_rng(1)
        boots = [rng.choice(d, len(d)).sum() for _ in range(5000)]
        print(f"  rozdíl Σ R kandidát − dnešní: {d.sum():+.1f} R, 90% interval {np.percentile(boots, 5):+.1f} až {np.percentile(boots, 95):+.1f}")
    # robustnost kandidáta: sousedé (jedna změna parametru) na datech před testem
    print("\nSousední nastavení kandidáta (MAR před testem, jen strategie zvlášť):")
    for k in (kd, kp):
        base = metrics(portfolio(allt[k]), t0, HOLDOUT)["mar"]
        neigh = []
        for i, vals in enumerate([[20, 40, 60], [2.0, 3.0, 4.0], [0.5, 0.0], [False, True], [0.8, 0.0]]):
            for v in vals:
                if v != k[i + 1]:
                    nk = k[:i + 1] + (v,) + k[i + 2:]
                    neigh.append(metrics(portfolio(allt[nk]), t0, HOLDOUT)["mar"])
        print(f"  {k}: MAR {base}, sousedé Ø {np.mean(neigh):.3f} (min {min(neigh):.3f}, max {max(neigh):.3f})")


if __name__ == "__main__":
    main()
