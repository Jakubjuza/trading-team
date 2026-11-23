"""Telegram pro Degen City (vlastní, nezávislý na skeneru desku; stejný bot/chat ze secrets)."""
import html
import json
import os
import sys

import requests


def h(x):
    return html.escape(str(x), quote=False)


def send(text, buttons=None):
    if os.environ.get("DEGEN_TG", "1") == "0" or os.environ.get("DRY_RUN"):
        print("[TG – neodesláno]\n" + text)
        return False
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID chybí – zpráva neodeslána.", file=sys.stderr)
        return False
    data = {"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}
    if buttons:
        rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
        data["reply_markup"] = json.dumps({"inline_keyboard": [[{"text": t, "url": u} for t, u in r] for r in rows]})
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20)
        if not r.ok:
            print(f"Telegram chyba {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return r.ok
    except Exception as e:
        print(f"Telegram výjimka {e}", file=sys.stderr)
        return False


def links(mint):
    return [("pump.fun", f"https://pump.fun/coin/{mint}"),
            ("DexScreener", f"https://dexscreener.com/solana/{mint}"),
            ("Solscan", f"https://solscan.io/token/{mint}")]
