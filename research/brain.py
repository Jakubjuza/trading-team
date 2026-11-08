#!/usr/bin/env python3
"""🧠 Mozek města – papírový organismus všech strategií (jen papír, nic se neposílá na burzu).

Pravidla převzatá beze změny ze studie research/experiments/brain_study.py (stanoveno předem 8. 11. 2026, studie
prošla – reports/brain_study.md, vítěz „Mozek strategií“):
  • běží VŠECHNY strategie kupolí současně, každá má vždy svůj díl kapitálu a vstupuje podle svých pravidel,
  • mozek jen přesouvá váhy podle fáze trhu: strategie, která v minulosti v dnešní fázi vydělávala (≥ 60 dní,
    průměr > 0, t ≥ 1), má váhu 1,5; která prodělávala (průměr < 0, t ≤ −1), 0,5; jinak 1; normalizace na 100 %,
  • učení walk-forward 1. den měsíce jen z minulých dní; fáze trhu z uzavřeného předchozího dne (Dispečer Downtownu),
  • kupole (riziko × ziskovost) a čtvrti (styl) jako ve studii; „Nováček“ zatím stojí mimo.
Účet: 1 000 USDT. Zpětný test = denní výnos mozku od 1. 1. 2024 (období testu studie); srovnání „všechno pořád“.
Živý papír od LIVE_START: denní změny papírových účtů strategií (research/city_accounts.py) vážené mozkem.
Fáze se mění jen jednou denně (z denní svíčky), proto stačí denní přepočet.
Na skener, registr, riziko, demo ani peníze nesahá.

    python3 research/brain.py /tmp/cache scanner/cache      → research/brain.json (čte ho Agentown, kolekce `brain`)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "experiments"))
from research import city_accounts as ca  # noqa: E402
from research.experiments import brain_study as bs  # noqa: E402

OUT = ROOT / "research" / "brain.json"
LIVE_START = "2026-11-09"


def live_returns(keys):
    """Denní výnosy živých papírových účtů strategií od LIVE_START (strategie bez obchodu = 0)."""
    from research import registry
    lab = ca.lab_paper_trades()
    out = {}
    for k in keys:
        kind, ref = k.split(":", 1)
        if kind == "lab":
            tr = [t for t in lab.get(ref, []) if ca._ts(t["entry"]) >= ca._ts(LIVE_START)]
        elif ref == "ensemble":
            rows = [json.loads(x) for x in (ROOT / "research" / "equity_log.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
            s = pd.Series({ca._ts(x["t"]): 1 + float((x.get("parts") or {}).get("ensemble") or 0) / 5000 for x in rows
                           if x.get("t", "") >= LIVE_START})
            out[k] = s.sort_index().pct_change().fillna(0) if len(s) else pd.Series(dtype=float)
            continue
        else:
            name, _, fn = ca.CORE_META[ref]
            tr = [t for t in ca.core_paper(ROOT / "research" / fn, name) if ca._ts(t["entry"]) >= ca._ts(LIVE_START)]
        eq = ca.daily_equity(tr)
        out[k] = eq.pct_change().fillna(0) if len(eq) else pd.Series(dtype=float)
    _ = registry
    return out


def main():
    cache = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cache")
    scache = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "scanner" / "cache")
    df, meta = bs.universe(cache, scache)
    phase, _ = bs.btc_phases(cache)
    df = df[df.index >= pd.Timestamp("2019-01-01", tz="UTC")]
    dome, st, med_dd, med_cg = bs.assign_domes(df, meta)
    used = [k for k in df.columns if dome[k] in bs.DOMES]
    months = bs.months_of(df.index)
    plan = bs.gates(df[used], phase, months)
    v2, _ = bs.run_plan(df[used], phase, plan)
    v0 = df[used].mean(axis=1, skipna=True).fillna(0)
    v0 = v0[v0.index >= bs.LEARN_FROM]
    start = bs.IS_END

    today = datetime.now(timezone.utc)
    ph_now = str(phase.dropna().iloc[-1])
    m_now = pd.Timestamp(today.year, today.month, 1, tz="UTC")
    if m_now not in plan:
        plan.update(bs.gates(df[used], phase, [m_now]))
    mult = (plan.get(m_now) or {}).get(ph_now, {})
    live_keys = [k for k in used if df[k].iloc[-60:].notna().any()]
    tot = sum(mult.get(k, bs.NEUTRAL) for k in live_keys) or 1
    domes = []
    for d in bs.DOMES:
        mem = []
        for k in live_keys:
            if dome[k] != d:
                continue
            m = mult.get(k, bs.NEUTRAL)
            mem.append({"id": k, "ref": meta[k]["ref"], "kind": meta[k]["kind"], "name": meta[k]["name"],
                        "style": meta[k]["style"], "tf": meta[k].get("tf"), "dir": meta[k].get("dir", "long"),
                        "mult": m, "weight_pct": round(m / tot * 100, 2),
                        "is_dd_pct": round(st[k]["dd"] * 100, 1), "is_cagr_pct": round(st[k]["cagr"] * 100, 1)})
        mem.sort(key=lambda x: (-x["mult"], x["style"], x["name"]))
        domes.append({"name": d, "weight_pct": round(sum(x["weight_pct"] for x in mem), 1), "members": mem,
                      "up": sum(x["mult"] > 1 for x in mem), "down": sum(x["mult"] < 1 for x in mem)})

    # živý papír: vážené denní výnosy papírových účtů
    lr = live_returns(live_keys)
    idx = pd.date_range(LIVE_START, today.strftime("%Y-%m-%d"), freq="D", tz="UTC")
    live_ret = []
    for dday in idx:
        mm = (plan.get(pd.Timestamp(dday.year, dday.month, 1, tz="UTC")) or {}).get(phase.get(dday), {})
        w = v = 0.0
        for k in live_keys:
            x = lr.get(k)
            r = float(x.get(dday, 0.0)) if x is not None and len(x) else 0.0
            kk = mm.get(k, bs.NEUTRAL)
            w += kk
            v += kk * r
        live_ret.append(v / w if w else 0.0)
    live = ca.returns_account(pd.Series(live_ret, index=idx)) if len(idx) > 1 else \
        ca.summarize([], [], ca._ts(LIVE_START), today)
    live["start"] = LIVE_START
    study = {}
    sp = ROOT / "research" / "brain_study.json"
    if sp.exists():
        s = json.loads(sp.read_text(encoding="utf-8"))
        study = {"winner": s.get("winner"), "results": s.get("results"), "verdict": s.get("verdict"), "updated": s.get("updated")}
    parts = ph_now.split(" · ")
    now = today.strftime("%Y-%m-%dT%H:%M+00:00")
    out = {"id": "state", "updated": now, "live_start": LIVE_START,
           "phase": {"name": ph_now, "trend": parts[0] if parts else None, "pohyb": parts[1] if len(parts) > 1 else None,
                     "vola": parts[2] if len(parts) > 2 else None},
           "med_dd_pct": round(med_dd * 100, 1), "med_cagr_pct": round(med_cg * 100, 1),
           "domes": domes, "n_strategies": len(live_keys),
           "backtest": ca.returns_account(v2[v2.index >= start]),
           "baseline": ca.returns_account(v0[v0.index >= start]),
           "live": live, "study": study}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), default=str) + "\n", encoding="utf-8")
    print(f"fáze {ph_now}; váhy kupolí: " + ", ".join(f"{d['name']} {d['weight_pct']} %" for d in domes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
