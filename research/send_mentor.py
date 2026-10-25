#!/usr/bin/env python3
"""Pošle týdenní shrnutí mentora (research/mentor_digest.md) na Telegram. Spouští workflow „Mentor na Telegram“."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scanner import notify  # noqa: E402

DIGEST = ROOT / "research" / "mentor_digest.md"


def main():
    text = DIGEST.read_text(encoding="utf-8").strip() if DIGEST.exists() else ""
    if not text:
        print("shrnutí mentora je prázdné")
        return
    ok = notify.telegram(("🎓 Mentor desku – týdenní shrnutí\n" + text)[:4000])
    print("odesláno" if ok else "neodesláno")


if __name__ == "__main__":
    main()
