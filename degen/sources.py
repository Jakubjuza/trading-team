"""Zdroje dat Degen City. Každá funkce vrací normalizovaná data nebo prázdný výsledek – nikdy nespadne.

- pump.fun (neoficiální frontend API): nově spuštěné coiny, tvůrce, sociální sítě, stav bonding curve
- DexScreener (veřejné API, ~300 dotazů/min): cena / market cap, objem, nákupy × prodeje, likvidita, DEX
- GeckoTerminal (veřejné API, ~30 dotazů/min): záložní zdroj nových poolů na Solaně
- Solana RPC (Helius s klíčem HELIUS_API_KEY, jinak veřejné RPC): držitelé, první kupci, bundly, financování peněženek
"""
import os
import time

import requests

UA = {"User-Agent": "Mozilla/5.0 (degen-city paper research)", "Accept": "application/json"}
PUMP_URLS = [
    "https://frontend-api-v3.pump.fun/coins?offset=0&limit=50&sort=created_timestamp&order=DESC&includeNsfw=true",
    "https://frontend-api.pump.fun/coins?offset=0&limit=50&sort=created_timestamp&order=DESC&includeNsfw=true",
]
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
SOL_MINT = "So11111111111111111111111111111111111111112"
GRAD_DEXES = {"pumpswap", "raydium", "meteora", "orca", "raydium-clmm", "raydium-cp", "meteora-dlmm", "pump-swap"}
CURVE_DEXES = {"pumpfun", "pump-fun", "pump.fun"}

STATUS = {}          # zdroj → "ok" / "chyba …" (zapisuje se do city.json)


def _get(url, timeout=12, params=None):
    try:
        r = requests.get(url, headers=UA, timeout=timeout, params=params)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        return r.json(), None
    except Exception as e:  # síť, JSON, timeout
        return None, type(e).__name__


def _f(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- pump.fun

def norm_pump(c):
    mint = c.get("mint")
    if not mint:
        return None
    ts = _f(c.get("created_timestamp"), 0) or 0
    if ts > 1e12:
        ts /= 1000
    return {
        "mint": mint, "name": (c.get("name") or "")[:40], "symbol": (c.get("symbol") or "")[:16],
        "creator": c.get("creator"), "created": ts or None,
        "twitter": bool(c.get("twitter")), "telegram": bool(c.get("telegram")), "website": bool(c.get("website")),
        "replies": int(_f(c.get("reply_count"), 0) or 0),
        "complete": bool(c.get("complete")),
        "mcap_usd": _f(c.get("usd_market_cap")),
        "curve_ata": c.get("associated_bonding_curve"),
        "image": c.get("image_uri") if str(c.get("image_uri") or "").startswith("https://") else None,
        "src": "pump",
    }


def pump_latest():
    last = None
    for url in PUMP_URLS:
        data, err = _get(url)
        if data is None:
            last = err
            continue
        rows = data if isinstance(data, list) else (data.get("coins") or data.get("data") or [])
        out = [t for t in (norm_pump(c) for c in rows if isinstance(c, dict)) if t]
        STATUS["pump.fun"] = "ok"
        return out
    STATUS["pump.fun"] = f"chyba {last}"
    return []


# ---------------------------------------------------------------- GeckoTerminal (záloha objevování)

def norm_gecko(pool):
    a = pool.get("attributes") or {}
    rel = pool.get("relationships") or {}
    base = (((rel.get("base_token") or {}).get("data") or {}).get("id") or "")
    dex = (((rel.get("dex") or {}).get("data") or {}).get("id") or "")
    mint = base.split("_", 1)[1] if "_" in base else None
    if not mint or mint == SOL_MINT:
        return None
    name = (a.get("name") or "").split(" / ")[0]
    created = a.get("pool_created_at")
    ts = None
    if created:
        try:
            ts = time.mktime(time.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
        except ValueError:
            ts = None
    return {"mint": mint, "name": name[:40], "symbol": name[:16], "creator": None, "created": ts,
            "twitter": False, "telegram": False, "website": False, "replies": 0,
            "complete": dex not in CURVE_DEXES, "mcap_usd": _f(a.get("market_cap_usd")) or _f(a.get("fdv_usd")),
            "curve_ata": None, "image": None, "src": "gecko", "dex": dex}


def gecko_new(pages=1):
    out = []
    for p in range(1, pages + 1):
        data, err = _get(f"https://api.geckoterminal.com/api/v2/networks/solana/new_pools?page={p}")
        if data is None:
            STATUS["geckoterminal"] = f"chyba {err}"
            break
        STATUS["geckoterminal"] = "ok"
        out += [t for t in (norm_gecko(x) for x in data.get("data") or []) if t]
    return out


# ---------------------------------------------------------------- DexScreener (trh)

def pick_pair(pairs):
    """Z párů jednoho tokenu vybere ten s největší likviditou/objemem a sečte nákupy/prodeje přes všechny páry."""
    if not pairs:
        return None
    best = max(pairs, key=lambda p: (_f((p.get("liquidity") or {}).get("usd"), 0) or 0,
                                     _f((p.get("volume") or {}).get("h1"), 0) or 0))
    buys = sum(int(((p.get("txns") or {}).get("m5") or {}).get("buys") or 0) for p in pairs)
    sells = sum(int(((p.get("txns") or {}).get("m5") or {}).get("sells") or 0) for p in pairs)
    vol_h1 = sum(_f((p.get("volume") or {}).get("h1"), 0) or 0 for p in pairs)
    vol_m5 = sum(_f((p.get("volume") or {}).get("m5"), 0) or 0 for p in pairs)
    info = best.get("info") or {}
    socials = {(s.get("type") or "").lower() for s in info.get("socials") or [] if isinstance(s, dict)}
    dexes = {(p.get("dexId") or "").lower() for p in pairs}
    created = [(_f(p.get("pairCreatedAt"), 0) or 0) / 1000 for p in pairs if p.get("pairCreatedAt")]
    grad = [(_f(p.get("pairCreatedAt"), 0) or 0) / 1000 for p in pairs
            if (p.get("dexId") or "").lower() in GRAD_DEXES and p.get("pairCreatedAt")]
    return {
        "mcap": _f(best.get("marketCap")) or _f(best.get("fdv")),
        "price": _f(best.get("priceUsd")),
        "liq": _f((best.get("liquidity") or {}).get("usd")),
        "buys5": buys, "sells5": sells, "vol5": vol_m5, "vol1h": vol_h1,
        "dex": (best.get("dexId") or "").lower(), "dexes": sorted(dexes),
        "graduated": bool(dexes & GRAD_DEXES), "grad_at": min(grad) if grad else None,
        "created": min(created) if created else None,
        "symbol": ((best.get("baseToken") or {}).get("symbol") or "")[:16],
        "name": ((best.get("baseToken") or {}).get("name") or "")[:40],
        "twitter": "twitter" in socials or "x" in socials, "telegram": "telegram" in socials,
        "website": bool(info.get("websites")),
    }


def dex_tokens(mints):
    """{mint: tržní data} pro až stovky mintů (dávky po 30)."""
    out, err = {}, None
    mints = list(dict.fromkeys(mints))
    for i in range(0, len(mints), 30):
        chunk = mints[i:i + 30]
        data, e = _get("https://api.dexscreener.com/tokens/v1/solana/" + ",".join(chunk))
        if data is None:
            err = e
            continue
        rows = data if isinstance(data, list) else (data.get("pairs") or [])
        by = {}
        for p in rows:
            m = ((p.get("baseToken") or {}).get("address"))
            if m in chunk:
                by.setdefault(m, []).append(p)
        for m, ps in by.items():
            v = pick_pair(ps)
            if v and v["mcap"]:
                out[m] = v
        time.sleep(0.25)
    STATUS["dexscreener"] = "ok" if err is None else f"chyba {err}"
    return out


# ---------------------------------------------------------------- Solana RPC

class Rpc:
    """JSON-RPC s počítadlem kreditů a denním limitem. Helius free = ~1 M kreditů/měsíc → výchozí limit 30 000/den."""

    def __init__(self, state):
        key = os.environ.get("HELIUS_API_KEY", "").strip()
        self.kind = "helius" if key else "public"
        self.url = f"https://mainnet.helius-rpc.com/?api-key={key}" if key else \
            os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self.limit = int(os.environ.get("DEGEN_RPC_DAILY", "30000" if key else "8000"))
        self.pause = 0.11 if key else 0.35
        day = time.strftime("%Y-%m-%d", time.gmtime())
        b = state.setdefault("rpc_budget", {})
        if b.get("day") != day:
            b.clear()
            b.update({"day": day, "used": 0, "errors": 0})
        self.b = b

    def left(self):
        return self.limit - self.b["used"]

    def call(self, method, params):
        if self.left() <= 0:
            return None
        self.b["used"] += 1
        for attempt in range(2):
            try:
                r = requests.post(self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                                  timeout=8, headers={"Content-Type": "application/json"})
                time.sleep(self.pause)
                if r.status_code == 429:
                    time.sleep(2 + 3 * attempt)
                    continue
                j = r.json()
                if "error" in j:
                    self.b["errors"] += 1
                    STATUS["rpc"] = f"chyba {str(j['error'].get('message', ''))[:60]}"
                    return None
                STATUS["rpc"] = f"ok ({self.kind})"
                return j.get("result")
            except Exception as e:
                self.b["errors"] += 1
                STATUS["rpc"] = f"chyba {type(e).__name__}"
                time.sleep(1)
        return None

    # -- pomocné dotazy
    def largest(self, mint):
        r = self.call("getTokenLargestAccounts", [mint, {"commitment": "confirmed"}])
        if not r:
            return None
        return [{"address": a.get("address"), "amount": _f(a.get("uiAmount"), 0) or 0} for a in r.get("value") or []]

    def sigs(self, address, limit=1000, before=None):
        opts = {"limit": limit, "commitment": "confirmed"}
        if before:
            opts["before"] = before
        r = self.call("getSignaturesForAddress", [address, opts])
        return r or []

    def tx(self, sig):
        return self.call("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0,
                                                   "commitment": "confirmed"}])
