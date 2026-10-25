"""🔺 Pyramida – samostatná papírová část: denní signály s přikupováním do vydělávající pozice.

Ověřeno v research/experiments/pyramid.py (reports/pyramid.md, varianta P2). Oddělené od hlavních papírových pozic:
vlastní limity, vlastní zprávy, vlastní deník research/pyramid_outcomes.jsonl. Na burzu se nic neposílá.
Pravidla (config `pyramid`):
  • start 1 kus = `unit_r` R (R = vzdálenost vstup–stop signálu), vstup na zavření signální denní svíčky,
  • za každý pohyb o `add_atr` × ATR od vstupu přidat stejný kus, max. `max_units`,
  • po přidání stop všech kusů = cena přidání − `add_stop_atr` × ATR (long), nikdy zpět,
  • trailing: nejlepší zavírací cena − `trail_atr` × ATR; max. `max_hold_bars` svíček; ve svíčce nejdřív stop, pak přidání,
  • limity: max. `max_open_per_direction` na strategii a směr, max. `max_new_per_day` nových za den, 1 na minci a strategii.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from scanner import notify

OUTCOMES = Path(__file__).resolve().parent.parent / "research" / "pyramid_outcomes.jsonl"
DEFAULTS = {"enabled": False, "strategies": ["donchian_1d", "pullback_1d"], "unit_r": 0.5, "add_atr": 1.0,
            "max_units": 4, "add_stop_atr": 2.0, "trail_atr": 3.0, "max_hold_bars": 20,
            "max_open_per_direction": 2, "max_new_per_day": 3}


def params(cfg):
    return {**DEFAULTS, **(cfg.get("pyramid") or {})}


def _num(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


def simulate(pos, after, p, cost_pct):
    """Projde uzavřené svíčky po vstupu. Vrací stav: units [(čas, cena)], stop, r (realizované nebo průběžné), closed."""
    long = pos["direction"] == "long"
    sg = 1 if long else -1
    e0, stop, atr = pos["entry"], pos["stop"], pos["atr"]
    risk = abs(e0 - stop)
    unit = p["unit_r"] / risk
    cost = cost_pct / 100
    units, best = [(pos["hold_time"], e0)], e0
    hi, lo, cl, idx = after["High"].values, after["Low"].values, after["Close"].values, after.index

    def value(px):
        return sum(unit * (sg * (px - e) - cost * (e + px)) for _, e in units)
    n = min(len(cl), p["max_hold_bars"])
    for i in range(n):
        if (lo[i] <= stop) if long else (hi[i] >= stop):
            return {"closed": True, "reason": "stop", "units": units, "stop": stop, "r": value(stop), "exit": stop,
                    "time": idx[i].isoformat(), "bars": i + 1}
        while len(units) < p["max_units"]:
            lvl = e0 + sg * len(units) * p["add_atr"] * atr
            if not ((hi[i] >= lvl) if long else (lo[i] <= lvl)):
                break
            units.append((idx[i].isoformat(), lvl))
            ns = lvl - sg * p["add_stop_atr"] * atr
            stop = max(stop, ns) if long else min(stop, ns)
        best = max(best, cl[i]) if long else min(best, cl[i])
        tr = best - sg * p["trail_atr"] * atr
        stop = max(stop, tr) if long else min(stop, tr)
    if n and n >= p["max_hold_bars"]:
        return {"closed": True, "reason": "time", "units": units, "stop": stop, "r": value(cl[n - 1]), "exit": float(cl[n - 1]),
                "time": idx[n - 1].isoformat(), "bars": n}
    mark = float(cl[n - 1]) if n else e0
    return {"closed": False, "units": units, "stop": stop, "r": value(mark), "bars": n}


def open_new(cfg, state, candidates, day, setup_id, dry_run=False, send=None):
    """Z denních kandidátů (stejné signály jako hlavní skener) otevře pyramidové pozice s vlastními limity."""
    p = params(cfg)
    if not p["enabled"]:
        return []
    st = state.data.setdefault("pyramid", {"open": [], "closed": [], "seen": {}, "per_day": {}})
    msgs = []
    for symbol, source, tf, df, s, strat in sorted(candidates, key=lambda x: x[4].rr[0], reverse=True):
        if strat["name"] not in p["strategies"] or s.rr[0] < strat.get("min_rr", 1.0):
            continue
        pid = "pyr|" + setup_id(symbol, tf, s)
        if pid in st["seen"]:
            continue
        st["seen"][pid] = day
        if any(o["symbol"] == symbol and o["strategy"] == strat["name"] for o in st["open"]):
            continue
        if sum(1 for o in st["open"] if o["strategy"] == strat["name"] and o["direction"] == s.direction) >= p["max_open_per_direction"]:
            continue
        if st["per_day"].get(day, 0) >= p["max_new_per_day"]:
            continue
        st["per_day"] = {day: st["per_day"].get(day, 0) + 1}
        atr = float((s.meta or {}).get("atr") or abs(s.entry - s.stop) / 2)
        pos = {"id": pid, "symbol": symbol, "timeframe": tf, "strategy": strat["name"], "direction": s.direction,
               "entry": float(s.entry), "stop": float(s.stop), "atr": atr, "hold_time": s.hold_time.isoformat(),
               "notified_units": 1, "opened": datetime.now(timezone.utc).isoformat()}
        st["open"].append(pos)
        sg = 1 if s.direction == "long" else -1
        adds = ", ".join(_fmt(s.entry + sg * k * p["add_atr"] * atr) for k in range(1, p["max_units"]))
        msgs.append(f"🔺 Pyramida (papírově): {symbol} {s.direction.upper()} ({strat['name']}) – 1. kus ({_num(p['unit_r'], 1)} R) "
                    f"@ {_fmt(s.entry)}, stop {_fmt(s.stop)}. Přikoupím po +{_num(p['add_atr'], 1)[1:]} ATR: {adds} "
                    f"(max. {p['max_units']} kusy), stop vždy přidání − {_num(p['add_stop_atr'], 1)[1:]} ATR, "
                    f"trailing {_num(p['trail_atr'], 1)[1:]} ATR, max. {p['max_hold_bars']} dní.")
    _send(msgs, cfg, dry_run, send)
    return msgs


def update(cfg, state, frames, cost_pct, dry_run=False, send=None):
    """Přidané kusy a uzavření oznámí; uzavřené zapíše do research/pyramid_outcomes.jsonl."""
    p = params(cfg)
    st = state.data.get("pyramid")
    if not p["enabled"] or not st:
        return []
    msgs, still = [], []
    for pos in st["open"]:
        df = frames.get((pos["symbol"], pos["timeframe"]))
        if df is None:
            still.append(pos)
            continue
        res = simulate(pos, df[df.index > pd.Timestamp(pos["hold_time"])], p, cost_pct)
        side = f"{pos['symbol']} {pos['direction'].upper()}"
        for k in range(pos["notified_units"], len(res["units"])):
            t, px = res["units"][k]
            msgs.append(f"🔺 Pyramida: {side} – přikoupen {k + 1}. kus @ {_fmt(px)}; stop všech kusů {_fmt(res['stop'])}.")
        pos["notified_units"] = len(res["units"])
        if not res["closed"]:
            pos["r_now"], pos["stop_now"] = round(res["r"], 3), res["stop"]
            still.append(pos)
            continue
        out = {"id": pos["id"], "symbol": pos["symbol"], "strategy": pos["strategy"], "direction": pos["direction"],
               "entry": pos["entry"], "stop": pos["stop"], "units": len(res["units"]), "unit_prices": [u[1] for u in res["units"]],
               "exit": res["exit"], "reason": res["reason"], "r": round(res["r"], 3), "bars": res["bars"],
               "closed_at": res["time"]}
        st.setdefault("closed", []).append(out)
        if not dry_run:
            try:
                with open(OUTCOMES, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(out, ensure_ascii=False) + "\n")
            except Exception as exc:
                print(f"pyramida deník: {exc}", file=sys.stderr)
        why = "stop" if res["reason"] == "stop" else "časový výstup"
        msgs.append(f"🔺📕 Pyramida uzavřena: {side} – {why}, {len(res['units'])} kus(y), {_num(res['r'])} R po nákladech.")
    st["open"] = still
    _send(msgs, cfg, dry_run, send)
    return msgs


def heartbeat_line(state):
    st = state.data.get("pyramid")
    if not st:
        return None
    closed = st.get("closed", [])
    opened = st.get("open", [])
    parts = [f"{o['symbol'].split('/')[0]} {o['direction'][0].upper()} {o.get('notified_units', 1)}× "
             f"{_num(o.get('r_now', 0))} R" for o in opened]
    return (f"🔺 Pyramida (papírově): otevřené {len(opened)}" + (f" ({', '.join(parts)})" if parts else "")
            + f", uzavřené {len(closed)}" + (f", Σ {_num(sum(c['r'] for c in closed))} R" if closed else ""))


def _fmt(x):
    return notify.fmt(x)


def _send(msgs, cfg, dry_run, send):
    tg = send or (None if dry_run or not cfg.get("notify", {}).get("telegram", True) else notify.telegram)
    for m in msgs:
        print(m)
        if tg:
            tg(m)
