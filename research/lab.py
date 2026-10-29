"""🔬 Noční laboratoř: průběžný výzkum strategií a sentimentu, plnění registru a papírové vyhodnocení.

Každou noc (.github/workflows/lab.yml):
  1. BALÍK – jeden díl rotace (research/lab_state.json): atlas jednoho timeframu na čerstvých datech
     (15 rodin strategií, research/experiments/strategy_atlas.py), nebo sentiment (Strach a chamtivost, 1D a 4H).
     Pravidla testů jsou stejná jako v atlasu: IS/OOS/HOLDOUT, vlastní náhoda, poplatky MEXC 0,05 %/stranu.
  2. VÝBĚR (stanoveno předem): kombinace, které splní pravidlo atlasu (Ø R > 0 ve všech třech obdobích, OOS i HOLDOUT
     nad 95. percentilem vlastní náhody, OOS t ≥ 2, IS ≥ 150 a OOS ≥ 50 obchodů); seřazené podle min(OOS t, HOLDOUT t);
     přednost má kombinace splňující i přísný výběr atlasu (top 50 podle IS t); nejlepší jedna na rodinu × timeframe ×
     směr, nejvýš 3 na rodinu; nejvýš 6 nových za noc (12 při prvním naplnění) a 24 aktivních celkem.
  3. REŽIMY: u vybrané strategie se z obchodů celé historie změří Ø R v režimech býčí / medvědí / boční / panika
     (research/regime.py). Aktivní je jen v režimech s ≥ 30 obchody a Ø R > 0,05. Bez takového režimu se nepřidá.
  4. PAPÍR: z research/lab_trades.jsonl (zapisuje skener) spočítá papírové výsledky a podle research/registry.py
     povýší (ověřeno) nebo vyřadí. Nic nejde na skutečné peníze.
  5. ZPRÁVY: v noci jen při změně registru; v pondělí souhrn laboratoře na Telegram.

    python3 research/lab.py nightly /tmp/cache     # celý noční běh
    python3 research/lab.py select /tmp/cache      # jen výběr + režimy + papír (z existujících výsledků atlasu)
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import regime, registry  # noqa: E402
from research.experiments import strategy_atlas as atlas  # noqa: E402

STATE = ROOT / "research" / "lab_state.json"
TRADES = ROOT / "research" / "lab_trades.jsonl"
LOGMD = ROOT / "research" / "lab_log.md"
ATLAS = ROOT / "reports" / "atlas"
ROTATION = ["atlas:4h", "atlas:1h", "sentiment", "atlas:2h", "atlas:6h", "atlas:12h", "atlas:1d", "atlas:15m"]
MAX_ACTIVE, MAX_NEW, PER_FAMILY = 24, 6, 3
M = atlas.MAIN


# ---------------------------------------------------------------- balíky
def fng_series():
    import urllib.request
    with urllib.request.urlopen("https://api.alternative.me/fng/?limit=0&format=json", timeout=30) as r:
        data = json.loads(r.read())["data"]
    s = pd.Series({pd.Timestamp(int(x["timestamp"]), unit="s", tz="UTC"): float(x["value"]) for x in data}).sort_index()
    s.index = s.index.floor("1D") + pd.Timedelta("1D")                # hodnota dne platí až od dalšího dne
    return s


def batch_sentiment(cache):
    fng = fng_series()
    var = [("fng", (mode, lvl)) for mode in ("into", "out") for lvl in (15, 20, 25, 30)]

    def attach(coin, z):
        z.fng = fng.reindex(z.df.index.floor("1D")).ffill().to_numpy(float)

    for tf in ("1d", "4h"):
        atlas.run(tf, cache, var=var, attach=attach, name=f"sent_{tf}")


def run_batch(kind, cache):
    t0 = time.time()
    if kind.startswith("atlas:"):
        atlas.run(kind.split(":")[1], cache)
    elif kind == "sentiment":
        batch_sentiment(cache)
    atlas.report(ATLAS)
    return f"{kind} hotovo za {(time.time() - t0) / 60:.0f} min"


# ---------------------------------------------------------------- výběr
def candidates():
    res = pd.concat([pd.read_csv(f) for f in sorted(ATLAS.glob("*.csv.gz"))], ignore_index=True)
    e = res[(res[f"{M}_is_n"] >= 150) & (res[f"{M}_oos_n"] >= 50)].copy()
    ok = ((e[f"{M}_is_r"] > 0) & (e[f"{M}_oos_r"] > 0) & (e[f"{M}_hold_r"] > 0)
          & (e[f"{M}_oos_r"] > e[f"{M}_rnd_oos_p95"]) & (e[f"{M}_hold_r"] > e[f"{M}_rnd_hold_p95"]) & (e[f"{M}_oos_t"] >= 2))
    top = e.sort_values(f"{M}_is_t", ascending=False).groupby("dir").head(50).index    # přísné pravidlo atlasu
    c = e[ok].copy()
    c["strict"] = c.index.isin(top)
    c["score"] = np.minimum(c[f"{M}_oos_t"], c[f"{M}_hold_t"].fillna(0))
    c = c.sort_values(["strict", "score"], ascending=[False, False])
    c = c.groupby(["family", "tf", "dir"], sort=False).head(1)
    c = c.groupby("family", sort=False).head(PER_FAMILY)
    return c


def load_frames(tf, cache):
    base_tf, start = ("15m", "2022-01-01") if tf == "15m" else ("1h", "2019-01-01")
    out = {}
    for coin in atlas.COINS:
        b = atlas.fetch(coin, base_tf, start, cache)
        h1 = b if base_tf == "1h" else atlas.fetch(coin, "1h", "2019-01-01", cache)
        df = atlas.resample(b, tf)
        z = atlas.Ind(df)
        bull, up = atlas.daily_regimes(h1)
        day = df.index.floor("1D")
        z.flt = {"d200": bull.reindex(day).to_numpy(float), "d50": up.reindex(day).to_numpy(float)}
        z.reg = regime.regime_series(atlas.resample(h1, "1d")).reindex(day).to_numpy(dtype=object)
        out[coin] = z
    return out


def regime_stats(row, frames, fng=None):
    p = tuple(_typed(x) for x in str(row["params"]).split("/"))
    d = 1 if row["dir"] == "long" else -1
    sa, ta, ga, uo, mh = atlas.EXITS[row["exit"]]
    R, G = [], []
    for coin, z in frames.items():
        if row["family"] == "fng":
            z.fng = fng.reindex(z.df.index.floor("1D")).ffill().to_numpy(float)
        ent, opp = atlas.family_signals(z, row["family"], p, d)
        if row["filter"] != "none":
            ent = ent[z.flt[row["filter"]][ent] == (1.0 if d > 0 else 0.0)]
        ii, xx, gg, rf = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, ent.astype(np.int64), np.asarray(opp, bool), d,
                                        sa, ta, ga, uo, mh)
        R.append((gg - 2 * atlas.COSTS[M]) / rf)
        G.append(z.reg[np.maximum(ii - 1, 0)])
    r, g = np.concatenate(R), np.concatenate(G)
    out = {}
    for lab in regime.LABELS:
        x = r[g == lab]
        out[lab] = {"n": int(len(x)), "mean_r": round(float(x.mean()), 3) if len(x) else None}
    return out


def _typed(x):
    for f in (int, float):
        try:
            return f(x)
        except ValueError:
            pass
    return x


# ---------------------------------------------------------------- papír
def paper_stats():
    out = {}
    if not TRADES.exists():
        return out
    rows = [json.loads(x) for x in TRADES.read_text(encoding="utf-8").splitlines() if x.strip()]
    for r in rows:
        if r.get("event") != "close":
            continue
        out.setdefault(r["sid"], []).append(r["r"])
    st = {}
    for k, v in out.items():
        a = np.array(v, float)
        st[k] = {"n": len(a), "mean_r": round(float(a.mean()), 3), "sum_r": round(float(a.sum()), 2),
                 "t": round(float(a.mean() / (a.std(ddof=1) / np.sqrt(len(a)))), 2) if len(a) > 1 and a.std(ddof=1) > 0 else None,
                 "win": round(float((a > 0).mean()), 2)}
    return st


def gate_stats():
    """Živé měření kontextové brány: vzaté papírové obchody vs. stínové (vyřazené bránou nebo limitem)."""
    shadow = ROOT / "research" / "lab_shadow.jsonl"
    out, by_ctx = {}, {"boční základna": [], "běžící trend": []}
    for name, path in (("vzaté", TRADES), ("vyřazené", shadow)):
        if not path.exists():
            continue
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        rows = [x for x in rows if x.get("event") == "close"]
        r = [x["r"] for x in rows]
        if r:
            out[name] = {"n": len(r), "mean_r": float(np.mean(r)), "sum_r": float(np.sum(r))}
        for x in rows:                                     # hypotéza H1 (reports/context_gate_notes.md)
            if "ctx_range" in x:
                by_ctx["boční základna" if x["ctx_range"] else "běžící trend"].append(x["r"])
    for k, r in by_ctx.items():
        if r:
            out[k] = {"n": len(r), "mean_r": float(np.mean(r)), "sum_r": float(np.sum(r))}
    return out


# ---------------------------------------------------------------- hlavní běh
def select(cache, log):
    reg = registry.load()
    today = datetime.now(timezone.utc).date().isoformat()
    changes = []
    # papírové výsledky a přechody
    ps = paper_stats()
    for s in reg["strategies"]:
        if s["id"] in ps:
            s["paper"] = ps[s["id"]]
        tr = registry.transition(s, s.get("paper") or {})
        if tr:
            s["status"] = tr[0]
            s.setdefault("history", []).append({"date": today, "status": tr[0], "reason": tr[1]})
            changes.append(f"{'✅' if tr[0] == 'ověřeno' else '🏚️'} {s['label']}: {tr[0]} ({tr[1]})")
    # noví kandidáti
    cand = candidates()
    known = {s["id"] for s in reg["strategies"]}
    n_active = len(registry.active(reg))
    max_new = MAX_NEW * 2 if not reg["strategies"] else MAX_NEW         # první naplnění registru
    frames_cache, fng = {}, None
    added = 0
    for _, r in cand.iterrows():
        if added >= max_new or n_active >= MAX_ACTIVE:
            break
        key = registry.sid(r)
        if key in known:
            continue
        if r["family"] == "fng" and fng is None:
            fng = fng_series()
        if r["tf"] not in frames_cache:
            frames_cache[r["tf"]] = load_frames(r["tf"], cache)
        rs = regime_stats(r, frames_cache[r["tf"]], fng)
        allowed = [k for k, v in rs.items() if v["n"] >= 30 and (v["mean_r"] or 0) > 0.05]
        entry = {"id": key, "label": registry.label(r), "family": r["family"], "params": str(r["params"]), "tf": r["tf"],
                 "filter": r["filter"], "exit": r["exit"], "dir": r["dir"], "added": today,
                 "source": f"atlas {today}",
                 "backtest": {k: (round(float(r[f"{M}_{k}"]), 3) if pd.notna(r[f"{M}_{k}"]) else None)
                              for k in ("is_r", "oos_r", "hold_r", "oos_t", "hold_t", "is_n", "oos_n", "hold_n")}
                             | {"maxdd_r": round(float(r["maxdd_r"]), 1), "per_month": round(float(r["per_month"]), 1)},
                 "regime_stats": rs, "regimes": allowed}
        if not allowed:
            entry["status"] = "kandidát"
            entry["history"] = [{"date": today, "status": "kandidát", "reason": "žádný režim s ≥ 30 obchody a Ø R > 0,05"}]
            reg["strategies"].append(entry)
            known.add(key)
            continue
        entry["status"] = "papír"
        entry["history"] = [{"date": today, "status": "papír", "reason": f"atlas: OOS {r[f'{M}_oos_r']:+.2f} R (t {r[f'{M}_oos_t']:+.1f}), "
                                                                         f"HOLDOUT {r[f'{M}_hold_r']:+.2f} R"}]
        reg["strategies"].append(entry)
        known.add(key)
        added += 1
        n_active += 1
        changes.append(f"🆕 {entry['label']} → papír, režimy: {', '.join(allowed)}")
    registry.save(reg)
    if changes:
        with LOGMD.open("a", encoding="utf-8") as f:
            f.write(f"\n## {today}\n" + "".join(f"- {c}\n" for c in changes) + "".join(f"- {x}\n" for x in log))
    return reg, changes


def summary(reg, changes, log, weekly=False):
    act = registry.active(reg)
    lines = [f"🔬 Laboratoř – {'týdenní souhrn' if weekly else 'noční běh'}"] + [f"• {x}" for x in log]
    if changes:
        lines.append("Změny v registru:")
        lines += changes
    if weekly:
        lines.append(f"Aktivní papírové strategie: {len(act)} (ověřeno {sum(1 for s in act if s['status'] == 'ověřeno')}).")
        best = sorted([s for s in act if (s.get("paper") or {}).get("n")], key=lambda s: -s["paper"]["sum_r"])[:5]
        for s in best:
            p = s["paper"]
            lines.append(f"• {s['label']}: {p['n']} obchodů, Ø {p['mean_r']:+.2f} R, Σ {p['sum_r']:+.1f} R".replace(".", ","))
    if weekly:
        gs = gate_stats()
        if gs:
            lines.append("🧠 Brána kontextu živě: " + " · ".join(
                f"{k} {v['n']} obch. Ø {v['mean_r']:+.2f} R".replace(".", ",") for k, v in gs.items()))
    lines.append("Papírově, nic se neobchoduje skutečnými penězi. Nejde o finanční poradenství.")
    return "\n".join(lines)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "nightly"
    cache = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/cache")
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"next": 0, "runs": []}
    log = []
    if cmd == "nightly":
        kind = ROTATION[st["next"] % len(ROTATION)]
        try:
            log.append(run_batch(kind, cache))
        except Exception as exc:
            log.append(f"{kind} selhal: {exc.__class__.__name__}: {str(exc)[:150]}")
        st["next"] = st["next"] + 1
        st["runs"] = (st.get("runs", []) + [{"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "batch": kind,
                                             "log": log[-1]}])[-60:]
        STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    reg, changes = select(cache, log)
    weekly = datetime.now(timezone.utc).weekday() == 0
    text = summary(reg, changes, log, weekly)
    print(text)
    if (changes or weekly) and "--no-send" not in sys.argv:
        try:
            from scanner import notify
            notify.telegram(text)
        except Exception as exc:
            print(f"Telegram selhal: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
