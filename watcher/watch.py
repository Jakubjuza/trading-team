#!/usr/bin/env python3
"""Hlídač úrovní: bez AI, běží v GitHub Actions každých 15 min.

Čte watcher/levels.json (zapisuje ho skener), stáhne svíčky přes yfinance
a když setup splní spouštěč, pošle zprávu na Telegram. Stav (co už bylo
oznámeno) drží ve watcher/state.json.

Proměnné prostředí: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
Použití: python3 watcher/watch.py [--test] [--dry-run]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ROOT / "watcher" / "levels.json"
STATE = ROOT / "watcher" / "state.json"
REPO_URL = "https://github.com/Jakubjuza/trading-team/blob/main/"
TF_MINUTES = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}
YF_INTERVAL = {"15m": "15m", "1h": "60m", "4h": "60m", "1d": "1d"}
YF_PERIOD = {"15m": "5d", "1h": "7d", "4h": "30d", "1d": "6mo"}


def fmt(p):
    if p is None:
        return "–"
    dec = 0 if abs(p) >= 1000 else (2 if abs(p) >= 1 else 4)
    return f"{p:,.{dec}f}".replace(",", " ").replace(".", ",")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def telegram(text, photo=None, dry=False):
    if dry:
        print("--- TELEGRAM (dry-run) ---\n" + text + (f"\n[foto: {photo}]" if photo else ""))
        return True
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Chybí TELEGRAM_BOT_TOKEN nebo TELEGRAM_CHAT_ID.", file=sys.stderr)
        return False
    base = f"https://api.telegram.org/bot{token}"
    if photo and Path(photo).exists() and len(text) <= 1000:
        with open(photo, "rb") as fh:
            r = requests.post(f"{base}/sendPhoto", data={"chat_id": chat, "caption": text}, files={"photo": fh}, timeout=30)
    else:
        r = requests.post(f"{base}/sendMessage", data={"chat_id": chat, "text": text, "disable_web_page_preview": True}, timeout=30)
    if not r.ok:
        print(f"Telegram chyba {r.status_code}: {r.text[:200]}", file=sys.stderr)
    return r.ok


def closed_candles(symbol, tf):
    """Uzavřené svíčky daného rámce (poslední rozpracovaná se zahodí)."""
    df = yf.download(symbol, period=YF_PERIOD[tf], interval=YF_INTERVAL[tf], progress=False, auto_adjust=False)
    if df is None or df.empty:
        return None
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)
    if tf == "4h":
        df = df.resample("4h", origin="epoch").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    now = datetime.now(timezone.utc)
    end = df.index + timedelta(minutes=TF_MINUTES[tf])
    return df[end <= now]


def check_trigger(setup, df):
    """Vrátí (spuštěno, popis) podle poslední uzavřené svíčky."""
    trig = setup["trigger"]
    t, lvl = trig["type"], float(trig["level"])
    last = df.iloc[-1]
    vol_ok = True
    if trig.get("min_volume_x") and len(df) > 21:
        avg = df["Volume"].iloc[-21:-1].mean()
        vol_ok = avg > 0 and last["Volume"] >= trig["min_volume_x"] * avg
    tol = float(trig.get("tolerance_pct", 0.3)) / 100
    if t == "close_above":
        hit = last["Close"] > lvl
    elif t == "close_below":
        hit = last["Close"] < lvl
    elif t == "retest_long":   # dotkne se úrovně shora a zavře nad ní
        hit = last["Low"] <= lvl * (1 + tol) and last["Close"] > lvl
    elif t == "retest_short":  # dotkne se úrovně zespodu a zavře pod ní
        hit = last["High"] >= lvl * (1 - tol) and last["Close"] < lvl
    else:
        return False, f"neznámý typ spouštěče {t}"
    return bool(hit and vol_ok), f"close {fmt(float(last['Close']))} ({df.index[-1]:%d.%m. %H:%M} UTC)"


def invalidated(setup, df):
    """Cena prošla stopem dřív, než se setup spustil."""
    last = df.iloc[-1]
    if setup["direction"] == "long":
        return float(last["Close"]) < setup["stop"]
    return float(last["Close"]) > setup["stop"]


def setup_lines(s):
    tg = " / ".join(f"{t.get('label', 'T')} {fmt(t['price'])}" for t in s.get("targets", []))
    lines = [
        f"Vstup {fmt(s.get('entry'))} · Stop {fmt(s['stop'])} · {tg}",
        f"R:R {s.get('rr', '–')} · {s.get('size', '')}".rstrip(" ·"),
    ]
    if s.get("risk"):
        lines.append(f"Hlavní riziko: {s['risk']}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="pošle testovací zprávu a skončí")
    ap.add_argument("--dry-run", action="store_true", help="nic neposílá, jen vypíše")
    ap.add_argument("--levels", type=Path, default=LEVELS)
    ap.add_argument("--state", type=Path, default=STATE)
    args = ap.parse_args()

    if args.test:
        ok = telegram("✅ Hlídač trading-team je připojený. Upozornění na spouštěče budou chodit sem.", dry=args.dry_run)
        sys.exit(0 if ok else 1)

    levels = load_json(args.levels, {"setups": []})
    state = load_json(args.state, {"announced": [], "fired": [], "closed": []})
    now = datetime.now(timezone.utc)
    changed = False
    cache = {}

    for s in levels.get("setups", []):
        sid = s["id"]
        if sid in state["fired"] or sid in state["closed"]:
            continue
        valid = datetime.fromisoformat(s["valid_until"])
        head = f"{s['ticker']} {s['direction'].upper()} – {s.get('setup', '')}".strip(" –")

        if valid < now:
            state["closed"].append(sid)
            changed = True
            continue

        if sid not in state["announced"]:
            trig = s["trigger"]
            msg = [f"📋 Nový hlídaný setup: {head} (kvalita {s.get('quality', '–')})",
                   f"Spouštěč: {trig.get('text') or trig['type'] + ' ' + fmt(trig['level'])} ({trig.get('timeframe', '1h')})",
                   *setup_lines(s),
                   f"Platí do {valid.astimezone(ZoneInfo('Europe/Prague')).strftime('%d.%m. %H:%M')} (Praha)"]
            if telegram("\n".join(msg), dry=args.dry_run):
                state["announced"].append(sid)
                changed = True

        tf = s["trigger"].get("timeframe", "1h")
        key = (s["yf_symbol"], tf)
        if key not in cache:
            try:
                cache[key] = closed_candles(*key)
            except Exception as exc:  # síť, Yahoo limit…
                print(f"{key}: data nedostupná ({exc})", file=sys.stderr)
                cache[key] = None
        df = cache[key]
        if df is None or df.empty:
            continue

        if invalidated(s, df):
            telegram(f"❌ {head}: zneplatněno, cena prošla stopem {fmt(s['stop'])} před spuštěním. Nevstupovat.",
                     dry=args.dry_run)
            state["closed"].append(sid)
            changed = True
            continue

        hit, desc = check_trigger(s, df)
        if hit:
            chart = ROOT / s["chart"] if s.get("chart") else None
            msg = [f"🔔 SPOUŠTĚČ: {head}",
                   f"{s['trigger'].get('text') or s['trigger']['type']} – {desc}",
                   *setup_lines(s),
                   f"Plán: {REPO_URL}{s['chart']}" if s.get("chart") else "",
                   "Nejde o finanční poradenství."]
            if telegram("\n".join(m for m in msg if m), photo=chart, dry=args.dry_run):
                state["fired"].append(sid)
                changed = True
        else:
            print(f"{sid}: čeká ({desc})")

    if changed and not args.dry_run:
        args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("state.json aktualizován")


if __name__ == "__main__":
    main()
