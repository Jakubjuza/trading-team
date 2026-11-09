#!/usr/bin/env python3
"""💰 $1M Future – poctivá simulace dvou let práce Agentownu. Jen papír, odděleno od desku.

Zadání uživatele (9. 11. 2026): „představ si, že Agentown děláme už rok nebo dva roky a máme strategie, které jsou
fakt silné – nasimuluj tu budoucnost a udělej strategie, ke kterým bychom se za 2 roky dostali“; kupole „$1M Future“.
Výsledky se nevymýšlejí: obě části spouštějí náš skutečný postup (evoluce pravidel z AI Labu + přísný test) a čísla
jsou jen to, co z dat vyjde – klidně i málo. Na skener, registr, riziko, demo ani peníze nesahá.

Stanoveno PŘEDEM (9. 11. 2026), před prvním spuštěním na datech:

  Společné: data, znaky, genom, simulace obchodů a poplatky 0,05 % na stranu přesně jako research/ai_lab.py
    (OKX spot, 8 mincí, hodinové svíčky od 1/2019). Jedno kolo = evoluce s populací 120 a 20 generacemi (menší než
    noční kolo AI Labu 200 × 30, aby se 72 kol vešlo do jednoho běhu Actions), turnaj 3, 30 nejlepších různých
    pravidel do ověření a kontrola 30 náhodnými pravidly stejné stavby. Zaměření kol se střídá jako v AI Labu
    (vše · jen short · rychlé 2–8 h · pomalé 16–32 h · jen long). Prahy znaků = decily jen z dat učení daného kola.

  A) STROJ ČASU ZPĚT – jako bychom Agentown dělali od 9. 11. 2024:
    24 kol, jedno na začátku každého měsíce od 9. 11. 2024 (místo každé noci – kvůli výpočtu). Kolo v čase t vidí
    jen data před t: učení < t − 12 měsíců ≤ ověření < t. Kandidát projde, když Ø R > 0 v učení, Ø R > 0 a t ≥ 2,5
    v ověření a kolo porazí svou náhodnou kontrolu. Registr max. 10 strategií; nejlepší kandidát kola (nejvyšší t
    v ověření) se přidá, při plném registru nahradí nejslabší jen s vyšším t. Strategie obchoduje papírově od data
    přidání do data vyřazení – to jsou data, která v době rozhodnutí neviděl nikdo. Fond A = všechny strategie
    registru v jednom účtu 1 000 USD od 9. 11. 2024, riziko 0,5 % účtu na obchod; každá strategie má i vlastní účet
    1 000 USD s rizikem 1 % (jako ostatní účty Agentownu). Srovnání: BTC drž za stejné období.

  B) ZRYCHLENÁ BUDOUCNOST – dva roky výzkumu stlačené do jednoho běhu:
    48 kol (dva roky po dvou týdnech) se semínky 20261109 + číslo kola. Všechna kola vidí jen data před
    9. 11. 2025: učení < 9. 11. 2024 ≤ ověření < 9. 11. 2025. Protože se testuje 48krát, je práh přísnější:
    Ø R > 0 v učení, v ověření Ø R > 0 a t ≥ 3, kolo porazí náhodnou kontrolu. Z prošlých se vezme nejvýš 10
    s nejvyšším t v ověření, každá s jinou kombinací (směr, sada znaků). ZÁVĚREČNÝ TEST = 9. 11. 2025 → dnes,
    data, která výzkum nikdy neviděl, vyhodnocená jednou. Fond B = vybrané strategie v jednom účtu 1 000 USD
    od 9. 11. 2025, riziko 0,5 % na obchod; vlastní účty 1 000 USD s rizikem 1 %. Srovnání: BTC drž.

  „Cesta k $1M“ na stránce = jen přepočet: kolik let by trvalo dojít z 1 000 USD na 1 000 000 USD, KDYBY se roční
    tempo fondu opakovalo – s jasným štítkem, že to není předpověď.

    python3 research/future_lab.py rounds /tmp/cache <index> <počet>  → /tmp/future/part_<index>.json (Actions matrix)
    python3 research/future_lab.py merge /tmp/cache /tmp/future        → research/future_lab.json + reports/future_lab.md
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research import ai_lab as al  # noqa: E402

OUT = ROOT / "research" / "future_lab.json"
OUT_MD = ROOT / "reports" / "future_lab.md"
POP, GENS = 120, 20
A_START = pd.Timestamp("2024-11-09", tz="UTC")
A_ROUNDS, A_VAL_MONTHS, A_T = 24, 12, 2.5
B_IS_END, B_OOS_END = pd.Timestamp("2024-11-09", tz="UTC"), pd.Timestamp("2025-11-09", tz="UTC")
B_ROUNDS, B_T, SEED_B = 48, 3.0, 20261109
SEED_A = 20241109
MAX_REG = 10
FUND_RISK, ACC_RISK, CASH = 0.005, 0.01, 1000.0


def tasks():
    """Všech 72 kol: ('A', n, čas kola) a ('B', n, None)."""
    out = [("A", n, A_START + pd.DateOffset(months=n - 1)) for n in range(1, A_ROUNDS + 1)]
    out += [("B", n, None) for n in range(1, B_ROUNDS + 1)]
    return out


def windows(part, t):
    if part == "A":
        return t - pd.DateOffset(months=A_VAL_MONTHS), t
    return B_IS_END, B_OOS_END


def run_one(frames, F, part, n, t):
    """Jedno kolo: evoluce jen na datech učení, ověření, náhodná kontrola. Vrátí kandidáty, kteří prošli."""
    is_end, oos_end = windows(part, t)
    focus, space = al.FOCUS[(n - 1) % len(al.FOCUS)]
    saved = (al.IS_END, al.OOS_END, al.SPACE, al.POP, al.GENS)
    al.IS_END, al.OOS_END, al.SPACE, al.POP, al.GENS = is_end, oos_end, space, POP, GENS
    try:
        evo = al.evolve(frames, F, seed=(SEED_A if part == "A" else SEED_B) + n)
    finally:
        al.IS_END, al.OOS_END, al.SPACE, al.POP, al.GENS = saved
    tmin = A_T if part == "A" else B_T
    sane = evo["top_oos_ok"] > evo["random_oos_ok"]
    cands = []
    for x in evo["top"]:
        st = x["splits"]
        if (st["is"]["mean_r"] or -1) > 0 and (st["oos"]["mean_r"] or -1) > 0 and (st["oos"]["t"] or 0) >= tmin:
            cands.append({"genome": x["genome"], "is": st["is"], "oos": st["oos"]})   # „hold“ (po kole) se nezapisuje
    cands.sort(key=lambda c: -(c["oos"]["t"] or 0))
    return {"part": part, "n": n, "t": t.isoformat() if t is not None else None, "focus": focus,
            "is_end": is_end.isoformat(), "oos_end": oos_end.isoformat(), "tested": evo["tested"],
            "top_oos_ok": evo["top_oos_ok"], "random_oos_ok": evo["random_oos_ok"], "sane": bool(sane),
            "cands": cands if sane else [], "n_cands_raw": len(cands), "thr": evo["thr"]}


def cmd_rounds(cache, idx, of, out_dir="/tmp/future"):
    frames = al.load(cache)
    F = al.features(frames)
    res = []
    for k, (part, n, t) in enumerate(tasks()):
        if k % of != idx:
            continue
        r = run_one(frames, F, part, n, t)
        print(f"{part}{n}: vyzkoušeno {r['tested']}, ověřením {r['top_oos_ok']} × náhodných {r['random_oos_ok']}, "
              f"kandidátů {len(r['cands'])}", flush=True)
        res.append(r)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / f"part_{idx}.json").write_text(json.dumps(res, default=str), encoding="utf-8")


# ---------------------------------------------------------------- skládání výsledků
def _thr(d):
    return {fi: {float(q): v for q, v in v2.items()} for fi, v2 in d.items()}


def sig(g):
    return (g["dir"], tuple(sorted({c[0] for c in g["conds"]})))


def registry_a(rounds):
    """Registr části A v čase: kdo kdy přibyl a kdo kdy odešel."""
    reg, hist, members = [], [], []
    for r in sorted(rounds, key=lambda x: x["t"]):
        known = {al.key(m["genome"]) for m in reg}
        best = next((c for c in r["cands"] if al.key(c["genome"]) not in known), None)
        ev = {"n": r["n"], "date": r["t"][:10], "focus": r["focus"], "tested": r["tested"], "top_oos_ok": r["top_oos_ok"],
              "random_oos_ok": r["random_oos_ok"], "added": None, "removed": None}
        if not r["sane"]:
            ev["reason"] = f"kolo neporazilo náhodnou kontrolu ({r['top_oos_ok']} × {r['random_oos_ok']})"
        elif best is None:
            ev["reason"] = "nic neprošlo testem"
        else:
            m = {"id": f"fa{r['n']}", "round": r["n"], "focus": r["focus"], "added": r["t"], "removed": None,
                 "genome": best["genome"], "thr": r["thr"], "is": best["is"], "oos": best["oos"]}
            if len(reg) < MAX_REG:
                reg.append(m); members.append(m); ev["added"] = m["id"]; ev["reason"] = "přidáno"
            else:
                weak = min(reg, key=lambda x: x["oos"]["t"] or 0)
                if (best["oos"]["t"] or 0) > (weak["oos"]["t"] or 0):
                    weak["removed"] = r["t"]; reg.remove(weak); reg.append(m); members.append(m)
                    ev["added"], ev["removed"], ev["reason"] = m["id"], weak["id"], "přidáno místo slabší"
                else:
                    ev["reason"] = "registr plný, kandidát není silnější"
        hist.append(ev)
    return members, hist


def registry_b(rounds):
    pool = []
    for r in rounds:
        for c in r["cands"]:
            pool.append({**c, "round": r["n"], "focus": r["focus"], "thr": r["thr"]})
    pool.sort(key=lambda c: -(c["oos"]["t"] or 0))
    out, keys, sigs = [], set(), set()
    for c in pool:
        k, s = al.key(c["genome"]), sig(c["genome"])
        if k in keys or s in sigs:
            continue
        keys.add(k); sigs.add(s)
        out.append({"id": f"fb{len(out) + 1}", **c})
        if len(out) >= MAX_REG:
            break
    return out, len(pool)


def stats(tr, lo, hi=None):
    r = np.array([t["r"] for t in tr if t["entry"] >= lo and (hi is None or t["entry"] < hi)])
    n = len(r)
    return {"n": n, "mean_r": round(float(r.mean()), 3) if n else None,
            "t": round(float(r.mean() / (r.std(ddof=1) / np.sqrt(n))), 2) if n > 2 and r.std(ddof=1) > 0 else None}


def btc_hold(frames, start, cash=CASH):
    cl = frames["BTC"].df["Close"]
    cl = cl[cl.index >= start].resample("1D").last().dropna()
    if not len(cl):
        return None
    eq = cash * cl / cl.iloc[0]
    step = max(1, len(eq) // 300)
    curve = eq.iloc[::step]
    if curve.index[-1] != eq.index[-1]:
        curve = pd.concat([curve, eq.iloc[-1:]])
    dd = float(((eq / eq.cummax()) - 1).min() * 100)
    return {"equity": round(float(eq.iloc[-1]), 2), "net_pct": round(float((eq.iloc[-1] / cash - 1) * 100), 1),
            "max_dd_pct": round(dd, 1), "curve": [[i.date().isoformat(), round(float(v), 2)] for i, v in curve.items()]}


def years_to_million(acc, start, now):
    days = max(1.0, (now - start).days)
    g = acc["equity"] / CASH
    if g <= 1 or days < 120:
        return None
    cagr = g ** (365.25 / days) - 1
    return {"cagr_pct": round(cagr * 100, 1), "years": round(float(np.log(1000) / np.log(1 + cagr)), 1)}


def cmd_merge(cache, parts_dir):
    from research import city_accounts as ca
    rounds = []
    for p in sorted(Path(parts_dir).glob("part_*.json")):
        rounds += json.loads(p.read_text(encoding="utf-8"))
    A = [r for r in rounds if r["part"] == "A"]
    B = [r for r in rounds if r["part"] == "B"]
    frames = al.load(cache)
    F = al.features(frames)
    now = datetime.now(timezone.utc)
    nowts = pd.Timestamp(now)

    def trades(m):
        return al.run_genome(frames, F, m["genome"], _thr(m["thr"]))

    # A: stroj času
    members, hist = registry_a(A)
    sa, fund_a = [], []
    for m in members:
        tr = trades(m)
        lo, hi = pd.Timestamp(m["added"]), (pd.Timestamp(m["removed"]) if m["removed"] else None)
        live = [t for t in tr if t["entry"] >= lo and (hi is None or t["entry"] < hi)]
        fund_a += live
        sa.append({"id": m["id"], "name": f"Budoucí #{m['round']} · {m['focus']}", "round": m["round"], "focus": m["focus"],
                   "added": m["added"][:10], "removed": m["removed"][:10] if m["removed"] else None,
                   "rule": al.genome_text(m["genome"], _thr(m["thr"])), "at_add": {"is": m["is"], "oos": m["oos"]},
                   "after": stats(tr, lo, hi),
                   "account": ca.account(live, start=m["added"][:10], risk=ACC_RISK)})
    acc_a = ca.account(fund_a, start=A_START.date().isoformat(), risk=FUND_RISK)
    part_a = {"start": A_START.date().isoformat(), "rounds": hist, "strategies": sa, "fund": acc_a,
              "fund_after": stats(fund_a, A_START), "btc": btc_hold(frames, A_START),
              "million": years_to_million(acc_a, A_START, nowts), "n_rounds": len(A),
              "tested": int(sum(r["tested"] for r in A)), "active": sum(1 for s in sa if not s["removed"])}

    # B: zrychlená budoucnost
    reg, n_pool = registry_b(B)
    sb, fund_b = [], []
    for m in reg:
        tr = trades(m)
        fin = [t for t in tr if t["entry"] >= B_OOS_END]
        fund_b += fin
        sb.append({"id": m["id"], "name": f"Future #{m['id'][2:]} · {m['focus']}", "round": m["round"], "focus": m["focus"],
                   "rule": al.genome_text(m["genome"], _thr(m["thr"])), "is": m["is"], "oos": m["oos"],
                   "final": stats(tr, B_OOS_END), "research_acc": ca.account([t for t in tr if B_IS_END <= t["entry"] < B_OOS_END],
                                                                             start=B_IS_END.date().isoformat(), end=B_OOS_END, risk=ACC_RISK),
                   "account": ca.account(fin, start=B_OOS_END.date().isoformat(), risk=ACC_RISK)})
    acc_b = ca.account(fund_b, start=B_OOS_END.date().isoformat(), risk=FUND_RISK)
    part_b = {"is_end": B_IS_END.date().isoformat(), "oos_end": B_OOS_END.date().isoformat(), "n_rounds": len(B),
              "tested": int(sum(r["tested"] for r in B)), "passed": n_pool,
              "sane_rounds": sum(r["sane"] for r in B), "strategies": sb, "fund": acc_b, "fund_final": stats(fund_b, B_OOS_END),
              "btc": btc_hold(frames, B_OOS_END), "million": years_to_million(acc_b, B_OOS_END, nowts),
              "rounds": [{"n": r["n"], "focus": r["focus"], "tested": r["tested"], "top_oos_ok": r["top_oos_ok"],
                          "random_oos_ok": r["random_oos_ok"], "sane": r["sane"], "cands": len(r["cands"])}
                         for r in sorted(B, key=lambda x: x["n"])]}
    out = {"id": "state", "updated": now.strftime("%Y-%m-%dT%H:%M+00:00"), "pop": POP, "gens": GENS,
           "fund_risk": FUND_RISK, "acc_risk": ACC_RISK, "a": part_a, "b": part_b}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), default=str) + "\n", encoding="utf-8")
    write_md(out)
    print(f"A: {len(sa)} strategií v čase, fond {acc_a['net_pct']} % · B: {len(sb)} strategií, fond {acc_b['net_pct']} %")


def _f(x, d=2):
    return "–" if x is None else f"{x:+.{d}f}".replace(".", ",")


def write_md(o):
    A, B = o["a"], o["b"]
    L = ["# 💰 $1M Future – simulace dvou let Agentownu", "",
         f"Přepočet {o['updated']} · `research/future_lab.py` (pravidla stanovená předem v hlavičce skriptu). Jen papír, ne rada.", "",
         "## A) Stroj času zpět (od 9. 11. 2024)", "",
         f"{A['n_rounds']} měsíčních kol, vyzkoušeno {A['tested']} pravidel. Strategie obchodují jen od přidání (data, která v době rozhodnutí nikdo neviděl).", "",
         f"Fond A (riziko {o['fund_risk'] * 100:g} %/obchod): {A['fund']['equity']} USD ({_f(A['fund']['net_pct'], 1)} %), "
         f"max. propad {A['fund']['max_dd_pct']} %, obchodů {A['fund']['n_trades']}, Ø R {_f(A['fund_after']['mean_r'], 3)} (t {_f(A['fund_after']['t'])}). "
         f"BTC drž: {_f((A['btc'] or {}).get('net_pct'), 1)} %.", "",
         "| kolo | datum | zaměření | ověřením / náhodných | výsledek |", "|---|---|---|---|---|"]
    L += [f"| {r['n']} | {r['date']} | {r['focus']} | {r['top_oos_ok']} / {r['random_oos_ok']} | {r['reason']} |" for r in A["rounds"]]
    L += ["", "| strategie | přidána | vyřazena | ověření t při přidání | po přidání Ø R (t, n) | účet |", "|---|---|---|---|---|---|"]
    L += [f"| {s['name']} | {s['added']} | {s['removed'] or '–'} | {_f(s['at_add']['oos']['t'])} | {_f(s['after']['mean_r'], 3)} ({_f(s['after']['t'])}, {s['after']['n']}) | {s['account']['equity']} |"
          for s in A["strategies"]]
    L += ["", f"## B) Zrychlená budoucnost (výzkum do {B['oos_end']}, závěrečný test potom)", "",
          f"{B['n_rounds']} kol, vyzkoušeno {B['tested']} pravidel, kol nad náhodou {B['sane_rounds']}, prošlo {B['passed']} kandidátů, vybráno {len(B['strategies'])}.", "",
          f"Fond B na závěrečném testu: {B['fund']['equity']} USD ({_f(B['fund']['net_pct'], 1)} %), max. propad {B['fund']['max_dd_pct']} %, "
          f"Ø R {_f(B['fund_final']['mean_r'], 3)} (t {_f(B['fund_final']['t'])}, n {B['fund_final']['n']}). BTC drž: {_f((B['btc'] or {}).get('net_pct'), 1)} %.", "",
          "| strategie | pravidlo | ověření Ø R (t) | závěrečný test Ø R (t, n) |", "|---|---|---|---|"]
    L += [f"| {s['name']} | {s['rule']} | {_f(s['oos']['mean_r'], 3)} ({_f(s['oos']['t'])}) | {_f(s['final']['mean_r'], 3)} ({_f(s['final']['t'])}, {s['final']['n']}) |"
          for s in B["strategies"]]
    L += ["", "„Cesta k $1M“ je jen přepočet tempa fondu, ne předpověď. Nejde o finanční poradenství.", ""]
    OUT_MD.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "rounds":
        cmd_rounds(a[1], int(a[2]), int(a[3]), a[4] if len(a) > 4 else "/tmp/future")
    elif a and a[0] == "merge":
        cmd_merge(a[1], a[2])
    else:
        print(__doc__)
