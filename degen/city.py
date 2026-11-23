"""🐸 Degen City – jeden průchod (spouští se každých ~30 s ve smyčce v GitHub Actions).

python3 -m degen.city --once [--dry-run]

Kroky: objevit nové coiny → tržní data → předfiltr → on-chain rozbor → skóre a vety → signály 5 strategií
→ papírové účty → štítky výsledků (kalibrace) → učení chytrých peněženek → Telegram → degen/city.json.
Jen papír. Na desk, skener, registr, riziko ani demo účet nesahá.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from degen import onchain, paper, postmortem, safety, score, sources, tg  # noqa: E402

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "cache" / "state.json"
PERSIST = ROOT / "persist.json"
CITY = ROOT / "city.json"
TRADES = ROOT / "trades.jsonl"

STRATS = [
    # klíč, název, budova ve městě, popis
    ("filtr", "Filtr 85+", "🔬 Laboratoř skóre",
     "Nový pump.fun coin s úplným skóre ≥ 85/100 a bez veta, do 15 min od spuštění."),
    ("kopie", "Kopírka peněženek", "🐋 Velrybí věž",
     "Mezi prvními kupci je ověřená chytrá peněženka (≥ 3 rané nákupy, ≥ 2 coiny 5×). Vstup se zpožděním."),
    ("graduace", "Graduace", "🎓 Univerzita",
     "Coin právě opustil bonding curve (PumpSwap/Raydium), likvidita ≥ 20 k$, nákupy převažují."),
    ("shoda", "Shoda signálů", "🤝 Radnice",
     "Kupuje jen, když se během 30 min shodnou aspoň 2 ze 3 strategií výše."),
    ("opice", "Kontrolní opice", "🐒 Klec",
     "Náhodný vzorek coinů z předfiltru. Měřítko: strategie, která neporazí opici, nemá výhodu."),
]
ALERT = {"filtr", "kopie", "graduace", "shoda"}

PRE_MIN_AGE, PRE_MAX_AGE = 90, 12 * 60
PRE_MIN_BUYS, PRE_MIN_MCAP = 12, 6000
TRACK_YOUNG = 20 * 60
TRACK_ANALYZED = 3 * 3600
ANALYZE_PER_CYCLE = 3
FILTER_MIN = 85
FILTER_MAX_AGE = 15 * 60
LABEL_TP, LABEL_SL, LABEL_MIN = 2.0, 0.6, 120
RUNNER_X = 5.0
MAX_ALERTS_HOUR = 8


# ------------------------------------------------------------------ stav

def load_state():
    for p in (STATE, PERSIST):
        if p.exists():
            try:
                st = json.loads(p.read_text())
                st.setdefault("tokens", {})
                return st
            except Exception:
                pass
    return {}


def init_state(st):
    st.setdefault("tokens", {})
    st.setdefault("creators", {})
    st.setdefault("wallets", {})
    st.setdefault("labels", [])
    st.setdefault("stack", [])
    st.setdefault("tape", [])
    st.setdefault("hourly", {})
    st.setdefault("alerts", [])
    st.setdefault("cycle", 0)
    st.setdefault("pitva", [])
    st.setdefault("pitva_queue", [])
    st.setdefault("pitva_counts", {})
    st.setdefault("crash_samples", [])
    st.setdefault("learned", [])
    st.setdefault("learn_log", [])
    st.setdefault("safety_stats", {"checked": 0, "vetoed": 0, "unverified": 0, "reasons": {}})
    acc = st.setdefault("accounts", {})
    for k, *_ in STRATS:
        acc.setdefault(k, paper.new_account(k))
    return st


def hour_bucket(st, now):
    k = time.strftime("%Y-%m-%dT%H", time.gmtime(now))
    b = st["hourly"].setdefault(k, {"launches": 0, "analyzed": 0, "passed": 0, "vetoed": 0, "signals": 0, "trades": 0})
    if len(st["hourly"]) > 50:
        for old in sorted(st["hourly"])[:-50]:
            del st["hourly"][old]
    return b


def age(tok, now):
    return now - (tok.get("created") or tok["first_seen"])


# ------------------------------------------------------------------ kroky

def discover(st, now, cycle):
    found = sources.pump_latest()
    if not found or cycle % 4 == 0:
        found += sources.gecko_new(2 if not found else 1)
    hb = hour_bucket(st, now)
    new = 0
    for t in found:
        if t["mint"] in st["tokens"]:
            old = st["tokens"][t["mint"]]
            for k in ("twitter", "telegram", "website"):
                old[k] = old.get(k) or t.get(k)
            old["replies"] = max(old.get("replies") or 0, t.get("replies") or 0)
            if t.get("creator") and not old.get("creator"):
                old["creator"] = t["creator"]
            continue
        if t.get("created") and now - t["created"] > 2 * 3600 and t["src"] == "pump":
            continue
        t["first_seen"] = now
        t["mcap0"] = None            # první cena z DexScreeneru (stejná definice MC jako dál)
        t["hist"] = []
        t["peak"] = 0
        t["signals"] = {}
        st["tokens"][t["mint"]] = t
        new += 1
        if t.get("creator"):
            c = st["creators"].setdefault(t["creator"], [])
            c.append(int(t.get("created") or now))
    hb["launches"] += new
    # tvůrci: jen posledních 24 h
    for c in list(st["creators"]):
        st["creators"][c] = [x for x in st["creators"][c] if now - x < 86400]
        if not st["creators"][c]:
            del st["creators"][c]
    return new


def open_mints(st):
    out = set()
    for a in st["accounts"].values():
        out |= set(a["open"]) | set(a["pending"])
    return out


def track(st, now):
    held = open_mints(st)
    mints = [m for m, t in st["tokens"].items()
             if m in held or age(t, now) < TRACK_YOUNG
             or (t.get("analyzed") and now - t["analyzed"] < TRACK_ANALYZED)
             or (t.get("grad_seen") and now - t["grad_seen"] < 3600)]
    mints = sorted(mints, key=lambda m: (m not in held, -st["tokens"][m]["first_seen"]))[:900]
    mk = sources.dex_tokens(mints)
    for m, v in mk.items():
        t = st["tokens"][m]
        t["mkt"] = v
        if not t.get("mcap0"):
            t["mcap0"] = v["mcap"]
        t["peak"] = max(t.get("peak") or 0, v["mcap"])
        if not t.get("created") and v.get("created"):
            t["created"] = v["created"]
        if not t.get("symbol"):
            t["symbol"], t["name"] = v["symbol"], v["name"]
        if v["graduated"] and not t.get("grad_seen"):
            t["grad_seen"] = now
            t["grad_at"] = v.get("grad_at") or now
        h = t.setdefault("hist", [])
        if not h or now - h[-1][0] >= 60:
            h.append([int(now), round(v["mcap"]), round(v["liq"]) if v.get("liq") else None])
            if len(h) > 200:
                t["hist"] = h[-200:]
    return mk


def creator_count(st, tok):
    c = tok.get("creator")
    return len(st["creators"].get(c, [])) - 1 if c else None


def rescore(st, tok, now):
    ch = score.channels(tok, tok.get("mkt"), tok.get("chain"), creator_count(st, tok))
    s, complete = score.total(ch)
    tok["ch"] = {k: (None if v is None else round(v, 2)) for k, v in ch.items()}
    tok["score"], tok["complete"] = s, complete
    tok["vetoes"] = (score.vetoes(tok.get("chain"), creator_count(st, tok))
                     + postmortem.learned_vetoes(st.get("learned") or [], tok.get("feat"))
                     + list((tok.get("safety") or {}).get("vetoes") or []))
    return s


def push_stack(st, tok, verdict, reason, now):
    st["stack"] = (st["stack"] + [{
        "t": int(now), "mint": tok["mint"], "symbol": tok.get("symbol") or "?", "score": tok.get("score"),
        "complete": tok.get("complete"), "verdict": verdict, "reason": reason, "ch": tok.get("ch"),
        "mcap": round((tok.get("mkt") or {}).get("mcap") or 0), "age_min": round(age(tok, now) / 60, 1),
    }])[-60:]


def analyze_step(st, rpc, now, deadline=None):
    hb = hour_bucket(st, now)
    per_cycle = ANALYZE_PER_CYCLE if rpc.kind == "helius" else 1
    deadline = deadline or (time.time() + 40)
    cands = []
    for t in st["tokens"].values():
        if t.get("analyzed") or t.get("skip"):
            continue
        m = t.get("mkt") or {}
        a = age(t, now)
        grad_new = t.get("grad_seen") and now - t["grad_seen"] < 1800
        if grad_new or (PRE_MIN_AGE <= a <= PRE_MAX_AGE and (m.get("buys5") or 0) >= PRE_MIN_BUYS
                        and (m.get("buys5") or 0) >= (m.get("sells5") or 0) and (m.get("mcap") or 0) >= PRE_MIN_MCAP):
            cands.append(t)
    cands.sort(key=lambda t: -((t.get("mkt") or {}).get("buys5") or 0))
    done = 0
    for t in cands:
        t["prefilter"] = t.get("prefilter") or now
        # kontrolní opice: deterministický náhodný vzorek z předfiltru
        if int(hashlib.sha1(t["mint"].encode()).hexdigest(), 16) % 25 == 0:
            t["signals"].setdefault("opice", now)
        if done >= per_cycle or rpc.left() < 60 or time.time() > deadline:
            continue
        chain = onchain.analyze(rpc, t, deadline=deadline)
        t["analyzed"] = now
        t["chain"] = chain or {}
        t["score_mcap"] = (t.get("mkt") or {}).get("mcap")
        t["feat"] = postmortem.features(t, creator_count(st, t), now)
        done += 1
        hb["analyzed"] += 1
        rescore(st, t, now)
        if t["vetoes"]:
            hb["vetoed"] += 1
            push_stack(st, t, "VETO", t["vetoes"][0], now)
        elif t["score"] >= FILTER_MIN and t["complete"]:
            hb["passed"] += 1
            push_stack(st, t, "BUY", f"skóre {t['score']} ≥ {FILTER_MIN}", now)
        else:
            why = "neúplná data" if not t["complete"] else f"skóre {t['score']} < {FILTER_MIN}"
            push_stack(st, t, "SKIP", why, now)
    return done


def smart_set(st):
    out = {}
    for w, s in st["wallets"].items():
        if s["n"] >= 3 and s["wins"] >= 2 and (s["wins"] + 1) / (s["n"] + 2) >= 0.5:
            out[w] = s
    return out


def signals_step(st, now):
    smart = smart_set(st)
    sig = []
    for t in st["tokens"].values():
        a = age(t, now)
        m = t.get("mkt") or {}
        if t.get("analyzed"):
            if a <= FILTER_MAX_AGE:
                rescore(st, t, now)
            veto = bool(t.get("vetoes"))
            if not veto and t.get("complete") and (t.get("score") or 0) >= FILTER_MIN and a <= FILTER_MAX_AGE:
                t["signals"].setdefault("filtr", now)
            hits = [b["w"] for b in (t.get("chain") or {}).get("buyers", []) if b["w"] in smart]
            if hits and not veto and a <= 20 * 60:
                t["signals"].setdefault("kopie", now)
                t["smart_hits"] = hits[:5]
        if t.get("grad_seen") and m.get("graduated"):
            ga = now - (t.get("grad_at") or t["grad_seen"])
            if (ga <= 1800 and (m.get("liq") or 0) >= 20000 and (m.get("buys5") or 0) >= 20
                    and m["buys5"] >= 1.3 * (m.get("sells5") or 0) and (m.get("vol1h") or 0) >= 30000
                    and not t.get("vetoes")):
                t["signals"].setdefault("graduace", now)
        recent = [k for k in ("filtr", "kopie", "graduace") if now - t["signals"].get(k, -1e9) <= 1800]
        if len(recent) >= 2:
            t["signals"].setdefault("shoda", now)
        for k, ts in t["signals"].items():
            if now - ts < 90:
                sig.append((k, t))
    return sig


def safety_gate(st, rpc, t, key, now, deadline):
    """True = smí se koupit. Opice se kontroluje taky (měření), ale nákup se jí neblokuje."""
    if "safety" not in t:
        if rpc.left() < 10 or time.time() > deadline:
            return key == "opice"
        t["safety"] = safety.check(rpc, t)
        ss = st["safety_stats"]
        ss["checked"] += 1
        if not t["safety"]["checked"]:
            ss["unverified"] += 1
        if t["safety"]["vetoes"]:
            ss["vetoed"] += 1
            for v in t["safety"]["vetoes"]:
                k = v.split(" – ")[0].split(" (")[0][:60]
                ss["reasons"][k] = ss["reasons"].get(k, 0) + 1
        rescore(st, t, now)
    if key == "opice":
        return True
    sf = t["safety"]
    if sf["vetoes"] or not sf["checked"]:
        if not t.get("safety_logged"):
            t["safety_logged"] = True
            hour_bucket(st, now)["vetoed"] += 1
            push_stack(st, t, "VETO", "🛡️ " + (sf["vetoes"][0] if sf["vetoes"] else "bezpečnost mintu nejde ověřit"), now)
        return False
    return not t.get("vetoes")


def trade_step(st, mk, sig, now, rpc=None, deadline=None):
    marks = {m: v["mcap"] for m, v in mk.items()}
    hb = hour_bucket(st, now)
    events, closed_all = [], []
    for key, *_ in STRATS:
        acc = st["accounts"][key]
        for p in paper.fill_pending(acc, mk, now):
            st["tape"].append({"t": int(now), "kind": "buy", "strat": key, "symbol": p["symbol"],
                               "mint": p["mint"], "mcap": round(p["fill_mcap"]), "usd": p["invested"]})
        closed = paper.manage(acc, mk, key, now)
        for c in closed:
            c["strat"] = key
            st["tape"].append({"t": int(now), "kind": "sell", "strat": key, "symbol": c["symbol"], "mint": c["mint"],
                               "pnl": c["pnl"], "ret": c["ret"], "why": c["why"]})
            closed_all.append(c)
            if c["ret"] <= -30:
                st["pitva_queue"].append({"mint": c["mint"], "t": int(now), "why": f"{dict((k, n) for k, n, *_ in STRATS)[key]} {c['ret']:.0f} %",
                                          "strat": key, "ret": c["ret"]})
    deadline = deadline or (time.time() + 20)
    for key, t in sig:
        acc = st["accounts"][key]
        if t["mint"] in acc["open"] or t["mint"] in acc["pending"] or t["mint"] in acc.get("done", {}):
            continue
        if rpc is not None and not safety_gate(st, rpc, t, key, now, deadline):
            continue
        if paper.order(acc, t["mint"], t.get("symbol") or "?", key, t.get("mkt"), now, t.get("score")):
            hb["signals"] += 1
            events.append((key, t))
    for key, *_ in STRATS:
        paper.mark_curve(st["accounts"][key], marks, now)
    st["tape"] = st["tape"][-120:]
    hb["trades"] += len(closed_all)
    return events, closed_all


def label_step(st, now):
    """Trojitá bariéra od okamžiku skóre: +100 % → TP, −40 % → SL, jinak po 120 min TIME. Měří, jestli skóre něco umí."""
    for t in st["tokens"].values():
        if not t.get("analyzed") or t.get("label") or not t.get("score_mcap"):
            continue
        m0 = t["score_mcap"]
        lab = None
        for row in t.get("hist", []):
            ts, mc = row[0], row[1]
            if ts < t["analyzed"]:
                continue
            if mc >= LABEL_TP * m0:
                lab = "TP"
                break
            if mc <= LABEL_SL * m0:
                lab = "SL"
                break
        if not lab and now - t["analyzed"] >= LABEL_MIN * 60:
            lab = "TIME"
        if not lab:
            continue
        t["label"] = lab
        st["labels"] = (st["labels"] + [{"t": int(now), "score": t.get("score"), "complete": t.get("complete"),
                                          "veto": bool(t.get("vetoes")), "ch": t.get("ch"), "label": lab}])[-5000:]


def crash_step(st, now):
    """Štítek „rychlý pád“ pro učení + zařazení pádů do pitvy (max 12 za hodinu)."""
    recent = [q for q in st["pitva"][-40:] if now - q["t"] < 3600] + [q for q in st["pitva_queue"] if now - q["t"] < 3600]
    for t in st["tokens"].values():
        if not t.get("analyzed") or "crash" in t or not t.get("feat"):
            continue
        c = postmortem.crash_label(t, now)
        if c is None:
            continue
        t["crash"] = c
        st["crash_samples"] = (st["crash_samples"] + [{"t": int(now), "crash": c, "f": t["feat"]}])[-4000:]
        if c and len(recent) < 12 and not any(q["mint"] == t["mint"] for q in st["pitva_queue"]):
            st["pitva_queue"].append({"mint": t["mint"], "t": int(now), "why": "rychlý pád po rozboru"})
            recent.append(st["pitva_queue"][-1])
    old = {r["key"]: r["state"] for r in st.get("learned") or []}
    p0, n0, table = postmortem.learn(st["crash_samples"])
    st["learned"], st["learn_base"] = table, {"p0": p0, "n": n0}
    changes = []
    for r in table:
        if r["state"] != old.get(r["key"], "sleduje se") and (r["state"] == "veto" or old.get(r["key"]) == "veto"):
            changes.append(r)
            st["learn_log"] = (st["learn_log"] + [{"t": int(now), "key": r["key"], "name": r["name"],
                                                   "from": old.get(r["key"], "sleduje se"), "to": r["state"],
                                                   "n": r["n"], "k": r["k"], "p0": p0}])[-50:]
    return changes


def pitva_step(st, rpc, now, deadline):
    done = 0
    keep = []
    for q in st["pitva_queue"]:
        t = st["tokens"].get(q["mint"])
        if not t or now - q["t"] > 3600:
            continue
        if done >= 1 or rpc.left() < 60 or time.time() > deadline - 5:
            keep.append(q)
            continue
        res = postmortem.run(rpc, t, deadline=deadline)
        done += 1
        sf = t.get("safety") or {}
        rec = {"t": int(now), "mint": q["mint"], "symbol": t.get("symbol") or "?", "why": q["why"], "strat": q.get("strat"),
               "ret": q.get("ret"), "cause": res["cause"], "text": res["text"], "sellers": res["sellers"],
               "dev_share": res["dev_share"], "insider_share": res["insider_share"], "top_share": res["top_share"],
               "liq_drop": res["liq_drop"], "tx": res["tx"], "score": t.get("score"),
               "age_min": round(age(t, now) / 60, 1),
               "peak_x": round((t.get("peak") or 0) / t["mcap0"], 2) if t.get("mcap0") else None,
               "feat": [k for k, v in (t.get("feat") or {}).items() if v],
               "safety": (sf.get("vetoes") or []) + (["RugCheck: " + ", ".join(sf["danger"][:3])] if sf.get("danger") else [])}
        st["pitva"] = (st["pitva"] + [rec])[-200:]
        st["pitva_counts"][res["cause"]] = st["pitva_counts"].get(res["cause"], 0) + 1
    st["pitva_queue"] = keep[-50:]
    return done


def wallet_step(st, now):
    """Po 2 h od rozboru: byl coin „runner“ (vrchol ≥ 5× první ceny)? Zapíše výsledek všem raným kupcům."""
    for t in st["tokens"].values():
        if not t.get("analyzed") or t.get("wallets_done") or now - t["analyzed"] < LABEL_MIN * 60:
            continue
        t["wallets_done"] = True
        buyers = (t.get("chain") or {}).get("buyers") or []
        if not buyers or not t.get("mcap0"):
            continue
        win = (t.get("peak") or 0) >= RUNNER_X * t["mcap0"]
        for b in buyers[:20]:
            s = st["wallets"].setdefault(b["w"], {"n": 0, "wins": 0, "first": int(now)})
            s["n"] += 1
            s["wins"] += int(win)
            s["last"] = int(now)
            if win:
                s["last_win"] = t.get("symbol")
    if len(st["wallets"]) > 30000:
        ranked = sorted(st["wallets"].items(), key=lambda kv: (kv[1]["wins"], kv[1]["last"]), reverse=True)
        st["wallets"] = dict(ranked[:25000])


def prune(st, now):
    held = open_mints(st)
    for m in list(st["tokens"]):
        t = st["tokens"][m]
        if m in held:
            continue
        a = now - t["first_seen"]
        if (not t.get("analyzed") and not t.get("grad_seen") and a > 30 * 60) or a > 4 * 3600:
            if t.get("analyzed") and not (t.get("label") and t.get("wallets_done")):
                continue
            del st["tokens"][m]


# ------------------------------------------------------------------ Telegram

def fmt_usd(x):
    if x is None:
        return "?"
    return f"${x / 1e6:.2f}M" if x >= 1e6 else f"${x / 1e3:.1f}k" if x >= 1e3 else f"${x:.0f}"


def alert(st, events, now, dry):
    st["alerts"] = [a for a in st["alerts"] if now - a < 3600]
    by = {}
    for key, t in events:
        if key in ALERT:
            by.setdefault(t["mint"], (t, []))[1].append(key)
    names = {k: n for k, n, *_ in STRATS}
    for mint, (t, keys) in by.items():
        if len(st["alerts"]) >= MAX_ALERTS_HOUR:
            print("limit upozornění/h – přeskočeno", t.get("symbol"))
            continue
        m = t.get("mkt") or {}
        ch = t.get("ch") or {}
        chs = " · ".join(f"{n.split()[0]} {ch[k]:.1f}" for k, n, _ in score.CHANNELS if ch.get(k) is not None)
        chain = t.get("chain") or {}
        lines = [
            f"🐸 <b>DEGEN CITY · {tg.h(' + '.join(names[k] for k in keys))}</b>",
            f"<b>${tg.h(t.get('symbol') or '?')}</b> {tg.h(t.get('name') or '')} · MC {fmt_usd(m.get('mcap'))}"
            f" · věk {age(t, now) / 60:.0f} min",
            f"Skóre <b>{t.get('score', '–')}/100</b>{'' if t.get('complete') else ' (neúplné)'}"
            + (f" · top10 {chain['top10'] * 100:.0f} %" if chain.get("top10") is not None else "")
            + (f" · bundly {chain['bundle'] * 100:.0f} %" if chain.get("bundle") is not None else ""),
            f"Kanály: {tg.h(chs)}" if chs else "",
            f"Nákupy/prodeje 5 min: {m.get('buys5', 0)}/{m.get('sells5', 0)} · objem 1 h {fmt_usd(m.get('vol1h'))}"
            + (f" · likvidita {fmt_usd(m['liq'])}" if m.get("liq") else ""),
            ("🐋 Chytré peněženky: " + ", ".join(w[:4] + "…" + w[-4:] for w in t.get("smart_hits", []))) if t.get("smart_hits") else "",
            "Papír: vstup na další ceně, stop −40 %, ½ na +100 %, zbytek trailing 35 %, max 2 h.",
            f"CA: <code>{tg.h(mint)}</code>",
            "⚠️ Papírový test, ne rada. Většina meme coinů jde k nule – ruční nákup jen s penězi, které můžeš ztratit.",
        ]
        btns = tg.links(mint) + ([("🐸 Degentown", os.environ["DEGEN_PAGE_URL"])] if os.environ.get("DEGEN_PAGE_URL") else [])
        tg.send("\n".join(x for x in lines if x), btns) if not dry else print("\n".join(lines))
        st["alerts"].append(now)


def daily_summary(st, now, dry):
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    if time.gmtime(now).tm_hour < 19 or st.get("summary_day") == day:
        return
    st["summary_day"] = day
    rows = []
    for key, name, *_ in STRATS:
        a = st["accounts"][key]
        eq = paper.equity(a, {})
        rows.append(f"{name}: {eq:,.0f} $ ({(eq / paper.START - 1) * 100:+.1f} %) · {a['n']} obchodů, "
                    f"{(a['wins'] / a['n'] * 100 if a['n'] else 0):.0f} % výher · otevřeno {len(a['open'])}")
    hrs = [v for k, v in st["hourly"].items()]
    tot = {k: sum(h.get(k, 0) for h in hrs[-24:]) for k in ("launches", "analyzed", "passed", "vetoed")}
    text = ("🐸 <b>DEGEN CITY · denní přehled</b>\n"
            f"24 h: {tot['launches']} coinů, {tot['analyzed']} rozborů, {tot['passed']} prošlo, {tot['vetoed']} veto\n"
            + "\n".join(tg.h(r) for r in rows)
            + f"\nChytrých peněženek: {len(smart_set(st))}\nPapír – jen měření, ne rada.")
    tg.send(text) if not dry else print(text)


# ------------------------------------------------------------------ výstup

def calibration(st):
    buckets = [("0–49", 0, 50), ("50–69", 50, 70), ("70–84", 70, 85), ("85+", 85, 101)]
    labs = [x for x in st["labels"] if x.get("score") is not None]
    out = []
    for name, lo, hi in buckets:
        xs = [x for x in labs if lo <= x["score"] < hi and not x.get("veto")]
        out.append({"range": name, "n": len(xs), **{k: sum(x["label"] == k for x in xs) for k in ("TP", "SL", "TIME")}})
    vet = [x for x in labs if x.get("veto")]
    out.append({"range": "veto", "n": len(vet), **{k: sum(x["label"] == k for x in vet) for k in ("TP", "SL", "TIME")}})
    chans = []
    for k, n, w in score.CHANNELS:
        xs = [x for x in labs if (x.get("ch") or {}).get(k) is not None]
        hi = [x for x in xs if x["ch"][k] >= 0.5]
        lo = [x for x in xs if x["ch"][k] < 0.5]
        rate = lambda g: (sum(x["label"] == "TP" for x in g) / len(g)) if g else None  # noqa: E731
        chans.append({"key": k, "name": n, "weight": w, "n_hi": len(hi), "n_lo": len(lo),
                      "tp_hi": rate(hi), "tp_lo": rate(lo),
                      "lift": (rate(hi) - rate(lo)) if hi and lo else None})
    return {"buckets": out, "channels": chans, "n": len(labs),
            "rule": f"TP = +{(LABEL_TP - 1) * 100:.0f} % dřív než {(LABEL_SL - 1) * 100:.0f} %, TIME = ani jedno za {LABEL_MIN} min"}


def build_city(st, rpc, now, page_url=None):
    hrs = [st["hourly"][k] for k in sorted(st["hourly"])][-24:]
    tot = {k: sum(h.get(k, 0) for h in hrs) for k in ("launches", "analyzed", "passed", "vetoed", "signals", "trades")}
    marks = {m: (t.get("mkt") or {}).get("mcap") for m, t in st["tokens"].items() if t.get("mkt")}
    accs = []
    for key, name, bld, desc in STRATS:
        a = st["accounts"][key]
        eq = paper.equity(a, marks)
        opens = []
        for p in a["open"].values():
            mc = marks.get(p["mint"]) or p["last_mcap"]
            opens.append({"mint": p["mint"], "symbol": p["symbol"], "t": int(p["t_open"]), "invested": p["invested"],
                          "remaining": p["remaining"], "entry_mcap": round(p["fill_mcap"]), "mcap": round(mc),
                          "ret": round((mc / p["entry_mcap"] - 1) * 100, 1), "tp1": p["tp1"], "score": p.get("score")})
        tr = a["trades"]
        accs.append({"key": key, "name": name, "building": bld, "desc": desc, "start": paper.START,
                     "equity": round(eq, 2), "cash": round(a["cash"], 2), "realized": round(a["realized"], 2),
                     "fees": round(a["fees"], 2), "n": a["n"], "wins": a["wins"], "open": opens,
                     "pending": len(a["pending"]), "curve": a["curve"][-200:], "trades": tr[-15:][::-1],
                     "best": max((t["ret"] for t in tr), default=None), "worst": min((t["ret"] for t in tr), default=None)})
    feed = sorted(st["tokens"].values(), key=lambda t: -t["first_seen"])[:30]
    feed = [{"mint": t["mint"], "symbol": t.get("symbol") or "?", "mcap": round((t.get("mkt") or {}).get("mcap") or t.get("mcap0") or 0),
             "x": round(((t.get("mkt") or {}).get("mcap") or 0) / t["mcap0"], 2) if t.get("mcap0") and t.get("mkt") else None,
             "age_min": round(age(t, now) / 60, 1), "score": t.get("score"), "veto": bool(t.get("vetoes")),
             "grad": bool(t.get("grad_seen"))} for t in feed]
    orb = []
    for t in sorted(st["tokens"].values(), key=lambda t: -t["first_seen"])[:400]:
        orb.append([round(age(t, now) / 60, 1), t.get("score"), 1 if t.get("vetoes") else 0,
                    round(math.log10(max(((t.get("mkt") or {}).get("mcap") or t.get("mcap0") or 1), 1)), 2),
                    1 if t.get("signals") else 0])
    smart = smart_set(st)
    wl = sorted(st["wallets"].items(), key=lambda kv: ((kv[1]["wins"] + 1) / (kv[1]["n"] + 2), kv[1]["n"]), reverse=True)
    wallets = [{"w": w, "n": s["n"], "wins": s["wins"], "smart": w in smart, "last": s.get("last"),
                "last_win": s.get("last_win")} for w, s in wl[:25] if s["n"] >= 2]
    return {
        "updated": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(now)),
        "ts": int(now), "page": page_url,
        "sources": {**sources.STATUS, "rpc_kind": rpc.kind if rpc else None,
                    "rpc_used": rpc.b["used"] if rpc else 0, "rpc_limit": rpc.limit if rpc else 0},
        "totals24": tot, "tracked": len(st["tokens"]), "wallets_known": len(st["wallets"]), "smart_n": len(smart),
        "accounts": accs, "stack": st["stack"][-20:][::-1], "tape": st["tape"][-40:][::-1], "feed": feed,
        "orb": orb, "wallets": wallets, "calibration": calibration(st),
        "hourly": [{"h": k, **st["hourly"][k]} for k in sorted(st["hourly"])][-24:],
        "rules": {"filter_min": FILTER_MIN, "weights": [{"key": k, "name": n, "weight": w} for k, n, w in score.CHANNELS],
                  "veto": {"bundle": score.VETO_BUNDLE, "top10": score.VETO_TOP10,
                           "shared_funder": score.VETO_SHARED_FUNDER, "serial": score.VETO_SERIAL},
                  "paper": {"start": paper.START, "size": paper.RISK_FRAC, "fee": paper.FEE, "tx": paper.TX_USD,
                            "max_open": paper.MAX_OPEN, "exits": paper.RULES}},
        "pitva": {
            "recent": st["pitva"][-25:][::-1], "counts": st["pitva_counts"], "queue": len(st["pitva_queue"]),
            "causes": postmortem.CAUSES,
            "learn": {"p0": (st.get("learn_base") or {}).get("p0"), "n": (st.get("learn_base") or {}).get("n", 0),
                      "rule": f"rychlý pád = MC ≤ {postmortem.CRASH_X * 100:.0f} % ceny při rozboru do {postmortem.CRASH_MIN} min; "
                              f"veto, když ≥ {postmortem.LEARN_MIN_N} coinů se znakem a dolní mez 95% intervalu > průměr + "
                              f"{postmortem.LEARN_MARGIN * 100:.0f} bodů",
                      "table": st.get("learned") or []},
            "log": st["learn_log"][-10:][::-1],
            "safety": st["safety_stats"],
        },
        "note": "Jen papírové obchody a měření. Ne finanční poradenství.",
    }


def persist(st):
    """Malá záloha do gitu (přežije ztrátu cache): účty, peněženky s ≥ 2 nákupy, štítky, tvůrci ne."""
    keep = {k: v for k, v in st.items() if k in ("accounts", "labels", "hourly", "stack", "tape", "summary_day", "pitva",
                                                "pitva_counts", "crash_samples", "learned", "learn_base", "learn_log",
                                                "safety_stats")}
    keep["wallets"] = {w: s for w, s in st["wallets"].items() if s["n"] >= 2}
    keep["labels"] = st["labels"][-3000:]
    keep["tokens"] = {m: t for m, t in st["tokens"].items() if m in open_mints(st)}
    PERSIST.write_text(json.dumps(keep, separators=(",", ":")))


def run_once(dry=False, now=None):
    now = time.time() if now is None else now
    st = init_state(load_state())
    st["cycle"] += 1
    t0 = time.time()
    rpc = sources.Rpc(st)
    discover(st, now, st["cycle"])
    t1 = time.time()
    mk = track(st, now)
    t2 = time.time()
    analyze_step(st, rpc, now, deadline=t0 + 45)
    t3 = time.time()
    sig = signals_step(st, now)
    events, closed = trade_step(st, mk, sig, now, rpc, deadline=t0 + 55)
    label_step(st, now)
    learned_changes = crash_step(st, now)
    pitva_step(st, rpc, now, deadline=t0 + 70)
    wallet_step(st, now)
    alert(st, events, now, dry)
    for r in learned_changes:
        msg = (f"🐸 <b>DEGENTOWN · {'nové naučené veto' if r['state'] == 'veto' else 'naučené veto zrušeno'}</b>\n{tg.h(r['name'])}\n"
               f"Rychlý pád u {r['k']}/{r['n']} coinů se znakem ({(r['rate'] or 0) * 100:.0f} %) proti průměru "
               f"{(st['learn_base']['p0'] or 0) * 100:.0f} %. Platí jen pro papírové účty.")
        tg.send(msg) if not dry else print(msg)
    daily_summary(st, now, dry)
    prune(st, now)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, separators=(",", ":")))
    if closed:
        with TRADES.open("a") as fh:
            for c in closed:
                fh.write(json.dumps({k: c[k] for k in ("strat", "mint", "symbol", "open", "close", "pnl", "ret",
                                                       "why", "score", "peak_x", "entry_mcap")}, ensure_ascii=False) + "\n")
    page = os.environ.get("DEGEN_PAGE_URL") or None
    city = build_city(st, rpc, now, page)
    CITY.write_text(json.dumps(city, ensure_ascii=False, separators=(",", ":")))
    if st["cycle"] % 10 == 0 or closed or events:
        persist(st)
    print(f"cyklus {st['cycle']}: sledováno {len(st['tokens'])}, trh {len(mk)}, signály {len(sig)}, "
          f"příkazy {len(events)}, uzavřeno {len(closed)}, RPC {rpc.b['used']}/{rpc.limit} ({rpc.kind}), "
          f"zdroje {sources.STATUS}, čas objev {t1 - t0:.0f}s trh {t2 - t1:.0f}s rozbor {t3 - t2:.0f}s celkem {time.time() - t0:.0f}s")
    return city


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run_once(dry=a.dry_run or bool(os.environ.get("DRY_RUN")))


if __name__ == "__main__":
    main()
