"""📊 Týdenní přehled – jedna zpráva s výsledky všech částí desku (pondělí ráno, config `weekly_report`).

Jádro (papírové denní obchody), vstup z 1H, 🔺 pyramida, 🧭 ensemble, 💰 carry, 🧪 demo OKX a zdraví strategií.
Výkon za uplynulý týden a od začátku; R se přepočítá na USD rizikem na obchod (account_size × risk_pct).
"""
import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from scanner import ensemble, notify


def _n(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


def _trades(rows, since):
    week = [r for r in rows if (r.get("closed_at") or "") >= since]
    return week, rows


def report(cfg, state, now, health=None, demo_log=None):
    loc = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC")))
    since_dt = now - timedelta(days=7)
    since = since_dt.isoformat()
    risk_usd = cfg.get("account_size", 10000) * cfg.get("risk_pct", 1.0) / 100
    lines = [f"📊 Týdenní přehled ({(loc - timedelta(days=7)):%d.%m.} – {loc:%d.%m.}) · 1 R = {notify.fmt(risk_usd)} USD"]
    usd_week = usd_total = 0.0

    closed = state.data.get("closed", [])
    opened = state.data.get("open", [])
    for label, pick in (("Jádro (denní signály)", lambda r: "+mtf" not in (r.get("strategy") or "")),
                        ("Vstup z 1H (papír)", lambda r: "+mtf" in (r.get("strategy") or ""))):
        rows = [r for r in closed if pick(r)]
        wk, al = _trades(rows, since)
        n_open = sum(1 for p in opened if pick(p))
        sw, sa = sum(r["r"] for r in wk), sum(r["r"] for r in al)
        if label.startswith("Jádro"):
            usd_week, usd_total = usd_week + sw * risk_usd, usd_total + sa * risk_usd
        lines.append(f"• {label}: týden {len(wk)} obch. {_n(sw)} R · celkem {len(al)} obch. {_n(sa)} R"
                     + (f", otevřené {n_open}" if n_open else ""))

    pyr = state.data.get("pyramid") or {}
    if pyr:
        wk, al = _trades(pyr.get("closed", []), since)
        sw, sa = sum(r["r"] for r in wk), sum(r["r"] for r in al)
        lines.append(f"• 🔺 Pyramida (papír): týden {len(wk)} obch. {_n(sw)} R · celkem {len(al)} obch. {_n(sa)} R"
                     + (f", otevřené {len(pyr.get('open', []))}" if pyr.get("open") else ""))

    ens = ensemble.week_change(state, since_dt.date().isoformat())
    if ens:
        start = (state.data.get("ensemble") or {}).get("start_equity") or ens["equity"]
        usd_week += ens["equity"] - ens["equity"] / (1 + ens["week"] / 100)
        usd_total += ens["equity"] - start
        lines.append(f"• 🧭 Ensemble (papír): týden {_n(ens['week'], 1)} % · celkem {_n(ens['total'], 1)} % "
                     f"(hodnota {notify.fmt(ens['equity'])} USD, v trhu {ens['expo']:.0f} %)")

    carry = state.data.get("carry") or {}
    if carry.get("positions") or carry.get("closed"):
        wk = [c for c in carry.get("closed", []) if c.get("until", "") >= since]
        acc = sum(p.get("accrued_pct", 0) for p in carry.get("positions", {}).values())
        lines.append(f"• 💰 Carry (papír): otevřeno {', '.join(carry.get('positions', {})) or 'nic'}"
                     + (f" ({_n(acc)} % nasbíráno)" if carry.get("positions") else "")
                     + f" · uzavřené týden {len(wk)}× {_n(sum(c['ret_pct'] for c in wk))} %, celkem "
                     f"{len(carry.get('closed', []))}× {_n(sum(c['ret_pct'] for c in carry.get('closed', [])))} %")

    if demo_log is not None and demo_log.exists():
        recs = []
        for line in demo_log.read_text(encoding="utf-8").splitlines():
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
        cl = [r for r in recs if r.get("event") == "close" and r.get("pnl_usdt") is not None and r.get("id") != "TEST"]
        wk = [r for r in cl if (r.get("closed") or "") >= since]
        lines.append(f"• 🧪 Demo OKX: týden {len(wk)} obch. {_n(sum(r['pnl_usdt'] for r in wk))} USDC · celkem "
                     f"{len(cl)} obch. {_n(sum(r['pnl_usdt'] for r in cl))} USDC")

    lines.append(f"Papírově celkem (jádro + ensemble): týden {_n(usd_week, 0)} USD · od začátku {_n(usd_total, 0)} USD")
    if health:
        lines.append(health)
    lines.append("Jen papírové a demo výsledky. Nejde o finanční poradenství.")
    return "\n".join(lines)


def maybe_send(cfg, state, now, health_fn=None, demo_log=None, dry_run=False, send=None):
    wc = cfg.get("weekly_report") or {}
    if not wc.get("enabled"):
        return None
    loc = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC")))
    week = f"{loc.isocalendar()[0]}-W{loc.isocalendar()[1]:02d}"
    st = state.data.setdefault("weekly_report", {})
    if loc.weekday() != wc.get("weekday", 0) or loc.hour < wc.get("hour", 8) or st.get("last") == week:
        return None
    health = None
    if health_fn:
        try:
            health = health_fn()
        except Exception as exc:
            print(f"zdraví strategií selhalo: {exc}")
    msg = report(cfg, state, now, health, demo_log)
    st["last"] = week
    state.save()
    print(msg)
    if not dry_run and cfg.get("notify", {}).get("telegram", True):
        (send or notify.telegram)(msg)
    return msg
