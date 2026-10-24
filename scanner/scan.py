#!/usr/bin/env python3
"""Rychlý skener bez AI: o vstupu rozhoduje jen kód (scanner/rules.py).

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

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import broker, notify, rules  # noqa: E402
from scanner.data import CandleCache  # noqa: E402

STATE = HERE / "state.json"
SIGNALS = HERE / "signals.jsonl"   # deník signálů (commituje se, čte ho evaluate.py)


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


def scan_once(cfg, cache, state, dry_run=False, now=None, status=None):
    """status (dict) se doplní o poslední ceny a chyby – pro zprávu o stavu."""
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC"))).date().isoformat()
    found = []
    status = status if status is not None else {}
    status.setdefault("prices", {})
    status.setdefault("errors", {})
    for t in cfg["tickers"]:
        symbol, source = t["symbol"], t["source"]
        tf = t.get("timeframe", cfg["timeframe"])
        try:
            df = cache.update(source, symbol, tf, now=now)
        except Exception as exc:  # síť, burza… další ticker
            print(f"[{symbol}] data nedostupná: {exc}", file=sys.stderr)
            status["errors"][symbol] = f"{exc.__class__.__name__}: {str(exc)[:80]}"
            continue
        if len(df):
            status["prices"][symbol] = (float(df["Close"].iloc[-1]), df.index[-1].isoformat())
        if len(df) < cfg["rules"]["range_lookback"] + 3:
            status["errors"][symbol] = f"málo dat ({len(df)} svíček)"
            continue
        for s in rules.latest_setup(df, t.get("direction", cfg["direction"]), cfg["rules"]):
            sid = setup_id(symbol, tf, s)
            if state.seen(sid):
                continue
            if s.rr[0] < cfg["min_rr"]:
                print(f"[{symbol}] {s.direction} setup vyřazen: R:R {s.rr[0]} < {cfg['min_rr']}")
                state.add(sid, day, {"sent": False, "reason": "rr"})
                continue
            if state.count_on(day) >= cfg["max_setups_per_day"]:
                print(f"[{symbol}] denní limit {cfg['max_setups_per_day']} vyčerpán")
                continue
            size = rules.position_size(s, cfg["account_size"], cfg["risk_pct"],
                                       fractional=source == "crypto", cash_only=cfg.get("cash_only", True))
            if size["qty"] <= 0:
                continue
            lines = notify.summary_lines(symbol, tf, s, size, cfg["account_size"])
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
            state.add(sid, day, {"sent": sent, "setup": s.to_dict(), "size": size})
            log_signal(SIGNALS, {"id": sid, "symbol": symbol, "source": source, "timeframe": tf,
                                 "found_at": now.isoformat(), "rules": cfg["rules"], "min_rr": cfg["min_rr"],
                                 "setup": s.to_dict(), "size": size, "telegram": sent})
            _ai_explain(cfg, s, sid)
    return found


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
    if status.get("errors"):
        lines.append("⚠️ Problém s daty: " + "; ".join(f"{k} – {v}" for k, v in status["errors"].items()))
    rules_txt = f"{cfg['timeframe']} · {cfg['direction']} · R:R ≥ {cfg['min_rr']} · breakout → retest → hold"
    lines.append(f"Hlídám: {rules_txt}. Další zpráva o stavu za {hours} h.")
    text = "\n".join(lines)
    ok = (send or notify.telegram)(text)
    if ok:
        state.data["heartbeat"] = {"last": now.isoformat(), "scans": 0, "setups": 0, "errors": 0}
    state.save()
    return text


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
