"""On-chain rozbor tokenu: první kupci, bundly v bloku spuštění, koncentrace držitelů, společné financování peněženek.

Parsovací funkce jsou čisté (testy v degen/tests). Jeden rozbor stojí ~35–40 RPC dotazů.
"""
import time
from collections import Counter

EARLY_TX = 25          # kolik nejstarších transakcí mintu projít
FUNDER_WALLETS = 5     # u kolika prvních kupců hledat, kdo je financoval
FRESH_LIMIT = 30       # peněženka s méně podpisy je „čerstvá“ → najdeme první příchozí SOL


def _keys(tx):
    msg = ((tx or {}).get("transaction") or {}).get("message") or {}
    out = []
    for k in msg.get("accountKeys") or []:
        out.append(k.get("pubkey") if isinstance(k, dict) else k)
    return out


def parse_tx(tx, mint):
    """→ {slot, time, signer, deltas{owner: změna počtu tokenů}} nebo None (chybná transakce)."""
    if not tx:
        return None
    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return None
    pre, post = {}, {}
    for side, store in (("preTokenBalances", pre), ("postTokenBalances", post)):
        for b in meta.get(side) or []:
            if b.get("mint") != mint:
                continue
            owner = b.get("owner") or f"idx{b.get('accountIndex')}"
            amt = ((b.get("uiTokenAmount") or {}).get("uiAmount")) or 0
            store[owner] = store.get(owner, 0) + float(amt)
    deltas = {o: post.get(o, 0) - pre.get(o, 0) for o in set(pre) | set(post)}
    deltas = {o: d for o, d in deltas.items() if abs(d) > 1e-9}
    keys = _keys(tx)
    return {"slot": tx.get("slot"), "time": tx.get("blockTime"), "signer": keys[0] if keys else None,
            "deltas": deltas}


def early_flow(parsed, creator=None, supply=1e9):
    """Z chronologicky seřazených parse_tx spočítá kupce, bundly a nákup tvůrce."""
    parsed = [p for p in parsed if p]
    if not parsed:
        return None
    first = parsed[0]
    create_slot = first["slot"]
    creator = creator or first["signer"]
    # bonding curve dostane při vytvoření skoro celou zásobu → poznáme ji podle obřího přírůstku
    curve = None
    big = [(d, o) for o, d in first["deltas"].items() if d > 0.5 * supply]
    if big:
        curve = max(big)[1]
    buyers, seen = [], set()
    bundle_amt = dev_amt = 0.0
    for p in parsed:
        for owner, d in sorted(p["deltas"].items(), key=lambda x: -x[1]):
            if owner == curve or d <= 0:
                continue
            if p["slot"] == create_slot:
                bundle_amt += d
                if owner == creator:
                    dev_amt += d
            if owner not in seen and owner != creator:
                seen.add(owner)
                buyers.append({"w": owner, "slot": p["slot"], "amt": round(d / supply * 100, 3)})
    return {"creator": creator, "curve_owner": curve, "create_slot": create_slot,
            "bundle_share": bundle_amt / supply, "dev_share": dev_amt / supply,
            "bundled_wallets": len({b["w"] for b in buyers if b["slot"] == create_slot}),
            "buyers": buyers[:30]}


def holder_share(largest, supply, exclude=(), drop_vault=True):
    """Podíl 10 největších držitelů (bez bonding curve / poolu). Vrací (podíl, vyřazené účty)."""
    if not largest or not supply:
        return None, []
    acc = [a for a in largest if a["address"] not in exclude]
    dropped = [a["address"] for a in largest if a["address"] in exclude]
    if drop_vault and not dropped and acc and acc[0]["amount"] > 0.2 * supply:
        dropped.append(acc[0]["address"])        # největší účet = curve / pool vault (heuristika)
        acc = acc[1:]
    top = sum(a["amount"] for a in acc[:10])
    return top / supply, dropped


def funder_of(tx, wallet):
    """Kdo poslal SOL do peněženky v dané transakci (system transfer, i vnořený)."""
    if not tx:
        return None
    ins = list((((tx.get("transaction") or {}).get("message") or {}).get("instructions")) or [])
    for inner in ((tx.get("meta") or {}).get("innerInstructions")) or []:
        ins += inner.get("instructions") or []
    best = None
    for i in ins:
        parsed = i.get("parsed") if isinstance(i, dict) else None
        if not isinstance(parsed, dict):
            continue
        if parsed.get("type") in ("transfer", "transferWithSeed", "createAccount"):
            info = parsed.get("info") or {}
            dest = info.get("destination") or info.get("newAccount")
            lam = info.get("lamports") or 0
            if dest == wallet and lam and (best is None or lam > best[1]):
                best = (info.get("source"), lam)
    return best[0] if best else None


def funder_stats(funders, creator):
    vals = [f for f in funders.values() if f]
    c = Counter(vals)
    shared = max(c.values()) if c else 0
    return {"checked": len(funders), "known": len(vals), "shared_max": shared,
            "creator_funded": bool(creator and creator in vals)}


def analyze(rpc, tok, with_funders=True, deadline=None):
    """Plný rozbor; vrací dict nebo None, když RPC nedává data."""
    mint = tok["mint"]
    sigs = [s for s in rpc.sigs(mint, 1000) if s.get("err") is None]
    if not sigs:
        return None
    full_history = len(sigs) < 1000
    oldest = list(reversed(sigs))[:EARLY_TX]
    parsed = [parse_tx(rpc.tx(s["signature"]), mint) for s in oldest]
    supply_r = rpc.call("getTokenSupply", [mint])
    supply = None
    if supply_r:
        supply = float(((supply_r.get("value") or {}).get("uiAmount")) or 0) or None
    supply = supply or 1e9
    flow = early_flow(parsed, tok.get("creator"), supply) if full_history else None
    largest = rpc.largest(mint)
    excl = {tok["curve_ata"]} if tok.get("curve_ata") else set()
    top10, dropped = holder_share(largest, supply, excl)
    res = {"t_sigs": len(sigs), "full_history": full_history, "top10": top10,
           "bundle": flow["bundle_share"] if flow else None, "dev": flow["dev_share"] if flow else None,
           "bundled_wallets": flow["bundled_wallets"] if flow else None,
           "buyers": flow["buyers"] if flow else [], "creator": (flow or {}).get("creator") or tok.get("creator"),
           "curve_owner": (flow or {}).get("curve_owner")}
    if with_funders and flow and rpc.left() > 50 and (deadline is None or time.time() < deadline):
        funders = {}
        for b in flow["buyers"][:FUNDER_WALLETS]:
            ws = rpc.sigs(b["w"], FRESH_LIMIT)
            if ws and len(ws) < FRESH_LIMIT:
                funders[b["w"]] = funder_of(rpc.tx(ws[-1]["signature"]), b["w"])
            else:
                funders[b["w"]] = None      # starší / aktivní peněženka – zdroj nehledáme
        res["funders"] = funder_stats(funders, res["creator"])
    return res
