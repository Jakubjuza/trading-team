"""IFVG (inverse fair value gap, ICT) – test na 7 timeframech, bez mozku i s mozkem. Jen výzkum, nic se nezapíná.

Proč: uživatel (18. 11. 2026) viděl tradera s IFVG a chce vědět, jestli to funguje – a hlavně jestli pomůže, když
„mozek“ posoudí, zda je trh na takový vstup nastavený (aby se nevstupovalo slepě do každého fake outu).

Stanoveno PŘEDEM (18. 11. 2026), po spuštění se nic neladí:

  Vzor (vše známé na close svíčky, žádný pohled do budoucnosti):
    FVG = mezera mezi 3 svíčkami: býčí, když low[k] > high[k−2] (zóna high[k−2] … low[k]); medvědí, když
          high[k] < low[k−2] (zóna high[k] … low[k−2]). Velikost zóny ≥ g × ATR(14), g ∈ {0; 0,5}.
    IFVG long  = medvědí FVG, kterou cena do W svíček po vzniku poprvé ZAVŘE NAD horní hranou (mezera se „překlopí“
                 v podporu). IFVG short = zrcadlo: býčí FVG zavřená pod spodní hranou. W ∈ {10, 30}.
    Vstup inv    = na open svíčky po překlopení.
    Vstup retest = po překlopení čeká až 5 svíček na návrat do zóny, která vydrží (long: low ≤ horní hrana a close
                   nad spodní hranou; short zrcadlo); vstup na open další svíčky. Bez retestu žádný obchod.
    → 8 variant × 7 timeframů {15M, 1H, 2H, 4H, 6H, 12H, 1D} × filtr {none, d200, d50} × výstup {opp, trail, target,
      opp_stop} × long/short = 1 344 kombinací. Výstup „opp“ = opačné IFVG překlopení. Simulace, filtry, výstupy,
      data (OKX spot, 8 mincí, 1H od 1/2019, 15M od 1/2022), poplatky (MEXC futures 0,05 %/stranu rozhoduje, ukáže
      se i 0,15 %), rozdělení IS < 2024-01-01 ≤ OOS < 2025-07-01 ≤ HOLDOUT a náhodné vstupy (10 opakování) přesně
      jako v atlasu (research/experiments/strategy_atlas.py).

  Mozek (učí se JEN z IS, v OOS a HOLDOUTU se jen použije):
    Fáze  – stejné fáze trhu jako Dispečer a Mozek města (research/downtown_dispatch.py): BTC nad/pod SMA200 ·
            trend/pila (efektivita 30 dní ≥ 0,25) · divoko/klid (30denní vola vs. medián 365 dní), z předchozího dne.
            Pro každou kombinaci je fáze zapnutá, když v ní IFVG v IS měla ≥ 12 obchodů, Ø R > 0 a t ≥ 1 (pravidlo
            Dispečera). Vstup jen v zapnuté fázi.
    Kontext – metriky research/context.py u každého signálu (trend mince a BTC, trendovost, ADX, chop, poloha
            v rozpětí, POKRAČOVÁNÍ PRŮRAZŮ = detektor fake outů, uklidnění, zavření svíčky, objem, přetažení,
            Strach a chamtivost). Váhy jako kontextová brána (context_gate.py): pro timeframe × směr z IS obchodů
            výstupu target bez filtru (všech 8 variant), horní vs. dolní třetina, váha = znaménko rozdílu při |t| ≥ 2
            (klastry po týdnech), jinak 0. Skóre = Σ váha × standardizovaná metrika; vstup jen se skóre ≥ 40. percentil IS.
    Mozek  – obojí zároveň (fáze zapnutá A kontext ≥ práh).

  PROJDE (bez mozku) – pravidlo atlasu: IS ≥ 150 a OOS ≥ 50 obchodů, Ø R > 0 v IS, OOS i HOLDOUT, OOS i HOLDOUT nad
    95. percentilem vlastních náhodných vstupů, OOS t ≥ 2. Výběr: 10 nejlepších podle IS t na směr.
  PROJDE (s mozkem, zvlášť Fáze / Kontext / Mozek) – IS ≥ 100, OOS ≥ 30, HOLDOUT ≥ 20 obchodů po bráně, Ø R > 0
    ve všech třech, OOS t ≥ 2, OOS i HOLDOUT nad p95 náhodných vstupů A nad p95 „náhodného mozku“ (stejný podíl
    obchodů vyřazený náhodně, 200 opakování). Výběr: 10 nejlepších podle IS t po bráně na směr.
  Pomáhá mozek obecně? Podíl kombinací, kde má brána v OOS i HOLDOUTU vyšší Ø R než bez ní (bez výhody ~25 %).

    python3 research/experiments/ifvg_study.py run 4h /tmp/cache     → reports/ifvg/4h.csv.gz (+ .meta, .json)
    python3 research/experiments/ifvg_study.py report reports/ifvg    → reports/ifvg.md
Nejde o finanční poradenství.
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
from research import context  # noqa: E402
from research.experiments import strategy_atlas as atlas  # noqa: E402
from research.experiments.strategy_atlas import njit  # noqa: E402

M = atlas.MAIN
COSTS = {"mexc_fut": atlas.COSTS["mexc_fut"], "old": atlas.COSTS["old"]}
VARIANTS = [(g, w, e) for g in (0.0, 0.5) for w in (10, 30) for e in ("inv", "retest")]
RETEST_BARS = 5
KEEP_Q = 0.40
PH_MIN_N, PH_T = 12, 1.0
N_DROP = 200
BRAINS = ("raw", "faze", "kontext", "mozek")
BRAIN_CS = {"raw": "bez mozku", "faze": "mozek: fáze trhu", "kontext": "mozek: kontext signálu", "mozek": "mozek: fáze + kontext"}
OUT = ROOT / "reports" / "ifvg"
WEEK = 7 * 86400 * 10**9


# ---------------------------------------------------------------- vzor
@njit(cache=True)
def ifvg_marks(h, l, c, atr, d, gmin, win, retest, rb):
    n = len(c)
    out = np.zeros(n, np.bool_)
    for k in range(2, n):
        a = atr[k]
        if not (a > 0):
            continue
        if d > 0:                       # long: medvědí FVG (high[k] < low[k−2]) zavřená nad horní hranou
            top, bot = l[k - 2], h[k]
        else:                           # short: býčí FVG (low[k] > high[k−2]) zavřená pod spodní hranou
            top, bot = l[k], h[k - 2]
        if not (top > bot) or top - bot < gmin * a:
            continue
        end = min(n, k + 1 + win)
        for j in range(k + 1, end):
            if (d > 0 and c[j] > top) or (d < 0 and c[j] < bot):
                if not retest:
                    out[j] = True
                else:
                    for t in range(j + 1, min(n, j + 1 + rb)):
                        if d > 0 and l[t] <= top and c[t] > bot:
                            out[t] = True
                            break
                        if d < 0 and h[t] >= bot and c[t] < top:
                            out[t] = True
                            break
                break
    return out


def signals(z, var, d):
    g, w, e = var
    ent = ifvg_marks(z.h, z.l, z.c, z.atr, float(d), g, w, e == "retest", RETEST_BARS)
    opp = ifvg_marks(z.h, z.l, z.c, z.atr, float(-d), g, w, False, RETEST_BARS)
    return np.flatnonzero(ent), opp


# ---------------------------------------------------------------- mozek
def fng_series():
    import urllib.request
    with urllib.request.urlopen("https://api.alternative.me/fng/?limit=0&format=json", timeout=30) as r:
        data = json.loads(r.read())["data"]
    s = pd.Series({pd.Timestamp(int(x["timestamp"]), unit="s", tz="UTC"): float(x["value"]) for x in data}).sort_index()
    s.index = s.index.floor("1D") + pd.Timedelta("1D")
    return s


def phases(btc_1h):
    """Fáze trhu – stejná pravidla jako research/downtown_dispatch.phases (platí pro den D z close dne D−1)."""
    b = pd.to_numeric(btc_1h["Close"], errors="coerce").resample("1D").last().dropna()
    b = b[b.index + pd.Timedelta("1D") <= datetime.now(timezone.utc)]
    sma200 = b.rolling(200).mean()
    er = (b - b.shift(30)).abs() / b.diff().abs().rolling(30).sum()
    vol = np.log(b).diff().rolling(30).std() * np.sqrt(365)
    volmed = vol.rolling(365, min_periods=120).median()
    ok = sma200.notna() & er.notna() & volmed.notna()
    f = pd.Series(np.where(b > sma200, "býk", "medvěd"), index=b.index) + " · " + \
        pd.Series(np.where(er >= 0.25, "trend", "pila"), index=b.index) + " · " + \
        pd.Series(np.where(vol > volmed, "divoko", "klid"), index=b.index)
    f = f[ok]
    f.index = f.index + pd.Timedelta("1D")
    return f


def cl_t(r, wk):
    r = np.asarray(r, float)
    n = len(r)
    if n < 3:
        return (r.mean() if n else np.nan), np.nan, np.nan
    m = r.mean()
    s = pd.Series(r - m).groupby(np.asarray(wk)).sum().to_numpy()
    var = (s ** 2).sum() / n ** 2
    return m, (m / np.sqrt(var) if var > 0 else np.nan), var


def fit_context(F, r, wk):
    """Váhy kontextu z IS obchodů (pravidla context_gate.py). F = {metrika: pole}."""
    weights, norm, info = {}, {}, {}
    for f in context.FEATURES:
        x = np.asarray(F[f], float)
        ok = np.isfinite(x)
        if ok.sum() < 60:
            weights[f], norm[f] = 0, [0.0, 1.0]
            continue
        q1, q2 = np.quantile(x[ok], [1 / 3, 2 / 3])
        lo, hi = ok & (x <= q1), ok & (x >= q2)
        ma, _, va = cl_t(r[hi], wk[hi])
        mb, _, vb = cl_t(r[lo], wk[lo])
        v = va + vb
        t = (ma - mb) / np.sqrt(v) if np.isfinite(v) and v > 0 else np.nan
        weights[f] = int(np.sign(ma - mb)) if np.isfinite(t) and abs(t) >= 2 else 0
        sd = float(np.std(x[ok]))
        norm[f] = [float(np.mean(x[ok])), sd if sd > 0 else 1.0]
        info[f] = {"t": None if not np.isfinite(t) else round(float(t), 2), "hi_r": round(float(ma), 3), "lo_r": round(float(mb), 3)}
    model = {"weights": weights, "norm": norm}
    s = context.score(model, F)
    model["threshold"] = float(np.quantile(s, KEEP_Q)) if any(weights.values()) else -np.inf
    model["info"] = info
    return model


# ---------------------------------------------------------------- běh jednoho timeframu
def load(tf, cache):
    base_tf, start = ("15m", "2022-01-01") if tf == "15m" else ("1h", "2019-01-01")
    try:
        fng = fng_series()
    except Exception as exc:
        print(f"Strach a chamtivost nedostupné: {exc.__class__.__name__}", flush=True)
        fng = None
    h1 = {c: atlas.fetch(c, "1h", "2019-01-01", cache) for c in atlas.COINS}
    base = {c: (atlas.fetch(c, base_tf, start, cache) if tf == "15m" else h1[c]) for c in atlas.COINS}
    ph = phases(h1["BTC"])
    daily = {c: atlas.resample(b, "1d") for c, b in h1.items()}
    prep = {}
    for coin, b in base.items():
        if len(b) < 500:
            print(f"{coin}: málo dat ({len(b)}), vynecháno", flush=True)
            continue
        df = atlas.resample(b, tf)
        z = atlas.Ind(df)
        bull, up50 = atlas.daily_regimes(h1[coin])
        day = df.index.floor("1D")
        z.flt = {"d200": bull.reindex(day).to_numpy(float), "d50": up50.reindex(day).to_numpy(float)}
        z.ns = df.index.as_unit("ns").asi8.astype(np.int64)
        z.ph = ph.reindex(day).fillna("").to_numpy(dtype=object)
        tfc = context.TfContext(df, context.daily_frame(daily[coin], daily["BTC"], fng))
        allidx = np.arange(len(df))
        z.F = {dd: {k: np.asarray(v, np.float32) for k, v in tfc.at(allidx, dd).items()} for dd in (1, -1)}
        prep[coin] = z
        print(f"{coin} {tf}: {len(df)} svíček {df.index[0]:%Y-%m-%d} → {df.index[-1]:%Y-%m-%d}", flush=True)
    return prep, fng is not None


def stats(r, ns, g, cost):
    out = {}
    for nm, m in atlas.split_masks(ns).items():
        x = r[m]
        n = len(x)
        sd = x.std(ddof=1) if n > 1 else np.nan
        out[f"{nm}_n"] = n
        out[f"{nm}_r"] = x.mean() if n else np.nan
        out[f"{nm}_t"] = x.mean() / (sd / np.sqrt(n)) if n > 1 and sd > 0 else np.nan
        out[f"{nm}_win"] = (x > 0).mean() if n else np.nan
        out[f"{nm}_pct"] = (g[m] - 2 * cost).mean() * 100 if n else np.nan
    return out


def run(tf, cache):
    t0 = time.time()
    prep, has_fng = load(tf, cache)
    span_m = max(1.0, np.mean([(z.df.index[-1] - z.df.index[0]).days for z in prep.values()]) / 30.4)
    rng = np.random.default_rng(20261118 + sum(map(ord, tf)))
    combos = list(product(VARIANTS, atlas.FILTERS, atlas.EXITS, atlas.DIRS.items()))
    T, okcache = [], {}
    # 1) obchody všech kombinací + náhodné vstupy
    for var, flt, ex, (dname, d) in combos:
        sa, ta, ga, uo, mh = atlas.EXITS[ex]
        parts = []
        RG, RR, RN = ([[] for _ in range(atlas.N_RAND)] for _ in range(3))
        for ci, (coin, z) in enumerate(prep.items()):
            ent, opp = signals(z, var, d)
            if flt != "none":
                ent = ent[z.flt[flt][ent] == (1.0 if d > 0 else 0.0)]
            ii, xx, gg, rf = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, ent.astype(np.int64), opp, d, sa, ta, ga, uo, mh)
            if not len(gg):
                continue
            parts.append((np.full(len(gg), ci), ii - 1, gg, rf, z.ns[ii], z.ns[xx]))
            key = (coin, d, flt)
            if key not in okcache:
                ok = ~np.isnan(z.atr) & (np.arange(len(z.c)) > 200)
                if flt != "none":
                    ok &= z.flt[flt] == (1.0 if d > 0 else 0.0)
                okcache[key] = np.flatnonzero(ok)
            cand = okcache[key]
            if not len(cand):
                continue
            k = int(len(gg) * 1.4) + 1
            for rep in range(atlas.N_RAND):
                re = np.unique(cand[rng.integers(0, len(cand), size=k)])
                i2, _, g2, r2 = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, re.astype(np.int64), opp, d, sa, ta, ga, uo, mh)
                RG[rep].append(g2); RR[rep].append(r2); RN[rep].append(z.ns[i2])
        if parts:
            ci, si, gg, rf, ns, xt = (np.concatenate(p) for p in zip(*parts))
        else:
            ci = si = np.zeros(0, np.int64); gg = rf = np.zeros(0); ns = xt = np.zeros(0, np.int64)
        rnd = {}
        for cname, cost in COSTS.items():
            for nm in ("oos", "hold"):
                vals = []
                for rep in range(atlas.N_RAND):
                    if not RG[rep]:
                        continue
                    g2, r2, n2 = np.concatenate(RG[rep]), np.concatenate(RR[rep]), np.concatenate(RN[rep])
                    m = atlas.split_masks(n2)[nm]
                    vals.append(((g2[m] - 2 * cost) / r2[m]).mean() if m.any() else np.nan)
                vals = np.array(vals, float)
                rnd[f"{cname}_rnd_{nm}_p95"] = np.quantile(vals[np.isfinite(vals)], .95) if np.isfinite(vals).any() else np.nan
        T.append({"var": var, "flt": flt, "ex": ex, "dir": dname, "d": d, "ci": ci, "si": si, "g": gg, "rf": rf,
                  "ns": ns, "xt": xt, "rnd": rnd})
    print(f"{tf}: obchody hotové za {time.time() - t0:.0f} s", flush=True)
    coins = list(prep.values())

    def feats(t):
        out = {f: np.full(len(t["si"]), np.nan) for f in context.FEATURES}
        for c in np.unique(t["ci"]):
            m = t["ci"] == c
            for f in context.FEATURES:
                out[f][m] = coins[c].F[t["d"]][f][t["si"][m]]
        return out

    def phase(t):
        out = np.empty(len(t["si"]), dtype=object)
        for c in np.unique(t["ci"]):
            m = t["ci"] == c
            out[m] = coins[c].ph[t["si"][m]]
        return out

    # 2) mozek – kontextové váhy pro směr z IS (výstup target, bez filtru, všech 8 variant)
    models = {}
    for dname in atlas.DIRS:
        fit = [t for t in T if t["dir"] == dname and t["ex"] == "target" and t["flt"] == "none"]
        Fs, rs, ws = [], [], []
        for t in fit:
            m = t["ns"] < atlas.SPLIT_OOS.value
            if not m.any():
                continue
            F = feats(t)
            Fs.append({f: v[m] for f, v in F.items()})
            rs.append(((t["g"] - 2 * COSTS[M]) / t["rf"])[m])
            ws.append(t["ns"][m] // WEEK)
        if not Fs:
            models[dname] = {"weights": {f: 0 for f in context.FEATURES}, "norm": {f: [0.0, 1.0] for f in context.FEATURES},
                             "threshold": -np.inf, "info": {}}
            continue
        F = {f: np.concatenate([x[f] for x in Fs]) for f in context.FEATURES}
        models[dname] = fit_context(F, np.concatenate(rs), np.concatenate(ws))
        print(f"{tf} {dname}: váhy {[(f, w) for f, w in models[dname]['weights'].items() if w]}", flush=True)

    # 3) statistiky bez mozku a s mozkem
    rows = []
    for t in T:
        row = {"tf": tf, "gap": t["var"][0], "win": t["var"][1], "entry": t["var"][2], "filter": t["flt"],
               "exit": t["ex"], "dir": t["dir"], "per_month": len(t["g"]) / span_m, **t["rnd"]}
        if len(t["g"]):
            isx = t["ns"] < atlas.SPLIT_OOS.value
            r_main = (t["g"] - 2 * COSTS[M]) / t["rf"]
            ph = phase(t)
            allowed = set()
            for p in set(ph[isx]) - {""}:
                m = isx & (ph == p)
                mu, tt, _ = cl_t(r_main[m], t["ns"][m] // WEEK)
                if m.sum() >= PH_MIN_N and mu > 0 and np.isfinite(tt) and tt >= PH_T:
                    allowed.add(p)
            g_faze = np.isin(ph, list(allowed)) if allowed else np.zeros(len(ph), bool)
            sc = context.score(models[t["dir"]], feats(t))
            g_ctx = sc >= models[t["dir"]]["threshold"]
            gates = {"raw": np.ones(len(ph), bool), "faze": g_faze, "kontext": g_ctx, "mozek": g_faze & g_ctx}
            row["faze_on"] = " | ".join(sorted(allowed))
        else:
            gates = {b: np.zeros(0, bool) for b in BRAINS}
            row["faze_on"] = ""
        for b, gm in gates.items():
            g, rf, ns, xt = t["g"][gm], t["rf"][gm], t["ns"][gm], t["xt"][gm]
            for cname, cost in COSTS.items():
                r = (g - 2 * cost) / rf
                row.update({f"{b}_{cname}_{k}": v for k, v in stats(r, ns, g, cost).items()})
                if cname == M:
                    row[f"{b}_maxdd_r"] = atlas.max_dd(r, xt)
                    row[f"{b}_sum_r"] = float(r.sum())
                    row[f"{b}_per_month"] = len(r) / span_m
                    if b != "raw" and len(t["g"]):          # náhodný mozek: stejný podíl vyřazený náhodně
                        rall = (t["g"] - 2 * cost) / t["rf"]
                        for nm, pm in atlas.split_masks(t["ns"]).items():
                            if nm == "is":
                                continue
                            x, k = rall[pm], int(gm[pm].sum())
                            if k < 2 or k >= len(x):
                                row[f"{b}_drop_{nm}_p95"] = np.nan
                                continue
                            sims = np.array([x[rng.permutation(len(x))[:k]].mean() for _ in range(N_DROP)])
                            row[f"{b}_drop_{nm}_p95"] = float(np.quantile(sims, .95))
        rows.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / f"{tf}.csv.gz", index=False, float_format="%.5f")
    (OUT / f"{tf}.json").write_text(json.dumps({d: {k: v for k, v in m.items() if k != "threshold"} | {"threshold": None if not np.isfinite(m["threshold"]) else m["threshold"]}
                                                for d, m in models.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
    per = {c: f"{z.df.index[0]:%m/%Y}" for c, z in prep.items()}
    (OUT / f"{tf}.meta").write_text(f"{tf}: {len(rows)} kombinací, {time.time() - t0:.0f} s, F&G {'ano' if has_fng else 'ne'}, data od "
                                    + ", ".join(f"{c} {v}" for c, v in per.items()), encoding="utf-8")
    print(f"{tf}: {len(rows)} kombinací za {time.time() - t0:.0f} s", flush=True)


# ---------------------------------------------------------------- report
TF_ORDER = ["15m", "1h", "2h", "4h", "6h", "12h", "1d"]
f2 = atlas.f2


def pc(x):
    return f"{x:.0%}".replace("%", " %") if np.isfinite(x) else "–"


def name(r):
    return (f"{r['tf']} {r['dir']} · zóna ≥ {str(r['gap']).replace('.', ',')} ATR · W {int(r['win'])} · "
            f"{'retest' if r['entry'] == 'retest' else 'hned'} · {r['filter']} · {r['exit']}")


def passes(df, b):
    p = f"{b}_{M}_"
    if b == "raw":
        base = (df[p + "is_n"] >= 150) & (df[p + "oos_n"] >= 50)
        extra = True
    else:
        base = (df[p + "is_n"] >= 100) & (df[p + "oos_n"] >= 30) & (df[p + "hold_n"] >= 20)
        extra = (df[p + "oos_r"] > df[f"{b}_drop_oos_p95"]) & (df[p + "hold_r"] > df[f"{b}_drop_hold_p95"])
    return (base & (df[p + "is_r"] > 0) & (df[p + "oos_r"] > 0) & (df[p + "hold_r"] > 0) & (df[p + "oos_t"] >= 2)
            & (df[p + "oos_r"] > df[f"{M}_rnd_oos_p95"]) & (df[p + "hold_r"] > df[f"{M}_rnd_hold_p95"]) & extra)


def eligible(df, b):
    p = f"{b}_{M}_"
    return (df[p + "is_n"] >= 150) & (df[p + "oos_n"] >= 50) if b == "raw" else \
        (df[p + "is_n"] >= 100) & (df[p + "oos_n"] >= 30) & (df[p + "hold_n"] >= 20)


def report(parts):
    parts = Path(parts)
    res = pd.concat([pd.read_csv(f) for f in sorted(parts.glob("*.csv.gz"))], ignore_index=True)
    metas = [m.read_text(encoding="utf-8") for m in sorted(parts.glob("*.meta"))]
    models = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(parts.glob("*.json"))}
    L = ["# IFVG (inverse fair value gap, ICT) – bez mozku a s mozkem\n",
         f"Přepočet {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. Pravidla stanovená předem jsou v hlavičce "
         "`research/experiments/ifvg_study.py`; po spuštění se nic neladilo. Jen výzkum, nic se nezapíná. "
         "Nejde o finanční poradenství.\n",
         "**Vzor:** FVG = mezera mezi knoty 1. a 3. svíčky. IFVG long = medvědí mezera, kterou cena zavře nahoru "
         "(překlopí se v podporu); short = zrcadlo. Vstup hned po překlopení, nebo až na retestu zóny.\n",
         "**Mozek:** *fáze* = vstup jen ve fázi trhu BTC, kde vzor v minulosti (IS) vydělával (pravidlo Dispečera); "
         "*kontext* = skóre z 14 metrik u signálu (mj. jestli průrazy na trhu pokračují, nebo jsou to fake outy), "
         "vstup jen nad 40. percentilem; *mozek* = obojí. Učení jen z IS (do 12/2023), test na OOS (1/2024–6/2025) "
         "a HOLDOUT (7/2025–dnes).\n"]
    for m in metas:
        L.append(f"- {m}")
    L.append(f"- {len(res)} kombinací. Poplatky MEXC futures 0,05 %/stranu (rozhoduje). R = výsledek po poplatcích / riziko.\n")

    L.append("## 1. Funguje IFVG sám o sobě? (bez mozku)\n")
    L.append("| TF | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | Obě nad p95 náhody | Medián OOS R | Medián HOLDOUT R | Medián obch./měs. |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    p = f"raw_{M}_"
    for tf in TF_ORDER:
        for dname in ("long", "short"):
            g = res[(res.tf == tf) & (res.dir == dname)]
            if not len(g):
                continue
            both = ((g[p + "oos_r"] > g[f"{M}_rnd_oos_p95"]) & (g[p + "hold_r"] > g[f"{M}_rnd_hold_p95"])).mean()
            L.append(f"| {tf} | {dname} | {len(g)} | {pc((g[p + 'oos_r'] > 0).mean())} | {pc((g[p + 'hold_r'] > 0).mean())} | "
                     f"{pc(both)} | {f2(g[p + 'oos_r'].median())} | {f2(g[p + 'hold_r'].median())} | {g.per_month.median():.0f} |")

    L.append("\n## 2. Pomáhá mozek? (stejné kombinace, Ø R v OOS / HOLDOUT)\n")
    L.append("„Lepší v obou“ = podíl kombinací, kde má brána v OOS i HOLDOUTU vyšší Ø R než stejná kombinace bez mozku "
             "(bez výhody ~25 %). „Ponecháno“ = medián podílu obchodů, které mozek pustí (OOS).\n")
    L.append("| TF | Směr | Bez mozku OOS / HOLD | Fáze OOS / HOLD | lepší v obou | Kontext OOS / HOLD | lepší v obou | Mozek OOS / HOLD | lepší v obou | ponecháno |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for tf in TF_ORDER:
        for dname in ("long", "short"):
            g = res[(res.tf == tf) & (res.dir == dname)]
            if not len(g):
                continue
            cells = [f"{f2(g[f'raw_{M}_oos_r'].median())} / {f2(g[f'raw_{M}_hold_r'].median())}"]
            for b in ("faze", "kontext", "mozek"):
                better = ((g[f"{b}_{M}_oos_r"] > g[f"raw_{M}_oos_r"]) & (g[f"{b}_{M}_hold_r"] > g[f"raw_{M}_hold_r"])).mean()
                cells += [f"{f2(g[f'{b}_{M}_oos_r'].median())} / {f2(g[f'{b}_{M}_hold_r'].median())}", pc(better)]
            kept = (g[f"mozek_{M}_oos_n"] / g[f"raw_{M}_oos_n"].replace(0, np.nan)).median()
            L.append(f"| {tf} | {dname} | " + " | ".join(cells) + f" | {pc(kept)} |")

    L.append("\n## 3. Předem stanovený výběr (10 nejlepších podle IS t na směr, pro každou variantu mozku)\n")
    winners = []
    for b in BRAINS:
        q = f"{b}_{M}_"
        el = res[eligible(res, b)].copy()
        if not len(el):
            L.append(f"**{BRAIN_CS[b]}:** žádná kombinace nemá dost obchodů.\n")
            continue
        el["pass"] = passes(el, b)
        picks = el.sort_values(q + "is_t", ascending=False).groupby("dir").head(10)
        L.append(f"**{BRAIN_CS[b]}** – prošlo {int(picks['pass'].sum())} z {len(picks)} "
                 f"(a ze všech {len(el)} způsobilých kombinací by kritéria splnilo {int(el['pass'].sum())}).\n")
        L.append("| Kombinace | IS n / Ø R / t | OOS n / Ø R / t | HOLDOUT n / Ø R | úspěšnost OOS | max. propad R | obch./měs. | Prošlo |")
        L.append("|---|---|---|---|---|---|---|---|")
        for _, r in picks.iterrows():
            L.append(f"| {name(r)} | {int(r[q + 'is_n'])} / {f2(r[q + 'is_r'])} / {f2(r[q + 'is_t'], 1)} | "
                     f"{int(r[q + 'oos_n'])} / {f2(r[q + 'oos_r'])} / {f2(r[q + 'oos_t'], 1)} | {int(r[q + 'hold_n'])} / "
                     f"{f2(r[q + 'hold_r'])} | {pc(r[q + 'oos_win'])} | {r[f'{b}_maxdd_r']:.0f} | {str(round(r[f'{b}_per_month'], 1)).replace('.', ',')} | "
                     f"{'✅' if r['pass'] else '❌'} |")
        L.append("")
        for _, r in picks[picks["pass"]].iterrows():
            winners.append((b, r))

    L.append("## 4. Co se mozek naučil (kontext, IS)\n")
    L.append("Metriky s váhou ≠ 0 (|t| ≥ 2): + = vyšší hodnota pomáhá, − = škodí. Prázdné = kontext nic spolehlivého nenašel.\n")
    for tf in TF_ORDER:
        if tf not in models:
            continue
        bits = []
        for dname, m in models[tf].items():
            w = [f"{'+' if v > 0 else '−'} {context.CS[f]}" for f, v in m["weights"].items() if v]
            bits.append(f"{dname}: {', '.join(w) if w else '—'}")
        L.append(f"- **{tf}** · " + " · ".join(bits))

    L.append("\n## Závěr\n")
    if winners:
        L.append("✅ **Předem stanovené pravidlo splnilo:** " + "; ".join(f"{name(r)} ({BRAIN_CS[b]})" for b, r in winners)
                 + ". Další krok je papírové ověření v laboratoři, ne ostré zapnutí.")
    else:
        L.append("❌ **Předem stanovené pravidlo nesplnila žádná kombinace – bez mozku ani s mozkem.**")
    L.append("\nCelá tabulka: `reports/ifvg/<timeframe>.csv.gz`. Nejde o finanční poradenství.")
    (ROOT / "reports" / "ifvg.md").write_text("\n".join(L), encoding="utf-8")
    print("Report: reports/ifvg.md")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "scanner" / "cache")
    else:
        report(sys.argv[2] if len(sys.argv) > 2 else OUT)
