"""🎯 Vstup NA PRŮRAZU ÚROVNĚ – papírově souběžně s denním donchian_1d (5. 11. 2026, reports/level_entry.md).

Místo čekání na zavření denní svíčky: na začátku dne je známá úroveň (20denní min/max z předchozích dní), trend
(close včera vs. EMA200) a panika (včera). Jakmile hodinová svíčka úroveň protne a 1H je v trendu ve směru
(EMA20 vs. EMA50 na 1H), papírově se vstoupí NA ÚROVNI (+ 0,05 % skluz) se stopem za posledním 1H swingem
(6 svíček + 0,1 denního ATR, min 1,5 %). Cíle 2R/4R, 50 % na 2R, zbytek trailing 3 denní ATR, max 20 dní, náklady
0,15 %/stranu. Jedna pozice na minci. Stejná logika jako varianta E3 v research/experiments/level_entry.py.

V testu E3 vyšlo +0,34 R/obchod vs. +0,18 R dnešního vstupu, ale předem daná laťka (obě poloviny) těsně neprošla
→ jen papír, nic se neposílá na burzu. Rozhodne se po ~30 živých obchodech. Log: research/level_trades.jsonl.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, notify, setups as st  # noqa: E402

LOG = ROOT / "research" / "level_trades.jsonl"
SLIP, COST = 0.0005, 0.15


def _log(rec, path=None):
    path = Path(path or LOG)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def find_entry(d1, h1, day, p):
    """Vstup v den `day` (dnešek), nebo None. d1 = uzavřené denní svíčky (bez dneška), h1 = uzavřené hodinové."""
    d1 = d1[d1.index < day]
    n = p["channel"]
    if len(d1) < max(n + 2, p["trend_ema"]):
        return None
    x = st.Ctx(d1)
    i = len(d1) - 1
    hi, lo = float(d1["High"].iloc[-n:].max()), float(d1["Low"].iloc[-n:].min())
    e200 = float(x.ema(p["trend_ema"])[i])
    rk = x.vol_rank(p.get("panic_window", 365))[i]
    if not np.isnan(rk) and rk >= p["panic_vol_rank"]:
        return None
    a, c = float(x.atr[i]), float(x.c[i])
    today = h1[(h1.index >= day) & (h1.index < day + pd.Timedelta(days=1))]
    if today.empty:
        return None
    e20, e50 = st.ema(h1["Close"], 20), st.ema(h1["Close"], 50)
    for direction in ("long", "short"):
        long = direction == "long"
        if long and not (c > e200 and c <= hi):
            continue
        if not long and not (c < e200 and c >= lo):
            continue
        level = hi if long else lo
        hit = next((t for t, r in today.iterrows() if (r["High"] >= level if long else r["Low"] <= level)), None)
        if hit is None:
            continue
        j = h1.index.get_loc(hit)
        if j < 7:
            continue
        if not ((e20.iat[j - 1] > e50.iat[j - 1]) if long else (e20.iat[j - 1] < e50.iat[j - 1])):
            return {"skip": "1H není v trendu ve směru", "dir": direction, "time": hit, "level": level}
        sg = 1 if long else -1
        entry = level * (1 + sg * SLIP)
        o = float(h1["Open"].iat[j])
        entry = max(entry, o) if long else min(entry, o)
        mind = entry * p["min_stop_pct"] / 100
        prev = h1.iloc[j - 6:j]
        sw = float(prev["Low"].min()) - 0.1 * a if long else float(prev["High"].max()) + 0.1 * a
        stop = min(sw, entry - mind) if long else max(sw, entry + mind)
        risk = abs(entry - stop)
        return {"dir": direction, "time": hit, "level": level, "entry": entry, "stop": stop, "atr": a,
                "targets": [entry + sg * 2 * risk, entry + sg * 4 * risk]}
    return None


def manage(pos, h1, ex):
    """Výsledek otevřené pozice simulací na hodinových svíčkách po vstupní hodině (None = ještě běží)."""
    after = h1[h1.index > pd.Timestamp(pos["time"])]
    s = {"direction": pos["dir"], "entry": pos["entry"], "stop": pos["stop"], "targets": pos["targets"],
         "meta": {"atr": pos["atr"]}}
    res = ev.simulate(s, after, ex["max_hold_bars"] * 24, ex["split"], COST, ex["trail_atr"])
    if res["result"] == "open" or res["bars"] == 0:
        return None
    res["exit_time"] = after.index[res["bars"] - 1].isoformat()
    return res


def update(cfg, state, now, dry_run=False, send=None, fetch=None):
    lc = cfg.get("level_entry") or {}
    if not lc.get("enabled"):
        return []
    now = pd.Timestamp(now)
    hour = (now.floor("1h") - pd.Timedelta(hours=1)).isoformat()      # poslední uzavřená hodina
    stt = state.data.setdefault("level", {"last_eval": None, "open": [], "taken": {}})
    if stt["last_eval"] == hour:
        return []
    strat = next(s for s in cfg["strategies"] if s["name"] == lc.get("strategy", "donchian_1d"))
    p = {**strat["params"]}
    ex = strat["exit"]
    if fetch is None:
        from scanner import lab_paper
        exch = lab_paper._exchange()
        fetch = lambda coin, tf, bars: lab_paper.candles(exch, coin, tf, now, bars=bars)  # noqa: E731
    tg = send or (None if dry_run or not cfg.get("notify", {}).get("telegram", True) else notify.telegram)
    coins = lc.get("coins") or [t["symbol"].split("/")[0] for t in cfg.get("tickers", []) if t.get("source") == "crypto"]
    day = now.floor("1D")
    msgs, still = [], []
    h1s = {}
    for coin in coins:
        try:
            h1s[coin] = fetch(coin, "1h", 600)
        except Exception as exc:
            print(f"level: {coin} 1H selhalo: {exc.__class__.__name__}", file=sys.stderr)
    for pos in stt["open"]:
        h1 = h1s.get(pos["coin"])
        res = manage(pos, h1, ex) if h1 is not None else None
        if res is None:
            still.append(pos)
            continue
        _log({"event": "close", **{k: pos[k] for k in ("coin", "dir", "time", "entry", "stop")}, "result": res["result"],
              "r": res["r"], "exit_time": res["exit_time"], "logged": now.isoformat()})
        msgs.append(f"🎯📕 Vstup na průrazu · {pos['coin']} {pos['dir'].upper()}: {res['r']:+.2f} R ({res['result']}), "
                    f"papírově.")
    stt["open"] = still
    busy = {o["coin"] for o in stt["open"]}
    for coin in coins:
        if coin in busy or coin not in h1s or stt["taken"].get(coin) == day.isoformat():
            continue
        try:
            d1 = fetch(coin, "1d", 900)
        except Exception as exc:
            print(f"level: {coin} 1D selhalo: {exc.__class__.__name__}", file=sys.stderr)
            continue
        e = find_entry(d1, h1s[coin], day, p)
        if not e:
            continue
        stt["taken"][coin] = day.isoformat()
        if "skip" in e:
            _log({"event": "skip", "coin": coin, "dir": e["dir"], "time": e["time"].isoformat(), "level": e["level"],
                  "why": e["skip"], "logged": now.isoformat()})
            continue
        pos = {"coin": coin, **{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in e.items()}}
        stt["open"].append(pos)
        _log({"event": "open", **pos, "logged": now.isoformat()})
        msgs.append(f"🎯 Vstup na průrazu 20denní úrovně · {coin} {e['dir'].upper()} (papír, test vedle denního vstupu)\n"
                    f"Úroveň {notify.fmt(e['level'])} protnuta {e['time']:%d. %m. %H:%M} UTC, 1H v trendu. "
                    f"Vstup {notify.fmt(e['entry'])}, stop {notify.fmt(e['stop'])} (za 1H swingem), "
                    f"cíle {notify.fmt(e['targets'][0])} / {notify.fmt(e['targets'][1])}. Papírově, ne rada.")
    stt["last_eval"] = hour
    stt["taken"] = {k: v for k, v in stt["taken"].items() if v == day.isoformat()}
    state.save()
    for m in msgs:
        if tg:
            tg(m)
        print(m)
    return msgs
