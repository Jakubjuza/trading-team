"""Příkazy z Telegramu: /pozice (aktuální stav všech pozic), /pomoc.

Skener při každém průchodu (1× za minutu) načte nové zprávy bota (getUpdates) a odpoví jen na zprávy z chatu
TELEGRAM_CHAT_ID – cizí chaty se ignorují. Ceny = poslední cena ze skeneru (hodinová svíčka v průběhu), demo stav
z účtu OKX (jen čtení). Nic se neobchoduje.
"""
import json
import os
import sys
import time

import requests

from scanner import notify

HELP = ("Příkazy: /pozice – přehled s grafem a stav otevřených pozic (jádro, pyramida, ensemble, laboratoř, demo OKX) · /nalada – index nálady trhu "
        "1–100 se složkami · /radar – radar vyprávění (sílí bear, nebo bull? potvrzuje to cena?) · /pomoc – tento seznam. "
        "Odpověď přijde do minuty.")


def _n(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


def positions_report(cfg, state, prices, demo=None, demo_log=None):
    def px(sym):
        return (prices.get(sym) or (None,))[0]
    lines = ["📋 Pozice teď (papírově, ceny ze skeneru)"]
    risk_usd = cfg.get("account_size", 10000) * cfg.get("risk_pct", 1.0) / 100

    core = state.data.get("open", [])
    lines.append(f"Jádro – otevřené {len(core)}:" if core else "Jádro: žádná otevřená pozice.")
    for p in core:
        s = p["setup"]
        sg = 1 if s["direction"] == "long" else -1
        now = px(p["symbol"])
        risk = abs(s["entry"] - s["stop"]) or None
        r = sg * (now - s["entry"]) / risk if now and risk else None
        lines.append(f"• {p['symbol']} {s['direction'].upper()}{' (1H)' if p.get('mtf') else ''}: vstup {notify.fmt(s['entry'])}, "
                     f"teď {notify.fmt(now) if now else '?'}" + (f" ({_n(r)} R ≈ {_n(r * risk_usd, 0)} USD)" if r is not None else "")
                     + f", stop {'vstup (po T1)' if p.get('t1_notified') else notify.fmt(s['stop'])}"
                     + (" · 🧪 demo" if (p.get("demo") or {}).get("status") == "open" else ""))

    pyr = (state.data.get("pyramid") or {}).get("open", [])
    if pyr:
        lines.append(f"🔺 Pyramida – otevřené {len(pyr)}:")
        pp = {**{"unit_r": 0.5, "add_atr": 1.0}, **(cfg.get("pyramid") or {})}
        for p in pyr:
            sg = 1 if p["direction"] == "long" else -1
            now = px(p["symbol"])
            n = p.get("notified_units", 1)
            unit = pp["unit_r"] / abs(p["entry"] - p["stop"])
            r = sum(unit * sg * (now - (p["entry"] + sg * k * pp["add_atr"] * p["atr"])) for k in range(n)) if now else None
            lines.append(f"• {p['symbol']} {p['direction'].upper()}: {n} kus(y), vstup {notify.fmt(p['entry'])}, teď "
                         f"{notify.fmt(now) if now else '?'}" + (f" ({_n(r)} R)" if r is not None else "")
                         + f", stop {notify.fmt(p.get('stop_now', p['stop']))}")

    ens = state.data.get("ensemble") or {}
    if ens.get("qty") or ens.get("equity"):
        fills = _paper_prices(demo_log)
        held = {c: q for c, q in ens.get("qty", {}).items() if q > 0}
        value = ens.get("cash", 0) + sum(q * (px(f"{c}/USDT") or 0) for c, q in held.items())
        start = ens.get("start_equity") or value
        lines.append(f"🧭 Ensemble: hodnota {notify.fmt(value)} USD ({_n((value / start - 1) * 100, 1)} %), "
                     f"v trhu {sum(q * (px(f'{c}/USDT') or 0) for c, q in held.items()) / max(value, 1) * 100:.0f} %:")
        for c, q in held.items():
            now = px(f"{c}/USDT")
            avg = (ens.get("avg") or {}).get(c) or fills.get(c)
            pl = f", {_n((now / avg - 1) * 100, 1)} % od nákupu" if now and avg else ""
            lines.append(f"• {c}: {notify.fmt(q * now) if now else '?'} USD{pl}")
        if not held:
            lines.append("• vše v hotovosti")

    try:
        from scanner import lab_report
        lines += lab_report.lines(state, prices)
    except Exception as exc:
        lines.append(f"⚡ Laboratoř: přehled nedostupný ({exc.__class__.__name__}).")
    if demo is not None:
        try:
            lines += _demo_lines(demo, state, prices)
        except Exception as exc:
            lines.append(f"🧪 Demo OKX: stav nedostupný ({exc.__class__.__name__}).")
    lines.append("Nejde o finanční poradenství.")
    return "\n".join(lines)


def mood_report(state):
    """🌡️ Poslední denní index nálady (počítá skener jednou denně ráno) se složkami a vývojem."""
    from research import mood
    st = state.data.get("mood") or {}
    if not st.get("last"):
        return "🌡️ Index nálady ještě není spočítaný (skener ho počítá jednou denně ráno)."
    text = mood.message(st["last"])
    hist = mood.history_line(state)
    return text.replace("\nPopis nálady", (f"\n{hist}" if hist else "") + f"\nSpočítáno {st['last']['as_of'][:10]}. Popis nálady", 1)


def _paper_prices(demo_log):
    """Průměrná cena nákupů ensemblu z deníku dema (záloha pro starší knihu bez průměrné ceny)."""
    out = {}
    if demo_log is None or not demo_log.exists():
        return out
    acc = {}
    for line in demo_log.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("event") == "ensemble" and r.get("side") == "buy" and r.get("paper_price"):
            c = r["symbol"].split("/")[0]
            q, v = acc.get(c, (0.0, 0.0))
            acc[c] = (q + r["amount"], v + r["amount"] * r["paper_price"])
    return {c: v / q for c, (q, v) in acc.items() if q}


def _demo_lines(demo, state, prices):
    bal = demo.ex.fetch_balance()
    quote = getattr(demo, "quote", None) or "USDT"
    ens_qty = (state.data.get("ensemble") or {}).get("demo_qty", {})
    coins = set(ens_qty) | {p["symbol"].split("/")[0] for p in state.data.get("open", [])
                             if (p.get("demo") or {}).get("status") == "open"}
    out = [f"🧪 Demo OKX: volné {quote} {notify.fmt(float((bal.get(quote) or {}).get('free') or 0))}"]
    for c in sorted(coins):
        tot = float((bal.get(c) or {}).get("total") or 0)
        now = (prices.get(f"{c}/USDT") or (None,))[0]
        mine = ens_qty.get(c, 0.0)
        out.append(f"• {c}: na účtu {tot:g}" + (f" (ensemble {mine:g} ≈ {notify.fmt(mine * now)} USD)" if mine and now else ""))
    return out


def poll(cfg, state, prices, demo=None, demo_log=None, dry_run=False, get=None, send=None):
    """Načte nové zprávy bota a odpoví na příkazy. Vrací seznam odpovědí."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if (not token or not chat) and get is None:
        return []
    st = state.data.setdefault("telegram", {})
    get = get or (lambda params: requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params=params,
                                              timeout=10).json())
    try:
        data = get({"offset": st.get("offset", 0), "timeout": 0, "allowed_updates": json.dumps(["message"])})
    except Exception as exc:
        print(f"Telegram getUpdates: {exc}", file=sys.stderr)
        return []
    replies = []
    for u in data.get("result", []):
        st["offset"] = u["update_id"] + 1
        m = u.get("message") or {}
        if str((m.get("chat") or {}).get("id")) != str(chat):
            continue                                                     # jen vlastní chat
        if time.time() - m.get("date", 0) > 15 * 60:
            continue                                                     # staré zprávy (po výpadku) neřešit
        text = (m.get("text") or "").strip().lower()
        cmd = text.split()[0].split("@")[0] if text else ""
        if cmd in ("/pozice", "pozice", "/stav"):
            if not dry_run and send is None:
                from scanner import lab_report
                lab_report.send_board(state, prices, "📊 Přehled papírových obchodů")
            replies.append(positions_report(cfg, state, prices, demo, demo_log))
        elif cmd in ("/nalada", "/nálada", "nalada", "nálada"):
            replies.append(mood_report(state))
        elif cmd in ("/radar", "radar"):
            from research import narrative
            replies.append(narrative.report(state))
        elif cmd in ("/pomoc", "/help", "/start"):
            replies.append(HELP)
    state.save()
    for r in replies:
        print(r)
        if not dry_run:
            (send or notify.telegram)(r)
    return replies
