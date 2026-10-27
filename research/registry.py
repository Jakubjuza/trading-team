"""Registr strategií: co laboratoř našla a v jakém je to stavu.

Stavy:  kandidát → papír → ověřeno, nebo → vyřazeno.
  - „papír“ a „ověřeno“ jsou aktivní: skener je papírově obchoduje (scanner/lab_paper.py), jen ve svých režimech trhu.
  - na skutečné peníze nejde nic automaticky – „ověřeno“ znamená jen „vyplatí se, abyste to posoudil“.
Pravidla přechodů (stanovena předem, research/lab.py):
  - papír → ověřeno:  ≥ 30 uzavřených papírových obchodů, Ø R > 0 a t ≥ 1,5
  - papír/ověřeno → vyřazeno:  ≥ 30 obchodů a Ø R < 0, nebo ≥ 15 obchodů a Ø R < −0,5
Soubor: research/registry.json (zapisuje laboratoř, čte skener a Agentown).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research" / "registry.json"
ACTIVE = ("papír", "ověřeno")

FAM_CS = {"ma_cross": "Protnutí průměrů", "price_ma": "Cena × průměr", "donchian": "Donchian průraz",
          "boll_break": "Bollinger průraz", "boll_fade": "Bollinger návrat", "rsi_revert": "RSI návrat",
          "rsi_mom": "RSI momentum", "macd": "MACD", "roc": "Momentum ROC", "supertrend": "Supertrend",
          "stoch": "Stochastic", "keltner": "Keltner průraz", "vol_break": "Průraz s objemem",
          "candle": "Svíčkové vzory", "sweep": "Sweep & reclaim", "fng": "Strach a chamtivost"}


def sid(r):
    return "|".join(str(r[k]) for k in ("family", "params", "tf", "filter", "exit", "dir"))


def label(r):
    d = "long" if r["dir"] == "long" else "short"
    return f"{FAM_CS.get(r['family'], r['family'])} {r['params'].replace('/', ' ')} · {r['tf'].upper()} {d}"


def load(path=PATH):
    p = Path(path)
    if not p.exists():
        return {"updated": None, "strategies": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save(reg, path=PATH):
    reg["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    Path(path).write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def active(reg):
    return [s for s in reg["strategies"] if s.get("status") in ACTIVE]


def find(reg, key):
    return next((s for s in reg["strategies"] if s["id"] == key), None)


def transition(s, paper):
    """Nový stav podle papírových výsledků {n, mean_r, t}; vrátí (stav, důvod) nebo None, když se nic nemění."""
    n, m, t = paper.get("n", 0), paper.get("mean_r"), paper.get("t")
    st = s.get("status")
    if st not in ACTIVE or m is None:
        return None
    if (n >= 30 and m < 0) or (n >= 15 and m < -0.5):
        return "vyřazeno", f"papírově {n} obchodů, Ø {m:+.2f} R"
    if st == "papír" and n >= 30 and m > 0 and (t or 0) >= 1.5:
        return "ověřeno", f"papírově {n} obchodů, Ø {m:+.2f} R, t {t:+.1f}"
    return None
