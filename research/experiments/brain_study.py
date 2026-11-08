#!/usr/bin/env python3
"""🧠 Mozek města – studie: kupole podle rizika × ziskovosti, čtvrti podle stylu a nasazování podle fáze trhu.

Zadání uživatele (8. 11. 2026): strategie rozdělit do víc kupolí podle riskantnosti a ziskovosti a nechat „mozek“
rozhodovat, co kdy nasadit – jako jeden organismus. Postup zvolen: NEJDŘÍV TEST, pak město. Jen papír, nic se nemění
na skeneru, registru, riziku, demu ani penězích.

Stanoveno PŘEDEM (8. 11. 2026), před prvním spuštěním, po spuštění se nic neladí:

  Vesmír: strategie registru Laboratoře (bez „vyřazeno“) + jádro (donchian_1d, pullback_1d, pyramida P2, ensemble).
    Každá má papírový účet jako v Agentownu (research/city_accounts.py: 1 000 USDT, riziko 1 % na obchod, reinvestice);
    denní výnos strategie = denní změna jejího účtu.
  Kupole (riziko × ziskovost), jen z dat PŘED 1. 1. 2024 (období vývoje, IS): pro každou strategii max. propad a roční
    výnos účtu v IS; hranice = mediány celého vesmíru.
      Pevnost   propad ≤ medián, výnos ≥ medián      Spořitelna  propad ≤ medián, výnos < medián
      Motor     propad > medián, výnos ≥ medián      Divočina    propad > medián, výnos < medián
    Strategie s méně než 250 dny v IS jde do kupole podle celé dostupné historie před 1. 1. 2024, jinak „Nováček“
    (do testu mozku nevstupuje). Čtvrti uvnitř kupole = styl podle rodiny (trend, průraz, návrat, kombinace, jádro).
  Fáze trhu: stejná jako Dispečer Downtownu (research/downtown_dispatch.phases): BTC nad/pod SMA200 × efektivita 30 dní
    (trend/pila) × volatilita 30 dní nad/pod mediánem 365 dní → 8 fází; platí fáze z uzavřeného předchozího dne.
  Varianty (denní výnos portfolia; učení walk-forward 1. den každého měsíce jen z minulých dní, od 1. 1. 2020):
    V0  „všechno pořád“ – rovná váha všech strategií v kupolích.
    Doplněk uživatele (8. 11. 2026, ještě před spuštěním): běží VŠECHNY strategie současně, každá má vždy svůj kapitál
    a vstupuje podle svých pravidel; mozek jen přesouvá váhy, nikdy nic úplně nevypne a nikdy nedrží hotovost.
    V1  „mozek kupolí“ – základní váha každé kupole = 1 (rovná váha strategií uvnitř). Z minulých dní v dnešní fázi
        (≥ 60 dní): průměrný denní výnos > 0 a t ≥ 1 → váha 1,5 (příznivá fáze); průměr < 0 a t ≤ −1 → váha 0,5
        (nepříznivá); jinak 1. Váhy se normalizují na 100 % kapitálu.
    V2  „mozek strategií“ – stejné násobky 1,5 / 1 / 0,5 pro každou strategii zvlášť.
    BTC  držení BTC (jen pro představu).
  Hodnocení: test 1. 1. 2024 – dnes, poloviny OOS (do 1. 7. 2025) a HOLDOUT (od 1. 7. 2025), stejné jako atlas.
    Sharpe (denní ×√365), roční výnos, max. propad, podíl dnů, kdy mozek váhy přesunul.
    Kontrola náhody: V1 a V2 s fázemi náhodně přeházenými po měsících (200 opakování) → 95. percentil Sharpe.
  PROJDE varianta mozku, když: Sharpe > V0 v OOS i v HOLDOUT, max. propad v celém testu ≤ V0, a Sharpe celého testu
    > 95. percentil své náhodné kontroly. Projdou-li obě, vyhraje vyšší min(Sharpe OOS, Sharpe HOLDOUT).
  Upozornění předem: strategie Laboratoře byly do registru vybrané i podle OOS/HOLDOUT, takže absolutní čísla v testu
    jsou optimistická. Výběr ale postihuje V0 i mozek stejně – test měří, jestli PŘEPÍNÁNÍ přidává hodnotu.
  Zjednodušení: přesun vah se počítá na denních výnosech účtů (velikost nových i běžících pozic se škáluje hned),
    bez nákladů na přesun.

Výstup: reports/brain_study.md a research/brain_study.json (kupole, čtvrti, tabulka fází, výsledky, dnešní plán).

    python3 research/experiments/brain_study.py /tmp/cache scanner/cache
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "experiments"))
from research import city_accounts as ca  # noqa: E402

OUT_MD = ROOT / "reports" / "brain_study.md"
OUT_JS = ROOT / "research" / "brain_study.json"
IS_END, OOS_END = pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")
LEARN_FROM = pd.Timestamp("2020-01-01", tz="UTC")
MIN_DAYS, T_MIN, N_RAND, MIN_IS_DAYS = 60, 1.0, 200, 250
DOMES = ["Pevnost", "Spořitelna", "Motor", "Divočina"]
STYLE = {"ma_cross": "trend", "price_ma": "trend", "supertrend": "trend", "macd": "trend", "rsi_mom": "trend",
         "roc": "trend", "donchian": "průraz", "boll_break": "průraz", "vol_break": "průraz", "keltner": "průraz",
         "candle": "průraz", "sweep": "návrat", "boll_fade": "návrat", "rsi_revert": "návrat", "stoch": "návrat",
         "fng": "sentiment", "combo": "kombinace"}


# ---------------------------------------------------------------- data
def universe(cache, scache):
    from research import registry
    from research.experiments import combo_study
    ca.patch_fetch()
    rets, meta, frames_by_tf = {}, {}, {}
    for s in registry.load()["strategies"]:
        if s.get("status") == "vyřazeno":
            continue
        try:
            if s["tf"] not in frames_by_tf:
                frames_by_tf[s["tf"]] = combo_study.frames_for(s["tf"], cache)[0]
            eq = ca.daily_equity(ca.lab_backtest_trades(s, frames_by_tf[s["tf"]]))
        except Exception as exc:
            print(f"{s['id']}: {exc.__class__.__name__}: {exc}", flush=True)
            continue
        if len(eq) > 30:
            key = "lab:" + s["id"]
            rets[key] = eq.pct_change().fillna(0)
            meta[key] = {"name": s.get("label") or s["id"], "kind": "lab", "ref": s["id"],
                         "style": STYLE.get(s["family"], s["family"]), "tf": s["tf"], "dir": s["dir"]}
    trades, ens = ca.core_backtests(scache)
    for sid, tr in trades.items():
        eq = ca.daily_equity(tr)
        rets["core:" + sid] = eq.pct_change().fillna(0)
        meta["core:" + sid] = {"name": ca.CORE_META[sid][1], "kind": "core", "ref": sid, "style": "jádro", "tf": "1d"}
    rets["core:ensemble"] = ens.fillna(0)
    meta["core:ensemble"] = {"name": "Ensemble · trendová alokace", "kind": "core", "ref": "ensemble", "style": "jádro",
                             "tf": "1d"}
    df = pd.DataFrame(rets)
    df.index = pd.DatetimeIndex(df.index).tz_convert("UTC").floor("1D")
    df = df.groupby(level=0).sum()          # NaN = strategie ještě neexistovala (před prvním obchodem)
    return df, meta


def btc_phases(cache):
    from research.experiments import strategy_atlas as atlas
    from research import downtown_dispatch as DD
    h1 = atlas.fetch("BTC", "1h", "2019-01-01", Path(cache))
    ph, feat = DD.phases(h1)
    ph.index = pd.DatetimeIndex(ph.index).tz_convert("UTC").floor("1D") if ph.index.tz else ph.index.tz_localize("UTC")
    return ph["faze"], feat["btc"]


# ---------------------------------------------------------------- kupole
def stats(r):
    r = r.dropna()
    if len(r) < 2:
        return {"n": len(r), "cagr": None, "dd": None, "sharpe": None}
    eq = (1 + r).cumprod()
    yrs = max(len(r) / 365, 1 / 365)
    sd = r.std()
    return {"n": int(len(r)), "cagr": float(eq.iloc[-1] ** (1 / yrs) - 1), "dd": float((eq / eq.cummax() - 1).min()),
            "sharpe": float(r.mean() / sd * np.sqrt(365)) if sd > 0 else None}


def assign_domes(df, meta):
    pre = df[df.index < IS_END]
    st = {k: stats(pre[k]) for k in df.columns}
    ok = [k for k in df.columns if st[k]["n"] >= MIN_IS_DAYS]
    med_dd = float(np.median([-st[k]["dd"] for k in ok])) if ok else 0
    med_cg = float(np.median([st[k]["cagr"] for k in ok])) if ok else 0
    dome = {}
    for k in df.columns:
        if st[k]["n"] < MIN_IS_DAYS:
            dome[k] = "Nováček"
            continue
        low = -st[k]["dd"] <= med_dd
        hi = st[k]["cagr"] >= med_cg
        dome[k] = "Pevnost" if low and hi else "Spořitelna" if low else "Motor" if hi else "Divočina"
    return dome, st, med_dd, med_cg


# ---------------------------------------------------------------- mozek
UP, NEUTRAL, DOWN = 1.5, 1.0, 0.5


def gates(units, phase, months):
    """units: DataFrame denních výnosů (kupole nebo strategie). Vrátí {měsíc: {fáze: {jednotka: násobek váhy}}}."""
    plan = {}
    for m in months:
        past = units[units.index < m]
        ph = phase.reindex(past.index)
        out = {}
        for f in phase.dropna().unique():
            sel = past[ph == f]
            mult = {}
            for u in units.columns:
                x = sel[u].dropna()
                mult[u] = NEUTRAL
                if len(x) < MIN_DAYS:
                    continue
                sd = x.std()
                t = x.mean() / (sd / np.sqrt(len(x))) if sd > 0 else 0
                if x.mean() > 0 and t >= T_MIN:
                    mult[u] = UP
                elif x.mean() < 0 and t <= -T_MIN:
                    mult[u] = DOWN
            out[f] = mult
        plan[m] = out
    return plan


def run_plan(units, phase, plan):
    idx = units.index[units.index >= LEARN_FROM]
    res, tilt = [], []
    ph = phase.reindex(idx)
    for d in idx:
        m = pd.Timestamp(d.year, d.month, 1, tz="UTC")
        mult = (plan.get(m) or {}).get(ph.get(d), {})
        w = v = 0.0
        moved = False
        for u in units.columns:
            x = units.at[d, u]
            if pd.isna(x):
                continue
            k = mult.get(u, NEUTRAL)
            moved |= k != NEUTRAL
            w += k
            v += k * x
        res.append(v / w if w else 0.0)
        tilt.append(moved)
    return pd.Series(res, index=idx), pd.Series(tilt, index=idx)


def months_of(idx):
    return sorted({pd.Timestamp(d.year, d.month, 1, tz="UTC") for d in idx if d >= LEARN_FROM})


def shuffled_phase(phase, rng):
    """Fáze přeházené po celých měsících (zachová délky období, rozbije vazbu na trh)."""
    p = phase.dropna()
    keys = p.index.to_period("M")
    blocks = [p[keys == k].to_numpy() for k in keys.unique()]
    order = rng.permutation(len(blocks))
    vals, out = [], []
    for k, o in zip(keys.unique(), order):
        n = int((keys == k).sum())
        src = blocks[o]
        vals.append(np.resize(src, n))
    return pd.Series(np.concatenate(vals), index=p.index)


def perf(r, start, end=None):
    x = r[(r.index >= start) & ((r.index < end) if end is not None else True)]
    s = stats(x)
    return {"sharpe": None if s["sharpe"] is None else round(s["sharpe"], 2),
            "cagr_pct": None if s["cagr"] is None else round(s["cagr"] * 100, 1),
            "dd_pct": None if s["dd"] is None else round(s["dd"] * 100, 1), "days": s["n"]}


def evaluate(name, r, cash=None):
    out = {"name": name, "test": perf(r, IS_END), "oos": perf(r, IS_END, OOS_END), "hold": perf(r, OOS_END),
           "dev": perf(r, LEARN_FROM, IS_END)}
    if cash is not None:
        c = cash[cash.index >= IS_END]
        out["tilt_pct"] = round(float(c.mean() * 100), 1) if len(c) else None
    return out


def main():
    cache = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cache")
    scache = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "scanner" / "cache")
    df, meta = universe(cache, scache)
    phase, btc = btc_phases(cache)
    df = df[df.index >= pd.Timestamp("2019-01-01", tz="UTC")]
    dome, st, med_dd, med_cg = assign_domes(df, meta)
    members = {d: [k for k in df.columns if dome[k] == d] for d in DOMES}
    used = [k for k in df.columns if dome[k] in DOMES]
    dome_r = pd.DataFrame({d: df[ks].mean(axis=1, skipna=True) for d, ks in members.items() if ks})
    months = months_of(df.index)

    v0 = df[used].mean(axis=1, skipna=True).fillna(0)
    v0 = v0[v0.index >= LEARN_FROM]
    plan1 = gates(dome_r, phase, months)
    v1, c1 = run_plan(dome_r, phase, plan1)
    plan2 = gates(df[used], phase, months)
    v2, c2 = run_plan(df[used], phase, plan2)
    b = btc.copy()
    b.index = pd.DatetimeIndex(b.index).tz_convert("UTC") if b.index.tz else b.index.tz_localize("UTC")
    vb = b.pct_change().reindex(v0.index).fillna(0)

    rng = np.random.default_rng(20261108)
    rand = {"V1": [], "V2": []}
    for i in range(N_RAND):
        sp = shuffled_phase(phase, rng)
        r1, _ = run_plan(dome_r, sp, gates(dome_r, sp, months))
        rand["V1"].append(perf(r1, IS_END)["sharpe"] or 0)
        if i < N_RAND // 4:                                   # strategie zvlášť jsou pomalé: 50 opakování
            r2, _ = run_plan(df[used], sp, gates(df[used], sp, months))
            rand["V2"].append(perf(r2, IS_END)["sharpe"] or 0)
        if i % 20 == 0:
            print(f"náhoda {i}/{N_RAND}", flush=True)
    p95 = {k: round(float(np.percentile(v, 95)), 2) if v else None for k, v in rand.items()}

    res = {"V0": evaluate("Všechno pořád", v0), "V1": evaluate("Mozek kupolí", v1, c1),
           "V2": evaluate("Mozek strategií", v2, c2), "BTC": evaluate("Držení BTC", vb)}
    verdict = {}
    for k in ("V1", "V2"):
        r, base = res[k], res["V0"]
        cond = {"oos": (r["oos"]["sharpe"] or -9) > (base["oos"]["sharpe"] or -9),
                "hold": (r["hold"]["sharpe"] or -9) > (base["hold"]["sharpe"] or -9),
                "dd": (r["test"]["dd_pct"] or -999) >= (base["test"]["dd_pct"] or -999),
                "rand": (r["test"]["sharpe"] or -9) > (p95[k] if p95[k] is not None else 9)}
        verdict[k] = {"pass": all(cond.values()), "cond": cond, "p95_random": p95[k]}
    winners = [k for k in ("V1", "V2") if verdict[k]["pass"]]
    winner = max(winners, key=lambda k: min(res[k]["oos"]["sharpe"], res[k]["hold"]["sharpe"])) if winners else None

    today_phase = str(phase.dropna().iloc[-1])
    last_m = months[-1]
    m1 = (plan1.get(last_m) or {}).get(today_phase, {})
    m2 = (plan2.get(last_m) or {}).get(today_phase, {})
    w1 = {d: m1.get(d, NEUTRAL) for d in dome_r.columns}
    tot = sum(w1.values()) or 1
    plan_today = {"phase": today_phase, "dome_weights_pct": {d: round(v / tot * 100, 1) for d, v in w1.items()},
                  "strategies_up": [k for k, v in m2.items() if v == UP], "strategies_down": [k for k, v in m2.items() if v == DOWN]}
    phase_table = {}
    for d in dome_r.columns:
        row = {}
        x = dome_r[d][dome_r.index < IS_END]
        ph = phase.reindex(x.index)
        for f in sorted(phase.dropna().unique()):
            y = x[ph == f].dropna()
            row[f] = {"n": int(len(y)), "mean_bp": round(float(y.mean() * 1e4), 1) if len(y) else None}
        phase_table[d] = row
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
    out = {"updated": now, "med_dd_pct": round(med_dd * 100, 1), "med_cagr_pct": round(med_cg * 100, 1),
           "domes": {d: [{"id": k, **meta[k], "is_dd_pct": round(st[k]["dd"] * 100, 1) if st[k]["dd"] is not None else None,
                          "is_cagr_pct": round(st[k]["cagr"] * 100, 1) if st[k]["cagr"] is not None else None}
                         for k in df.columns if dome[k] == d] for d in DOMES + ["Nováček"]},
           "results": res, "verdict": verdict, "winner": winner, "today": plan_today, "phase_table_is": phase_table}
    OUT_JS.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    write_md(out)
    print(json.dumps({"verdict": verdict, "winner": winner, "today": plan_today}, ensure_ascii=False, default=str))


def f(x, suf=""):
    return "–" if x is None else f"{x}{suf}".replace(".", ",")


def write_md(o):
    L = ["# 🧠 Mozek města – studie kupolí a nasazování podle fáze trhu", "",
         f"Přepočet {o['updated']}. Pravidla stanovená předem jsou v hlavičce `research/experiments/brain_study.py`. "
         "Jen papír; nic se nemění na skeneru, registru, riziku ani penězích. Nejde o finanční poradenství.", "",
         "## Verdikt", ""]
    w = o["winner"]
    L.append(f"**{'PROJDE: ' + o['results'][w]['name'] if w else 'NEPROJDE – mozek nepřidal hodnotu proti „všechno pořád“'}**")
    L.append("")
    for k in ("V1", "V2"):
        v = o["verdict"][k]
        c = v["cond"]
        L.append(f"- {o['results'][k]['name']}: Sharpe OOS {'✅' if c['oos'] else '❌'} · HOLDOUT {'✅' if c['hold'] else '❌'} · "
                 f"propad {'✅' if c['dd'] else '❌'} · nad 95. percentilem náhody ({f(v['p95_random'])}) {'✅' if c['rand'] else '❌'}")
    L += ["", "## Výsledky (test od 1. 1. 2024)", "",
          "| Varianta | Sharpe test | OOS | HOLDOUT | roční výnos test | max. propad test | dnů s přesunem vah | vývoj 2020–23 Sharpe |",
          "|---|---|---|---|---|---|---|---|"]
    for k, r in o["results"].items():
        L.append(f"| {r['name']} | {f(r['test']['sharpe'])} | {f(r['oos']['sharpe'])} | {f(r['hold']['sharpe'])} | "
                 f"{f(r['test']['cagr_pct'], ' %')} | {f(r['test']['dd_pct'], ' %')} | {f(r.get('tilt_pct'), ' %')} | {f(r['dev']['sharpe'])} |")
    L += ["", f"## Kupole (z období vývoje do 1. 1. 2024; mediány: propad {f(o['med_dd_pct'], ' %')}, roční výnos {f(o['med_cagr_pct'], ' %')})", ""]
    for d, items in o["domes"].items():
        L.append(f"**{d}** ({len(items)})")
        styles = {}
        for it in items:
            styles.setdefault(it["style"], []).append(f"{it['name']} ({f(it['is_dd_pct'], ' %')} / {f(it['is_cagr_pct'], ' %')})")
        for s, names in styles.items():
            L.append(f"- čtvrť {s}: " + "; ".join(names))
        L.append("")
    L += ["## Kupole × fáze trhu v období vývoje (průměrný denní výnos v bazických bodech, počet dnů)", ""]
    phases = sorted({p for row in o["phase_table_is"].values() for p in row})
    L.append("| Kupole | " + " | ".join(phases) + " |")
    L.append("|---|" + "---|" * len(phases))
    for d, row in o["phase_table_is"].items():
        L.append(f"| {d} | " + " | ".join(f"{f(row.get(p, {}).get('mean_bp'))} ({row.get(p, {}).get('n', 0)})" for p in phases) + " |")
    t = o["today"]
    L += ["", f"## Dnes (jen ukázka, nic se nenasazuje): fáze {t['phase']}", "",
          "- Mozek kupolí – váhy kapitálu: " + ", ".join(f"{d} {f(v, ' %')}" for d, v in t["dome_weights_pct"].items()),
          f"- Mozek strategií: {len(t['strategies_up'])} strategií s vyšší vahou, {len(t['strategies_down'])} s nižší, ostatní základní.", "",
          "Upozornění: strategie Laboratoře byly vybrané i podle OOS/HOLDOUT, absolutní čísla jsou proto optimistická; "
          "test měří, jestli přepínání přidává hodnotu proti stejnému vesmíru bez přepínání."]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
