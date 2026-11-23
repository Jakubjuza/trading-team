"""Papírové účty Degen City. Konzervativní: vstup až na další ověřené ceně (zpoždění jako u člověka s botem),
poplatek pump.fun/DEX, priority fee, skluz podle likvidity, mezery ve stopu se plní za zjištěnou cenu."""
import time

START = 1000.0            # USD na účet
RISK_FRAC = 0.02          # velikost pozice = 2 % účtu
MIN_SIZE = 5.0
MAX_OPEN = 8
FEE = 0.0125              # poplatek na stranu (pump.fun curve / PumpSwap ~1–1,25 %)
TX_USD = 0.40             # priority / Jito fee za transakci
PENDING_TTL = 180         # neplněný příkaz po 3 min propadá
STALE_EXIT = 15 * 60      # bez cen 15 min → výstup za 30 % poslední ceny („bez dat“)

RULES = {
    "default": {"sl": -0.40, "tp1": 1.0, "trail": 0.35, "max_min": 120},
    "graduace": {"sl": -0.30, "tp1": 0.8, "trail": 0.30, "max_min": 240},
}


def slip(size, mkt):
    base = (mkt or {}).get("liq") or (mkt or {}).get("mcap") or 1
    return 0.01 + min(0.25, size / max(base, 1.0))


def new_account(key):
    return {"key": key, "cash": START, "open": {}, "pending": {}, "n": 0, "wins": 0, "realized": 0.0,
            "curve": [], "trades": [], "fees": 0.0}


def equity(acc, marks):
    val = acc["cash"]
    for p in acc["open"].values():
        m = marks.get(p["mint"]) or p.get("last_mcap") or p["entry_mcap"]
        val += p["invested"] * p["remaining"] * m / p["entry_mcap"] * (1 - FEE)
    return val


def order(acc, mint, symbol, reason, mkt, now=None, score=None):
    """Zapíše příkaz k nákupu (plní se na další ceně). Vrací True, když byl přijat."""
    now = time.time() if now is None else now
    if mint in acc["open"] or mint in acc["pending"] or mint in acc.get("done", {}):
        return False
    if len(acc["open"]) + len(acc["pending"]) >= MAX_OPEN:
        return False
    eq = equity(acc, {})
    size = max(MIN_SIZE, eq * RISK_FRAC)
    if acc["cash"] < size + TX_USD:
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
        sl = slip(o["size"], m)
        eff = m["mcap"] * (1 + FEE + sl)
        acc["cash"] -= o["size"] + TX_USD
        acc["fees"] += o["size"] * (FEE + sl) + TX_USD
        acc["open"][mint] = {"mint": mint, "symbol": o["symbol"], "t_open": now, "entry_mcap": eff,
                             "sig_mcap": o["sig_mcap"], "fill_mcap": m["mcap"], "invested": o["size"],
                             "remaining": 1.0, "peak": m["mcap"], "tp1": False, "realized": -TX_USD,
                             "reason": o["reason"], "score": o.get("score"), "last_mcap": m["mcap"], "last_t": now}
        del acc["pending"][mint]
        filled.append(acc["open"][mint])
    return filled


def _sell(acc, p, frac, mcap, mkt, why, now):
    size_now = p["invested"] * frac * mcap / p["entry_mcap"]
    sl = slip(size_now, mkt)
    proceeds = max(0.0, size_now * (1 - FEE - sl) - TX_USD)
    acc["cash"] += proceeds
    acc["fees"] += size_now * (FEE + sl) + TX_USD
    p["realized"] += proceeds - p["invested"] * frac
    p["remaining"] = round(p["remaining"] - frac, 6)
    p.setdefault("exits", []).append({"t": now, "frac": frac, "mcap": round(mcap), "why": why})


def manage(acc, mkts, strat, now=None):
    """Projde otevřené pozice: stop, první cíl (½), trailing, čas, chybějící data. Vrací uzavřené obchody."""
    now = time.time() if now is None else now
    r = RULES.get(strat, RULES["default"])
    closed = []
    for mint, p in list(acc["open"].items()):
        m = mkts.get(mint)
        if m and m.get("mcap"):
            p["last_mcap"], p["last_t"] = m["mcap"], now
            p["peak"] = max(p["peak"], m["mcap"])
            ret = m["mcap"] / p["entry_mcap"] - 1
            if ret <= r["sl"]:
                _sell(acc, p, p["remaining"], m["mcap"], m, "stop", now)
            else:
                if not p["tp1"] and ret >= r["tp1"]:
                    _sell(acc, p, p["remaining"] / 2, m["mcap"], m, "cíl ½", now)
                    p["tp1"] = True
                if p["tp1"] and p["remaining"] > 0 and m["mcap"] <= p["peak"] * (1 - r["trail"]):
                    _sell(acc, p, p["remaining"], m["mcap"], m, "trailing", now)
                if p["remaining"] > 0 and p["tp1"] and m["mcap"] <= p["entry_mcap"] * 1.0:
                    _sell(acc, p, p["remaining"], m["mcap"], m, "break-even", now)
                if p["remaining"] > 0 and now - p["t_open"] >= r["max_min"] * 60:
                    _sell(acc, p, p["remaining"], m["mcap"], m, "čas", now)
        elif now - p.get("last_t", p["t_open"]) >= STALE_EXIT:
            _sell(acc, p, p["remaining"], p["last_mcap"] * 0.3, None, "bez dat", now)
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
                 "entry_mcap": round(p["fill_mcap"]), "exits": p["exits"]}
            acc["trades"] = (acc["trades"] + [t])[-40:]
            closed.append(t)
    # zapomenout staré „done“ (aby slovník nerostl)
    acc["done"] = {k: v for k, v in acc.get("done", {}).items() if now - v < 48 * 3600}
    return closed


def mark_curve(acc, marks, now=None, every=900, keep=400):
    now = time.time() if now is None else now
    eq = round(equity(acc, marks), 2)
    if not acc["curve"] or now - acc["curve"][-1][0] >= every:
        acc["curve"] = (acc["curve"] + [[int(now), eq]])[-keep:]
    return eq
