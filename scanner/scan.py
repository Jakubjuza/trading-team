#!/usr/bin/env python3
"""Rychlý skener bez AI: o vstupu rozhoduje jen kód (scanner/setups.py, strategie v config.yaml).

Použití:
    python3 scanner/scan.py              # běží nepřetržitě, kontrola každých poll_seconds
    python3 scanner/scan.py --once       # jeden průchod a konec (cron, GitHub Actions)
    python3 scanner/scan.py --once --dry-run   # nic neposílá, jen vypíše
"""
import argparse
import json
import shlex
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import broker, notify, rules, setups  # noqa: E402
from scanner.calibrate import strategies as cfg_strategies  # noqa: E402
from scanner.evaluate import simulate  # noqa: E402
from scanner.data import CandleCache  # noqa: E402
from research import sessions  # noqa: E402

STATE = HERE / "state.json"
SIGNALS = HERE / "signals.jsonl"   # deník signálů (commituje se, čte ho evaluate.py)
FACTSHEETS = HERE.parent / "research" / "factsheets"   # datové listy k signálům pro AI desk


class State:
    """Odeslané setupy (deduplikace) a počítadlo za den."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {"sent": {}}

    def seen(self, sid):
        return sid in self.data["sent"]

    def count_on(self, day):
        return sum(1 for v in self.data["sent"].values() if v.get("day") == day and "setup" in v)

    def add(self, sid, day, info):
        self.data["sent"][sid] = {"day": day, **info}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n")


def log_signal(path, rec):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def setup_id(symbol, tf, s):
    return f"{symbol}|{tf}|{s.direction}|{s.kind}|{s.breakout_time.isoformat()}"


def load_probabilities(cfg):
    """Tabulka pravděpodobností (scanner/calibrate.py) → {strategie: {"all", "recent", "after_t1"}}."""
    path = HERE.parent / cfg.get("probabilities", "scanner/probabilities.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    out = {}
    for name, v in data.get("strategies", {}).items():
        t = v.get("table", {})
        out[name] = {"all": t.get("*|*|*", {}), "recent": v.get("recent", {}), "after_t1": t.get("_after_t1", {})}
    return out


def scan_once(cfg, cache, state, dry_run=False, now=None, status=None):
    """status (dict) se doplní o poslední ceny a chyby – pro zprávu o stavu."""
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC"))).date().isoformat()
    found = []
    status = status if status is not None else {}
    status.setdefault("prices", {})
    status.setdefault("errors", {})
    strats = cfg_strategies(cfg)
    probs = load_probabilities(cfg)
    candidates, frames = [], {}
    for t in cfg["tickers"]:
        symbol, source = t["symbol"], t["source"]
        for strat in strats:
            tf = strat.get("timeframe") or t.get("timeframe", cfg["timeframe"])
            if (symbol, tf) not in frames:
                try:
                    frames[(symbol, tf)] = cache.update(source, symbol, tf, now=now)
                except Exception as exc:  # síť, burza… další ticker
                    print(f"[{symbol} {tf}] data nedostupná: {exc}", file=sys.stderr)
                    status["errors"][symbol] = f"{exc.__class__.__name__}: {str(exc)[:80]}"
                    frames[(symbol, tf)] = None
            df = frames[(symbol, tf)]
            if df is None or len(df) < 23:
                if df is not None:
                    status["errors"][symbol] = f"málo dat {tf} ({len(df)} svíček)"
                continue
            if tf == cfg.get("timeframe", "1h") or symbol not in status["prices"]:
                status["prices"][symbol] = (float(df["Close"].iloc[-1]), df.index[-1].isoformat())
            for s in setups.find(strat["setup"], df, t.get("direction", cfg["direction"]), strat.get("params"),
                                 last_only=True):
                candidates.append((symbol, source, tf, df, s, strat))

    costs = cfg.get("costs", {})
    cost_pct = costs.get("fee_pct", 0) + costs.get("slippage_pct", 0)
    update_paper_positions(cfg, state, frames, cost_pct, dry_run, probs)
    approach_alerts(cfg, state, frames, strats, now, day, dry_run)

    # krypto se hýbe spolu → max. N otevřených (papírových) pozic stejným směrem na strategii; přednost má lepší R:R
    candidates.sort(key=lambda x: x[4].rr[0], reverse=True)
    per_dir = {}
    for pos in state.data.get("open", []):
        k = (pos.get("strategy", strats[0]["name"]), pos["setup"]["direction"])
        per_dir[k] = per_dir.get(k, 0) + 1
    for symbol, source, tf, df, s, strat in candidates:
        sid = setup_id(symbol, tf, s)
        if state.seen(sid):
            continue
        min_rr = strat.get("min_rr", cfg.get("min_rr", 1.0))
        if s.rr[0] < min_rr:
            print(f"[{symbol}] {strat['name']} {s.direction} vyřazen: R:R {s.rr[0]} < {min_rr}")
            state.add(sid, day, {"sent": False, "reason": "rr"})
            continue
        key = (strat["name"], s.direction)
        if per_dir.get(key, 0) >= strat.get("max_open_per_direction", cfg.get("max_open_per_direction", 99)):
            print(f"[{symbol}] {strat['name']} {s.direction} vyřazen: plno otevřených pozic stejným směrem (korelace)")
            state.add(sid, day, {"sent": False, "reason": "correlation"})
            continue
        if state.count_on(day) >= cfg["max_setups_per_day"]:
            print(f"[{symbol}] denní limit {cfg['max_setups_per_day']} vyčerpán")
            continue
        size = rules.position_size(s, cfg["account_size"], cfg["risk_pct"],
                                   fractional=source == "crypto", cash_only=cfg.get("cash_only", True))
        if size["qty"] <= 0:
            continue
        per_dir[key] = per_dir.get(key, 0) + 1
        prob = probs.get(strat["name"])
        try:
            ctx = sessions.context_line(now, symbol.split("/")[0])
        except Exception as exc:                                      # kontext nesmí shodit signál
            ctx = ""
            print(f"[{symbol}] kontext burz selhal: {exc}", file=sys.stderr)
        lines = notify.summary_lines(symbol, tf, s, size, cfg["account_size"], cost_pct, prob=prob, context=ctx)
        print("\n".join(lines))
        found.append((sid, s, size))
        if dry_run:
            continue
        chart = None
        if cfg["notify"].get("chart", True):
            chart = notify.render_chart(symbol, tf, s, df, lines, HERE / "out", cfg["notify"].get("chart_bars", 80))
        sent = notify.telegram("\n".join(lines), photo=chart) if cfg["notify"].get("telegram", True) else False
        if cfg.get("paper_trading", True):
            broker.place_order({"setup_id": sid, "symbol": symbol, "side": "buy" if s.direction == "long" else "sell",
                                "qty": size["qty"], "entry": s.entry, "stop": s.stop, "targets": s.targets}, cfg)
        state.add(sid, day, {"sent": sent, "setup": s.to_dict(), "size": size, "strategy": strat["name"]})
        state.data.setdefault("open", []).append({"id": sid, "symbol": symbol, "timeframe": tf, "setup": s.to_dict(),
                                                  "strategy": strat["name"], "exit": strat.get("exit", {})})
        state.save()
        rec = {"id": sid, "symbol": symbol, "source": source, "timeframe": tf, "strategy": strat["name"],
               "found_at": now.isoformat(), "rules": strat.get("params", {}), "exit": strat.get("exit", {}),
               "min_rr": min_rr, "setup": s.to_dict(), "size": size, "telegram": sent,
               "probabilities": prob}
        rec["factsheet"] = _write_factsheet(cfg, rec)
        log_signal(SIGNALS, rec)
        _ai_explain(cfg, s, sid)
    return found


def approach_alerts(cfg, state, frames, strats, now, day, dry_run=False):
    """„⏳ setup se blíží“: cena u hladiny Donchian kanálu ve směru trendu (jen informace)."""
    ac = cfg.get("approach_alerts") or {}
    if not ac.get("enabled"):
        return []
    sent_today = state.data.setdefault("approach", {})
    sent_today = {k: v for k, v in sent_today.items() if v == day}
    out = []
    for strat in strats:
        if strat["setup"] != "donchian_breakout":
            continue
        p = setups.params_for("donchian_breakout", strat.get("params"))
        for (symbol, tf), df in frames.items():
            if tf != strat["timeframe"] or df is None or len(df) < max(p["channel"], p.get("trend_ema") or 0) + 2:
                continue
            live = frames.get((symbol, cfg.get("timeframe", "1h")))
            price = float(live["Close"].iloc[-1]) if live is not None and len(live) else float(df["Close"].iloc[-1])
            x = setups.Ctx(df)
            hi, lo = float(df["High"].iloc[-p["channel"]:].max()), float(df["Low"].iloc[-p["channel"]:].min())
            atr = float(x.atr[-1])
            ema = x.ema(p["trend_ema"])[-1] if p.get("trend_ema") else None
            for d, lvl in (("long", hi), ("short", lo)):
                if ema is not None and ((d == "long" and price <= ema) or (d == "short" and price >= ema)):
                    continue
                dist = (lvl - price) if d == "long" else (price - lvl)
                if not (0 < dist <= ac.get("atr_distance", 0.5) * atr):
                    continue
                key = f"{symbol}|{strat['name']}|{d}"
                if key in sent_today or len(sent_today) >= ac.get("max_per_day", 4):
                    continue
                word = "nad" if d == "long" else "pod"
                msg = (f"⏳ Blíží se: {symbol} {d.upper()} – {setups.NAMES_CS['donchian_breakout']} ({tf}). "
                       f"Signál vznikne, pokud denní svíčka zavře {word} {notify.fmt(lvl)} "
                       f"(teď {notify.fmt(price)}, {abs(dist) / price * 100:.1f} %). Denní svíčka končí v 00:00 UTC. "
                       f"Jen informace, ne signál ke vstupu.").replace(".", ",", 0)
                print(msg)
                sent_today[key] = day
                out.append(msg)
                if not dry_run and cfg.get("notify", {}).get("telegram", True):
                    notify.telegram(msg)
    state.data["approach"] = sent_today
    state.save()
    return out


def update_paper_positions(cfg, state, frames, cost_pct, dry_run=False, probs=None):
    """Vyhodnotí otevřené papírové pozice na nových svíčkách; T1 a uzavření oznámí na Telegram."""
    probs = probs or {}
    still_open = []
    tg = (not dry_run) and cfg.get("notify", {}).get("telegram", True)
    for pos in state.data.get("open", []):
        df = frames.get((pos["symbol"], pos["timeframe"]))
        if df is None:
            still_open.append(pos)
            continue
        ex = {**cfg.get("exit", {}), **pos.get("exit", {})}
        after = df[df.index > pd.Timestamp(pos["setup"]["hold_time"])]
        res = simulate(pos["setup"], after, ex.get("max_hold_bars", 48), ex.get("split", 0.5),
                       cost_pct, ex.get("trail_atr", 0))
        side = pos["setup"]["direction"].upper()
        if res["result"] == "open":
            if res.get("t1") and not pos.get("t1_notified"):
                pos["t1_notified"] = True
                a = (probs.get(pos.get("strategy")) or {}).get("after_t1", {})
                hist = (f" Z historie po T1: Ø {a['avg_r']:+.2f} R, ≥2R v {a['p_2r']:.0%} případů ({a['n']} obchodů)."
                        .replace(".", ",", 0) if a.get("n") else "")
                msg = (f"🎯 T1 dosažen: {pos['symbol']} {side} – vybrána část pozice, stop zbytku na vstup "
                       f"(break-even).{hist}")
                print(msg)
                if tg:
                    notify.telegram(msg)
            still_open.append(pos)
            continue
        state.data.setdefault("closed", []).append({"id": pos["id"], "symbol": pos["symbol"], "strategy": pos.get("strategy"),
                                                    "direction": pos["setup"]["direction"], **res})
        txt = {"stop": "stop", "T1+BE": "T1, zbytek na break-even / trailing stop", "T2": "T1 i T2",
               "time": "časový výstup"}[res["result"]]
        msg = (f"📕 Papírový obchod uzavřen: {pos['symbol']} {side} – {txt}, "
               f"{res['r']:+.2f} R po nákladech ({res['bars']} svíček)")
        print(msg)
        if tg:
            notify.telegram(msg)
    state.data["open"] = still_open
    state.save()


def maybe_heartbeat(cfg, state, status, found, now, send=None):
    """Zpráva „skener běží“ každých heartbeat_hours (0 = vypnuto), i když nic nenašel.

    Počítadla se drží v state.json, takže to funguje i při --once v GitHub Actions.
    """
    hours = cfg.get("heartbeat_hours", 4) if cfg.get("notify", {}).get("telegram", True) or send else 0
    hb = state.data.setdefault("heartbeat", {"last": None, "scans": 0, "setups": 0, "errors": 0})
    hb["scans"] += 1
    hb["setups"] += len(found)
    hb["errors"] += 1 if status.get("errors") else 0
    last = datetime.fromisoformat(hb["last"]) if hb["last"] else None
    due = hours and (last is None or (now - last).total_seconds() >= hours * 3600)
    if not due:
        state.save()
        return None
    tz = ZoneInfo(cfg.get("timezone", "UTC"))
    title = "🟢 Skener spuštěn a hledá" if last is None else "🟢 Skener běží"
    period = "od spuštění" if last is None else f"za posledních {hours} h"
    lines = [f"{title} ({now.astimezone(tz):%d.%m. %H:%M})",
             f"{period}: {hb['scans']} průchodů, nových setupů: {hb['setups']}"]
    if status.get("prices"):
        lines.append(" · ".join(f"{sym} {notify.fmt(p)}" for sym, (p, _) in status["prices"].items()))
    closed = state.data.get("closed", [])
    lines.append(f"Papírově: otevřené {len(state.data.get('open', []))}, uzavřené {len(closed)}"
                 + (f", Σ {sum(c['r'] for c in closed):+.2f} R" if closed else ""))
    if status.get("errors"):
        lines.append("⚠️ Problém s daty: " + "; ".join(f"{k} – {v}" for k, v in status["errors"].items()))
    try:
        up = sessions.upcoming_line(now, hours)
        if up:
            lines.append(up)
    except Exception as exc:
        print(f"kontext burz selhal: {exc}", file=sys.stderr)
    rules_txt = ", ".join(f"{setups.NAMES_CS.get(st['setup'], st['setup'])} {st['timeframe']}" for st in cfg_strategies(cfg))
    lines.append(f"Hlídám: {rules_txt}. Další zpráva o stavu za {hours} h.")
    text = "\n".join(lines)
    ok = (send or notify.telegram)(text)
    if ok:
        state.data["heartbeat"] = {"last": now.isoformat(), "scans": 0, "setups": 0, "errors": 0}
    state.save()
    return text


def _write_factsheet(cfg, rec):
    """Datový list k signálu pro AI desk (research/factsheets/). Vrátí relativní cestu, nebo None."""
    if not cfg.get("factsheet", False) or rec["source"] != "crypto":
        return None
    try:
        from research import factsheet
        sheet = factsheet.build(rec["symbol"], cfg.get("exchange", "kraken"), signal=rec)
        name = rec["id"].replace("|", "_").replace("/", "-").replace(":", "")
        path = FACTSHEETS / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sheet, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
        return str(path.relative_to(HERE.parent))
    except Exception as exc:
        print(f"Datový list se nepovedl: {exc}", file=sys.stderr)
        return None


def _ai_explain(cfg, s, sid):
    """Volitelně: AI vysvětlení AŽ po nalezení setupu."""
    ai = cfg.get("ai_explain") or {}
    if not ai.get("enabled"):
        return
    path = HERE / "out" / (sid.replace("|", "_").replace("/", "-").replace(":", "") + ".json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(s.to_dict(), ensure_ascii=False, indent=2))
    try:
        r = subprocess.run(shlex.split(ai["command"].format(setup_json=path)), capture_output=True, text=True, timeout=600)
        if r.stdout.strip():
            notify.telegram(r.stdout.strip()[:4000])
    except Exception as exc:
        print(f"AI vysvětlení selhalo: {exc}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=HERE / "config.yaml")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if cfg.get("live_trading"):
        print("POZOR: live_trading je zapnuté, ale skener ostré příkazy nikdy neposílá bez potvrzení.", file=sys.stderr)
    cache = CandleCache(HERE / "cache", cfg.get("history_bars", 300), cfg.get("exchange", "kraken"))
    state = State(STATE)
    while True:
        started = time.time()
        try:
            status = {}
            found = scan_once(cfg, cache, state, dry_run=args.dry_run, status=status)
            print(f"{datetime.now():%H:%M:%S} průchod hotov, nových setupů: {len(found)}")
            if not args.dry_run:
                maybe_heartbeat(cfg, state, status, found, datetime.now(timezone.utc))
        except Exception:
            traceback.print_exc()
        if args.once:
            break
        time.sleep(max(1, cfg.get("poll_seconds", 60) - (time.time() - started)))


if __name__ == "__main__":
    main()
