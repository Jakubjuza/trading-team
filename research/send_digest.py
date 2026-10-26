#!/usr/bin/env python3
"""Pošle týdenní shrnutí na Telegram: mentor (research/mentor_digest.md) nebo nálada trhu (research/mood_digest.md).

Spouští workflow „Mentor na Telegram“ a „Nálada trhu na Telegram“:  python3 research/send_digest.py mentor|mood
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scanner import notify  # noqa: E402

DIGESTS = {"mentor": (ROOT / "research" / "mentor_digest.md", "🎓 Mentor desku – týdenní shrnutí"),
           "mood": (ROOT / "research" / "mood_digest.md", "🌡️ Nálada trhu – týdenní report")}


def main():
    path, header = DIGESTS[sys.argv[1] if len(sys.argv) > 1 else "mentor"]
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    if not text:
        print(f"{path.name} je prázdné")
        return
    ok = notify.telegram((header + "\n" + text)[:4000])
    print("odesláno" if ok else "neodesláno")


if __name__ == "__main__":
    main()
