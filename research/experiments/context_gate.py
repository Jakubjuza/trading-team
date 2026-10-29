"""🧠 Kontextová brána – test, jestli „vnímání trhu“ zlepší obchody laboratoře.

Stanoveno PŘEDEM (29. 10. 2026), po spuštění se nic neladí:

  ČÁST A – brána pro aktivní strategie registru (research/registry.json):
    Obchody: každý signál aktivní strategie na 8 mincích (1H svíčky OKX od 1/2019), se stejným filtrem a režimy
    jako papír, simulovaný SAMOSTATNĚ (vstup na open další svíčky, výstupy strategie, poplatky MEXC 0,05 %/stranu).
    U každého signálu metriky kontextu z research/context.py (trend mince a BTC, trendovost, ADX, chop, poloha
    v rozpětí, follow-through průrazů, uklidnění, zavření svíčky, objem, přetažení, Strach a chamtivost).
    Váhy jen z IS (< 2024-01-01): u metriky porovnám Ø R horní a dolní třetiny (meze třetin z IS); váha = znaménko
    rozdílu, pokud |t| ≥ 2 (t s klastry po týdnech, obchody ze stejného týdne nejsou nezávislé), jinak 0.
    Skóre = Σ váha × standardizovaná metrika (průměr a směrodatná odchylka z IS, ořez ±3).
    Brána: vyřadí signály se skóre pod 40. percentilem IS (zůstane ~60 %).
    PROJDE, když: Ø R ponechaných > Ø R všech v OOS (2024-01 … 2025-06) I v HOLDOUTU (od 2025-07)
                  a rozdíl ponechané − vyřazené má v OOS+HOLDOUT t ≥ 2 (klastry po týdnech).
  ČÁST B – strategie „návrat do rozpětí“ jen v bočním kontextu:
    Rodiny boll_fade, rsi_revert, sweep, stoch (všechny varianty atlasu), TF 1H–12H, výstupy opp / opp_stop / target,
    long i short, bez filtru. Boční kontext = follow-through průrazů I denní trendovost pod mediánem IS.
    PROJDE kombinace: v bočním kontextu IS ≥ 150 a OOS ≥ 50 obchodů, Ø R > 0 v IS, OOS i HOLDOUT, OOS t ≥ 2.
    Pro srovnání se totéž spočítá bez kontextu a v trendovém kontextu (doplněk). Kandidáti jdou jen na papír
    (nejlepší jeden na rodinu × TF × směr, nejvýš 6), s příznakem context = "range".

Výstup: reports/context_gate.md (report), research/context_model.json (váhy, normy, meze, verdikt; čte skener).
S --apply zapíše kandidáty části B do registru (status papír, context range); `apply` je zapíše z uloženého modelu.

    python3 research/experiments/context_gate.py /tmp/cache [--apply]
    python3 research/experiments/context_gate.py apply
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import context, regime, registry  # noqa: E402
from research.experiments import strategy_atlas as atlas  # noqa: E402
from research.experiments.strategy_atlas import njit  # noqa: E402

REPORT = ROOT / "reports" / "context_gate.md"
MODEL = ROOT / "research" / "context_model.json"
M = atlas.MAIN
COST = atlas.COSTS[M]
KEEP_Q = 0.40
CURVE_Q = (0.25, 0.40, 0.50, 0.60, 0.75)
FADE_FAMS = ("boll_fade", "rsi_revert", "sweep", "stoch")
FADE_TFS = ("1h", "2h", "4h", "6h", "12h")
FADE_EXITS = ("opp", "opp_stop", "target")
RECENT_DAYS = 180


@njit(cache=True)
def sim_each(o, h, l, c, atr, entries, opp, d, sa, ta, ga, uo, mh):
    m = len(entries)
    g = np.full(m, np.nan)
    rf = np.full(m, np.nan)
    for j in range(m):
        ii, xx, gg, rr = atlas.simulate(o, h, l, c, atr, entries[j:j + 1], opp, d, sa, ta, ga, uo, mh)
        if len(ii):
            g[j] = gg[0]
            rf[j] = rr[0]
    return g, rf


def period(t):
    t = pd.DatetimeIndex(t)
    return np.where(t < atlas.SPLIT_OOS, "is", np.where(t < atlas.SPLIT_HOLD, "oos", "hold"))


def cl_t(r, wk):
    """Průměr a t-statistika s klastry po týdnech."""
    r = np.asarray(r, float)
    n = len(r)
    if n < 3:
        return (r.mean() if n else np.nan), np.nan, 0.0
    m = r.mean()
    s = pd.Series(r - m).groupby(np.asarray(wk)).sum().to_numpy()
    var = (s ** 2).sum() / n ** 2
    return m, (m / np.sqrt(var) if var > 0 else np.nan), var


def diff_t(a, wa, b, wb):
    ma, _, va = cl_t(a, wa)
    mb, _, vb = cl_t(b, wb)
    v = va + vb
    return ma - mb, ((ma - mb) / np.sqrt(v) if v > 0 else np.nan)


# ---------------------------------------------------------------- data
def load(cache):
    try:
        from research.lab import fng_series
        fng = fng_series()
    except Exception as exc:
        print(f"Strach a chamtivost nedostupné: {exc.__class__.__name__}", flush=True)
        fng = None
    h1 = {coin: atlas.fetch(coin, "1h", "2019-01-01", cache) for coin in atlas.COINS}
    daily = {coin: atlas.resample(b, "1d") for coin, b in h1.items()}
    dctx = {coin: context.daily_frame(daily[coin], daily["BTC"], fng) for coin in atlas.COINS}
    regs = {coin: regime.regime_series(daily[coin]) for coin in atlas.COINS}
    return h1, daily, dctx, regs, fng


def frames(tf, h1, dctx, regs):
    out = {}
    for coin, b in h1.items():
        df = atlas.resample(b, tf)
        z = atlas.Ind(df)
        bull, up = atlas.daily_regimes(b)
        day = df.index.floor("1D")
        z.flt = {"d200": bull.reindex(day).to_numpy(float), "d50": up.reindex(day).to_numpy(float)}
        z.reg = regs[coin].reindex(day).to_numpy(dtype=object)
        z.ctx = context.TfContext(df, dctx[coin])
        out[coin] = z
    return out


def trades_for(z, fam, params, d, exit_, flt="none", regimes=None):
    ent, opp = atlas.family_signals(z, fam, params, d)
    ent = np.asarray(ent, np.int64)
    if flt != "none":
        ent = ent[z.flt[flt][ent] == (1.0 if d > 0 else 0.0)]
    if regimes:
        ent = ent[np.isin(z.reg[ent].astype(str), list(regimes))]
    ent = ent[ent + 1 < len(z.c)]
    if not len(ent):
        return None
    sa, ta, ga, uo, mh = atlas.EXITS[exit_]
    g, rf = sim_each(z.o, z.h, z.l, z.c, z.atr, ent, np.asarray(opp, bool), d, sa, ta, ga, uo, mh)
    ok = np.isfinite(g) & (rf > 0)
    ent, g, rf = ent[ok], g[ok], rf[ok]
    t = z.df.index[ent]
    out = pd.DataFrame({"t": t, "r": (g - 2 * COST) / rf})
    for k, v in z.ctx.at(ent, d).items():
        out[k] = v
    return out


# ---------------------------------------------------------------- část A
def part_a(h1, dctx, regs):
    reg = registry.load()
    strats = [s for s in registry.active(reg) if s.get("context") != "range"]
    rows = []
    cache_f = {}
    for s in strats:
        tf = s["tf"]
        if tf not in cache_f:
            t0 = time.time()
            cache_f[tf] = frames(tf, h1, dctx, regs)
            print(f"rámce {tf}: {time.time() - t0:.0f} s", flush=True)
        d = 1 if s["dir"] == "long" else -1
        p = tuple(context_typed(x) for x in s["params"].split("/"))
        for coin, z in cache_f[tf].items():
            tr = trades_for(z, s["family"], p, d, s["exit"], s["filter"], s.get("regimes"))
            if tr is None:
                continue
            tr["sid"], tr["coin"], tr["tf"] = s["id"], coin, tf
            rows.append(tr)
        print(f"A: {s['label']} hotovo", flush=True)
    df = pd.concat(rows, ignore_index=True)
    df["per"] = period(df["t"])
    df["wk"] = pd.DatetimeIndex(df["t"]).tz_localize(None).to_period("W").astype(str)
    return df, strats, cache_f


def context_typed(x):
    for f in (int, float):
        try:
            return f(x)
        except ValueError:
            pass
    return x


def fit(df):
    is_ = df[df.per == "is"]
    weights, norm, terc, tstat = {}, {}, {}, {}
    for f in context.FEATURES:
        x = is_[f].to_numpy(float)
        fin = np.isfinite(x)
        if fin.sum() < 300:
            weights[f], norm[f], terc[f], tstat[f] = 0, (0.0, 1.0), (np.nan, np.nan), np.nan
            continue
        q1, q2 = np.nanquantile(x, [1 / 3, 2 / 3])
        lo, hi = is_[fin & (x <= q1)], is_[fin & (x >= q2)]
        dif, t = diff_t(hi.r, hi.wk, lo.r, lo.wk)
        mu, sd = float(np.nanmean(x)), float(np.nanstd(x))
        norm[f] = (mu, sd if sd > 0 else 1.0)
        terc[f] = (float(q1), float(q2))
        tstat[f] = float(t) if np.isfinite(t) else np.nan
        weights[f] = int(np.sign(dif)) if np.isfinite(t) and abs(t) >= 2 else 0
    return {"weights": weights, "norm": norm}, terc, tstat


def stats(r):
    r = np.asarray(r, float)
    if not len(r):
        return {"n": 0, "mean": np.nan, "sum": 0.0, "win": np.nan}
    return {"n": len(r), "mean": r.mean(), "sum": r.sum(), "win": (r > 0).mean()}


# ---------------------------------------------------------------- část B
def part_b(h1, dctx, regs, cache_f, range_cut):
    rows = []
    for tf in FADE_TFS:
        fr = cache_f.get(tf) or frames(tf, h1, dctx, regs)
        cache_f[tf] = fr
        for fam, p in [v for v in atlas.variants() if v[0] in FADE_FAMS]:
            for ex in FADE_EXITS:
                for dname, d in (("long", 1), ("short", -1)):
                    parts = []
                    for coin, z in fr.items():
                        tr = trades_for(z, fam, p, d, ex)
                        if tr is not None:
                            parts.append(tr)
                    if not parts:
                        continue
                    tr = pd.concat(parts, ignore_index=True)
                    tr["per"] = period(tr["t"])
                    tr["wk"] = pd.DatetimeIndex(tr["t"]).tz_localize(None).to_period("W").astype(str)
                    rng = (tr.ft_tf < range_cut["ft_tf_max"]) & (tr.er_d < range_cut["er_d_max"])
                    rec = {"family": fam, "params": "/".join(str(x) for x in p), "tf": tf, "filter": "none", "exit": ex,
                           "dir": dname}
                    for ctx_name, mask in (("all", np.ones(len(tr), bool)), ("range", rng.to_numpy()),
                                           ("trend", ~rng.to_numpy())):
                        sub = tr[mask]
                        for per in ("is", "oos", "hold"):
                            x = sub[sub.per == per]
                            m, t, _ = cl_t(x.r, x.wk)
                            rec[f"{ctx_name}_{per}_n"] = len(x)
                            rec[f"{ctx_name}_{per}_r"] = m
                            rec[f"{ctx_name}_{per}_t"] = t
                    rows.append(rec)
        print(f"B: {tf} hotovo", flush=True)
    return pd.DataFrame(rows)


def passes(b, ctx_name):
    return ((b[f"{ctx_name}_is_n"] >= 150) & (b[f"{ctx_name}_oos_n"] >= 50) & (b[f"{ctx_name}_is_r"] > 0)
            & (b[f"{ctx_name}_oos_r"] > 0) & (b[f"{ctx_name}_hold_r"] > 0) & (b[f"{ctx_name}_oos_t"] >= 2))


# ---------------------------------------------------------------- report
def fmt(x, d=3):
    return "–" if x is None or not np.isfinite(x) else f"{x:+.{d}f}".replace(".", ",")


def run(cache, apply=False):
    t0 = time.time()
    h1, daily, dctx, regs, fng = load(cache)
    print(f"data: {time.time() - t0:.0f} s", flush=True)
    df, strats, cache_f = part_a(h1, dctx, regs)
    model, terc, tstat = fit(df)
    df["score"] = context.score(model, {f: df[f].to_numpy(float) for f in context.FEATURES})
    is_scores = df.loc[df.per == "is", "score"].to_numpy()
    cuts = {q: float(np.quantile(is_scores, q)) for q in CURVE_Q}
    thr = cuts[KEEP_Q]
    df["keep"] = df.score >= thr
    last = df.t.max()
    df.loc[df.t >= last - pd.Timedelta(days=RECENT_DAYS), "recent"] = True
    df["recent"] = df["recent"].fillna(False).astype(bool)

    oh = df[df.per.isin(["oos", "hold"])]
    dif, dt = diff_t(oh[oh.keep].r, oh[oh.keep].wk, oh[~oh.keep].r, oh[~oh.keep].wk)
    per_ok = {}
    for per in ("oos", "hold"):
        x = df[df.per == per]
        per_ok[per] = bool(x[x.keep].r.mean() > x.r.mean())
    gate_pass = bool(per_ok["oos"] and per_ok["hold"] and np.isfinite(dt) and dt >= 2)

    # meze bočního kontextu (medián IS přes signály části A – stanoveno předem)
    is_ = df[df.per == "is"]
    range_cut = {"ft_tf_max": float(np.nanmedian(is_.ft_tf)), "er_d_max": float(np.nanmedian(is_.er_d))}
    df["range"] = (df.ft_tf < range_cut["ft_tf_max"]) & (df.er_d < range_cut["er_d_max"])

    b = part_b(h1, dctx, regs, cache_f, range_cut)
    cnt = {c: int(passes(b, c).sum()) for c in ("all", "range", "trend")}
    cand = b[passes(b, "range")].copy()
    if len(cand):
        cand["score"] = np.minimum(cand.range_oos_t, cand.range_hold_t.fillna(0))
        cand = cand.sort_values("score", ascending=False).groupby(["family", "tf", "dir"], sort=False).head(1).head(6)

    model.update({
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "threshold": thr, "keep_q": KEEP_Q, "range": range_cut,
        "gate": {"pass": gate_pass, "oos_better": per_ok["oos"], "hold_better": per_ok["hold"],
                 "diff_r": float(dif) if np.isfinite(dif) else None, "diff_t": float(dt) if np.isfinite(dt) else None},
        "range_candidates": [] if not len(cand) else
        [{k: (v.item() if hasattr(v, "item") else v) for k, v in r.items()} for r in
         cand[["family", "params", "tf", "filter", "exit", "dir", "range_is_r", "range_oos_r", "range_hold_r",
               "range_oos_t", "range_hold_t", "range_is_n", "range_oos_n", "range_hold_n"]].to_dict("records")],
    })
    MODEL.write_text(json.dumps(model, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")

    # ------------------------------------------------ text
    L = ["# 🧠 Kontextová brána – výsledky testu", "",
         f"Spuštěno {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · {len(strats)} aktivních strategií × 8 mincí · "
         f"{len(df)} signálů · F&G {'ano' if fng is not None else 'NEDOSTUPNÉ'} · {time.time() - t0:.0f} s.",
         "Pravidla stanovena předem (hlavička research/experiments/context_gate.py). IS < 2024-01-01 ≤ OOS < 2025-07-01 ≤ HOLDOUT.",
         "", f"## A) Brána pro současné strategie: **{'PROŠLA ✅' if gate_pass else 'NEPROŠLA ❌'}**", "",
         f"Rozdíl ponechané − vyřazené v OOS+HOLDOUT: {fmt(dif)} R, t {fmt(dt, 2)} (klastry po týdnech). "
         f"Ø R ponechaných lepší než všech: OOS {'ano' if per_ok['oos'] else 'ne'}, HOLDOUT {'ano' if per_ok['hold'] else 'ne'}.", "",
         "| období | všechny: n | Ø R | Σ R | výhry | brána: n | Ø R | Σ R | výhry | vyřazené Ø R |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for name, mask in (("IS", df.per == "is"), ("OOS", df.per == "oos"), ("HOLDOUT", df.per == "hold"),
                       (f"posl. {RECENT_DAYS} dní", df.recent)):
        x = df[mask]
        a, k, rm = stats(x.r), stats(x[x.keep].r), stats(x[~x.keep].r)
        L.append(f"| {name} | {a['n']} | {fmt(a['mean'])} | {fmt(a['sum'], 0)} | {a['win']:.0%} | {k['n']} | {fmt(k['mean'])} | "
                 f"{fmt(k['sum'], 0)} | {k['win']:.0%} | {fmt(rm['mean'])} |")
    L += ["", "Křivka (OOS+HOLDOUT): kolik vyřadit → Ø R ponechaných", "", "| vyřadit spodních | ponecháno | Ø R | Σ R |", "|---|---|---|---|"]
    for q, c in cuts.items():
        x = oh[oh.score >= c]
        s = stats(x.r)
        L.append(f"| {q:.0%} | {s['n']} | {fmt(s['mean'])} | {fmt(s['sum'], 0)} |")
    L += ["", "### Co kontext říká (IS třetiny → Ø R v OOS+HOLDOUT)", "",
          "| metrika | váha | t (IS) | dolní třetina | střed | horní třetina |", "|---|---|---|---|---|---|"]
    for f in context.FEATURES:
        q1, q2 = terc[f]
        if not np.isfinite(q1):
            L.append(f"| {context.CS[f]} | 0 | – | – | – | – |")
            continue
        x = oh[f]
        lo, mid, hi = oh[x <= q1].r.mean(), oh[(x > q1) & (x < q2)].r.mean(), oh[x >= q2].r.mean()
        L.append(f"| {context.CS[f]} | {model['weights'][f]:+d} | {fmt(tstat[f], 1)} | {fmt(lo)} | {fmt(mid)} | {fmt(hi)} |")
    L += ["", "### Trendový vs. boční kontext (současné strategie, Ø R)", "",
          "| období | trendový: n | Ø R | boční: n | Ø R |", "|---|---|---|---|---|"]
    for name, mask in (("IS", df.per == "is"), ("OOS", df.per == "oos"), ("HOLDOUT", df.per == "hold"),
                       (f"posl. {RECENT_DAYS} dní", df.recent)):
        x = df[mask]
        tr_, rg_ = stats(x[~x.range].r), stats(x[x.range].r)
        L.append(f"| {name} | {tr_['n']} | {fmt(tr_['mean'])} | {rg_['n']} | {fmt(rg_['mean'])} |")
    L += ["", "### Po strategiích (OOS+HOLDOUT)", "", "| strategie | n | Ø R všech | Ø R s bránou | podíl ponechaných |", "|---|---|---|---|---|"]
    lab = {s["id"]: s["label"] for s in strats}
    better = 0
    for sid_, x in oh.groupby("sid"):
        a, k = x.r.mean(), x[x.keep].r.mean()
        better += int(k > a)
        L.append(f"| {lab.get(sid_, sid_)} | {len(x)} | {fmt(a)} | {fmt(k)} | {x.keep.mean():.0%} |")
    L.append(f"\nBrána zlepšila Ø R u {better} z {oh.sid.nunique()} strategií.")
    L += ["", f"## B) Návrat do rozpětí jen v bočním kontextu", "",
          f"Boční kontext = pokračování průrazů < {range_cut['ft_tf_max']:.2f} a denní trendovost < {range_cut['er_d_max']:.2f} (mediány IS).",
          f"Prošlo pravidlem: bez kontextu {cnt['all']}, v bočním kontextu **{cnt['range']}**, v trendovém {cnt['trend']} "
          f"(z {len(b)} kombinací).", ""]
    if len(cand):
        L += ["| kandidát | IS Ø R | OOS Ø R (t) | HOLDOUT Ø R (t) | n IS/OOS/HOLD |", "|---|---|---|---|---|"]
        for _, r in cand.iterrows():
            L.append(f"| {registry.label(r)} | {fmt(r.range_is_r)} | {fmt(r.range_oos_r)} ({fmt(r.range_oos_t, 1)}) | "
                     f"{fmt(r.range_hold_r)} ({fmt(r.range_hold_t, 1)}) | {r.range_is_n}/{r.range_oos_n}/{r.range_hold_n} |")
    else:
        L.append("Žádná kombinace neprošla – návrat do rozpětí se nepřidává.")
    L += ["", "Poznámky: každý signál simulovaný samostatně (bez pravidla „jedna pozice naráz“); funding futures není "
          "započten; mnoho testovaných kombinací v části B znamená, že část průchodů může být náhoda – proto jen papír.",
          "Papírově, nejde o finanční poradenství."]
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))

    if apply and len(cand):
        _apply(cand)
    return model


def _apply(cand):
    """Kandidáti části B → registr (status papír, context range)."""
    reg = registry.load()
    known = {s["id"] for s in reg["strategies"]}
    today = datetime.now(timezone.utc).date().isoformat()
    for _, r in cand.iterrows():
        key = registry.sid(r)
        if key in known:
            s = registry.find(reg, key)
            s["context"] = "range"
            continue
        reg["strategies"].append({
            "id": key, "label": registry.label(r) + " · boční", "family": r.family, "params": r.params, "tf": r.tf,
            "filter": "none", "exit": r.exit, "dir": r.dir, "added": today, "source": f"context_gate {today}",
            "context": "range", "regimes": [],
            "backtest": {"is_r": round(float(r.range_is_r), 3), "oos_r": round(float(r.range_oos_r), 3),
                         "hold_r": round(float(r.range_hold_r), 3), "oos_t": round(float(r.range_oos_t), 3),
                         "hold_t": round(float(r.range_hold_t), 3) if np.isfinite(r.range_hold_t) else None,
                         "is_n": int(r.range_is_n), "oos_n": int(r.range_oos_n), "hold_n": int(r.range_hold_n)},
            "status": "papír",
            "history": [{"date": today, "status": "papír",
                         "reason": f"context_gate: jen boční kontext, OOS {r.range_oos_r:+.2f} R (t {r.range_oos_t:+.1f})"}]})
    registry.save(reg)


def apply_from_model(path=MODEL):
    """Zapíše kandidáty části B z uloženého modelu do registru (bez nového výpočtu) – použije se na větvi main."""
    model = json.loads(Path(path).read_text(encoding="utf-8"))
    cand = pd.DataFrame(model.get("range_candidates") or [])
    if not len(cand):
        print("žádní kandidáti")
        return 0
    _apply(cand)
    return len(cand)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        print(f"zapsáno {apply_from_model()} kandidátů")
    else:
        run(Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("/tmp/cache"),
            apply="--apply" in sys.argv)
