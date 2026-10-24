#!/usr/bin/env python3
"""Pošle na Telegram verdikty desku, které přibyly do research/verdicts.jsonl mezi dvěma commity.

Použití (GitHub Actions): python3 research/send_verdicts.py <before_sha> <after_sha>
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scanner import notify  # noqa: E402

GRADE = {"A": "🟢 A", "B": "🟡 B", "C": "🟠 C – jen sledovat", "NO_TRADE": "🔴 NEOBCHODOVAT"}


def added_lines(before, after, path="research/verdicts.jsonl"):
    if not before or set(before) == {"0"}:
        diff = subprocess.run(["git", "show", f"{after}:{path}"], capture_output=True, text=True, cwd=ROOT).stdout
        return [l for l in diff.splitlines() if l.strip()]
    diff = subprocess.run(["git", "diff", "--unified=0", before, after, "--", path],
                          capture_output=True, text=True, cwd=ROOT).stdout
    return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++") and l[1:].strip()]


def format_verdict(v):
    head = f"🧠 Desk verdikt: {v.get('symbol', '?')} {str(v.get('direction', '')).upper()} – {GRADE.get(v.get('grade'), v.get('grade'))}"
    lines = [head]
    lines += v.get("summary") or []
    if v.get("vetoes"):
        lines.append("Veto: " + "; ".join(map(str, v["vetoes"])))
    lines.append("Nejde o finanční poradenství.")
    return "\n".join(lines)[:4000]


def main():
    before, after = (sys.argv[1:3] + [None, None])[:2]
    sent = 0
    for line in added_lines(before, after or "HEAD"):
        try:
            v = json.loads(line)
        except json.JSONDecodeError:
            print(f"Neplatný řádek: {line[:80]}", file=sys.stderr)
            continue
        if v.get("grade") == "SKIPPED":          # zastaralé signály bez analýzy se neposílají
            continue
        if notify.telegram(format_verdict(v)):
            sent += 1
    print(f"Odesláno verdiktů: {sent}")


if __name__ == "__main__":
    main()
