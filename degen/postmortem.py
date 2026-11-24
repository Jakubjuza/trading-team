"""🔎 Pitva – proč coin tak rychle spadl, a co se z toho město naučí.

1. Pitva jednoho pádu: posledních ~30 transakcí kolem pádu → kdo prodával (tvůrce, raní kupci/bundly,
   jedna velryba, nebo hodně malých prodejů) a jestli zmizela likvidita poolu.
2. Učení: u každého rozebraného coinu se při rozboru uloží znaky (dev drží hodně, bundly, bez sítí …)
   a po 30 min štítek „rychlý pád“ (MC spadla na ≤ 30 % ceny při rozboru). Znak, u kterého je rychlý pád
   průkazně častější než průměr, se stane NAUČENÝM VETEM – podle předem daného testu, ne podle pocitu:
   aspoň 40 coinů se znakem a dolní mez 95% intervalu (Wilson) podílu pádů > průměr + 10 bodů.
"""
import math

from degen import onchain

CRASH_X = 0.30          # rychlý pád = MC ≤ 30 % ceny při rozboru …
CRASH_MIN = 30          # … do 30 minut
LEARN_MIN_N = 40
LEARN_MARGIN = 0.10
CAND_MIN_N = 15

FEATURES = [
    # klíč, popis
    ("dev5", "tvůrce si při spuštění koupil ≥ 5 %"),
    ("top25", "10 největších drží ≥ 25 %"),
    ("bundle10", "bundly ≥ 10 % v bloku spuštění"),
    ("bund3", "≥ 3 peněženky nakoupily v bloku spuštění"),
    ("funder2", "≥ 2 první kupci mají stejného financovatele"),
    ("nosocial", "žádný web, X ani Telegram"),
    ("serial2", "tvůrce spustil ≥ 2 další coiny za 24 h"),
    ("sellheavy", "prodeje ≥ 60 % nákupů (5 min)"),
    ("young3", "rozbor dřív než 3 min po spuštění"),
    ("tiny8k", "MC při rozboru < 8 000 $"),
    ("pumped3", "už ≥ 3× od první ceny při rozboru"),
]
FEAT_NAME = dict(FEATURES)


def features(tok, creator_launches, now):
    """Znaky známé v okamžiku rozboru (bool nebo None = neznámé)."""
    ch = tok.get("chain") or {}
    m = tok.get("mkt") or {}
    f = ch.get("funders") or {}
    b, s = m.get("buys5"), m.get("sells5")
    age = now - (tok.get("created") or tok.get("first_seen") or now)
    mc, m0 = m.get("mcap"), tok.get("mcap0")
    nb = lambda v, thr: None if v is None else v >= thr  # noqa: E731
    return {
        "dev5": nb(ch.get("dev"), 0.05), "top25": nb(ch.get("top10"), 0.25), "bundle10": nb(ch.get("bundle"), 0.10),
        "bund3": nb(ch.get("bundled_wallets"), 3), "funder2": nb(f.get("shared_max") if f else None, 2),
        "nosocial": not any(tok.get(k) or m.get(k) for k in ("twitter", "telegram", "website")),
        "serial2": nb(creator_launches, 2), "sellheavy": (s / b >= 0.6) if b else None,
        "young3": age < 180, "tiny8k": nb(-mc, -8000) if mc else None, "pumped3": (mc / m0 >= 3) if mc and m0 else None,
    }


def crash_label(tok, now):
    """None = ještě nevíme; True/False po pádu nebo po 30 min."""
    m0, t0 = tok.get("score_mcap"), tok.get("analyzed")
    if not m0 or not t0:
        return None
    for row in tok.get("hist", []):
        ts, mc = row[0], row[1]
        if t0 <= ts <= t0 + CRASH_MIN * 60 and mc <= CRASH_X * m0:
            return True
    return False if now - t0 >= CRASH_MIN * 60 else None


def wilson_low(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - r) / d


def learn(samples):
    """samples = [{"crash": bool, "f": {klíč: bool/None}}] → (průměr, [{key, name, n, k, rate, low, state}])."""
    xs = [x for x in samples if x.get("crash") is not None]
    n0 = len(xs)
    p0 = sum(x["crash"] for x in xs) / n0 if n0 else None
    out = []
    for key, name in FEATURES:
        g = [x for x in xs if (x.get("f") or {}).get(key) is True]
        n, k = len(g), sum(x["crash"] for x in g)
        rate = k / n if n else None
        low = wilson_low(k, n) if n else None
        state = "sleduje se"
        if p0 is not None and n >= LEARN_MIN_N and low > p0 + LEARN_MARGIN:
            state = "veto"
        elif p0 is not None and n >= CAND_MIN_N and rate > p0 + LEARN_MARGIN:
            state = "kandidát"
        out.append({"key": key, "name": name, "n": n, "k": k, "rate": rate, "low": low, "state": state})
    out.sort(key=lambda r: (-(r["rate"] or 0), -r["n"]))
    return p0, n0, out


def learned_vetoes(table, feats):
    return [f"naučené veto: {r['name']} (rychlý pád u {r['k']}/{r['n']})" for r in table
            if r["state"] == "veto" and (feats or {}).get(r["key"]) is True]


# ------------------------------------------------------------- pitva jednoho pádu

def classify(parsed, creator, insiders, liq_hist=None, pump_origin=True, supply=1e9, pools_known=()):
    """parsed = parse_tx výsledky (libovolné pořadí). Vrací {cause, text, shares…}."""
    parsed = [p for p in parsed if p]
    # pool / bonding curve je v (skoro) každém swapu – účet, který je v ≥ 70 % transakcí, je pool, ne prodejce
    seen = {}
    for p in parsed:
        for owner in p["deltas"]:
            seen[owner] = seen.get(owner, 0) + 1
    pools = {o for o, c in seen.items() if len(parsed) >= 4 and c >= 0.7 * len(parsed)} | set(pools_known or ())
    sold = {}
    for p in parsed:
        for owner, d in p["deltas"].items():
            if d < 0 and owner not in pools:
                sold[owner] = sold.get(owner, 0) + (-d)
    total = sum(sold.values())
    liq_drop = None
    if liq_hist:
        vals = [l for l in liq_hist if l]
        if len(vals) >= 2 and max(vals[:-1]) > 0:
            liq_drop = 1 - vals[-1] / max(vals[:-1])
    res = {"sellers": len(sold), "sold_pct": round(total / supply * 100, 2), "dev_share": 0.0, "insider_share": 0.0,
           "top_share": 0.0, "liq_drop": None if liq_drop is None else round(liq_drop, 2)}
    if not pump_origin and liq_drop is not None and liq_drop >= 0.8:
        res.update(cause="lp", text=f"likvidita poolu zmizela o {liq_drop * 100:.0f} % – vybrané LP")
        return res
    if total <= 0:
        res.update(cause="unknown", text="v transakcích kolem pádu nejsou vidět prodeje (data chybí)")
        return res
    dev = sold.get(creator, 0) if creator else 0
    ins = sum(v for o, v in sold.items() if o in insiders and o != creator)
    top_o, top_v = max(sold.items(), key=lambda kv: kv[1])
    res.update(dev_share=round(dev / total, 2), insider_share=round(ins / total, 2), top_share=round(top_v / total, 2),
               top_seller=top_o)
    if dev / total >= 0.3:
        res.update(cause="dev", text=f"prodal tvůrce – {dev / total * 100:.0f} % všech prodejů ({dev / supply * 100:.1f} % zásoby)")
    elif ins / total >= 0.4:
        res.update(cause="insider", text=f"prodali raní kupci / bundly – {ins / total * 100:.0f} % prodejů")
    elif top_v / total >= 0.4:
        res.update(cause="whale", text=f"jedna peněženka prodala {top_v / total * 100:.0f} % všech prodejů")
    else:
        res.update(cause="exodus", text=f"odliv kupců – {len(sold)} prodejců, nikdo výrazně nepřevažuje")
    return res


CAUSES = {"dev": "prodal tvůrce", "insider": "raní kupci / bundly", "whale": "jedna velryba", "exodus": "odliv kupců",
          "lp": "vybraná likvidita", "unknown": "nejasné"}


def run(rpc, tok, n_tx=30, deadline=None):
    """Pitva přes RPC (~n_tx + 1 dotazů). Bere nejnovější transakce mintu (pád se zachytí do ~1 min)."""
    import time
    mint = tok["mint"]
    sigs = [s for s in rpc.sigs(mint, n_tx) if s.get("err") is None]
    parsed = []
    for s in sigs[:n_tx]:
        if deadline and time.time() > deadline:
            break
        parsed.append(onchain.parse_tx(rpc.tx(s["signature"]), mint))
    ch = tok.get("chain") or {}
    insiders = {b["w"] for b in ch.get("buyers") or []}
    liq = [r[2] for r in tok.get("hist", []) if len(r) > 2]
    pump_origin = mint.endswith("pump")
    res = classify(parsed, ch.get("creator") or tok.get("creator"), insiders, liq[-10:], pump_origin,
                   pools_known=[ch["curve_owner"]] if ch.get("curve_owner") else ())
    res["tx"] = len([p for p in parsed if p])
    return res
