#!/usr/bin/env python3
"""🤖 AI Lab – strategie, které vymyslel sám Claude (AI), a evoluce pravidel. Jen papír, oddělené od desku.

Zadání uživatele (8. 11. 2026): „totálně AI generated“ strategie nebo způsob obchodování, klidně hodně rychlý,
s co největší ziskovostí, a vlastní část Agentownu pro průzkum čistě AI tradingu. Stejně jako Downtown NIKDY nesahá
na skener, registr, riziko, demo ani peníze; pravidla se po spuštění neladí.

Stanoveno PŘEDEM (8. 11. 2026), před prvním spuštěním na datech:

  Data: OKX spot, 8 mincí (BTC ETH SOL XRP ADA LINK AVAX DOGE), hodinové svíčky od 1/2019 (cache laboratoře).
    Rychlejší obchodování (sekundy, order book) bez historie order booku poctivě otestovat nejde – nejrychlejší
    je tu 1 hodina. Poplatky 0,05 % na stranu (MEXC futures taker + skluz, jako atlas).
  Dělení: učení (IS) < 1. 1. 2024 ≤ ověření (OOS) < 1. 7. 2025 ≤ závěrečný test (HOLDOUT).
  Účty na stránce: 1 000 USDT od 1. 1. 2024 (jen data, která se k vymýšlení ani učení nepoužila), živý papír od
    LIVE_START. Strategie se stopem: riziko 1 % účtu na obchod (jako ostatní účty Agentownu); alokační strategie:
    kapitál rozdělený podle pravidla, bez páky.

  Vlastní nápady (pevné parametry, nic se nehledalo):
    A1 Ozvěna BTC (lead-lag, 1H) – když BTC za hodinu udělá pohyb ≥ 2 své směrodatné odchylky (posledních 168 h)
       a altcoin se pohnul méně než o polovinu, vstup do altcoinu ve směru BTC na další svíčce; stop 1,5 ATR,
       nejvýš 4 h. Myšlenka: altcoiny dobíhají BTC se zpožděním.
    A2 Tichý průraz (1H) – trh je stažený (ATR14 / ATR200 < 0,65 na předchozí svíčce) a zavře nad maximem 48 h →
       long, pokud je denní trend mince nahoru (nad denní EMA200); zrcadlově short pod minimem 48 h
       v denním trendu dolů. Stop 2 ATR, posuvný stop 2,5 ATR, nejvýš 72 h.
    A3 Hodiny trhu (1H, učí se) – pro každou minci a hodinu dne (UTC) průměrný hodinový výnos v IS; long jen
       v hodinách s t ≥ 2. Každá mince má 1/8 kapitálu.
    A4 Rotace síly (4H, tržně neutrální) – každé 4 h seřadí mince podle výnosu 72 h děleného volatilitou 72 h;
       long 2 nejsilnější, short 2 nejslabší, každá 25 % kapitálu, náklady z obratu.
  Evoluce (AI hledá pravidla sama): genom = 1–3 podmínky nad 13 znaky (výnosy 1/4/24 h normované volatilitou,
    pohyb BTC 1/24 h, vzdálenost od EMA50/200 v ATR, RSI14, objem, stažení ATR14/ATR200, poloha v rozpětí 24 h,
    hodina, den v týdnu; prahy = decily IS), směr, držení {2,4,8,16,32} h, stop {1; 1,5; 2; 3} ATR.
    Fitness JEN z IS: t-statistika Ø R × min(1, n/400) − 0,1 × počet podmínek, nejméně 300 obchodů.
    Populace 200, 30 generací, turnaj 3, křížení a mutace, náhoda se semínkem 20261108. Po evoluci 30 nejlepších
    různých genomů podle IS → ověření OOS. Vítěz = nejvyšší OOS t mezi těmi s Ø R > 0 v IS i OOS a OOS t ≥ 2;
    HOLDOUT se jen ukáže. Kontrola: 30 náhodných genomů stejné stavby – kolik z nich projde OOS stejně.
    Vítězný genom se uloží (research/ai_lab_genome.json) a dál se neladí.
  Opravy chyb po prvním běhu (8. 11., nejde o ladění parametrů): obchody se stopem blíž než 0,1 % od vstupu se
    vyřazují (svíčky s nulovým rozpětím dávaly R ~1e64); Hodiny trhu používaly při obchodování posunutý klíč hodiny
    a účtovaly poplatek každou hodinu místo jen při vstupu a výstupu. Evoluce se znovu nespouštěla.
  PROJDE (strategie se stopem): Ø R > 0 v IS, OOS i HOLDOUT a OOS t ≥ 2. Alokační: Sharpe > 0 ve všech třech
    obdobích a OOS Sharpe ≥ 1. Neprošlé zůstávají na stránce jako pokus, s jasným štítkem.

    python3 research/ai_lab.py /tmp/cache            → research/ai_lab.json + reports/ai_lab.md
    python3 research/ai_lab.py /tmp/cache --evolve   → znovu evoluce (jen když chybí uložený genom)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "research" / "ai_lab.json"
OUT_MD = ROOT / "reports" / "ai_lab.md"
GENOME = ROOT / "research" / "ai_lab_genome.json"
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
IS_END, OOS_END = pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")
ACC_START = "2024-01-01"
LIVE_START = "2026-11-09"
COST = 0.0005
MIN_RISK = 0.001        # stop aspoň 0,1 % od vstupu, jinak je obchod chyba dat (nulové rozpětí svíček)
SEED, POP, GENS, TOURN, TOP_K = 20261108, 200, 30, 3, 30
HOLDS, STOPS = [2, 4, 8, 16, 32], [1.0, 1.5, 2.0, 3.0]
QS = [.1, .2, .3, .4, .5, .6, .7, .8, .9]
FEATS = ["r1z", "r4z", "r24z", "btc1z", "btc24z", "ema50", "ema200", "rsi14", "volz", "comp", "pos24", "hour", "dow"]
FEAT_CS = {"r1z": "výnos 1 h (σ)", "r4z": "výnos 4 h (σ)", "r24z": "výnos 24 h (σ)", "btc1z": "BTC 1 h (σ)",
           "btc24z": "BTC 24 h (σ)", "ema50": "od EMA50 (ATR)", "ema200": "od EMA200 (ATR)", "rsi14": "RSI 14",
           "volz": "objem vs. průměr", "comp": "stažení ATR14/200", "pos24": "poloha v rozpětí 24 h",
           "hour": "hodina UTC", "dow": "den v týdnu"}


# ---------------------------------------------------------------- data a znaky
def load(cache):
    from research import city_accounts as ca
    from research.experiments import strategy_atlas as atlas
    ca.patch_fetch()
    out = {}
    for c in COINS:
        b = atlas.fetch(c, "1h", "2019-01-01", Path(cache))
        df = atlas.resample(b, "1h")
        z = atlas.Ind(df)
        bull, _ = atlas.daily_regimes(b)
        z.d200 = bull.reindex(df.index.floor("1D")).to_numpy(float)
        out[c] = z
    return out


def features(frames):
    """Kauzální znaky na zavření svíčky i (vstup až na otevření i+1)."""
    btc = frames["BTC"].df["Close"]
    bret = np.log(btc).diff()
    bsd = bret.rolling(168, min_periods=100).std()
    F = {}
    for c, z in frames.items():
        d = z.df
        cl = d["Close"]
        r = np.log(cl).diff()
        sd = r.rolling(168, min_periods=100).std()
        tr = pd.concat([d["High"] - d["Low"], (d["High"] - cl.shift()).abs(), (d["Low"] - cl.shift()).abs()], axis=1).max(axis=1)
        atr200 = tr.ewm(alpha=1 / 200, adjust=False, min_periods=200).mean()
        atr = pd.Series(z.atr, index=d.index)
        b1 = bret.reindex(d.index)
        bs = bsd.reindex(d.index)
        hi24, lo24 = d["High"].rolling(24).max(), d["Low"].rolling(24).min()
        f = pd.DataFrame({
            "r1z": r / sd, "r4z": np.log(cl).diff(4) / (sd * 2), "r24z": np.log(cl).diff(24) / (sd * np.sqrt(24)),
            "btc1z": b1 / bs, "btc24z": np.log(btc).diff(24).reindex(d.index) / (bs * np.sqrt(24)),
            "ema50": (cl - cl.ewm(span=50, adjust=False).mean()) / atr, "ema200": (cl - cl.ewm(span=200, adjust=False).mean()) / atr,
            "rsi14": pd.Series(z.rsi(14), index=d.index),
            "volz": np.log(d["Volume"].replace(0, np.nan) / d["Volume"].rolling(48).mean().shift(1)),
            "comp": atr / atr200, "pos24": (cl - lo24) / (hi24 - lo24).replace(0, np.nan),
            "hour": d.index.hour.astype(float), "dow": d.index.dayofweek.astype(float)}, index=d.index)
        f["ret"] = r
        f["btc_ret"] = b1
        F[c] = f.replace([np.inf, -np.inf], np.nan)
    return F


def trades_from(z, ent_mask, d, stop, trail, hold):
    from research.experiments import strategy_atlas as atlas
    ent = np.flatnonzero(np.nan_to_num(ent_mask, nan=0).astype(bool)).astype(np.int64)
    if not len(ent):
        return np.empty(0, np.int64), np.empty(0, np.int64), np.empty(0)
    ii, xx, gg, rf = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, ent, np.zeros(len(z.c), bool), d, stop, trail, 0.0, False, hold)
    ok = rf >= MIN_RISK                       # oprava dat (8. 11.): svíčky s nulovým rozpětím dávaly stop ~0 a R ~1e64
    return ii[ok], xx[ok], (gg[ok] - 2 * COST) / rf[ok]


def to_list(z, coin, d, ii, xx, rr):
    idx, last = z.df.index, len(z.df.index) - 1
    return [{"entry": idx[i], "exit": idx[x], "coin": coin, "dir": int(d), "r": float(r)}
            for i, x, r in zip(ii, xx, rr) if x < last]          # obchod, který ještě běží, se nepočítá


# ---------------------------------------------------------------- vlastní nápady
def a1_echo(frames, F):
    out = []
    for c, z in frames.items():
        if c == "BTC":
            continue
        f = F[c]
        bz, br, ar = f["btc1z"].to_numpy(), f["btc_ret"].to_numpy(), f["ret"].to_numpy()
        for d in (1, -1):
            m = (d * bz >= 2) & (d * ar < 0.5 * d * br)
            out += to_list(z, c, d, *trades_from(z, m, d, 1.5, 0.0, 4))
    return out


def a2_quiet(frames, F):
    out = []
    for c, z in frames.items():
        comp = F[c]["comp"].shift(1).to_numpy()
        cl = z.c
        for d in (1, -1):
            brk = cl > z.hi(48) if d > 0 else cl < z.lo(48)
            trend = z.d200 == (1.0 if d > 0 else 0.0)
            m = (comp < 0.65) & brk & trend
            out += to_list(z, c, d, *trades_from(z, m, d, 2.0, 2.5, 72))
    return out


def a3_hours(frames, F):
    """Vrátí denní výnosy portfolia a naučené hodiny (jen z IS)."""
    learned, parts = {}, []
    for c in frames:
        f = F[c]
        nxt = f["ret"].shift(-1)                                   # výnos svíčky, která začíná po zavření i
        isr = nxt[f.index < IS_END]
        g = isr.groupby(f.index[f.index < IS_END].hour)
        st = g.agg(["mean", "std", "count"])
        t = st["mean"] / (st["std"] / np.sqrt(st["count"]))
        hrs = sorted(int(h) for h in t[t >= 2].index)
        learned[c] = hrs
        on = np.isin(f.index.hour, hrs).astype(float)             # oprava (8. 11.): stejný klíč hodiny jako při učení
        chg = np.abs(np.diff(np.r_[0.0, on]))                      # poplatek jen při vstupu a výstupu, držení přes víc hodin nic nestojí
        r = (on * (np.exp(nxt.fillna(0)) - 1) - chg * COST) / len(frames)
        parts.append(pd.Series(r, index=f.index + pd.Timedelta("1h")))
    tot = pd.concat(parts, axis=1).fillna(0).sum(axis=1)
    return tot, learned


def a4_rotation(frames, F):
    cl = pd.DataFrame({c: z.df["Close"] for c, z in frames.items()}).dropna(how="all")
    c4 = cl.resample("4h").last()
    lr = np.log(c4)
    score = lr.diff(18) / lr.diff().rolling(18).std()                 # 72 h
    fwd = c4.pct_change().shift(-1)
    rows, prev = [], pd.Series(0.0, index=c4.columns)
    for t in c4.index:
        s = score.loc[t].dropna()
        w = pd.Series(0.0, index=c4.columns)
        if len(s) >= 6:
            o = s.sort_values()
            w[o.index[-2:]] = 0.25
            w[o.index[:2]] = -0.25
        cost = (w - prev).abs().sum() * COST
        r = float((w * fwd.loc[t].fillna(0)).sum()) - cost
        rows.append((t + pd.Timedelta("4h"), r))
        prev = w
    return pd.Series(dict(rows)).sort_index().iloc[:-1]


# ---------------------------------------------------------------- evoluce
def gene_mask(F, coin, g, thr):
    f = F[coin]
    m = np.ones(len(f), bool)
    for fi, op, q in g["conds"]:
        x = f[fi].to_numpy()
        th = thr[fi][q]
        m &= (x > th) if op == ">" else (x < th)
    return m


def run_genome(frames, F, g, thr):
    out = []
    for c, z in frames.items():
        out += to_list(z, c, g["dir"], *trades_from(z, gene_mask(F, c, g, thr), g["dir"], g["stop"], 0.0, g["hold"]))
    return out


def split_stats(tr):
    res = {}
    for k, lo, hi in (("is", None, IS_END), ("oos", IS_END, OOS_END), ("hold", OOS_END, None)):
        r = np.array([t["r"] for t in tr if (lo is None or t["entry"] >= lo) and (hi is None or t["entry"] < hi)])
        n = len(r)
        res[k] = {"n": n, "mean_r": round(float(r.mean()), 3) if n else None,
                  "t": round(float(r.mean() / (r.std(ddof=1) / np.sqrt(n))), 2) if n > 2 and r.std(ddof=1) > 0 else None}
    return res


def ret_split(r):
    out = {}
    for k, lo, hi in (("is", None, IS_END), ("oos", IS_END, OOS_END), ("hold", OOS_END, None)):
        x = r[(r.index >= lo if lo is not None else True) & (r.index < hi if hi is not None else True)]
        d = x.resample("1D").apply(lambda s: float(np.prod(1 + s) - 1)) if len(x) else x
        sd = d.std()
        out[k] = {"days": int(len(d)), "sharpe": round(float(d.mean() / sd * np.sqrt(365)), 2) if len(d) > 2 and sd > 0 else None,
                  "ret_pct": round(float((np.prod(1 + d) - 1) * 100), 1) if len(d) else None}
    return out


def fitness(tr):
    r = np.array([t["r"] for t in tr if t["entry"] < IS_END])
    if len(r) < 300 or r.std(ddof=1) == 0:
        return -99.0
    return float(r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) * min(1.0, len(r) / 400))


def rand_gene(rng):
    k = int(rng.integers(1, 4))
    return {"conds": [(FEATS[rng.integers(len(FEATS))], ">" if rng.random() < .5 else "<", float(QS[rng.integers(len(QS))])) for _ in range(k)],
            "dir": 1 if rng.random() < .5 else -1, "hold": int(HOLDS[rng.integers(len(HOLDS))]),
            "stop": float(STOPS[rng.integers(len(STOPS))])}


def mutate(g, rng):
    g = json.loads(json.dumps(g))
    g["conds"] = [tuple(c) for c in g["conds"]]
    x = rng.random()
    if x < .35 and g["conds"]:
        i = rng.integers(len(g["conds"]))
        fi, op, q = g["conds"][i]
        g["conds"][i] = (fi, op, float(QS[rng.integers(len(QS))]))
    elif x < .5 and g["conds"]:
        i = rng.integers(len(g["conds"]))
        g["conds"][i] = (FEATS[rng.integers(len(FEATS))], g["conds"][i][1], g["conds"][i][2])
    elif x < .6 and g["conds"]:
        i = rng.integers(len(g["conds"]))
        fi, op, q = g["conds"][i]
        g["conds"][i] = (fi, "<" if op == ">" else ">", q)
    elif x < .7 and len(g["conds"]) < 3:
        g["conds"].append(rand_gene(rng)["conds"][0])
    elif x < .78 and len(g["conds"]) > 1:
        g["conds"].pop(int(rng.integers(len(g["conds"]))))
    elif x < .88:
        g["hold"] = int(HOLDS[rng.integers(len(HOLDS))])
    elif x < .96:
        g["stop"] = float(STOPS[rng.integers(len(STOPS))])
    else:
        g["dir"] = -g["dir"]
    return g


def cross(a, b, rng):
    pool = list(a["conds"]) + list(b["conds"])
    k = int(rng.integers(1, min(3, len(pool)) + 1))
    idx = rng.choice(len(pool), size=k, replace=False)
    src = a if rng.random() < .5 else b
    return {"conds": [tuple(pool[i]) for i in idx], "dir": src["dir"], "hold": src["hold"], "stop": src["stop"]}


def key(g):
    return json.dumps([sorted([list(c) for c in g["conds"]]), g["dir"], g["hold"], g["stop"]])


def evolve(frames, F):
    pooled = pd.concat([F[c][F[c].index < IS_END] for c in frames])
    thr = {fi: {q: float(pooled[fi].quantile(q)) for q in QS} for fi in FEATS}
    rng = np.random.default_rng(SEED)
    cache = {}

    def fit(g):
        k = key(g)
        if k not in cache:
            fv = fitness(run_genome(frames, F, g, thr)) - 0.1 * len(g["conds"])
            cache[k] = (fv, g)
        return cache[k][0]

    pop = [rand_gene(rng) for _ in range(POP)]
    for gen in range(GENS):
        scores = [fit(g) for g in pop]
        nxt = [pop[int(np.argmax(scores))]]                                   # elita
        while len(nxt) < POP:
            def pick():
                ids = rng.integers(len(pop), size=TOURN)
                return pop[max(ids, key=lambda i: scores[i])]
            child = cross(pick(), pick(), rng) if rng.random() < .5 else pick()
            nxt.append(mutate(child, rng))
        pop = nxt
        print(f"generace {gen + 1}/{GENS}: nejlepší IS {max(scores):.2f}, vyzkoušeno {len(cache)}", flush=True)
    ranked = sorted(cache.values(), key=lambda x: -x[0])[:TOP_K]
    top = []
    for fv, g in ranked:
        st = split_stats(run_genome(frames, F, g, thr))
        top.append({"genome": g, "fitness": round(fv, 2), "splits": st,
                    "oos_ok": bool((st["is"]["mean_r"] or -1) > 0 and (st["oos"]["mean_r"] or -1) > 0 and (st["oos"]["t"] or 0) >= 2)})
    winner = max((x for x in top if x["oos_ok"]), key=lambda x: x["splits"]["oos"]["t"], default=None)
    rnd_ok = 0
    for _ in range(TOP_K):
        st = split_stats(run_genome(frames, F, rand_gene(rng), thr))
        rnd_ok += int((st["is"]["mean_r"] or -1) > 0 and (st["oos"]["mean_r"] or -1) > 0 and (st["oos"]["t"] or 0) >= 2)
    return {"tested": len(cache), "thr": thr, "top": top, "winner": winner, "random_oos_ok": rnd_ok,
            "top_oos_ok": sum(x["oos_ok"] for x in top), "created": datetime.now(timezone.utc).strftime("%Y-%m-%d")}


def genome_text(g, thr=None):
    parts = []
    for fi, op, q in g["conds"]:
        v = f" ({thr[fi][q]:.2f})" if thr else ""
        parts.append(f"{FEAT_CS.get(fi, fi)} {op} {int(q * 100)}. percentil{v}")
    return ("LONG" if g["dir"] > 0 else "SHORT") + " když " + " a ".join(parts) + f" · stop {str(g['stop']).replace('.', ',')} ATR · držení {g['hold']} h"


# ---------------------------------------------------------------- celkový běh
def main():
    from research import city_accounts as ca
    cache = Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/tmp/cache")
    frames = load(cache)
    F = features(frames)
    now = datetime.now(timezone.utc)
    if GENOME.exists() and "--evolve" not in sys.argv:
        evo = json.loads(GENOME.read_text(encoding="utf-8"))
    else:
        evo = evolve(frames, F)
        GENOME.write_text(json.dumps(evo, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    thr = {fi: {float(q): v for q, v in d.items()} for fi, d in evo["thr"].items()}

    S = []

    def r_strategy(sid, name, tag, how, tf, tr, kind="vlastní nápad"):
        st = split_stats(tr)
        ok = all((st[k]["mean_r"] or -1) > 0 for k in ("is", "oos", "hold")) and (st["oos"]["t"] or 0) >= 2
        S.append({"id": sid, "name": name, "tag": tag, "how": how, "tf": tf, "kind": kind, "type": "r",
                  "splits": st, "pass": bool(ok),
                  "backtest": ca.account([t for t in tr if t["entry"] >= ca._ts(ACC_START)], start=ACC_START),
                  "live": ca.account([t for t in tr if t["entry"] >= ca._ts(LIVE_START)], start=LIVE_START)})

    def ret_strategy(sid, name, tag, how, tf, r, kind="vlastní nápad", extra=None):
        st = ret_split(r)
        r = (1 + r).resample("1D").prod() - 1                     # účet z denních výnosů
        ok = all((st[k]["sharpe"] or -1) > 0 for k in ("is", "oos", "hold")) and (st["oos"]["sharpe"] or 0) >= 1
        S.append({"id": sid, "name": name, "tag": tag, "how": how, "tf": tf, "kind": kind, "type": "ret",
                  "splits": st, "pass": bool(ok), **(extra or {}),
                  "backtest": ca.returns_account(r, start=ACC_START),
                  "live": ca.returns_account(r, start=LIVE_START) if (r.index >= ca._ts(LIVE_START)).any() else
                  ca.summarize([], [], ca._ts(LIVE_START), now)})

    r_strategy("a1", "Ozvěna BTC", "altcoiny dobíhají BTC · 1H", "Když BTC za hodinu skočí o ≥ 2σ a altcoin se pohne méně než o polovinu, vstup do altcoinu ve směru BTC; stop 1,5 ATR, nejvýš 4 h.", "1h", a1_echo(frames, F))
    r_strategy("a2", "Tichý průraz", "stažený trh se vylomí · 1H", "Po stažení volatility (ATR14/ATR200 < 0,65) průraz 48h maxima/minima ve směru denního trendu; stop 2 ATR, posuvný 2,5 ATR, nejvýš 72 h.", "1h", a2_quiet(frames, F))
    r3, hrs = a3_hours(frames, F)
    ret_strategy("a3", "Hodiny trhu", "obchoduje jen v silných hodinách dne · 1H", "Pro každou minci se z let 2019–2023 naučí hodiny dne s nadprůměrným výnosem (t ≥ 2) a jen v nich drží long.", "1h", r3, extra={"hours": hrs})
    ret_strategy("a4", "Rotace síly", "tržně neutrální · 4H", "Každé 4 h long 2 nejsilnější a short 2 nejslabší mince podle výnosu za 72 h děleného volatilitou; každá 25 % kapitálu.", "4h", a4_rotation(frames, F))
    if evo.get("winner"):
        g = evo["winner"]["genome"]
        r_strategy("ga", "Evoluce · vítěz", f"pravidlo vymyšlené evolucí z {evo['tested']} pokusů · 1H", genome_text(g, thr), "1h",
                   run_genome(frames, F, g, thr), kind="evoluce")
    out = {"updated": now.strftime("%Y-%m-%dT%H:%M+00:00"), "live_start": LIVE_START, "acc_start": ACC_START,
           "strategies": S,
           "evolution": {"tested": evo["tested"], "pop": POP, "gens": GENS, "top_oos_ok": evo["top_oos_ok"], "top_k": TOP_K,
                         "random_oos_ok": evo["random_oos_ok"], "created": evo.get("created"),
                         "winner": genome_text(evo["winner"]["genome"], thr) if evo.get("winner") else None,
                         "top": [{"rule": genome_text(x["genome"]), "fitness": x["fitness"], "splits": x["splits"], "oos_ok": x["oos_ok"]}
                                 for x in evo["top"][:10]]}}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), default=str) + "\n", encoding="utf-8")
    write_md(out)
    for s in S:
        print(f"{s['id']} {s['name']}: {'PROJDE' if s['pass'] else 'neprojde'} · od 2024 {s['backtest']['net']} USDT", flush=True)
    return 0


def _f(x):
    return "–" if x is None else str(x).replace(".", ",")


def write_md(o):
    L = ["# 🤖 AI Lab – strategie vymyšlené AI", "",
         f"Přepočet {o['updated']}. Pravidla stanovená předem jsou v hlavičce `research/ai_lab.py`. Jen papír, odděleno od desku; "
         "nejde o finanční poradenství.", "", "| Strategie | Typ | IS | OOS | HOLDOUT | Výsledek | Účet od 2024 |", "|---|---|---|---|---|---|---|"]
    for s in o["strategies"]:
        sp = s["splits"]
        if s["type"] == "r":
            cell = lambda k: f"{_f(sp[k]['mean_r'])} R (t {_f(sp[k]['t'])}, n {sp[k]['n']})"
        else:
            cell = lambda k: f"Sharpe {_f(sp[k]['sharpe'])}"
        L.append(f"| {s['name']} | {s['kind']} | {cell('is')} | {cell('oos')} | {cell('hold')} | {'✅ projde' if s['pass'] else '❌ neprojde'} | {_f(s['backtest']['net'])} USDT |")
    e = o["evolution"]
    L += ["", "## Evoluce", "", f"Vyzkoušeno {e['tested']} pravidel (populace {e['pop']}, {e['gens']} generací, fitness jen z let 2019–2023). "
          f"Z {e['top_k']} nejlepších v učení prošlo ověřením {e['top_oos_ok']}; z {e['top_k']} náhodných pravidel stejné stavby {e['random_oos_ok']}.",
          "", f"Vítěz: {e['winner'] or 'žádný – ověřením neprošlo nic'}", "", "| Pravidlo | fitness IS | OOS Ø R (t) | HOLDOUT Ø R (t) |", "|---|---|---|---|"]
    for x in e["top"]:
        L.append(f"| {x['rule']} | {_f(x['fitness'])} | {_f(x['splits']['oos']['mean_r'])} ({_f(x['splits']['oos']['t'])}) | {_f(x['splits']['hold']['mean_r'])} ({_f(x['splits']['hold']['t'])}) |")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
