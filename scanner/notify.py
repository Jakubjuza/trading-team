"""Telegram + graf. Token a chat ID jen z proměnných prostředí."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / ".claude" / "skills" / "chart-report" / "render_chart.py"


def fmt(p):
    dec = 0 if abs(p) >= 1000 else (2 if abs(p) >= 1 else 4)
    return f"{p:,.{dec}f}".replace(",", " ").replace(".", ",")


def pct(x):
    return f"{x:.2f}".replace(".", ",")


def prob_line(prob):
    """Řádek s historickými pravděpodobnostmi strategie (z scanner/probabilities.json)."""
    if not prob:
        return "Historie: pro tuto strategii zatím není tabulka pravděpodobností."
    t, rec = prob.get("all", {}), prob.get("recent", {})
    if not t.get("n"):
        return "Historie: málo dat."
    out = (f"Historie ({t['n']} obchodů): zisk {t['p_win']:.0%} · T1 {t['p_t1']:.0%} · ≥2R {t['p_2r']:.0%} · "
           f"Ø {t['avg_r']:+.2f} R".replace(".", ",").replace("%", " %"))
    if rec.get("n"):
        out += f" (posledních 30 %: Ø {rec['avg_r']:+.2f} R)".replace(".", ",")
    return out


def summary_lines(ticker, tf, s, size, account, cost_pct=0.0, setup_name=None, prob=None, context="", outlook=""):
    """Pět řádků shrnutí (formát z CLAUDE.md, bez AI)."""
    from scanner.setups import NAMES_CS
    side = "LONG" if s.direction == "long" else "SHORT"
    name = setup_name or NAMES_CS.get(s.kind, s.kind)
    tg = " / ".join(f"T{i + 1} {fmt(t)}" for i, t in enumerate(s.targets))
    rr = " / ".join(str(r).replace(".", ",") for r in s.rr)
    stop_pct = abs(s.entry - s.stop) / s.entry * 100
    risk = abs(s.entry - s.stop)
    rr_net = " / ".join(pct(abs(t - s.entry) / risk - cost_pct / 100 * (s.entry + t) / risk).rstrip("0").rstrip(",")
                        for t in s.targets)
    inval = "close pod" if s.direction == "long" else "close nad"
    level = f" u {fmt(s.level)}" if s.kind in ("breakout_retest_hold", "donchian_breakout", "sweep_reclaim") else ""
    return [
        f"1. {ticker} {side} {tf} – {name}{level}",
        f"2. Vstup {fmt(s.entry)} · Stop {fmt(s.stop)} ({pct(stop_pct)} %) · {tg}" + (f" · {outlook}" if outlook else ""),
        f"3. R:R {rr} (po nákladech {rr_net}) · {str(size['qty']).replace('.', ',')} ks ≈ {fmt(size['notional'])} USD · riziko {fmt(size['risk_usd'])} USD ({pct(size['risk_usd'] / account * 100)} % účtu)",
        f"4. Zneplatnění: {inval} stop {fmt(s.stop)} · ATR {fmt(s.meta['atr'])}" + (f" · {context}" if context else ""),
        f"5. {prob_line(prob)} · papírově · nejde o finanční poradenství",
    ]


def render_chart(ticker, tf, s, df, lines, out_dir, bars=80):
    """Vykreslí PNG přes skript chart-report. Vrátí cestu, nebo None."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{ticker.replace('/', '-')}_{tf}_{s.hold_time:%Y%m%d_%H%M}"
    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "data.csv"
        d = df.tail(bars).copy()
        d.index.name = "Date"
        d.index = d.index.tz_convert(None)
        d.to_csv(csv)
        spec = {
            "ticker": ticker, "direction": s.direction,
            "title": f"{ticker} {tf} – {'LONG' if s.direction == 'long' else 'SHORT'} {lines[0].split(' – ', 1)[-1]}",
            "bars": bars, "horizon_bars": 10, "datetime_format": "%d.%m." if tf == "1d" else "%d.%m. %H:%M", "decimals": 0 if s.entry >= 1000 else (2 if s.entry >= 1 else 4),
            "entry": s.entry, "stop": s.stop,
            "targets": [{"label": f"T{i + 1}", "price": t} for i, t in enumerate(s.targets)],
            "range": {"low": s.range_low, "high": s.range_high, "label": "Range", "high_label": "Range high"},
            "scenarios": [],
            "caption": " · ".join(l.split(". ", 1)[1] for l in lines[1:4]),
            "data_source": "cache skeneru",
        }
        spec_path = Path(tmp) / "spec.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False))
        out = out_dir / f"{stem}.png"
        r = subprocess.run([sys.executable, str(RENDER), "--spec", str(spec_path), "--csv", str(csv), "--out", str(out)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"Graf se nepovedl: {r.stdout}{r.stderr}", file=sys.stderr)
            return None
    return out


def telegram(text, photo=None):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID nejsou nastavené – zpráva neodeslána.", file=sys.stderr)
        return False
    base = f"https://api.telegram.org/bot{token}"
    if photo and Path(photo).exists() and len(text) <= 1024:
        with open(photo, "rb") as fh:
            r = requests.post(f"{base}/sendPhoto", data={"chat_id": chat, "caption": text}, files={"photo": fh}, timeout=30)
    else:
        r = requests.post(f"{base}/sendMessage", data={"chat_id": chat, "text": text}, timeout=30)
    if not r.ok:
        print(f"Telegram chyba {r.status_code}: {r.text[:200]}", file=sys.stderr)
    return r.ok
