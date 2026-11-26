#!/usr/bin/env python3
"""🔧 Opravna AI Labu + ⏳ Test v čase. Jen papír, odděleno od desku.

Zadání uživatele (26. 11. 2026): AI má vzít strategie, které neprošly testem, a zkusit je upravit tak, aby prošly;
a strategie se mají testovat na různých datech z různých období, ne jen na jednom rozdělení a jednom timeframu.
Rozhodnutí uživatele: nový test platí jen pro NOVÉ a OPRAVENÉ strategie (stávající prošlé strategie AI Labu zůstávají
podle starých pravidel) a jako nikdy neviděná data se přidají další likvidní mince z OKX.
Stejně jako AI Lab NIKDY nesahá na skener, registr, riziko, demo ani peníze.

Stanoveno PŘEDEM (26. 11. 2026), před prvním spuštěním na datech:

  Data: stejná jako AI Lab (OKX spot, hodinové svíčky od 1/2019, 8 mincí, poplatky 0,05 % na stranu, dělení
    učení < 1. 1. 2024 ≤ ověření < 1. 7. 2025 ≤ závěrečný test). NOVÉ MINCE (data, která při vymýšlení ani testech
    AI Labu nikdo neviděl): EXTRA níže; použijí se jen mince s historií aspoň 3 roky, ostatní se přeskočí.

  ⏳ TEST V ČASE (pro nové strategie z kol od kola TT_FROM_ROUND a pro všechny opravy):
    Strategie se stopem (R):
      a) roky – Ø R za každý kalendářní rok 2019 → dnes (8 mincí, 1H), počítají se roky s ≥ 30 obchody; projde při
         aspoň 4 takových letech a Ø R > 0 v aspoň 2/3 z nich.
      b) režimy trhu – režim BTC v den vstupu (research/regime.py: býčí / medvědí / boční / panika), počítají se režimy
         s ≥ 30 obchody; projde při Ø R > 0 v aspoň 2 z nich.
      c) jiné timeframy – stejné pravidlo na 2H a 4H svíčkách (délky v počtu svíček, prahy = decily učení daného
         timeframu); projde při Ø R > 0 (n ≥ 50) aspoň na jednom z nich.
      d) nové mince – stejné pravidlo se stejnými prahy na EXTRA mincích za celou historii: n ≥ 200, Ø R > 0,
         t ≥ 2 (u oprav t ≥ 2,5, protože oprava zkouší víc variant) a Ø R > 0 u aspoň poloviny mincí s ≥ 20 obchody.
      Projde jen při splnění a) až d).
    Alokační strategie (denní výnosy):
      a) roky – Sharpe > 0 v aspoň 2/3 let s ≥ 100 dny; b) režimy – Ø denní výnos > 0 v aspoň 2 režimech s ≥ 60 dny;
      c) jiné timeframy jen tam, kde to dává smysl (Hodiny trhu na 2H/4H: Sharpe > 0 aspoň na jednom); Rotace síly
         pracuje vždy na 4H, bod c) se u ní nepočítá; d) nové mince – Sharpe ≥ 0,5 (u oprav ≥ 0,75) za celou historii.

  🔧 OPRAVNA – každá neprošlá strategie dostane JEDEN pokus o opravu (žádné opakování do úspěchu):
    Kandidáti: vlastní nápady AI Labu, které neprošly (Ozvěna BTC, Tichý průraz, Hodiny trhu, Rotace síly), a od kola
      TT_FROM_ROUND nejlepší pravidlo kola podle učení (fitness z IS, ne podle ověření) u kol, kde nic neprošlo.
    Varianty jsou dané předem (GRIDS níže; u pravidel z evoluce všichni „sousedé“ = jedna změna: jiný percentil,
      opačné znaménko, vynechaná podmínka, jiné držení nebo stop). Vybírá se JEN podle učení (IS < 2024):
      R – t-statistika Ø R × min(1, n/400), aspoň 150 obchodů (u evoluce fitness AI Labu); alokační – Sharpe v IS.
      Ověření, závěrečný test ani nové mince výběr neovlivní.
    Oprava PROJDE: R – Ø R > 0 v IS, v OOS Ø R > 0 a t ≥ 2,5, v HOLDOUT Ø R > 0 a t ≥ 1 (jako kola AI Labu)
      + Test v čase s t ≥ 2,5 na nových mincích; alokační – Sharpe > 0 ve všech třech obdobích, OOS Sharpe ≥ 1,5
      + Test v čase. Prošlá oprava se přidá do AI Labu jako „🔧 … (oprava)“ a obchoduje papírově od data opravy.
      Neprošlá zůstane v reportu s výsledky, druhý pokus nedostane.

    python3 research/ai_repair.py /tmp/cache /tmp/extra   → research/ai_repair.json + reports/ai_repair.md
"""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import ai_lab as al  # noqa: E402

OUT = ROOT / "research" / "ai_repair.json"
OUT_MD = ROOT / "reports" / "ai_repair.md"
EXTRA = ["LTC", "BCH", "DOT", "TRX", "ATOM", "ETC", "UNI", "FIL", "NEAR", "AAVE", "XLM", "ALGO", "SAND", "MANA", "CRV", "EOS"]
MIN_YEARS_HIST = 3
TT_FROM_ROUND = 18
# ⏸ POZASTAVENO 26. 11. 2026 na přání uživatele po auditu přeučení (dokument „Agentown – audit přeučení strategií“):
# Opravna ani Test v čase v nočních kolech AI Labu se nespouštějí, kód a pravidla zůstávají beze změny.
# Znovu zapnout = PAUSED = False (až po schváleném návrhu nápravy).
PAUSED = True
TFS = ["2h", "4h"]
GRIDS = {
    "a1": [{"kind": "a1", "z": z, "lag": lag, "stop": s, "hold": h}
           for z in (1.5, 2.0, 2.5, 3.0) for lag in (0.25, 0.5) for s in (1.0, 1.5, 2.0) for h in (2, 4, 8)],
    "a2": [{"kind": "a2", "comp": c, "lb": lb, "stop": s, "trail": tr, "hold": 72, "trend": tn}
           for c in (0.55, 0.65, 0.75) for lb in (24, 48, 96) for s in (1.5, 2.0, 3.0) for tr in (0.0, 2.5) for tn in (True, False)],
    "a3": [{"kind": "a3", "tmin": t, "trend": tn} for t in (2.0, 2.5, 3.0) for tn in (False, True)],
    "a4": [{"kind": "a4", "lb": lb, "k": k, "mode": m, "rev": rv}
           for lb in (6, 18, 42) for k in (1, 2, 3) for m in ("ls", "long") for rv in (False, True)],
}
ORIG = {"a1": {"kind": "a1", "z": 2.0, "lag": 0.5, "stop": 1.5, "hold": 4},
        "a2": {"kind": "a2", "comp": 0.65, "lb": 48, "stop": 2.0, "trail": 2.5, "hold": 72, "trend": True},
        "a3": {"kind": "a3", "tmin": 2.0, "trend": False},
        "a4": {"kind": "a4", "lb": 18, "k": 2, "mode": "ls", "rev": False}}
NAMES = {"a1": "Ozvěna BTC", "a2": "Tichý průraz", "a3": "Hodiny trhu", "a4": "Rotace síly"}


# ---------------------------------------------------------------- varianty strategií
def a1v(frames, F, p):
    out = []
    for c, z in frames.items():
        if c == "BTC":
            continue
        f = F[c]
        bz, br, ar = f["btc1z"].to_numpy(), f["btc_ret"].to_numpy(), f["ret"].to_numpy()
        for d in (1, -1):
            m = (d * bz >= p["z"]) & (d * ar < p["lag"] * d * br)
            out += al.to_list(z, c, d, *al.trades_from(z, m, d, p["stop"], 0.0, p["hold"]))
    return out


def a2v(frames, F, p):
    out = []
    for c, z in frames.items():
        comp = F[c]["comp"].shift(1).to_numpy()
        for d in (1, -1):
            brk = z.c > z.hi(p["lb"]) if d > 0 else z.c < z.lo(p["lb"])
            m = (comp < p["comp"]) & brk
            if p["trend"]:
                m &= z.d200 == (1.0 if d > 0 else 0.0)
            out += al.to_list(z, c, d, *al.trades_from(z, m, d, p["stop"], p["trail"], p["hold"]))
    return out


def a3v(frames, F, p, learn_end=None):
    learn_end = learn_end or al.IS_END
    parts, learned = [], {}
    for c, z in frames.items():
        f = F[c]
        nxt = f["ret"].shift(-1)
        isr = nxt[f.index < learn_end]
        st = isr.groupby(f.index[f.index < learn_end].hour).agg(["mean", "std", "count"])
        t = st["mean"] / (st["std"] / np.sqrt(st["count"]))
        hrs = sorted(int(h) for h in t[t >= p["tmin"]].index)
        learned[c] = hrs
        on = np.isin(f.index.hour, hrs).astype(float)
        if p["trend"]:
            on *= (np.nan_to_num(z.d200, nan=0.0) == 1.0)
        chg = np.abs(np.diff(np.r_[0.0, on]))
        bar = f.index[1] - f.index[0] if len(f.index) > 1 else pd.Timedelta("1h")
        r = (on * (np.exp(nxt.fillna(0)) - 1) - chg * al.COST) / len(frames)
        parts.append(pd.Series(r, index=f.index + bar))
    return pd.concat(parts, axis=1).fillna(0).sum(axis=1), learned


def a4v(frames, F, p):
    cl = pd.DataFrame({c: z.df["Close"] for c, z in frames.items()}).dropna(how="all")
    c4 = cl.resample("4h").last()
    lr = np.log(c4)
    score = lr.diff(p["lb"]) / lr.diff().rolling(p["lb"]).std()
    if p["rev"]:
        score = -score
    fwd = c4.pct_change().shift(-1)
    rows, prev, k = [], pd.Series(0.0, index=c4.columns), p["k"]
    for t in c4.index:
        s = score.loc[t].dropna()
        w = pd.Series(0.0, index=c4.columns)
        if len(s) >= max(6, 2 * k + 2):
            o = s.sort_values()
            if p["mode"] == "ls":
                w[o.index[-k:]] = 0.5 / k
                w[o.index[:k]] = -0.5 / k
            else:
                w[o.index[-k:]] = 1.0 / k
        cost = (w - prev).abs().sum() * al.COST
        rows.append((t + pd.Timedelta("4h"), float((w * fwd.loc[t].fillna(0)).sum()) - cost))
        prev = w
    return pd.Series(dict(rows)).sort_index().iloc[:-1]


def kind_type(spec):
    return "ret" if spec["kind"] in ("a3", "a4") else "r"


def run_spec(spec, frames, F, thr=None):
    k = spec["kind"]
    if k == "a1":
        return a1v(frames, F, spec)
    if k == "a2":
        return a2v(frames, F, spec)
    if k == "a3":
        return a3v(frames, F, spec)[0]
    if k == "a4":
        return a4v(frames, F, spec)
    return al.run_genome(frames, F, spec["genome"], thr)


def spec_text(spec, thr=None):
    k = spec["kind"]
    n = lambda x: str(x).replace(".", ",")
    if k == "a1":
        return (f"BTC za hodinu ≥ {n(spec['z'])}σ a altcoin se pohne méně než o {int(spec['lag'] * 100)} % pohybu BTC → vstup ve směru BTC; "
                f"stop {n(spec['stop'])} ATR, nejvýš {spec['hold']} h")
    if k == "a2":
        return (f"stažení ATR14/ATR200 < {n(spec['comp'])} a průraz {spec['lb']}h maxima/minima"
                + (" ve směru denního trendu" if spec["trend"] else " bez filtru trendu")
                + f"; stop {n(spec['stop'])} ATR" + (f", posuvný {n(spec['trail'])} ATR" if spec["trail"] else ", bez posuvného stopu")
                + f", nejvýš {spec['hold']} h")
    if k == "a3":
        return f"long jen v hodinách dne s t ≥ {n(spec['tmin'])} (naučeno 2019–2023)" + (" a jen nad denní EMA200" if spec["trend"] else "")
    if k == "a4":
        h = spec["lb"] * 4
        what = f"long {spec['k']} nejsilnější a short {spec['k']} nejslabší" if spec["mode"] == "ls" else f"jen long {spec['k']} nejsilnější"
        if spec["rev"]:
            what = what.replace("nejsilnější", "XX").replace("nejslabší", "nejsilnější").replace("XX", "nejslabší")
        return f"každé 4 h {what} mince podle výnosu {h} h / volatilita {h} h"
    return al.genome_text(spec["genome"], thr)


# ---------------------------------------------------------------- statistiky
def r_stats(r):
    r = np.asarray(r, float)
    n = len(r)
    sd = r.std(ddof=1) if n > 2 else 0.0
    return {"n": n, "mean_r": round(float(r.mean()), 3) if n else None,
            "t": round(float(r.mean() / (sd / np.sqrt(n))), 2) if n > 2 and sd > 0 else None}


def daily(r):
    return (1 + r).resample("1D").prod() - 1 if len(r) else r


def sharpe(d):
    sd = d.std()
    return round(float(d.mean() / sd * np.sqrt(365)), 2) if len(d) > 2 and sd > 0 else None


def is_score(spec, frames, F, thr=None):
    """Skóre jen z učení (IS < 2024) – jediné, podle čeho Opravna vybírá variantu."""
    out = run_spec(spec, frames, F, thr)
    if kind_type(spec) == "ret":
        return al.ret_split(out)["is"]["sharpe"] or -99.0, out
    if spec["kind"] == "genome":
        return al.fitness(out) - 0.1 * len(spec["genome"]["conds"]), out
    r = np.array([t["r"] for t in out if t["entry"] < al.IS_END])
    if len(r) < 150 or r.std(ddof=1) == 0:
        return -99.0, out
    return float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) * min(1.0, len(r) / 400)), out


def neighbours(g):
    """Všechny genomy, které se od g liší jednou změnou."""
    out = []
    conds = [tuple(c) for c in g["conds"]]
    for i, (fi, op, q) in enumerate(conds):
        for q2 in al.QS:
            if q2 != q:
                out.append({**g, "conds": conds[:i] + [(fi, op, float(q2))] + conds[i + 1:]})
        out.append({**g, "conds": conds[:i] + [(fi, "<" if op == ">" else ">", q)] + conds[i + 1:]})
        if len(conds) > 1:
            out.append({**g, "conds": conds[:i] + conds[i + 1:]})
    out += [{**g, "conds": conds, "hold": h} for h in al.HOLDS if h != g["hold"]]
    out += [{**g, "conds": conds, "stop": s} for s in al.STOPS if s != g["stop"]]
    return out


# ---------------------------------------------------------------- data pro Test v čase
class World:
    """Všechna data, na kterých se strategie zkouší: 8 mincí 1H, 2H a 4H, režimy BTC a nové mince."""

    def __init__(self, frames, F, thr, extra=None, tf=None, reg=None):
        self.frames, self.F, self.thr = frames, F, thr
        self.extra = extra or {}                       # {mince: Ind} bez BTC
        self.Fx = al.features({"BTC": frames["BTC"], **self.extra}) if self.extra else {}
        self.tf = tf or {}                             # {"2h": (frames, F, thr)}
        self.reg = reg

    @classmethod
    def build(cls, frames, F, thr, extra_cache):
        from research import regime
        from research.experiments import strategy_atlas as atlas
        btc_d = atlas.resample(frames["BTC"].df, "1d")
        reg = regime.regime_series(btc_d)
        tf = {}
        for t in TFS:
            fr = {}
            for c, z in frames.items():
                df = atlas.resample(z.df, t)
                zz = atlas.Ind(df)
                bull, _ = atlas.daily_regimes(z.df)
                zz.d200 = bull.reindex(df.index.floor("1D")).to_numpy(float)
                fr[c] = zz
            Ft = al.features(fr)
            tf[t] = (fr, Ft, al.is_thresholds(fr, Ft))
        return cls(frames, F, thr, load_extra(extra_cache, frames["BTC"].df.index), tf, reg)

    # -------------------------------------------------------------- test
    def time_test(self, spec, coin_t=2.0, coin_sharpe=0.5, main_out=None):
        typ = kind_type(spec)
        out = main_out if main_out is not None else run_spec(spec, self.frames, self.F, self.thr)
        res = {"years": {}, "regimes": {}, "tf": {}, "coins": {}}
        if typ == "r":
            years = sorted({t["entry"].year for t in out})
            for y in years:
                res["years"][str(y)] = r_stats([t["r"] for t in out if t["entry"].year == y])
            ok_y = [v for v in res["years"].values() if v["n"] >= 30]
            a = len(ok_y) >= 4 and sum((v["mean_r"] or 0) > 0 for v in ok_y) >= math.ceil(2 / 3 * len(ok_y))
            if self.reg is not None and out:
                from research import regime
                labs = regime.at(self.reg, [t["entry"] for t in out])
                for lab in regime.LABELS:
                    res["regimes"][lab] = r_stats([t["r"] for t, l in zip(out, labs) if l == lab])
            ok_r = [v for v in res["regimes"].values() if v["n"] >= 30]
            b = sum((v["mean_r"] or 0) > 0 for v in ok_r) >= 2
            for t, (fr, Ft, th) in self.tf.items():
                res["tf"][t] = r_stats([x["r"] for x in run_spec(spec, fr, Ft, th)])
            c = any(v["n"] >= 50 and (v["mean_r"] or 0) > 0 for v in res["tf"].values())
            per, pooled = {}, []
            if self.extra:
                for t in run_spec(spec, self.extra, self.Fx, self.thr):
                    per.setdefault(t["coin"], []).append(t["r"])
                    pooled.append(t["r"])
            res["coins"] = {"all": r_stats(pooled), "per": {k: r_stats(v) for k, v in sorted(per.items())}, "n_coins": len(self.extra)}
            pc = [v for v in res["coins"]["per"].values() if v["n"] >= 20]
            ca = res["coins"]["all"]
            d = (ca["n"] >= 200 and (ca["mean_r"] or 0) > 0 and (ca["t"] or 0) >= coin_t
                 and len(pc) > 0 and sum((v["mean_r"] or 0) > 0 for v in pc) >= len(pc) / 2)
            res["checks"] = {"years": bool(a), "regimes": bool(b), "tf": bool(c), "coins": bool(d)}
        else:
            dd = daily(out)
            for y in sorted(set(dd.index.year)):
                x = dd[dd.index.year == y]
                res["years"][str(y)] = {"days": int(len(x)), "sharpe": sharpe(x)}
            ok_y = [v for v in res["years"].values() if v["days"] >= 100]
            a = len(ok_y) >= 3 and sum((v["sharpe"] or 0) > 0 for v in ok_y) >= math.ceil(2 / 3 * len(ok_y))
            if self.reg is not None and len(dd):
                from research import regime
                labs = regime.at(self.reg, dd.index)
                for lab in regime.LABELS:
                    x = dd[labs == lab]
                    res["regimes"][lab] = {"days": int(len(x)), "mean_pct": round(float(x.mean() * 100), 3) if len(x) else None}
            ok_r = [v for v in res["regimes"].values() if v["days"] >= 60]
            b = sum((v["mean_pct"] or 0) > 0 for v in ok_r) >= 2
            if spec["kind"] == "a4":
                res["tf"] = {"pozn": "Rotace síly pracuje vždy na 4H – jiné timeframy se nepočítají"}
                c = True
            else:
                for t, (fr, Ft, th) in self.tf.items():
                    res["tf"][t] = {"sharpe": sharpe(daily(run_spec(spec, fr, Ft, th)))}
                c = any((v.get("sharpe") or 0) > 0 for v in res["tf"].values())
            sx = sharpe(daily(run_spec(spec, self.extra, self.Fx, self.thr))) if self.extra else None
            res["coins"] = {"sharpe": sx, "n_coins": len(self.extra)}
            d = (sx or 0) >= coin_sharpe
            res["checks"] = {"years": bool(a), "regimes": bool(b), "tf": bool(c), "coins": bool(d)}
        res["pass"] = all(res["checks"].values())
        return res


def load_extra(cache, main_index=None):
    from research import city_accounts as ca
    from research.experiments import strategy_atlas as atlas
    ca.patch_fetch()
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.DateOffset(years=MIN_YEARS_HIST)
    out = {}
    for c in EXTRA:
        try:
            b = atlas.fetch(c, "1h", "2019-01-01", cache)
        except Exception as exc:
            print(f"  {c}: data nejdou stáhnout ({exc.__class__.__name__}) – přeskočeno", flush=True)
            continue
        if b is None or len(b) < 24 * 365 or b.index[0] > cutoff:
            print(f"  {c}: historie kratší než {MIN_YEARS_HIST} roky – přeskočeno", flush=True)
            continue
        df = atlas.resample(b, "1h")
        z = atlas.Ind(df)
        bull, _ = atlas.daily_regimes(b)
        z.d200 = bull.reindex(df.index.floor("1D")).to_numpy(float)
        out[c] = z
    print(f"nové mince: {len(out)}/{len(EXTRA)} ({', '.join(out)})", flush=True)
    return out


# ---------------------------------------------------------------- Opravna
def repair_pass(spec, out):
    if kind_type(spec) == "ret":
        st = al.ret_split(out)
        return all((st[k]["sharpe"] or -1) > 0 for k in ("is", "oos", "hold")) and (st["oos"]["sharpe"] or 0) >= 1.5, st
    st = al.split_stats(out)
    return al.round_pass(st), st


def repair(world, sid, name, orig, today):
    """Jeden pokus o opravu: výběr varianty jen podle učení, pak ověření, závěrečný test a Test v čase."""
    if orig["kind"] == "genome":
        variants = [{"kind": "genome", "genome": g} for g in neighbours(orig["genome"])]
    else:
        variants = GRIDS[orig["kind"]]
    seen, best = set(), None
    o_score, _ = is_score(orig, world.frames, world.F, world.thr)
    for v in variants:
        k = json.dumps(v, sort_keys=True, default=str)
        if k in seen:
            continue
        seen.add(k)
        sc, out = is_score(v, world.frames, world.F, world.thr)
        if best is None or sc > best[0]:
            best = (sc, v, out)
    sc, v, out = best
    ok, st = repair_pass(v, out)
    tt = world.time_test(v, coin_t=2.5, coin_sharpe=0.75, main_out=out)
    passed = bool(ok and tt["pass"])
    print(f"oprava {name}: {len(seen)} variant, IS {sc:.2f} (původně {o_score:.2f}) → {'PROJDE' if passed else 'neprojde'}", flush=True)
    return {"id": f"fix_{sid}", "of": sid, "name": f"🔧 {name} (oprava)", "orig_name": name, "date": today,
            "type": kind_type(v), "orig": orig, "spec": v, "orig_text": spec_text(orig, world.thr), "text": spec_text(v, world.thr),
            "n_variants": len(seen), "is_score": round(float(sc), 2), "orig_is_score": round(float(o_score), 2),
            "same_as_orig": json.dumps(v, sort_keys=True) == json.dumps(orig, sort_keys=True),
            "splits": st, "split_ok": bool(ok), "time_test": tt, "pass": passed}


def load():
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        return {"repairs": []}


def todo(ai_lab_json, rounds):
    """Co ještě nedostalo pokus o opravu: neprošlé vlastní nápady a neúspěšná kola od TT_FROM_ROUND."""
    done = {r["of"] for r in load().get("repairs", [])}
    out = []
    for s in (ai_lab_json or {}).get("strategies", []):
        if s["id"] in ORIG and not s.get("pass") and s["id"] not in done:
            out.append((s["id"], NAMES[s["id"]], ORIG[s["id"]]))
    for r in rounds.get("rounds", []):
        sid = f"r{r['n']}"
        if r["n"] >= TT_FROM_ROUND and not r.get("added") and r.get("repair_genome") and sid not in done:
            out.append((sid, f"Kolo {r['n']} · {r['focus']}", {"kind": "genome", "genome": r["repair_genome"]}))
    return out


def main():
    if PAUSED:
        print("Opravna je pozastavená (PAUSED = True v research/ai_repair.py) – nic se nespouští.", flush=True)
        return 0
    cache = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cache")
    extra_cache = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/extra")
    try:
        aj = json.loads(al.OUT.read_text(encoding="utf-8"))
    except Exception:
        aj = {}
    jobs = todo(aj, al.load_rounds())
    D = load()
    now = datetime.now(timezone.utc)
    if not jobs:
        print("Opravna: nic nového k opravě", flush=True)
        return 0
    frames = al.load(cache)
    F = al.features(frames)
    evo = json.loads(al.GENOME.read_text(encoding="utf-8"))
    thr = {fi: {float(q): v for q, v in d.items()} for fi, d in evo["thr"].items()}
    world = World.build(frames, F, thr, extra_cache)
    today = now.strftime("%Y-%m-%d")
    new = [repair(world, sid, name, orig, today) for sid, name, orig in jobs]
    D["repairs"] = D.get("repairs", []) + new
    D["updated"] = now.strftime("%Y-%m-%dT%H:%M+00:00")
    D["extra_coins"] = list(world.extra)
    OUT.write_text(json.dumps(D, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    write_md(D)
    notify(new)
    return 0


def notify(new):
    import os
    if not new or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        return
    try:
        from scanner.notify import h, telegram
    except Exception:
        return
    L = ["<b>🔧 AI LAB · Opravna</b>", ""]
    for x in new:
        L.append(f"{'✅' if x['pass'] else '❌'} <b>{h(x['orig_name'])}</b> · {x['n_variants']} variant · "
                 + ("oprava prošla – od dneška papírově" if x["pass"] else "ani oprava neprošla"))
        if x["pass"]:
            L.append(f"<i>{h(x['text'])}</i>")
    L += ["", "Varianta vybraná jen podle let 2019–2023; rozhodly ověření, závěrečný test, roky, režimy, 2H/4H a nové mince.",
          "<i>Jen papír, odděleno od desku. Nejde o finanční poradenství.</i>"]
    try:
        telegram("\n".join(L))
    except Exception as exc:
        print(f"Telegram: {exc}", flush=True)


def _f(x):
    return "–" if x is None else str(x).replace(".", ",")


def tt_lines(tt, typ):
    ck = tt.get("checks", {})
    m = lambda k: "✅" if ck.get(k) else "❌"
    if typ == "r":
        yrs = " · ".join(f"{y}: {_f(v['mean_r'])} R (n {v['n']})" for y, v in tt["years"].items())
        rg = " · ".join(f"{k}: {_f(v['mean_r'])} R (n {v['n']})" for k, v in tt["regimes"].items())
        tf = " · ".join(f"{k}: {_f(v['mean_r'])} R (t {_f(v['t'])}, n {v['n']})" for k, v in tt["tf"].items())
        ca = tt["coins"]["all"]
        co = f"{tt['coins']['n_coins']} mincí: {_f(ca['mean_r'])} R (t {_f(ca['t'])}, n {ca['n']})"
    else:
        yrs = " · ".join(f"{y}: Sharpe {_f(v['sharpe'])}" for y, v in tt["years"].items())
        rg = " · ".join(f"{k}: {_f(v['mean_pct'])} %/den ({v['days']} d)" for k, v in tt["regimes"].items())
        tf = tt["tf"].get("pozn") or " · ".join(f"{k}: Sharpe {_f(v['sharpe'])}" for k, v in tt["tf"].items())
        co = f"{tt['coins']['n_coins']} mincí: Sharpe {_f(tt['coins']['sharpe'])}"
    return [f"- {m('years')} roky: {yrs}", f"- {m('regimes')} režimy BTC: {rg}", f"- {m('tf')} jiné timeframy: {tf}", f"- {m('coins')} nové mince: {co}"]


def write_md(D):
    L = ["# 🔧 Opravna AI Labu + ⏳ Test v čase", "",
         f"Přepočet {D.get('updated')}. Pravidla stanovená předem jsou v hlavičce `research/ai_repair.py`. Každá neprošlá strategie "
         "dostane jeden pokus; varianta se vybírá jen podle let 2019–2023. Jen papír, odděleno od desku; nejde o finanční poradenství.", "",
         f"Nové mince (nikdy neviděná data): {', '.join(D.get('extra_coins') or []) or '–'}.", "",
         "| Strategie | Variant | IS skóre (původně) | Ověření a závěr | Test v čase | Výsledek |", "|---|---|---|---|---|---|"]
    for x in D.get("repairs", []):
        sp = x["splits"]
        if x["type"] == "r":
            so = f"OOS {_f(sp['oos']['mean_r'])} R (t {_f(sp['oos']['t'])}) · závěr {_f(sp['hold']['mean_r'])} R (t {_f(sp['hold']['t'])})"
        else:
            so = f"OOS Sharpe {_f(sp['oos']['sharpe'])} · závěr Sharpe {_f(sp['hold']['sharpe'])}"
        ck = x["time_test"]["checks"]
        L.append(f"| {x['orig_name']} | {x['n_variants']} | {_f(x['is_score'])} ({_f(x['orig_is_score'])}) | {so} {'✅' if x['split_ok'] else '❌'} | "
                 f"{sum(ck.values())}/4 | {'✅ projde' if x['pass'] else '❌ neprojde'} |")
    for x in D.get("repairs", []):
        L += ["", f"## {x['orig_name']} · {x['date']}", "", f"Původně: {x['orig_text']}", "",
              f"Vybraná varianta: {x['text']}" + (" (původní nastavení bylo v učení nejlepší)" if x["same_as_orig"] else ""), ""]
        L += tt_lines(x["time_test"], x["type"])
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
