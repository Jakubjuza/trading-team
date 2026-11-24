"""Papírové účty Degen City (motor v2 od 24. 11. 2026).

Každý nákup i prodej se počítá přes hloubku poolu (konstantní součin x·y = k), ne jen podle market capu:
- pool s likviditou (DexScreener `liq`): quote strana = liq / 2, víc než ta se z poolu vybrat nedá,
- pump.fun bonding curve: virtuální rezervy 30 SOL × 1,073 mld tokenů → z MC se dopočítá SOL v křivce,
  vybrat jde jen skutečné SOL (virtuální minus 30).
Když likvidita zmizí, prodej vynese skoro nic – papír tak už nemůže „vydělat“ na MC, která vyskočila
nad prázdným poolem (chyba motoru v1: Graduace „vydělala“ 2 mil. $ prodejem do vybrané likvidity).
Vstup až na další ověřené ceně, poplatek, priority fee, 1 % navíc na zpoždění/MEV.
"""
import math
import time

START = 1000.0            # USD na účet
RISK_FRAC = 0.02          # velikost pozice = 2 % účtu …
POOL_FRAC = 0.03          # … ale nejvýš 3 % quote strany poolu (do mělkého poolu se velká pozice nevejde)
MIN_SIZE = 5.0
MAX_OPEN = 8
FEE = 0.0125              # poplatek na stranu (pump.fun curve / PumpSwap ~1–1,25 %)
EXTRA = 0.01              # zpoždění, MEV, sandwich
TX_USD = 0.40             # priority / Jito fee za transakci
PENDING_TTL = 180         # neplněný příkaz po 3 min propadá
STALE_EXIT = 15 * 60      # bez cen 15 min → coin se počítá jako mrtvý (0)
DEAD_LIQ = 500.0          # likvidita poolu pod 500 $ → pozice se počítá jako ztracená (zbytky vyberou rychlejší)
CURVE_K = 30.0 * 1.073e9  # pump.fun: virtuální SOL × virtuální tokeny
CURVE_VSOL0 = 30.0
CURVE_DEXES = {"pumpfun", "pump-fun", "pump.fun"}
ENGINE = 2

RULES = {
    "default": {"sl": -0.40, "tp1": 1.0, "trail": 0.35, "max_min": 120},
    "graduace": {"sl": -0.30, "tp1": 0.8, "trail": 0.30, "max_min": 240},
}


def pool(mkt):
    """→ (hloubka quote strany v USD, kolik USD jde z poolu nejvýš vybrat)."""
    if not mkt:
        return 0.0, 0.0
    liq, mcap = mkt.get("liq"), mkt.get("mcap") or 0.0
    if liq:
        return liq / 2, liq / 2
    on_curve = (mkt.get("dex") in CURVE_DEXES) or not mkt.get("graduated")
    solp = mkt.get("sol_px")
    if on_curve and solp and mcap:
        vsol = math.sqrt(max(mcap / solp, 0.0) * CURVE_K / 1e9)
        return vsol * solp, max(0.0, vsol - CURVE_VSOL0) * solp
    if on_curve and mcap:
        return 0.3 * mcap, 0.1 * mcap            # bez ceny SOL: hrubý, opatrný odhad
    return 0.0, 0.0                              # pool bez známé likvidity = nic nejde vybrat


def sell_value(v, mkt):
    """Kolik USD skutečně dostaneš za pozici v hodnotě v (podle ceny), po poplatcích, bez TX."""
    q, cap = pool(mkt)
    if q <= 0 or v <= 0:
        return 0.0
    out = min(q * v / (q + v), cap)
    return max(0.0, out * (1 - FEE - EXTRA))


def new_account(key):
    return {"key": key, "cash": START, "open": {}, "pending": {}, "n": 0, "wins": 0, "realized": 0.0,
            "curve": [], "trades": [], "fees": 0.0, "engine": ENGINE}


def _mk(m):
    return {k: (m or {}).get(k) for k in ("mcap", "liq", "sol_px", "dex", "graduated")}


def pos_value(p, mkt=None):
    m = mkt if (mkt and mkt.get("mcap")) else p.get("last_mkt")
    if not m or not m.get("mcap") or (m.get("liq") is not None and m["liq"] < DEAD_LIQ):
        return 0.0
    v = p["invested"] * p["remaining"] * m["mcap"] / p["entry_mcap"]
    return sell_value(v, m)


def equity(acc, mkts):
    """Hodnota účtu = hotovost + kolik by šlo z otevřených pozic opravdu vybrat."""
    return acc["cash"] + sum(pos_value(p, (mkts or {}).get(p["mint"])) for p in acc["open"].values())


def order(acc, mint, symbol, reason, mkt, now=None, score=None):
    """Zapíše příkaz k nákupu (plní se na další ceně). Vrací True, když byl přijat."""
    now = time.time() if now is None else now
    if mint in acc["open"] or mint in acc["pending"] or mint in acc.get("done", {}):
        return False
    if len(acc["open"]) + len(acc["pending"]) >= MAX_OPEN:
        return False
    q, _ = pool(mkt)
    size = min(equity(acc, {}) * RISK_FRAC, POOL_FRAC * q)
    if size < MIN_SIZE or acc["cash"] < size + TX_USD:
        return False
    acc["pending"][mint] = {"mint": mint, "symbol": symbol, "t": now, "sig_mcap": (mkt or {}).get("mcap"),
                            "size": round(size, 2), "reason": reason, "score": score}
    return True


def fill_pending(acc, mkts, now=None):
    now = time.time() if now is None else now
    filled = []
    for mint, o in list(acc["pending"].items()):
        m = mkts.get(mint)
        if now - o["t"] > PENDING_TTL:
            del acc["pending"][mint]
            continue
        if not m or not m.get("mcap") or now - o["t"] < 5:
            continue
        q, _ = pool(m)
        size = min(o["size"], POOL_FRAC * q)
        if size < MIN_SIZE:
            del acc["pending"][mint]
            continue
        got = size * q / (q + size) * (1 - FEE - EXTRA)          # hodnota tokenů za aktuální cenu
        eff = m["mcap"] * size / got                             # efektivní nákupní MC (vč. dopadu a poplatků)
        acc["cash"] -= size + TX_USD
        acc["fees"] += size - got + TX_USD
        acc["open"][mint] = {"mint": mint, "symbol": o["symbol"], "t_open": now, "entry_mcap": eff,
                             "sig_mcap": o["sig_mcap"], "fill_mcap": m["mcap"], "invested": size,
                             "remaining": 1.0, "peak": m["mcap"], "tp1": False, "realized": -TX_USD,
                             "reason": o["reason"], "score": o.get("score"), "last_mcap": m["mcap"], "last_t": now,
                             "last_mkt": _mk(m), "entry_liq": m.get("liq")}
        del acc["pending"][mint]
        filled.append(acc["open"][mint])
    return filled


def _sell(acc, p, frac, mkt, why, now, zero=False):
    m = mkt or p.get("last_mkt") or {}
    v = p["invested"] * frac * (m.get("mcap") or 0) / p["entry_mcap"]
    got = 0.0 if zero else sell_value(v, m)
    proceeds = max(0.0, got - TX_USD)
    acc["cash"] += proceeds
    acc["fees"] += TX_USD + max(0.0, min(v, pool(m)[1]) - got) if not zero else TX_USD
    p["realized"] += proceeds - p["invested"] * frac
    p["remaining"] = round(p["remaining"] - frac, 6)
    p.setdefault("exits", []).append({"t": now, "frac": frac, "mcap": round(m.get("mcap") or 0),
                                      "liq": round(m["liq"]) if m.get("liq") else None, "got": round(proceeds, 2),
                                      "why": why})


def manage(acc, mkts, strat, now=None):
    """Projde otevřené pozice: stop, první cíl (½), trailing, čas, zmizelá likvidita, chybějící data."""
    now = time.time() if now is None else now
    r = RULES.get(strat, RULES["default"])
    closed = []
    for mint, p in list(acc["open"].items()):
        m = mkts.get(mint)
        if m and m.get("mcap"):
            p["last_mcap"], p["last_t"], p["last_mkt"] = m["mcap"], now, _mk(m)
            p["peak"] = max(p["peak"], m["mcap"])
            ret = m["mcap"] / p["entry_mcap"] - 1
            if m.get("liq") is not None and m["liq"] < DEAD_LIQ:
                _sell(acc, p, p["remaining"], m, "likvidita zmizela (počítáno jako 0)", now, zero=True)
            elif ret <= r["sl"]:
                _sell(acc, p, p["remaining"], m, "stop", now)
            else:
                if not p["tp1"] and ret >= r["tp1"]:
                    _sell(acc, p, p["remaining"] / 2, m, "cíl ½", now)
                    p["tp1"] = True
                if p["tp1"] and p["remaining"] > 0 and m["mcap"] <= p["peak"] * (1 - r["trail"]):
                    _sell(acc, p, p["remaining"], m, "trailing", now)
                if p["remaining"] > 0 and p["tp1"] and m["mcap"] <= p["entry_mcap"]:
                    _sell(acc, p, p["remaining"], m, "break-even", now)
                if p["remaining"] > 0 and now - p["t_open"] >= r["max_min"] * 60:
                    _sell(acc, p, p["remaining"], m, "čas", now)
        elif now - p.get("last_t", p["t_open"]) >= STALE_EXIT:
            _sell(acc, p, p["remaining"], None, "bez dat (počítáno jako 0)", now, zero=True)
        if p["remaining"] <= 1e-6:
            del acc["open"][mint]
            acc["n"] += 1
            win = p["realized"] > 0
            acc["wins"] += win
            acc["realized"] += p["realized"]
            acc.setdefault("done", {})[mint] = now
            t = {"mint": mint, "symbol": p["symbol"], "open": p["t_open"], "close": now,
                 "pnl": round(p["realized"], 2), "ret": round(p["realized"] / p["invested"] * 100, 1),
                 "invested": p["invested"], "why": p["exits"][-1]["why"], "reason": p["reason"],
                 "score": p.get("score"), "peak_x": round(p["peak"] / p["fill_mcap"], 2),
                 "entry_mcap": round(p["fill_mcap"]), "entry_liq": p.get("entry_liq"), "exits": p["exits"],
                 "engine": ENGINE}
            acc["trades"] = (acc["trades"] + [t])[-40:]
            closed.append(t)
    acc["done"] = {k: v for k, v in acc.get("done", {}).items() if now - v < 48 * 3600}
    return closed


def mark_curve(acc, mkts, now=None, every=900, keep=400):
    now = time.time() if now is None else now
    eq = round(equity(acc, mkts), 2)
    if not acc["curve"] or now - acc["curve"][-1][0] >= every:
        acc["curve"] = (acc["curve"] + [[int(now), eq]])[-keep:]
    return eq
