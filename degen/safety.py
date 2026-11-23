"""🛡️ Bezpečnost tokenu před nákupem – věci, kvůli kterým coin nejde prodat nebo jde „vybrat“ likvidita.

Na pump.fun (bonding curve) likviditu vybrat nejde – SOL drží program a po graduaci na PumpSwap se LP tokeny pálí.
Tam „rug“ = prodej tvůrce / bundlů / insiderů do křivky. Skutečné vybrání likvidity hrozí u coinů spuštěných
přímo na Raydium/Meteora/Orca s neodemčeným LP. „Nejde prodat“ = freeze authority nebo zrádná rozšíření Token-2022.

Tvrdé veto (nekoupit nikdy):
- mint authority není zrušená (tvůrce může natisknout další tokeny),
- freeze authority existuje (tvůrce může zmrazit tvoje tokeny → nejde prodat),
- Token-2022: permanent delegate, transfer hook, non-transferable, výchozí zmrazený účet, pausable, poplatek za převod > 5 %,
- coin mimo pump.fun na DEX poolu, kde je LP zamčené/spálené < 90 % (RugCheck),
- tvůrce pořád drží ≥ 10 % zásoby,
- tvůrce už dřív rugoval jiné coiny (RugCheck „Creator history of rugged tokens“).
"""
import time

import requests

TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLwvjqNDEYYDf6V7f5e"
BAD_EXT = {
    "permanentDelegate": "trvalý delegát (tvůrce může vzít tokeny z tvé peněženky)",
    "transferHook": "transfer hook (převod může zablokovat cizí program)",
    "nonTransferable": "token nejde převést ani prodat",
    "defaultAccountState": "nové účty jsou zmrazené",
    "pausableConfig": "převody jde pozastavit",
    "pausable": "převody jde pozastavit",
}
MAX_FEE_BPS = 500
DEV_HOLD_VETO = 0.10
LP_LOCK_MIN = 90.0
PUMP_SUFFIX = "pump"


def parse_mint(info):
    """Z getAccountInfo(jsonParsed) mintu → {mint_auth, freeze_auth, program, extensions[], fee_bps}."""
    v = (info or {}).get("value") or {}
    data = (v.get("data") or {}) if isinstance(v.get("data"), dict) else {}
    parsed = (data.get("parsed") or {}).get("info") or {}
    exts, fee = [], 0
    for e in parsed.get("extensions") or []:
        name = e.get("extension") or ""
        exts.append(name)
        if name == "transferFeeConfig":
            st = e.get("state") or {}
            for k in ("newerTransferFee", "olderTransferFee"):
                fee = max(fee, int(((st.get(k) or {}).get("transferFeeBasisPoints")) or 0))
        if name == "defaultAccountState" and ((e.get("state") or {}).get("accountState") or "").lower() != "frozen":
            exts[-1] = "defaultAccountState:ok"
    return {"mint_auth": parsed.get("mintAuthority"), "freeze_auth": parsed.get("freezeAuthority"),
            "program": v.get("owner"), "extensions": exts, "fee_bps": fee, "ok": bool(parsed)}


def mint_vetoes(m):
    out = []
    if not m or not m.get("ok"):
        return out
    if m.get("mint_auth"):
        out.append("mint authority aktivní – tvůrce může tisknout další tokeny")
    if m.get("freeze_auth"):
        out.append("freeze authority aktivní – tvůrce může zmrazit tvoje tokeny (nejde prodat)")
    for e in m.get("extensions") or []:
        if e in BAD_EXT:
            out.append("Token-2022: " + BAD_EXT[e])
    if (m.get("fee_bps") or 0) > MAX_FEE_BPS:
        out.append(f"poplatek za převod {m['fee_bps'] / 100:.0f} %")
    return out


def rugcheck(mint, timeout=8):
    """Veřejné RugCheck API (bez klíče). Vrací {score, risks:[{name, level}], lp_locked} nebo None."""
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report/summary", timeout=timeout,
                         headers={"Accept": "application/json", "User-Agent": "degen-city paper research"})
        if r.status_code != 200:
            return None
        j = r.json()
    except Exception:
        return None
    risks = [{"name": (x.get("name") or "")[:60], "level": x.get("level") or ""} for x in j.get("risks") or []
             if isinstance(x, dict)]
    lp = j.get("lpLockedPct")
    return {"score": j.get("score_normalised", j.get("score")), "risks": risks[:12],
            "lp_locked": float(lp) if isinstance(lp, (int, float)) else None}


def lp_vetoes(mint, mkt, rc):
    """Vybrání likvidity hrozí jen mimo pump.fun: pool na Raydium/Meteora/Orca bez zamčeného/spáleného LP."""
    if not mkt or not mkt.get("graduated"):
        return []
    pump_origin = mint.endswith(PUMP_SUFFIX) or "pumpswap" in (mkt.get("dexes") or [])
    if pump_origin:
        return []
    if not rc:
        return ["mimo pump.fun a RugCheck nedostupný – zamčení LP nejde ověřit"]
    if rc.get("lp_locked") is None:
        return ["mimo pump.fun a zamčení LP nejde ověřit"]
    if rc["lp_locked"] < LP_LOCK_MIN:
        return [f"likvidita jde vybrat – LP zamčené/spálené jen {rc['lp_locked']:.0f} %"]
    return []


def dev_hold(rpc, creator, mint, supply=1e9):
    if not creator:
        return None
    r = rpc.call("getTokenAccountsByOwner", [creator, {"mint": mint}, {"encoding": "jsonParsed"}])
    if r is None:
        return None
    amt = 0.0
    for a in r.get("value") or []:
        amt += float((((((a.get("account") or {}).get("data") or {}).get("parsed") or {}).get("info") or {})
                      .get("tokenAmount") or {}).get("uiAmount") or 0)
    return amt / supply


def check(rpc, tok, with_rugcheck=True):
    """Úplná kontrola před nákupem (~2 RPC dotazy + 1 RugCheck). Výsledek se uloží k tokenu."""
    mint = tok["mint"]
    m = parse_mint(rpc.call("getAccountInfo", [mint, {"encoding": "jsonParsed", "commitment": "confirmed"}]))
    vet = mint_vetoes(m)
    rc = rugcheck(mint) if with_rugcheck else None
    vet += lp_vetoes(mint, tok.get("mkt"), rc)
    if any("rugged" in (x.get("name") or "").lower() for x in (rc or {}).get("risks", [])):
        vet.append("tvůrce už dřív rugoval jiné coiny (RugCheck)")
    creator = (tok.get("chain") or {}).get("creator") or tok.get("creator")
    dh = dev_hold(rpc, creator, mint)
    if dh is not None and dh >= DEV_HOLD_VETO:
        vet.append(f"tvůrce pořád drží {dh * 100:.0f} % zásoby")
    return {"t": int(time.time()), "checked": m.get("ok"), "vetoes": vet, "mint": {k: m.get(k) for k in
            ("mint_auth", "freeze_auth", "extensions", "fee_bps")}, "rugcheck": rc, "dev_hold": dh,
            "danger": [x["name"] for x in (rc or {}).get("risks", []) if x.get("level") == "danger"]}
