"""📋 Přehled otevřených papírových pozic pro Agentown (tlačítko „Pozice“) → research/positions.json.

Stejná data jako /pozice v Telegramu, ale strojově: u každé pozice vstup, cena teď, stop, cíle, výsledek teď
(plus poslední ceny mincí v `prices`, ze kterých stránka dopočítá i stav pozic Downtownu)
a možná ztráta (do stopu) a možný zisk (do posledního cíle) v R i v USD. USD = R × riziko na obchod
z nastavení skeneru (account_size × risk_pct). Ceny jsou poslední uzavřené svíčky skeneru, bez poplatků
(u laboratoře výsledek teď po poplatcích, stejně jako v deníku). Jen papír, nic se neobchoduje.

Soubor se zapisuje nejvýš jednou za `every_min` minut, nebo hned, když se změní seznam otevřených pozic
(otevření / uzavření / T1), aby skener necommitoval každou minutu. Workflow ho commitne do repozitáře
a naplánovaná úloha „Agentown – otevřené pozice“ ho každou hodinu zapíše do databáze stránky (kolekce `positions`).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "research" / "positions.json"
LAB_EXITS = {"opp": (0.0, 0.0, 0.0, True), "trail": (2.0, 3.0, 0.0, False),          # = strategy_atlas.EXITS
             "target": (2.0, 0.0, 3.0, False), "opp_stop": (1.5, 0.0, 0.0, True)}   # (stop, trailing, cíl v ATR, opačný signál)


def _r(x, d=3):
    return None if x is None else round(float(x), d)


def _px(prices, sym):
    q = (prices or {}).get(sym)
    return float(q[0]) if q else None


def _money(pos, risk_usd):
    for k in ("now", "loss", "gain"):
        r = pos.get("r_" + k)
        pos["usd_" + k] = None if r is None else round(r * risk_usd, 2)
    return pos


def core(cfg, state, prices, risk_usd):
    """Jádro: polovina pozice na T1, zbytek na T2; po T1 stop zbytku na vstup (stejně jako scan.simulate)."""
    split = float((cfg.get("exit") or {}).get("split", 0.5))
    out = []
    for p in state.data.get("open", []):
        s = p.get("setup") or {}
        try:
            entry, stop = float(s["entry"]), float(s["stop"])
        except (KeyError, TypeError, ValueError):
            continue
        sg = 1 if s.get("direction") == "long" else -1
        risk = abs(entry - stop) or None
        tg = [float(t) for t in (s.get("targets") or [])]
        rt = [sg * (t - entry) / risk for t in tg] if risk else []
        now = _px(prices, p["symbol"])
        t1 = bool(p.get("t1_notified"))
        r_move = sg * (now - entry) / risk if now and risk else None
        if len(rt) >= 2:
            gain = split * rt[0] + (1 - split) * rt[-1]
        else:
            gain = rt[0] if rt else None
        if t1 and rt:
            loss = split * rt[0]                                   # zbytek má stop na vstupu
            r_now = split * rt[0] + (1 - split) * r_move if r_move is not None else None
        else:
            loss, r_now = -1.0, r_move
        notes = []
        if t1:
            notes.append("T1 dosažen – polovina vybrána, stop zbytku na vstupu")
        if p.get("mtf"):
            notes.append("vstup z nižšího timeframu")
        trail = (p.get("exit") or {}).get("trail_atr") or (cfg.get("exit") or {}).get("trail_atr")
        if trail:
            notes.append(f"po T1 trailing {trail:g} ATR")
        out.append(_money({
            "id": p.get("id"), "part": "core", "symbol": p["symbol"], "coin": p["symbol"].split("/")[0],
            "dir": s.get("direction"), "tf": p.get("timeframe"), "strategy": p.get("strategy"),
            "since": s.get("hold_time"), "entry": _r(entry, 8), "now": _r(now, 8),
            "stop": _r(entry if t1 else stop, 8), "stop_orig": _r(stop, 8), "targets": [_r(t, 8) for t in tg],
            "r_now": _r(r_now), "r_loss": _r(loss), "r_gain": _r(gain),
            "pct_now": _r(sg * (now / entry - 1) * 100 if now else None, 2),
            "demo": (p.get("demo") or {}).get("status") == "open", "notes": notes}, risk_usd))
    return out


def pyramid(cfg, state, prices, risk_usd):
    """Pyramida: každý kus = unit_r R, kusy po add_atr × ATR, společný stop (stop_now), bez pevného cíle (trailing)."""
    from scanner import pyramid as pyr
    pp = pyr.params(cfg)
    out = []
    for p in (state.data.get("pyramid") or {}).get("open", []):
        sg = 1 if p["direction"] == "long" else -1
        risk = abs(p["entry"] - p["stop"]) or None
        if not risk:
            continue
        n = int(p.get("notified_units", 1))
        unit = pp["unit_r"] / risk
        ents = [p["entry"] + sg * k * pp["add_atr"] * p["atr"] for k in range(n)]
        stop = float(p.get("stop_now", p["stop"]))
        now = _px(prices, p["symbol"])
        r_now = sum(unit * sg * (now - e) for e in ents) if now else None
        loss = sum(unit * sg * (stop - e) for e in ents)
        out.append(_money({
            "id": p.get("id"), "part": "pyramid", "symbol": p["symbol"], "coin": p["symbol"].split("/")[0],
            "dir": p["direction"], "tf": p.get("timeframe"), "strategy": p.get("strategy"),
            "since": p.get("opened") or p.get("hold_time"), "entry": _r(p["entry"], 8), "now": _r(now, 8),
            "stop": _r(stop, 8), "stop_orig": _r(p["stop"], 8), "targets": [], "units": n,
            "unit_entries": [_r(e, 8) for e in ents],
            "r_now": _r(r_now), "r_loss": _r(loss), "r_gain": None,
            "pct_now": _r(sg * (now / p["entry"] - 1) * 100 if now else None, 2), "demo": False,
            "notes": [f"{n} kus(y) po {pp['unit_r']:g} R", f"bez pevného cíle – trailing {pp['trail_atr']:g} ATR"]}, risk_usd))
    return out


def lab(cfg, state, prices, risk_usd):
    """Laboratoř: stop a cíl podle výstupu strategie (ATR v době signálu), výsledek teď po poplatcích (lab_report)."""
    from scanner import lab_report
    out = []
    for o in lab_report.open_positions(state, prices):
        d = 1 if o["dir"] == "long" else -1
        ex = (o.get("strategy") or {}).get("exit") or ""
        sa, ta, ga, uo = LAB_EXITS.get(ex, (0.0, 0.0, 0.0, False))
        close, entry, rf = o.get("signal_close"), o.get("entry_px"), o.get("rf")
        risk = rf * close if rf and close else None
        atr = risk / sa if risk and sa else (risk / 2.0 if risk else None)   # bez stopu je riziko 2 ATR (lab_paper)
        stop = o.get("stop")
        tgt = close + d * ga * atr if ga and atr and close else None
        r_loss = d * (stop - entry) / risk if stop is not None and entry and risk else None
        r_gain = d * (tgt - entry) / risk if tgt is not None and entry and risk else None
        notes = []
        if ta:
            notes.append(f"trailing {ta:g} ATR – stop se posouvá za cenou")
        if uo:
            notes.append("výstup i opačným signálem")
        if stop is None:
            notes.append("bez pevného stopu")
        if tgt is None:
            notes.append("bez pevného cíle")
        out.append(_money({
            "id": f"{o.get('sid')}|{o['coin']}|{o.get('signal_bar')}", "part": "lab", "symbol": f"{o['coin']}/USDT",
            "coin": o["coin"], "dir": o["dir"], "tf": o.get("tf"), "strategy": o.get("label") or o.get("sid"),
            "since": o.get("signal_bar"), "entry": _r(entry, 8), "now": _r(o.get("now"), 8),
            "stop": _r(stop, 8), "targets": [_r(tgt, 8)] if tgt is not None else [],
            "r_now": _r(o.get("r")), "r_loss": _r(r_loss), "r_gain": _r(r_gain),
            "pct_now": _r(o.get("pct"), 2), "demo": False, "notes": notes}, risk_usd))
    return out


def ensemble(state, prices):
    ens = state.data.get("ensemble") or {}
    held = {c: q for c, q in (ens.get("qty") or {}).items() if q > 0}
    if not held and not ens.get("equity"):
        return None
    rows, inv = [], 0.0
    for c, q in sorted(held.items()):
        now = _px(prices, f"{c}/USDT")
        avg = (ens.get("avg") or {}).get(c)
        val = q * now if now else None
        inv += val or 0
        rows.append({"coin": c, "qty": _r(q, 8), "now": _r(now, 8), "avg": _r(avg, 8), "value": _r(val, 2),
                     "pct": _r((now / avg - 1) * 100 if now and avg else None, 2)})
    value = (ens.get("cash") or 0) + inv
    start = ens.get("start_equity") or value
    return {"value": _r(value, 2), "start": _r(start, 2), "pct": _r((value / start - 1) * 100 if start else None, 2),
            "cash": _r(ens.get("cash") or 0, 2), "in_market_pct": _r(inv / value * 100 if value else None, 1), "held": rows}


def build(cfg, state, prices, now=None):
    now = now or datetime.now(timezone.utc)
    risk_usd = float(cfg.get("account_size", 10000)) * float(cfg.get("risk_pct", 1.0)) / 100
    parts = []
    for key, name, fn in (("core", "Jádro", core), ("pyramid", "Pyramida", pyramid), ("lab", "Laboratoř", lab)):
        try:
            parts.append({"key": key, "name": name, "positions": fn(cfg, state, prices, risk_usd)})
        except Exception as exc:                                        # jedna část nesmí shodit export
            parts.append({"key": key, "name": name, "positions": [], "error": exc.__class__.__name__})
    try:
        ens = ensemble(state, prices)
    except Exception as exc:
        ens = {"error": exc.__class__.__name__}
    return {"id": "state", "updated": now.isoformat(timespec="seconds"), "risk_usd": round(risk_usd, 2),
            "account_size": cfg.get("account_size"), "risk_pct": cfg.get("risk_pct"), "parts": parts, "ensemble": ens,
            "prices": {sym.split("/")[0]: _r(q[0], 8) for sym, q in (prices or {}).items() if q and sym.endswith("/USDT")},
            "note": "Papírové pozice skeneru. Možná ztráta = do stopu, možný zisk = do posledního cíle; USD = R × riziko "
                    "na obchod z nastavení skeneru, bez poplatků (laboratoř teď po poplatcích). Ceny = poslední uzavřené "
                    "svíčky. Nejde o finanční poradenství."}


def _sig(doc):
    return sorted(f"{p['part']}|{p.get('id')}|{p.get('stop')}" for part in doc["parts"] for p in part["positions"])


def maybe_write(cfg, state, prices, now=None, path=None, every_min=55):
    """Zapíše soubor, když se změnily pozice (nebo stopy) nebo je starší než `every_min` minut. Vrací True při zápisu."""
    path = Path(path or OUT)
    now = now or datetime.now(timezone.utc)
    doc = build(cfg, state, prices, now)
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        age = (now - datetime.fromisoformat(old["updated"])).total_seconds() / 60
        if _sig(old) == _sig(doc) and age < every_min:
            return False
    except (OSError, ValueError, KeyError, TypeError):
        pass
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return True
