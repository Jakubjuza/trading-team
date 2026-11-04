"""🧩 Studie KOMBINACÍ: spouštěč z atlasu + 1–2 potvrzení/filtry z jiných rodin nebo kontextu.

Postupná studie, jeden díl za běh (stav research/combo_state.json, report reports/combo_study.md).
Stanoveno PŘEDEM (4. 11. 2026), po spuštění se nic neladí:

  Data, náklady, simulace a dělení IS < 2024-01-01 ≤ OOS < 2025-07-01 ≤ HOLDOUT jsou STEJNÉ jako v atlasu
  (research/experiments/strategy_atlas.py): OKX spot USDT, 8 mincí, poplatky MEXC futures 0,05 %/stranu,
  vstup na open další svíčky, výstup z atlasu (opp / trail / target / opp_stop), vlastní náhoda 10×.
  Kombinace = spouštěč + filtry, params v registru: "<rodina>:<parametry atlasu>+<filtr>:<hodnota>[+…]",
  např. "donchian:20+vol:1.5+rsi:50". Spouštěč nese výstup z atlasu.

  SPOUŠTĚČE (díl si je vybere jen podle IS – OOS a HOLDOUT se při výběru nevidí): z reports/atlas/<tf>.csv.gz
  řádky bez filtru, IS ≥ 300 obchodů, IS Ø R > 0; na směr nejlepší varianta každé rodiny podle IS t, 6 rodin
  na směr (bez rodiny fng) → nejvýš 12 spouštěčů na timeframe.

  FILTRY (long; short je zrcadlo), vše z dat do close signální svíčky:
    trend       ema:N   close nad EMA N vlastního TF a EMA N roste (proti 10 svíčkám zpět), N {50, 100, 200}
                d:N     denní filtr atlasu: d:200 = close 1D nad EMA 200, d:50 = EMA 50 1D roste (z předch. dne)
    režim       reg:trend (býčí pro long / medvědí pro short), reg:notpanic, reg:side – research/regime.py
    objem       vol:x   objem svíčky ≥ x × průměr 20 předchozích, x {1,0; 1,5; 2,0}
    volatilita  atrlo:q / atrhi:q – percentil ATR % ceny za 200 svíček ≤ q / ≥ q, q {0,3; 0,5; 0,7}
    momentum    rsi:x   RSI 14 ≥ x (short ≤ 100 − x), x {45, 50, 55, 60}
                rsix:x  RSI 14 ≤ x – není překoupeno (short ≥ 100 − x), x {60, 70, 80}
                macd:sig / macd:zero – MACD (12, 26, 9) nad signální / nad nulou
    sentiment   fng:x   Strach a chamtivost ≤ x (strach, short ≥ 100 − x), x {30, 45, 60}
                fngg:x  Strach a chamtivost ≥ x (chamtivost, short ≤ 100 − x), x {40, 55, 70}
    Funding/OI: historie 2019+ pro 8 mincí není v repozitáři k dispozici → zatím netestováno.

  DÍLY (rotace, research/combo_state.json): timeframy 1h, 2h, 4h, 6h, 12h, 1d.
    pair:A / pair:B  spouštěč + 1 filtr (A = trend, režim, objem; B = volatilita, momentum, sentiment)
    deep             6 nejlepších párů timeframu PODLE IS t (s IS zlepšením proti spouštěči) + druhý filtr z jiné
                     skupiny (všechny hodnoty) + sousední hodnoty prvního filtru (pro kontrolu citlivosti)
    sens             citlivost: kombinace, které prošly, se sousedními parametry SPOUŠTĚČE (sousední varianta atlasu)
    Mřížka dílu se zapíše do stavu DŘÍV, než se spočítá jediný výsledek; zapíše se i počet testů.

  PRAVIDLO PRŮCHODU (atlas + přísněji): Ø R > 0 v IS, OOS i HOLDOUT; OOS i HOLDOUT nad p95 vlastní náhody (náhodné
  vstupy jen na svíčkách, kde platí filtry kombinace); OOS t ≥ 2; IS ≥ 150 a OOS ≥ 50 obchodů; OOS Ø R o ≥ 0,05 R
  nad samotným spouštěčem; zlepšení proti spouštěči (> 0 v OOS) drží i v sousedních hodnotách každého číselného
  filtru; u kategorických filtrů (d, reg, macd) místo toho musí být zlepšení i v IS. Režimy jako lab: aktivní jen
  režimy s ≥ 30 obchody a Ø R > 0,05 (jinak se nezařadí).
  ZAŘAZENÍ: research/registry.json, stav „papír“, nejvýš 2 nové za běh, nejvýš 10 aktivních combo; při plném limitu
  nahradí nejslabší combo jen nová s vyšším min(OOS t, HOLDOUT t). Necombo strategie se nemění.

    python3 research/experiments/combo_study.py run /tmp/cache      # jeden díl + zařazení + report
    python3 research/experiments/combo_study.py report              # jen report z uložených výsledků
"""
import json
import sys
import time
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import regime, registry  # noqa: E402
from research.experiments import strategy_atlas as atlas  # noqa: E402

STATE = ROOT / "research" / "combo_state.json"
OUT = ROOT / "reports" / "combo"
REPORT = ROOT / "reports" / "combo_study.md"
KNOWLEDGE = ROOT / "research" / "knowledge.md"
M = atlas.MAIN
TFS = ["1h", "2h", "4h", "6h", "12h", "1d"]
FILTERS = {                     # skupina → [(typ, hodnoty v pořadí – sousední hodnoty pro citlivost)]
    "trend": [("ema", [50, 100, 200]), ("d", [50, 200])],
    "režim": [("reg", ["trend", "notpanic", "side"])],
    "objem": [("vol", [1.0, 1.5, 2.0])],
    "volatilita": [("atrlo", [0.3, 0.5, 0.7]), ("atrhi", [0.3, 0.5, 0.7])],
    "momentum": [("rsi", [45, 50, 55, 60]), ("rsix", [60, 70, 80]), ("macd", ["sig", "zero"])],
    "sentiment": [("fng", [30, 45, 60]), ("fngg", [40, 55, 70])],
}
GROUP_SETS = {"A": ["trend", "režim", "objem"], "B": ["volatilita", "momentum", "sentiment"]}
CATEGORICAL = {"d", "reg", "macd"}
FILTER_CS = {"ema": "trend EMA{}", "d": "denní {}", "reg": "režim {}", "vol": "objem×{}", "atrlo": "ATR pctl ≤ {}",
             "atrhi": "ATR pctl ≥ {}", "rsi": "RSI ≥ {}", "rsix": "RSI ≤ {}", "macd": "MACD {}", "fng": "F&G ≤ {}",
             "fngg": "F&G ≥ {}"}
N_TRIG_FAM, MIN_TRIG_IS = 6, 300
DEEP_TOP = 6
MAX_NEW, MAX_ACTIVE = 2, 10
MIN_GAIN = 0.05


# ---------------------------------------------------------------- parametry
def _typed(x):
    for f in (int, float):
        try:
            return f(x)
        except ValueError:
            pass
    return x


def fmt_val(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def make_params(fam, p, filters):
    """('donchian', '20', [('vol', 1.5)]) → 'donchian:20+vol:1.5'."""
    return "+".join([f"{fam}:{p}"] + [f"{k}:{fmt_val(v)}" for k, v in filters])


def parse_params(s):
    """'donchian:20+vol:1.5' → ('donchian', (20,), [('vol', 1.5)])."""
    parts = str(s).split("+")
    fam, p = parts[0].split(":", 1)
    flts = []
    for x in parts[1:]:
        k, v = x.split(":", 1)
        flts.append((k, _typed(v)))
    return fam, tuple(_typed(x) for x in p.split("/")), flts


def pretty(params):
    fam, p, flts = parse_params(params)
    trig = f"{registry.FAM_CS.get(fam, fam)} {' '.join(map(str, p))}"
    out = [FILTER_CS.get(k, k + " {}").format(fmt_val(v).replace(".", ",")) for k, v in flts]
    return " + ".join([trig] + out)


def neighbors(kind, val):
    """Sousední hodnoty číselného filtru v mřížce (kategorické nemají)."""
    if kind in CATEGORICAL:
        return []
    for vals in (v for g in FILTERS.values() for k, v in g if k == kind):
        if val in vals:
            i = vals.index(val)
            return [vals[j] for j in (i - 1, i + 1) if 0 <= j < len(vals)]
    return []


# ---------------------------------------------------------------- filtry
def filter_mask(z, kind, val, d):
    """Bool pole: platí filtr na close svíčky i? (NaN = neplatí)."""
    L = d > 0
    c = z.c
    with np.errstate(invalid="ignore"):
        if kind == "ema":
            e = z.ma("ema", int(val))
            ep = np.r_[np.full(10, np.nan), e[:-10]]
            m = (c > e) & (e > ep) if L else (c < e) & (e < ep)
            return m & ~np.isnan(ep)
        if kind == "d":
            f = z.flt["d200" if int(val) == 200 else "d50"]
            return f == (1.0 if L else 0.0)
        if kind == "reg":
            r = np.asarray(z.reg, dtype=object)
            if val == "trend":
                return r == ("býčí" if L else "medvědí")
            if val == "notpanic":
                return np.array([x is not None and x == x and x != "panika" for x in r], bool)
            if val == "side":
                return r == "boční"
        if kind == "vol":
            va = z.vavg(20)
            return (z.v >= float(val) * va) & ~np.isnan(va)
        if kind in ("atrlo", "atrhi"):
            rk = z.get(("atr_rank",), lambda: pd.Series(z.atr / c).rolling(200, min_periods=100).rank(pct=True).to_numpy())
            return (rk <= float(val)) if kind == "atrlo" else (rk >= float(val))
        if kind in ("rsi", "rsix"):
            r = z.rsi(14)
            x = float(val)
            if kind == "rsi":
                return (r >= x) if L else (r <= 100 - x)
            return (r <= x) if L else (r >= 100 - x)
        if kind == "macd":
            line, sig = z.macd(12, 26, 9)
            ref = sig if val == "sig" else 0.0
            return (line > ref) if L else (line < ref)
        if kind in ("fng", "fngg"):
            f = getattr(z, "fng", None)
            if f is None:
                return np.zeros(len(c), bool)
            x = float(val)
            if kind == "fng":
                return (f <= x) if L else (f >= 100 - x)
            return (f >= x) if L else (f <= 100 - x)
    raise ValueError(kind)


def combined_mask(z, flts, d, cache=None):
    m = np.ones(len(z.c), bool)
    for k, v in flts:
        key = (k, v, d)
        if cache is not None and key in cache:
            fm = cache[key]
        else:
            fm = np.asarray(filter_mask(z, k, v, d), bool)
            if cache is not None:
                cache[key] = fm
        m &= fm
    return m


def combo_signals(z, params, d, cache=None):
    """Stejné rozhraní jako atlas.family_signals: (indexy vstupů, výstupní signál spouštěče)."""
    fam, p, flts = parse_params(params)
    ent, opp = atlas.family_signals(z, fam, p, d)
    if flts and len(ent):
        ent = ent[combined_mask(z, flts, d, cache)[ent]]
    return ent, opp


def needs_fng(params):
    return any(k in ("fng", "fngg") for _, _, f in [parse_params(params)] for k, _ in f)


# ---------------------------------------------------------------- vyhodnocení
def evaluate(frames, fam, p, flts, exit_name, dname, rng, masks, keep=False):
    """Jedna kombinace na všech mincích: statistiky jako atlas (+ volitelně R a režim každého obchodu)."""
    d = atlas.DIRS[dname]
    sa, ta, ga, uo, mh = atlas.EXITS[exit_name]
    cost = atlas.COSTS[M]
    G, RF, NS, XT, REG = [], [], [], [], []
    RG = [[] for _ in range(atlas.N_RAND)]
    RR = [[] for _ in range(atlas.N_RAND)]
    RN = [[] for _ in range(atlas.N_RAND)]
    for coin, z in frames.items():
        sigs = masks.setdefault("_sig", {})
        if (coin, fam, p, d) not in sigs:
            sigs[(coin, fam, p, d)] = atlas.family_signals(z, fam, p, d)
        ent, opp = sigs[(coin, fam, p, d)]
        opp = np.asarray(opp, bool)
        fm = combined_mask(z, flts, d, masks.setdefault(coin, {})) if flts else np.ones(len(z.c), bool)
        ent = ent[fm[ent]] if len(ent) else ent
        ii, xx, gg, rf = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, ent.astype(np.int64), opp, d, sa, ta, ga, uo, mh)
        G.append(gg); RF.append(rf); NS.append(z.ns[ii]); XT.append(z.ns[xx])
        if keep:
            REG.append(np.asarray(z.reg, dtype=object)[np.maximum(ii - 1, 0)] if len(ii) else np.array([], object))
        if not len(gg):
            continue
        cand = np.flatnonzero(fm & ~np.isnan(z.atr) & (np.arange(len(z.c)) > 200))
        if not len(cand):
            continue
        k = int(len(gg) * 1.4) + 1
        for rep in range(atlas.N_RAND):
            re = np.unique(cand[rng.integers(0, len(cand), size=k)])
            i2, _, g2, r2 = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, re.astype(np.int64), opp, d, sa, ta, ga, uo, mh)
            RG[rep].append(g2); RR[rep].append(r2); RN[rep].append(z.ns[i2])
    g, rf, ns = np.concatenate(G), np.concatenate(RF), np.concatenate(NS)
    st, r = atlas.stats_for(g, rf, ns, cost)
    row = {f"{M}_{k}": v for k, v in st.items()}
    rnd = [(np.concatenate(RG[k]), np.concatenate(RR[k]), np.concatenate(RN[k])) for k in range(atlas.N_RAND) if RG[k]]
    for nm in ("is", "oos", "hold"):
        vals = []
        for g2, r2, n2 in rnd:
            mm = atlas.split_masks(n2)[nm]
            vals.append(((g2[mm] - 2 * cost) / r2[mm]).mean() if mm.any() else np.nan)
        vals = np.array(vals, float)
        fin = np.isfinite(vals)
        row[f"{M}_rnd_{nm}_p95"] = np.quantile(vals[fin], .95) if fin.any() else np.nan
    if keep:
        row["_r"], row["_reg"], row["_xt"] = r, (np.concatenate(REG) if REG else np.array([], object)), np.concatenate(XT)
    return row


def regime_stats(r, regs):
    out = {}
    for lab in regime.LABELS:
        x = r[regs == lab]
        out[lab] = {"n": int(len(x)), "mean_r": round(float(x.mean()), 3) if len(x) else None}
    return out


# ---------------------------------------------------------------- mřížky dílů
def parts():
    seq = [("pair", tf, gs) for tf in TFS for gs in ("A", "B")]
    seq += [("deep", tf, None) for tf in TFS]
    seq += [("sens", tf, None) for tf in TFS]
    return seq


def triggers(tf, atlas_dir=None):
    """Spouštěče timeframu – jen podle IS (OOS/HOLDOUT se nevidí)."""
    path = Path(atlas_dir or ROOT / "reports" / "atlas") / f"{tf}.csv.gz"
    a = pd.read_csv(path, dtype={"params": str})
    a = a[(a["filter"] == "none") & (a.family != "fng") & (a[f"{M}_is_n"] >= MIN_TRIG_IS) & (a[f"{M}_is_r"] > 0)]
    a = a.sort_values(f"{M}_is_t", ascending=False)
    out = []
    for dname in ("long", "short"):
        g = a[a.dir == dname].groupby("family", sort=False).head(1).head(N_TRIG_FAM)
        out += [{"family": r.family, "params": str(r.params), "exit": r.exit, "dir": dname,
                 "is_t": round(float(r[f"{M}_is_t"]), 2)} for _, r in g.iterrows()]
    return out


def filter_values(groups):
    return [(k, v) for g in groups for k, vals in FILTERS[g] for v in vals]


def group_of(kind):
    return next(g for g, lst in FILTERS.items() for k, _ in lst if k == kind)


def load_results(tf=None):
    files = sorted(OUT.glob("part_*.csv.gz"))
    if not files:
        return pd.DataFrame()
    res = pd.concat([pd.read_csv(f, dtype={"params": str, "trigger": str}) for f in files], ignore_index=True)
    return res[res.tf == tf] if tf is not None else res


def grid_for(kind, tf, gs, state, atlas_dir=None):
    """Seznam kombinací dílu (trigger dict + filtry). Stanoví se a zapíše PŘED výpočtem."""
    if kind == "pair":
        trig = triggers(tf, atlas_dir)
        fv = filter_values(GROUP_SETS[gs])
        combos = [(t, [f]) for t, f in product(trig, fv)]
        return {"triggers": trig, "filters": [f"{k}:{fmt_val(v)}" for k, v in fv]}, combos
    prev = load_results(tf)
    if not len(prev):
        return {"note": "žádné předchozí výsledky timeframu"}, []
    if kind == "deep":
        pairs = prev[(prev.n_filters == 1) & (prev.is_gain > 0) & (prev[f"{M}_is_n"] >= 200)]
        pairs = pairs.sort_values(f"{M}_is_t", ascending=False).drop_duplicates("params").head(DEEP_TOP)
        combos, seen = [], set()
        for _, r in pairs.iterrows():
            fam, p, (f1,) = parse_params(r.params)
            t = {"family": fam, "params": "/".join(map(str, p)), "exit": r.exit, "dir": r.dir}
            first_vals = [f1[1]] + neighbors(*f1)
            for v1 in first_vals:
                for f2 in filter_values([g for g in FILTERS if g != group_of(f1[0])]):
                    key = (t["family"], t["params"], t["exit"], t["dir"], (f1[0], v1), f2)
                    if key not in seen:
                        seen.add(key)
                        combos.append((t, [(f1[0], v1), f2]))
        return {"base_pairs": list(pairs.params + " · " + pairs.exit + " · " + pairs.dir),
                "second_filter_groups": "všechny skupiny kromě skupiny prvního filtru"}, combos
    # sens: sousední varianty spouštěče u kombinací, které prošly (i se sousedními hodnotami filtrů → plná kontrola)
    ok = prev[prev["passed"].astype(str) == "True"] if "passed" in prev else prev.iloc[:0]
    V = atlas.variants()
    combos, seen = [], set()
    for _, r in ok.drop_duplicates(["params", "exit", "dir"]).iterrows():
        fam, p, flts = parse_params(r.params)
        idx = [i for i, (f, q) in enumerate(V) if f == fam and tuple(map(str, q)) == tuple(map(str, p))]
        for i in idx:
            for j in (i - 1, i + 1):
                if not (0 <= j < len(V) and V[j][0] == fam):
                    continue
                t = {"family": fam, "params": "/".join(map(str, V[j][1])), "exit": r.exit, "dir": r.dir, "origin": r.params}
                for vals in product(*[[(k, v)] + [(k, x) for x in neighbors(k, v)] for k, v in flts]):
                    key = (t["params"], t["exit"], t["dir"], vals)
                    if key not in seen:
                        seen.add(key)
                        combos.append((t, list(vals)))
    return {"of": list(ok.params.unique())}, combos


# ---------------------------------------------------------------- pravidlo průchodu
def basic_pass(r):
    g = lambda k: r.get(f"{M}_{k}")  # noqa: E731
    try:
        return bool(g("is_n") >= 150 and g("oos_n") >= 50 and g("is_r") > 0 and g("oos_r") > 0 and g("hold_r") > 0
                    and g("oos_r") > g("rnd_oos_p95") and g("hold_r") > g("rnd_hold_p95") and g("oos_t") >= 2
                    and r.get("oos_gain", -9) >= MIN_GAIN)
    except TypeError:
        return False


def robust(row, lookup):
    """Zlepšení drží i v sousedních hodnotách filtrů. lookup: params → řádek výsledků (stejný výstup a směr)."""
    fam, p, flts = parse_params(row["params"])
    why = []
    for i, (k, v) in enumerate(flts):
        nb = neighbors(k, v)
        if not nb:
            if not (row.get("is_gain", -9) > 0):
                why.append(f"{k}: bez zlepšení v IS")
            continue
        for v2 in nb:
            alt = list(flts)
            alt[i] = (k, v2)
            r2 = lookup.get(make_params(fam, "/".join(map(str, p)), alt))
            if r2 is None:
                why.append(f"{k}:{fmt_val(v2)} nespočteno")
            elif not (r2.get("oos_gain", -9) > 0):
                why.append(f"{k}:{fmt_val(v2)} OOS zlepšení {r2.get('oos_gain', float('nan')):+.2f}")
    return not why, "; ".join(why)


def fail_reason(r):
    g = lambda k: r.get(f"{M}_{k}")  # noqa: E731
    out = []
    if not (g("is_n") >= 150 and g("oos_n") >= 50):
        out.append("málo obchodů")
    for nm, lab in (("is", "IS"), ("oos", "OOS"), ("hold", "HOLDOUT")):
        if not (g(f"{nm}_r") > 0):
            out.append(f"{lab} ≤ 0")
    if not (g("oos_r") > g("rnd_oos_p95")) or not (g("hold_r") > g("rnd_hold_p95")):
        out.append("pod p95 náhody")
    if not (g("oos_t") >= 2):
        out.append("OOS t < 2")
    if not (r.get("oos_gain", -9) >= MIN_GAIN):
        out.append("neporáží spouštěč o 0,05 R")
    return ", ".join(out)


# ---------------------------------------------------------------- registr
def register(cands, reg, today, part_no):
    """cands: seznam dictů (řádek výsledků + regime_stats + regimes). Vrací seznam změn (texty)."""
    changes = []
    known = {s["id"] for s in reg["strategies"]}
    added = 0
    score = lambda b: min(b.get("oos_t") or -9, b.get("hold_t") or -9)  # noqa: E731
    for c in sorted(cands, key=lambda c: -min(c[f"{M}_oos_t"], c[f"{M}_hold_t"])):
        if added >= MAX_NEW:
            break
        e = {"family": "combo", "params": c["params"], "tf": c["tf"], "filter": "none", "exit": c["exit"], "dir": c["dir"]}
        key = registry.sid(e)
        if key in known:
            continue
        bt = {k: (round(float(c[f"{M}_{k}"]), 3) if pd.notna(c[f"{M}_{k}"]) else None)
              for k in ("is_r", "oos_r", "hold_r", "oos_t", "hold_t", "is_n", "oos_n", "hold_n")}
        bt |= {"maxdd_r": round(float(c.get("maxdd_r", np.nan)), 1) if pd.notna(c.get("maxdd_r")) else None,
               "per_month": round(float(c.get("per_month", np.nan)), 1) if pd.notna(c.get("per_month")) else None,
               "trigger_oos_r": round(float(c["base_oos_r"]), 3)}
        active_combo = [s for s in registry.active(reg) if s["family"] == "combo"]
        replaced = None
        if len(active_combo) >= MAX_ACTIVE:
            weakest = min(active_combo, key=lambda s: score(s.get("backtest", {})))
            if score(bt) <= score(weakest.get("backtest", {})):
                continue
            weakest["status"] = "vyřazeno"
            weakest.setdefault("history", []).append(
                {"date": today, "status": "vyřazeno",
                 "reason": f"combo_study: nahrazeno silnější kombinací (min t {score(bt):.2f} > {score(weakest.get('backtest', {})):.2f})"})
            replaced = weakest["label"]
        reason = (f"combo_study: díl {part_no}, OOS {bt['oos_r']:+.2f} R (t {bt['oos_t']:+.1f}), HOLDOUT {bt['hold_r']:+.2f} R "
                  f"(t {bt['hold_t']:+.1f}), spouštěč sám OOS {bt['trigger_oos_r']:+.2f} R")
        entry = e | {"id": key, "label": registry.label(e), "added": today, "source": f"combo_study díl {part_no} {today}",
                     "backtest": bt, "regime_stats": c["regime_stats"], "regimes": c["regimes"], "status": "papír",
                     "history": [{"date": today, "status": "papír", "reason": reason}]}
        reg["strategies"].append(entry)
        known.add(key)
        added += 1
        changes.append(f"🆕 {entry['label']} → papír ({reason}); režimy: {', '.join(c['regimes'])}"
                       + (f"; nahradila {replaced}" if replaced else ""))
    return changes


# ---------------------------------------------------------------- běh dílu
def frames_for(tf, cache):
    from research import lab
    frames = lab.load_frames(tf, cache)
    fng_ok = True
    try:
        fng = lab.fng_series()
    except Exception as exc:
        print(f"Strach a chamtivost nedostupné: {exc.__class__.__name__}", flush=True)
        fng, fng_ok = None, False
    for z in frames.values():
        z.ns = z.df.index.as_unit("ns").asi8.astype(np.int64)
        if fng is not None:
            z.fng = fng.reindex(z.df.index.floor("1D")).ffill().to_numpy(float)
    span_m = max(1.0, np.mean([(z.df.index[-1] - z.df.index[0]).days for z in frames.values()]) / 30.4)
    return frames, fng_ok, span_m


def run_part(cache, state=None, frames=None, atlas_dir=None, save=True):
    st = state if state is not None else load_state()
    no = st["next"]
    kind, tf, gs = parts()[no % len(parts())]
    meta, combos = grid_for(kind, tf, gs, st, atlas_dir)
    trig_keys = sorted({(t["family"], t["params"], t["exit"], t["dir"]) for t, _ in combos})
    part = {"no": no + 1, "kind": kind, "tf": tf, "groups": GROUP_SETS.get(gs) if gs else None, "grid": meta,
            "n_combos": len(combos), "n_baselines": len(trig_keys), "n_tests": len(combos) + len(trig_keys),
            "started": datetime.now(timezone.utc).isoformat(timespec="seconds"), "status": "běží"}
    st.setdefault("parts", []).append(part)
    st["total_tests"] = st.get("total_tests", 0) + part["n_tests"]
    if save:
        save_state(st)                                                   # mřížka zapsána PŘED výsledky
    t0 = time.time()
    fng_ok, span_m = True, 1.0
    if frames is None:
        frames, fng_ok, span_m = frames_for(tf, cache)
    if not fng_ok:
        combos = [(t, f) for t, f in combos if not any(k in ("fng", "fngg") for k, _ in f)]
        part["note"] = "Strach a chamtivost nedostupné – sentiment filtry vynechány"
    rng = np.random.default_rng(20261104 + no)
    masks = {}
    base = {}
    for fam, p, ex, dname in trig_keys:
        base[(fam, p, ex, dname)] = evaluate(frames, fam, tuple(_typed(x) for x in p.split("/")), [], ex, dname, rng, masks)
    rows = []
    for t, flts in combos:
        key = (t["family"], t["params"], t["exit"], t["dir"])
        r = evaluate(frames, t["family"], tuple(_typed(x) for x in t["params"].split("/")), flts, t["exit"], t["dir"], rng, masks)
        b = base[key]
        r |= {"part": no + 1, "kind": kind, "tf": tf, "params": make_params(t["family"], t["params"], flts),
              "trigger": f"{t['family']}:{t['params']}", "exit": t["exit"], "dir": t["dir"], "n_filters": len(flts),
              "base_is_r": b[f"{M}_is_r"], "base_oos_r": b[f"{M}_oos_r"], "base_hold_r": b[f"{M}_hold_r"],
              "base_oos_n": b[f"{M}_oos_n"]}
        r["is_gain"] = r[f"{M}_is_r"] - r["base_is_r"] if pd.notna(r[f"{M}_is_r"]) and pd.notna(r["base_is_r"]) else np.nan
        r["oos_gain"] = r[f"{M}_oos_r"] - r["base_oos_r"] if pd.notna(r[f"{M}_oos_r"]) and pd.notna(r["base_oos_r"]) else np.nan
        r["origin"] = t.get("origin", "")
        rows.append(r)
    res = pd.DataFrame(rows)
    if len(res):
        lookup = {(x["params"], x["exit"], x["dir"]): x for x in res.to_dict("records")}
        prev = load_results(tf)
        for x in (prev.to_dict("records") if len(prev) else []):
            lookup.setdefault((x["params"], x["exit"], x["dir"]), x)
        res["basic"] = [basic_pass(x) for x in res.to_dict("records")]
        rob = [robust(x, {k[0]: v for k, v in lookup.items() if k[1] == x["exit"] and k[2] == x["dir"]}) if x["basic"]
               else (False, "") for x in res.to_dict("records")]
        res["robust"] = [a for a, _ in rob]
        res["why"] = [w if b else fail_reason(x) for (a, w), b, x in zip(rob, res["basic"], res.to_dict("records"))]
    else:
        res = pd.DataFrame(columns=["params", "basic", "robust", "why"])
    # režimy pro prošlé
    cands = []
    for i, x in res[res.robust == True].iterrows():  # noqa: E712
        fam, p, flts = parse_params(x["params"])
        k = evaluate(frames, fam, p, flts, x["exit"], x["dir"], np.random.default_rng(1), masks, keep=True)
        rs = regime_stats(k["_r"], k["_reg"])
        allowed = [lab for lab, v in rs.items() if v["n"] >= 30 and (v["mean_r"] or 0) > 0.05]
        res.loc[i, "regimes"] = ", ".join(allowed) if allowed else "–"
        res.loc[i, "maxdd_r"] = atlas.max_dd(k["_r"], k["_xt"])
        res.loc[i, "per_month"] = len(k["_r"]) / span_m
        if allowed:
            cands.append(x.to_dict() | {"regime_stats": rs, "regimes": allowed, "maxdd_r": res.loc[i, "maxdd_r"],
                                        "per_month": res.loc[i, "per_month"]})
        else:
            res.loc[i, "why"] = "žádný režim s ≥ 30 obchody a Ø R > 0,05"
    res["passed"] = res["robust"].astype(bool) & res["params"].isin([c["params"] for c in cands]) if len(res) else []
    part.update({"status": "hotovo", "seconds": round(time.time() - t0), "n_basic": int(res["basic"].sum()) if len(res) else 0,
                 "n_passed": len(cands)})
    if save:
        OUT.mkdir(parents=True, exist_ok=True)
        res.drop(columns=[c for c in res.columns if c.startswith("_")]).to_csv(
            OUT / f"part_{no + 1:03d}.csv.gz", index=False, float_format="%.5f")
    st["next"] = no + 1
    return st, part, res, cands


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"started": datetime.now(timezone.utc).date().isoformat(), "next": 0, "total_tests": 0, "parts": []}


def save_state(st):
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- report
def _f(x, d=2):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{d}f}".replace(".", ",")


def knowledge_lines(res):
    """Filtry, které na timeframu průměrně zhoršily OOS spouštěčů (≥ 6 spouštěčů, OOS i IS zhoršení)."""
    out = []
    if not len(res):
        return out
    pairs = res[res.n_filters == 1].copy()
    pairs["ftype"] = pairs.params.str.split("+").str[1].str.split(":").str[0]
    for (tf, ft), g in pairs.groupby(["tf", "ftype"]):
        if g.trigger.nunique() >= 6 and g.oos_gain.mean() <= -0.05 and g.is_gain.mean() <= 0:
            out.append((tf, ft, g.oos_gain.mean(), g.trigger.nunique()))
    out.sort(key=lambda x: x[2])
    return out[:6]


def update_knowledge(res, today):
    lines = knowledge_lines(res)
    if not KNOWLEDGE.exists():
        return
    txt = KNOWLEDGE.read_text(encoding="utf-8")
    a, b = "<!-- combo-study:start -->", "<!-- combo-study:end -->"
    body = "".join(f"- **Kombinace: filtr {FILTER_CS.get(ft, ft).split(' ')[0]} ({ft}) jako potvrzení na {tf.upper()}** – "
                   f"průměrně zhoršil OOS spouštěčů o {_f(g)} R (n spouštěčů {n}, IS také bez zlepšení) – "
                   f"`reports/combo_study.md` – {today}.\n" for tf, ft, g, n in lines)
    block = f"{a}\n{body}{b}"
    if a in txt:
        pre, rest = txt.split(a, 1)
        txt = pre + block + rest.split(b, 1)[1]
    elif body:
        head = "## 🧪 Vnější důkazy"
        txt = txt.replace(head, block + "\n\n" + head, 1)
    else:
        return
    KNOWLEDGE.write_text(txt, encoding="utf-8")


def report(state=None, changes=None):
    st = state or load_state()
    res = load_results()
    reg = registry.load()
    L = ["# 🧩 Studie kombinací ukazatelů, signálů a spouštěčů\n",
         "Průběžná studie: spouštěč z atlasu + 1–2 potvrzení/filtry z jiných rodin nebo kontextu. Metoda, filtry a pravidla "
         "jsou stanoveny předem v hlavičce `research/experiments/combo_study.py`; data, náklady (MEXC 0,05 %/stranu), "
         "simulace a dělení IS (do 12/2023) / OOS (1/2024–6/2025) / HOLDOUT (7/2025–) jsou stejné jako v atlasu. "
         "Papírově, nic nejde na skutečné peníze. Nejde o finanční poradenství.\n"]
    done = [p for p in st.get("parts", []) if p.get("status") == "hotovo"]
    L.append(f"- Hotových dílů: **{len(done)}**, testovaných kombinací celkem (vč. samotných spouštěčů): "
             f"**{st.get('total_tests', 0)}** – při tolika testech projde pravidlem i něco čistě náhodou, proto jen papír.")
    if done:
        p = done[-1]
        L.append(f"- Poslední díl {p['no']}: **{p['kind']} {p['tf'].upper()}**"
                 + (f" (skupiny {', '.join(p['groups'])})" if p.get("groups") else "")
                 + f", {p['n_combos']} kombinací + {p['n_baselines']} spouštěčů samotných, {p.get('seconds', '?')} s; "
                 f"základní pravidlo splnilo {p.get('n_basic', 0)}, prošlo vč. citlivosti a režimů {p.get('n_passed', 0)}."
                 + (f" {p['note']}." if p.get("note") else ""))
        g = p.get("grid", {})
        if g.get("triggers"):
            L.append("- Mřížka (stanovena před výpočtem): spouštěče " + "; ".join(
                f"{t['family']} {t['params']} · {t['exit']} · {t['dir']}" for t in g["triggers"]) + " × filtry "
                + ", ".join(g.get("filters", [])) + ".")
        elif g.get("base_pairs"):
            L.append("- Mřížka (stanovena před výpočtem): nejlepší páry podle IS t: " + "; ".join(g["base_pairs"])
                     + " + druhý filtr (" + g.get("second_filter_groups", "") + ") + sousední hodnoty prvního filtru.")
        elif "of" in g:
            L.append("- Mřížka (stanovena před výpočtem): sousední varianty spouštěče u prošlých kombinací: "
                     + (", ".join(g["of"]) or "žádné prošlé – díl prázdný") + ".")
    nxt = parts()[st.get("next", 0) % len(parts())]
    L.append(f"- Další díl: **{nxt[0]} {nxt[1].upper()}**" + (f" (skupiny {', '.join(GROUP_SETS[nxt[2]])})" if nxt[2] else "") + ".\n")
    if changes:
        L.append("## Změny v registru v tomto běhu\n")
        L += [f"- {c}" for c in changes]
        L.append("")
    act = [s for s in registry.active(reg) if s["family"] == "combo"]
    L.append(f"## Combo strategie v registru ({len(act)} aktivních, limit {MAX_ACTIVE})\n")
    if act:
        L.append("| Strategie | Stav | OOS Ø R (t) | HOLDOUT Ø R (t) | Spouštěč sám OOS | Režimy | Papír |")
        L.append("|---|---|---|---|---|---|---|")
        for s in act:
            b, pp = s.get("backtest", {}), s.get("paper") or {}
            L.append(f"| {s['label']} | {s['status']} | {_f(b.get('oos_r'))} ({_f(b.get('oos_t'), 1)}) | "
                     f"{_f(b.get('hold_r'))} ({_f(b.get('hold_t'), 1)}) | {_f(b.get('trigger_oos_r'))} | "
                     f"{', '.join(s.get('regimes', []))} | {pp.get('n', 0)} obch., Ø {_f(pp.get('mean_r'))} R |")
    else:
        L.append("Zatím žádná.")
    L.append("")
    if len(res):
        L.append("## Top 10 kombinací (podle min(OOS t, HOLDOUT t), všechny díly)\n")
        L.append("| Díl | TF | Kombinace | Výstup · směr | IS Ø R (t) | OOS Ø R (t) | HOLDOUT Ø R (t) | p95 náhody OOS / HOLD | "
                 "Spouštěč sám OOS | Obchodů IS/OOS/HOLD | Výsledek |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        r = res.copy()
        r["score"] = np.minimum(r[f"{M}_oos_t"].fillna(-9), r[f"{M}_hold_t"].fillna(-9))
        for _, x in r.sort_values("score", ascending=False).drop_duplicates(["params", "exit", "dir"]).head(10).iterrows():
            res_txt = "✅ prošlo" if x.get("passed") in (True, "True") else f"❌ {x.get('why') or 'neprošlo'}"
            L.append(f"| {int(x.part)} | {x.tf.upper()} | {pretty(x.params)} | {x.exit} · {x.dir} | "
                     f"{_f(x[f'{M}_is_r'])} ({_f(x[f'{M}_is_t'], 1)}) | {_f(x[f'{M}_oos_r'])} ({_f(x[f'{M}_oos_t'], 1)}) | "
                     f"{_f(x[f'{M}_hold_r'])} ({_f(x[f'{M}_hold_t'], 1)}) | {_f(x[f'{M}_rnd_oos_p95'])} / "
                     f"{_f(x[f'{M}_rnd_hold_p95'])} | {_f(x.base_oos_r)} | {int(x[f'{M}_is_n'])}/{int(x[f'{M}_oos_n'])}/"
                     f"{int(x[f'{M}_hold_n'])} | {res_txt} |")
        L.append("\n## Co filtry dělají se spouštěči (páry, průměr přes spouštěče)\n")
        pr = res[res.n_filters == 1].copy()
        if len(pr):
            pr["filtr"] = pr.params.str.split("+").str[1]
            L.append("| TF | Filtr | Spouštěčů | Ø zlepšení IS | Ø zlepšení OOS | Podíl OOS zlepšení > 0 | Splnilo základní pravidlo |")
            L.append("|---|---|---|---|---|---|---|")
            for (tf, f), g in pr.groupby(["tf", "filtr"]):
                L.append(f"| {tf.upper()} | {f} | {g.trigger.nunique()} | {_f(g.is_gain.mean())} | {_f(g.oos_gain.mean())} | "
                         f"{(g.oos_gain > 0).mean():.0%} | {int(g.basic.astype(str).eq('True').sum())} |")
        L.append("\n## Proč neprošly (nejčastější důvody)\n")
        why = res[res.passed.astype(str) != "True"].why.fillna("").str.split(", ").explode()
        for w, n in why[why != ""].value_counts().head(8).items():
            L.append(f"- {w}: {n}×")
    L.append("\n## Plán studie\n")
    L.append("Páry spouštěč + 1 filtr (každý TF ve dvou skupinách filtrů) → nejlepší páry podle IS + druhý filtr → citlivost "
             "sousedních parametrů spouštěče. Pak znovu na čerstvých datech. Funding/OI zatím chybí historická data.")
    L.append("\nPovyšování a vyřazování combo strategií dělá laboratoř (`research/lab.py`) podle papírových výsledků.")
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    return "\n".join(L)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "report":
        report()
        return
    cache = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/cache")
    today = datetime.now(timezone.utc).date().isoformat()
    st = load_state()
    summary = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "changes": [], "error": None}
    try:
        st, part, res, cands = run_part(cache, st)
        reg = registry.load()
        changes = register(cands, reg, today, part["no"])
        if changes:
            registry.save(reg)
        save_state(st)
        update_knowledge(load_results(), today)
        report(st, changes)
        summary |= {"part": part, "changes": changes,
                    "passed": [{k: (v if not isinstance(v, float) else round(v, 3)) for k, v in c.items()
                                if k in ("params", "tf", "exit", "dir", "regimes", f"{M}_oos_r", f"{M}_oos_t",
                                         f"{M}_hold_r", f"{M}_hold_t", "base_oos_r")} for c in cands]}
    except Exception as exc:
        summary["error"] = f"{exc.__class__.__name__}: {str(exc)[:300]}"
        if st.get("parts") and st["parts"][-1].get("status") == "běží":
            st["parts"][-1]["status"] = "selhalo"
            st["parts"][-1]["error"] = summary["error"]
            save_state(st)
        raise
    finally:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "last_run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str) + "\n",
                                           encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
