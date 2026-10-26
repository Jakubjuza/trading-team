#!/usr/bin/env python3
"""Rychlý skener bez AI: o vstupu rozhoduje jen kód (scanner/setups.py, strategie v config.yaml).

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

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from scanner import broker, ensemble, mtf, notify, pyramid, rules, setups, weekly  # noqa: E402
from scanner.calibrate import strategies as cfg_strategies  # noqa: E402
from scanner.evaluate import backtest, simulate  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402
from scanner.data import CandleCache  # noqa: E402
from research import events as events_mod  # noqa: E402
from research import carry as carry_mod  # noqa: E402
from research import scenarios, sessions  # noqa: E402

STATE = HERE / "state.json"
_DEMO = {"broker": None, "error": None}


def demo_broker(cfg):
    """DemoBroker (OKX demo), nebo None – vypnuto, chybí klíče, nebo se nepodařilo připojit (zkusí se znovu za 30 min)."""
    dc = cfg.get("demo") or {}
    if not dc.get("enabled"):
        return None
    if _DEMO["broker"] is not None:
        return _DEMO["broker"]
    if _DEMO["error"] and time.time() - _DEMO["error"][0] < 1800:
        return None
    try:
        from scanner.demo import make_broker
        _DEMO["broker"] = make_broker(cfg)
        return _DEMO["broker"]
    except Exception as exc:
        _DEMO["error"] = (time.time(), f"{exc.__class__.__name__}: {str(exc)[:120]}")
        print(f"demo OKX nedostupné: {_DEMO['error'][1]}", file=sys.stderr)
        return None


def demo_open(cfg, pos, size, dry_run=False):
    """Otevře zrcadlo papírové pozice na demo účtu; vrátí zprávu pro Telegram nebo None."""
    dc = cfg.get("demo") or {}
    variant = "mtf" if pos.get("mtf") else "daily"
    if dry_run or dc.get("variant", "daily") != variant:
        return None
    b = demo_broker(cfg)
    if b is None:
        return None
    side = pos["setup"]["direction"].upper()
    try:
        rec = b.open(pos, size)
    except Exception as exc:
        pos["demo"] = {"status": "error", "error": str(exc)[:200]}
        return f"⚠️ Demo OKX: {pos['symbol']} {side} se nepodařilo otevřít ({exc.__class__.__name__}: {str(exc)[:120]})."
    pos["demo"] = rec
    if rec["status"] != "open":
        why = {"skipped_short": "spotový demo účet umí jen longy",
               "no_funds": "na demo účtu není dost peněz",
               "no_market": "pro tuto minci nemá demo účet futures kontrakt"}.get(rec["status"], "pozice je menší než minimum burzy")
        return f"🧪 Demo OKX: {pos['symbol']} {side} vynecháno – {why}."
    spot = rec.get("mode") == "spot"
    slip = f", skluz {notify.pct(rec['slippage_pct'])} %" if rec.get("slippage_pct") is not None else ""
    unit = pos["symbol"].split("/")[0] if spot else "kontr."
    note = ("stop je na burze, polovinu na T1 prodá skener" if rec.get("sl_id") else "⚠️ stop se nepodařilo zadat")
    return (f"🧪 Demo OKX{' spot' if spot else ''}: {rec['symbol']} {side} otevřeno {str(rec['contracts']).replace('.', ',')} {unit} @ "
            f"{notify.fmt(rec['entry']) if rec.get('entry') else '?'} (plán {notify.fmt(rec['planned_entry'])}{slip}), "
            f"poplatek {notify.pct(rec.get('entry_fee') or 0)} {rec['symbol'].split('/')[1].split(':')[0]} · {note if spot else 'stop i T1 jsou na burze'}.")
SIGNALS = HERE / "signals.jsonl"   # deník signálů (commituje se, čte ho evaluate.py)
FACTSHEETS = HERE.parent / "research" / "factsheets"   # datové listy k signálům pro AI desk
OUTCOMES = HERE.parent / "research" / "outcomes.jsonl"  # výsledky uzavřených papírových obchodů (reflexe desku)


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


def load_probabilities(cfg):
    """Tabulka pravděpodobností (scanner/calibrate.py) → {strategie: {"all", "recent", "after_t1"}}."""
    path = HERE.parent / cfg.get("probabilities", "scanner/probabilities.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    out = {}
    for name, v in data.get("strategies", {}).items():
        t = v.get("table", {})
        out[name] = {"all": t.get("*|*|*", {}), "recent": v.get("recent", {}), "after_t1": t.get("_after_t1", {})}
    return out


def scan_once(cfg, cache, state, dry_run=False, now=None, status=None):
    """status (dict) se doplní o poslední ceny a chyby – pro zprávu o stavu."""
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC"))).date().isoformat()
    found = []
    status = status if status is not None else {}
    status.setdefault("prices", {})
    status.setdefault("errors", {})
    strats = cfg_strategies(cfg)
    probs = load_probabilities(cfg)
    candidates, frames = [], {}
    base_tf = cfg.get("timeframe", "1h")                                # aktuální cena (zpráva o stavu, „blíží se“)
    for t in cfg["tickers"]:
        symbol, source = t["symbol"], t["source"]
        for strat in [{"timeframe": base_tf, "_price_only": True}] + strats:
            tf = strat.get("timeframe") or t.get("timeframe", cfg["timeframe"])
            if (symbol, tf) not in frames:
                try:
                    frames[(symbol, tf)] = cache.update(source, symbol, tf, now=now)
                except Exception as exc:  # síť, burza… další ticker
                    print(f"[{symbol} {tf}] data nedostupná: {exc}", file=sys.stderr)
                    status["errors"][symbol] = f"{exc.__class__.__name__}: {str(exc)[:80]}"
                    frames[(symbol, tf)] = None
            df = frames[(symbol, tf)]
            if df is None or len(df) < 23:
                if df is not None:
                    status["errors"][symbol] = f"málo dat {tf} ({len(df)} svíček)"
                continue
            if tf == base_tf or symbol not in status["prices"]:
                status["prices"][symbol] = (float(df["Close"].iloc[-1]), df.index[-1].isoformat())
            if strat.get("_price_only"):
                continue
            for s in setups.find(strat["setup"], df, t.get("direction", cfg["direction"]), strat.get("params"),
                                 last_only=True):
                candidates.append((symbol, source, tf, df, s, strat))

    costs = cfg.get("costs", {})
    cost_pct = costs.get("fee_pct", 0) + costs.get("slippage_pct", 0)
    status["frames"] = frames                                          # pro zdraví strategií ve zprávě o stavu
    update_paper_positions(cfg, state, frames, cost_pct, dry_run, probs)
    try:
        pyramid.update(cfg, state, frames, cost_pct, dry_run)
    except Exception as exc:                                          # samostatná papírová část nesmí shodit skener
        print(f"pyramida selhala: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    try:
        ens_demo = demo_broker(cfg) if (cfg.get("ensemble") or {}).get("demo") and not dry_run else None
        ensemble.update(cfg, state, frames, cost_pct, dry_run, demo=ens_demo)
    except Exception as exc:                                          # samostatná část nesmí shodit skener
        print(f"ensemble selhal: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    try:
        mtf_entries(cfg, state, frames, now, dry_run)
    except Exception as exc:                                          # vstup z nižších TF nesmí shodit skener
        print(f"vstup z nižších TF selhal: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    approach_alerts(cfg, state, frames, strats, now, day, dry_run)
    try:
        event_alerts(cfg, state, now, dry_run,
                     prices={sym.split("/")[0]: p for sym, (p, _) in status["prices"].items()})
    except Exception as exc:                                          # zprávy a kalendář nesmí shodit skener
        print(f"kalendář/zprávy selhaly: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    try:
        weekly_outlook(cfg, state, frames, now, dry_run)
    except Exception as exc:
        print(f"týdenní výhled selhal: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    try:
        from scanner.demo import LOG as DEMO_LOG
        weekly.maybe_send(cfg, state, now, health_fn=lambda: strategy_health(cfg, frames, now), demo_log=DEMO_LOG,
                          dry_run=dry_run)
    except Exception as exc:
        print(f"týdenní přehled selhal: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    try:
        carry_update(cfg, state, now, dry_run)
    except Exception as exc:
        print(f"carry selhal: {exc.__class__.__name__}: {exc}", file=sys.stderr)

    # krypto se hýbe spolu → max. N otevřených (papírových) pozic stejným směrem na strategii; přednost má lepší R:R
    candidates.sort(key=lambda x: x[4].rr[0], reverse=True)
    try:
        pyramid.open_new(cfg, state, [c for c in candidates if c[2] == "1d"], day, setup_id, dry_run)
    except Exception as exc:
        print(f"pyramida (otevření) selhala: {exc.__class__.__name__}: {exc}", file=sys.stderr)
    per_dir = {}
    for pos in state.data.get("open", []):
        k = (pos.get("strategy", strats[0]["name"]), pos["setup"]["direction"])
        per_dir[k] = per_dir.get(k, 0) + 1
    for symbol, source, tf, df, s, strat in candidates:
        sid = setup_id(symbol, tf, s)
        if state.seen(sid):
            continue
        min_rr = strat.get("min_rr", cfg.get("min_rr", 1.0))
        if s.rr[0] < min_rr:
            print(f"[{symbol}] {strat['name']} {s.direction} vyřazen: R:R {s.rr[0]} < {min_rr}")
            state.add(sid, day, {"sent": False, "reason": "rr"})
            continue
        key = (strat["name"], s.direction)
        if per_dir.get(key, 0) >= strat.get("max_open_per_direction", cfg.get("max_open_per_direction", 99)):
            print(f"[{symbol}] {strat['name']} {s.direction} vyřazen: plno otevřených pozic stejným směrem (korelace)")
            state.add(sid, day, {"sent": False, "reason": "correlation"})
            continue
        if state.count_on(day) >= cfg["max_setups_per_day"]:
            print(f"[{symbol}] denní limit {cfg['max_setups_per_day']} vyčerpán")
            continue
        size = rules.position_size(s, cfg["account_size"], cfg["risk_pct"],
                                   fractional=source == "crypto", cash_only=cfg.get("cash_only", True))
        if size["qty"] <= 0:
            continue
        per_dir[key] = per_dir.get(key, 0) + 1
        prob = probs.get(strat["name"])
        ctx = []
        try:
            ctx.append(sessions.context_line(now, symbol.split("/")[0]))
            if (cfg.get("events") or {}).get("enabled"):
                ctx.append(events_mod.context_line(now, cfg["events"].get("signal_hours", 24)))
        except Exception as exc:                                      # kontext nesmí shodit signál
            print(f"[{symbol}] kontext burz/událostí selhal: {exc}", file=sys.stderr)
        ctx = " · ".join(c for c in ctx if c)
        lines = notify.summary_lines(symbol, tf, s, size, cfg["account_size"], cost_pct, prob=prob, context=ctx,
                                     outlook=scenario_note(s, frames.get((symbol, "1d"))))
        mc = cfg.get("mtf_entry") or {}
        use_mtf = mc.get("enabled") and strat["name"] in mc.get("strategies", [])
        if use_mtf:
            lines.append(f"6. Vstup z nižších TF (papírově souběžně): čekám max. {mc.get('wait_hours', 72)} h na 4H ve směru, "
                         f"návrat k EMA20 na 1H a obratovou 1H svíčku – pak pošlu 📍 vstup se stopem za swingem.")
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
        state.add(sid, day, {"sent": sent, "setup": s.to_dict(), "size": size, "strategy": strat["name"]})
        state.data.setdefault("open", []).append({"id": sid, "symbol": symbol, "timeframe": tf, "setup": s.to_dict(),
                                                  "strategy": strat["name"], "exit": strat.get("exit", {})})
        dm = demo_open(cfg, state.data["open"][-1], size, dry_run)
        if dm:
            print(dm)
            if cfg["notify"].get("telegram", True):
                notify.telegram(dm)
        if use_mtf:
            state.data.setdefault("mtf_pending", []).append({
                "id": sid, "symbol": symbol, "strategy": strat["name"], "setup": s.to_dict(), "exit": strat.get("exit", {}),
                "t0": (s.hold_time + pd.Timedelta(tf)).isoformat()})
        state.save()
        rec = {"id": sid, "symbol": symbol, "source": source, "timeframe": tf, "strategy": strat["name"],
               "found_at": now.isoformat(), "rules": strat.get("params", {}), "exit": strat.get("exit", {}),
               "min_rr": min_rr, "setup": s.to_dict(), "size": size, "telegram": sent,
               "probabilities": prob}
        rec["factsheet"] = _write_factsheet(cfg, rec)
        log_signal(SIGNALS, rec)
        _ai_explain(cfg, s, sid)
    return found


def carry_update(cfg, state, now, dry_run=False, current=None, history=None, send=None):
    """💰 Papírový carry z fundingu (long spot + short perp): jednou denně po 00:00 UTC podle 7denního fundingu.
    Vstup > enter_apr, výstup < exit_apr; výnos v % kapitálu (1,5 × pozice) po nákladech. Nic se neposílá na burzu."""
    cc = cfg.get("carry") or {}
    if not cc.get("enabled"):
        return []
    st = state.data.setdefault("carry", {"positions": {}, "closed": []})
    day = now.astimezone(timezone.utc).date().isoformat()
    if st.get("last_day") == day:
        return []
    last_try = st.get("last_try")
    if last_try and (now - datetime.fromisoformat(last_try)).total_seconds() < 1800:
        return []
    st["last_try"] = now.isoformat()
    coins = cc.get("coins", carry_mod.COINS)
    cur = current if current is not None else carry_mod.current(coins)
    hist = history or (lambda c, since: carry_mod.funding_history(c, since, pause=0.2))
    if all("error" in (cur.get(c) or {"error": 1}) for c in coins):
        state.save()
        return []
    enter, exit_ = cc.get("enter_apr", carry_mod.ENTER_APR), cc.get("exit_apr", carry_mod.EXIT_APR)
    cost = carry_mod.COST_ROUND_TRIP / 2 / carry_mod.CAPITAL_PER_NOTIONAL * 100          # % kapitálu za vstup / výstup
    msgs = []
    for c in coins:
        info = cur.get(c) or {}
        if "error" in info:
            continue
        pos = st["positions"].get(c)
        if pos:                                                     # připsat funding od poslední kontroly
            since = datetime.fromisoformat(pos["checked"])
            try:
                f = hist(c, since)
                f = f[f.index > pd.Timestamp(since)]
                pos["accrued_pct"] += float(f.sum()) / carry_mod.CAPITAL_PER_NOTIONAL * 100
                if len(f):
                    pos["checked"] = f.index[-1].to_pydatetime().isoformat()
            except Exception as exc:
                print(f"[carry {c}] funding nedostupný: {exc}", file=sys.stderr)
        apr = info["apr_7d_pct"]
        if not pos and apr > enter:
            st["positions"][c] = {"since": now.isoformat(), "checked": now.isoformat(), "accrued_pct": -cost, "apr_in": apr}
            msgs.append(f"💰 Carry (papírově): vstup {c} – 7denní funding {apr:.1f} % p.a. (long spot + short perp, "
                        f"bez směrového rizika; výnos ≈ funding).".replace(".", ",", 1))
        elif pos and apr < exit_:
            res = pos["accrued_pct"] - cost
            days = max(1, (now - datetime.fromisoformat(pos["since"])).days)
            st["closed"].append({"coin": c, "since": pos["since"], "until": now.isoformat(), "ret_pct": round(res, 3), "days": days})
            del st["positions"][c]
            msgs.append(f"💰 Carry (papírově): výstup {c} – funding klesl na {apr:.1f} % p.a.; výsledek {res:+.2f} % kapitálu "
                        f"za {days} dní (≈ {res / days * 365:+.1f} % p.a.).".replace(".", ","))
    st["last_day"] = day
    state.save()
    tg = send or (notify.telegram if cfg.get("notify", {}).get("telegram", True) else None)
    for m in msgs:
        print(m)
        if not dry_run and tg:
            tg(m)
    return msgs


def carry_line(state):
    st = state.data.get("carry") or {}
    pos, closed = st.get("positions", {}), st.get("closed", [])
    if not pos and not closed:
        return ""
    acc = sum(p["accrued_pct"] for p in pos.values()) / max(1, len(pos)) if pos else 0.0
    done = sum(c["ret_pct"] for c in closed)
    return (f"Carry (papírově): otevřeno {', '.join(pos) or 'nic'}"
            + (f", Ø nasbíráno {acc:+.2f} % kapitálu" if pos else "")
            + (f" · uzavřené {len(closed)}× Σ {done:+.2f} %" if closed else "")).replace(".", ",")


def scenario_note(s, daily, horizon="4 týdny"):
    """„4 týdny 80 %: a – b“ z historických scénářů při dnešní volatilitě; upozorní, když T2 leží mimo pásmo."""
    try:
        rng = scenarios.quick_range(daily, horizon)
    except Exception as exc:
        print(f"scénáře selhaly: {exc}", file=sys.stderr)
        return ""
    if not rng:
        return ""
    lo, hi = rng["medvědí (10 %)"], rng["býčí (90 %)"]
    t2 = s.targets[-1]
    out = f"{horizon} 80 %: {notify.fmt(lo)} – {notify.fmt(hi)}"
    if (s.direction == "long" and t2 > hi) or (s.direction == "short" and t2 < lo):
        out += " (T2 mimo pásmo)"
    return out


def weekly_outlook(cfg, state, frames, now, dry_run=False, send=None):
    """📆 týdenní výhled (pondělí ráno): stav týden/měsíc a rozpětí scénářů pro každou minci."""
    oc = cfg.get("outlook") or {}
    if not oc.get("enabled"):
        return None
    loc = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC")))
    week = f"{loc.isocalendar()[0]}-W{loc.isocalendar()[1]:02d}"
    st = state.data.setdefault("outlook", {})
    if loc.weekday() != oc.get("weekday", 0) or loc.hour < oc.get("hour", 8) or st.get("last") == week:
        return None
    daily = {sym.split("/")[0]: df for (sym, tf), df in frames.items() if tf == "1d" and df is not None and len(df) > 300}
    if not daily:
        return None
    horizon = oc.get("horizon", "13 týdnů")
    lines = [f"📆 Týdenní výhled – {horizon}, pásmo 10–90 % z historie při dnešní volatilitě"]
    lines += scenarios.outlook_lines(daily, list(daily), horizon)
    halv = pd.Timestamp(scenarios.HALVINGS[-1], tz="UTC")
    months = (pd.Timestamp(now) - halv).days / 30.44
    peaks = [p["peak_after_months"] for p in (scenarios.load_stats().get("btc_cycle_peaks") or [])]
    lines.append(f"BTC cyklus: {months:.0f} měsíců po halvingu"
                 + (f" (vrcholy minulých cyklů {min(peaks):.0f}–{max(peaks):.0f} měsíců po halvingu, jen {len(peaks)} případy)"
                    if peaks else "") + ".")
    lines.append("Rozpětí je v testu od roku 2022 kalibrované, směr podle trendu ne (reports/scenarios.md). Jen informace.")
    msg = "\n".join(lines)
    st["last"] = week
    state.save()
    print(msg)
    if not dry_run and cfg.get("notify", {}).get("telegram", True):
        (send or notify.telegram)(msg)
    return msg


def event_alerts(cfg, state, now, dry_run=False, events=None, news=None, send=None, prices=None):
    """📅 ranní kalendář, ⚠️ upozornění před důležitou událostí, 📰 důležité titulky k mincím (bez AI)."""
    ec = cfg.get("events") or {}
    if not ec.get("enabled"):
        return []
    tz = ZoneInfo(cfg.get("timezone", "UTC"))
    loc = now.astimezone(tz)
    day = loc.date().isoformat()
    st = state.data.setdefault("events", {})
    sent = {k: v for k, v in st.get("sent", {}).items() if v >= (loc.date() - pd.Timedelta(days=3)).isoformat()}
    st["sent"] = sent
    evs = events if events is not None else events_mod.upcoming(now, 2)[0]
    stats = events_mod.load_stats()
    high = [e for e in evs if e["impact"] == "High"]
    msgs = []
    if loc.hour >= ec.get("digest_hour", 8) and st.get("digest") != day:
        st["digest"] = day
        soon = [e for e in high if e["time"].astimezone(tz).date() <= loc.date() + pd.Timedelta(days=1)]
        if soon:
            msgs.append("📅 Kalendář dnes a zítra:\n" + "\n".join("• " + events_mod.event_line(e, stats) for e in soon)
                        + "\nKolem těchto časů počítej s většími knoty. Jen informace.")
    due = {}
    for e in high:
        mins = (e["time"] - now).total_seconds() / 60
        key = f"pre|{e['title']}|{e['time'].isoformat()}"
        if 0 < mins <= ec.get("pre_alert_minutes", 60) and key not in sent:
            sent[key] = day
            due.setdefault(e["time"], []).append(e)
    for ts, group in sorted(due.items()):
        mins = round((ts - now).total_seconds() / 60)
        n_open = len(state.data.get("open", []))
        what = "; ".join(events_mod.event_line(e, stats) for e in group)
        msgs.append(f"⚠️ Za {mins} min: {what}. Otevřené papírové pozice: {n_open}"
                    + (" – stop může zasáhnout knot." if n_open else "."))
    if ec.get("news_alerts", True):
        coins = [t["symbol"].split("/")[0] for t in cfg["tickers"] if t.get("source") == "crypto"]
        raw = news if news is not None else events_mod.cached("news_watch", 30 * 60, lambda: events_mod.fetch_news(coins))
        per_day = st.setdefault("news_count", {})
        per_day = st["news_count"] = {day: per_day.get(day, 0)}
        important = set(ec.get("news_tags", ["regulace", "etf", "bezpečnost", "burzy"]))
        for x in raw.get("items", []):
            if per_day[day] >= ec.get("news_max_per_day", 4):
                break
            ts = datetime.fromisoformat(x["time"]) if x.get("time") else None
            if ts is None or (now - ts).total_seconds() > ec.get("news_max_age_min", 120) * 60 or ts > now:
                continue
            coin = next((c for c in coins if events_mod.mentions(x["title"], c)), None)
            tags, tone = events_mod.tag(x["title"])
            key = "news|" + events_mod.title_key(x["title"])
            if not coin or not important & set(tags) or tone == "neutrální" or key in sent:
                continue
            price = (prices or {}).get(coin)
            if events_mod.stale_price(x["title"], price, ec.get("news_price_tol_pct", 6.0)):
                print(f"📰 vynecháno (ceny v titulku daleko od aktuální {price}): {x['title']}")
                continue
            if events_mod.is_rehash(x, raw.get("items", []), coin, ec.get("news_rehash_hours", 12)):
                print(f"📰 vynecháno (stejné téma už dřív): {x['title']}")
                continue
            sent[key] = day
            per_day[day] += 1
            icon = "🟢" if tone == "pozitivní" else "🔴"
            msgs.append(f"📰 {icon} {coin}: {x['title']} ({x.get('source')}, {events_mod.prague(ts)}"
                        + (f"; cena teď {notify.fmt(price)}" if price else "") + ")\n"
                        f"Klíčová slova: {', '.join(tags)} · jen titulek, ne analýza · {x.get('link', '')}")
    tg = send or (notify.telegram if cfg.get("notify", {}).get("telegram", True) else None)
    for m in msgs:
        print(m)
        if not dry_run and tg:
            tg(m)
    state.save()
    return msgs


def approach_alerts(cfg, state, frames, strats, now, day, dry_run=False):
    """„⏳ setup se blíží“: cena u hladiny Donchian kanálu ve směru trendu (jen informace)."""
    ac = cfg.get("approach_alerts") or {}
    if not ac.get("enabled"):
        return []
    sent_today = state.data.setdefault("approach", {})
    sent_today = {k: v for k, v in sent_today.items() if v == day}
    out = []
    for strat in strats:
        if strat["setup"] != "donchian_breakout":
            continue
        p = setups.params_for("donchian_breakout", strat.get("params"))
        for (symbol, tf), df in frames.items():
            if tf != strat["timeframe"] or df is None or len(df) < max(p["channel"], p.get("trend_ema") or 0) + 2:
                continue
            live = frames.get((symbol, cfg.get("timeframe", "1h")))
            price = float(live["Close"].iloc[-1]) if live is not None and len(live) else float(df["Close"].iloc[-1])
            x = setups.Ctx(df)
            hi, lo = float(df["High"].iloc[-p["channel"]:].max()), float(df["Low"].iloc[-p["channel"]:].min())
            atr = float(x.atr[-1])
            ema = x.ema(p["trend_ema"])[-1] if p.get("trend_ema") else None
            for d, lvl in (("long", hi), ("short", lo)):
                if ema is not None and ((d == "long" and price <= ema) or (d == "short" and price >= ema)):
                    continue
                dist = (lvl - price) if d == "long" else (price - lvl)
                if not (0 < dist <= ac.get("atr_distance", 0.5) * atr):
                    continue
                key = f"{symbol}|{strat['name']}|{d}"
                if key in sent_today or len(sent_today) >= ac.get("max_per_day", 4):
                    continue
                word = "nad" if d == "long" else "pod"
                msg = (f"⏳ Blíží se: {symbol} {d.upper()} – {setups.NAMES_CS['donchian_breakout']} ({tf}). "
                       f"Signál vznikne, pokud denní svíčka zavře {word} {notify.fmt(lvl)} "
                       f"(teď {notify.fmt(price)}, {notify.pct(abs(dist) / price * 100)} %). Denní svíčka končí v 00:00 UTC. "
                       f"Jen informace, ne signál ke vstupu.")
                print(msg)
                sent_today[key] = day
                out.append(msg)
                if not dry_run and cfg.get("notify", {}).get("telegram", True):
                    notify.telegram(msg)
    state.data["approach"] = sent_today
    state.save()
    return out


def mtf_entries(cfg, state, frames, now, dry_run=False, send=None):
    """Pro čekající denní signály hledá vstup na nižších TF (scanner/mtf.py); po spouštěči otevře papírovou
    pozici „+mtf“ (hodinové svíčky, stejné výstupy jako denní strategie) vedle denní varianty."""
    mc = cfg.get("mtf_entry") or {}
    if not mc.get("enabled"):
        return []
    base_tf = cfg.get("timeframe", "1h")
    wait = mc.get("wait_hours", 72)
    keep, msgs = [], []
    for p in state.data.get("mtf_pending", []):
        s, sym = p["setup"], p["symbol"]
        side = s["direction"].upper()
        t0 = pd.Timestamp(p["t0"])
        h1 = frames.get((sym, base_tf))
        if h1 is None or len(h1) < 60:
            keep.append(p)
            continue
        r = mtf.find_trigger(s["direction"], h1, t0, s["stop"], s["targets"], s["meta"]["atr"], wait,
                             mc.get("ema", 20), mc.get("swing_bars", 6), mc.get("min_stop_pct", 1.5))
        if r is None:
            if pd.Timestamp(now) >= t0 + pd.Timedelta(hours=wait):
                msgs.append(f"⌛ Vstup z nižších TF nenastal: {sym} {side} – do {wait} h se nepotvrdil, varianta „+mtf“ "
                            f"se neotevírá (denní varianta běží dál).")
            else:
                keep.append(p)
            continue
        if r["status"] == "entry":
            entry, stop = r["entry"], r["stop"]
            risk = abs(entry - stop)
            rr = [round(abs(t - entry) / risk, 2) for t in s["targets"]]
            setup = {**s, "entry": entry, "stop": stop, "hold_time": r["time"].isoformat(), "rr": rr}
            ex = {**cfg.get("exit", {}), **p.get("exit", {})}
            state.data.setdefault("open", []).append({
                "id": p["id"] + "|mtf", "symbol": sym, "timeframe": base_tf, "setup": setup, "strategy": p["strategy"] + "+mtf",
                "mtf": True, "exit": {"split": ex.get("split", 0.5), "trail_atr": ex.get("trail_atr", 0),
                                      "max_hold_bars": ex.get("max_hold_bars", 20) * 24}})
            risk_usd = cfg.get("account_size", 0) * cfg.get("risk_pct", 0) / 100
            dm = demo_open(cfg, state.data["open"][-1], {"qty": risk_usd / risk if risk else 0}, dry_run)
            if dm:
                msgs.append(dm)
            tg = " / ".join(f"T{i + 1} {notify.fmt(t)}" for i, t in enumerate(s["targets"]))
            msgs.append(f"📍 Vstup z nižších TF (papírově): {sym} {side} – 4H ve směru, 1H návrat k EMA20 a obratová svíčka.\n"
                        f"Vstup {notify.fmt(entry)} · Stop {notify.fmt(stop)} ({notify.pct(risk / entry * 100)} %) · {tg} · "
                        f"R:R {' / '.join(str(x).replace('.', ',') for x in rr)} (denní vstup: "
                        f"{' / '.join(str(x).replace('.', ',') for x in s['rr'])}). Nejde o finanční poradenství.")
        elif r["status"] == "stopped":
            msgs.append(f"❌ Vstup z nižších TF zrušen: {sym} {side} – cena zasáhla denní stop dřív, než se vstup potvrdil.")
        else:
            msgs.append(f"⏭ Vstup z nižších TF vynechán: {sym} {side} – cena už je za T1.")
    state.data["mtf_pending"] = keep
    state.save()
    tgf = send or (notify.telegram if cfg.get("notify", {}).get("telegram", True) else None)
    for m in msgs:
        print(m)
        if not dry_run and tgf:
            tgf(m)
    return msgs


def update_paper_positions(cfg, state, frames, cost_pct, dry_run=False, probs=None):
    """Vyhodnotí otevřené papírové pozice na nových svíčkách; T1 a uzavření oznámí na Telegram."""
    probs = probs or {}
    still_open = []
    tg = (not dry_run) and cfg.get("notify", {}).get("telegram", True)
    for pos in state.data.get("open", []):
        df = frames.get((pos["symbol"], pos["timeframe"]))
        if df is None:
            still_open.append(pos)
            continue
        ex = {**cfg.get("exit", {}), **pos.get("exit", {})}
        after = df[df.index > pd.Timestamp(pos["setup"]["hold_time"])]
        res = simulate(pos["setup"], after, ex.get("max_hold_bars", 48), ex.get("split", 0.5),
                       cost_pct, ex.get("trail_atr", 0))
        side = pos["setup"]["direction"].upper() + (" (vstup z 1H)" if pos.get("mtf") else "")
        if res["result"] == "open":
            if res.get("t1") and not pos.get("t1_notified"):
                pos["t1_notified"] = True
                a = (probs.get(pos.get("strategy")) or {}).get("after_t1", {})
                avg = f"{a.get('avg_r', 0):+.2f}".replace(".", ",")
                hist = (f" Z historie po T1: Ø {avg} R, ≥2R v {a.get('p_2r', 0) * 100:.0f} % případů ({a['n']} obchodů)."
                        if a.get("n") else "")
                msg = (f"🎯 T1 dosažen: {pos['symbol']} {side} – vybrána část pozice, stop zbytku na vstup "
                       f"(break-even).{hist}")
                print(msg)
                if tg:
                    notify.telegram(msg)
                if (pos.get("demo") or {}).get("status") == "open" and not dry_run and demo_broker(cfg):
                    try:
                        pos["demo"] = demo_broker(cfg).move_stop(pos, pos["demo"], pos["setup"]["entry"])
                    except Exception as exc:
                        print(f"demo posun stopu selhal: {exc}", file=sys.stderr)
            still_open.append(pos)
            continue
        closed = {"id": pos["id"], "symbol": pos["symbol"], "strategy": pos.get("strategy"),
                  "direction": pos["setup"]["direction"], **res, "closed_at": datetime.now(timezone.utc).isoformat()}
        state.data.setdefault("closed", []).append(closed)
        if not dry_run:
            log_signal(OUTCOMES, {**closed, "timeframe": pos["timeframe"], "entry": pos["setup"]["entry"],
                                  "stop": pos["setup"]["stop"], "targets": pos["setup"]["targets"],
                                  "closed_at": df.index[-1].isoformat()})
        txt = {"stop": "stop", "T1+BE": "T1, zbytek na break-even / trailing stop", "T2": "T1 i T2",
               "time": "časový výstup"}[res["result"]]
        msg = (f"📕 Papírový obchod uzavřen: {pos['symbol']} {side} – {txt}, "
               f"{res['r']:+.2f} R po nákladech ({res['bars']} svíček)".replace(f"{res['r']:+.2f}", f"{res['r']:+.2f}".replace(".", ",")))
        print(msg)
        if tg:
            notify.telegram(msg)
        if (pos.get("demo") or {}).get("status") == "open" and not dry_run and demo_broker(cfg):
            try:
                out = demo_broker(cfg).close(pos, pos["demo"], res["result"], round(res["r"], 3))
                pnl = out.get("pnl_usdt")
                closed["demo_pnl"] = pnl
                closed["demo_ccy"] = out["symbol"].split("/")[1].split(":")[0]
                dmsg = (f"🧪 Demo OKX: {pos['symbol']} {side} uzavřeno ({txt})"
                        + (f" – výsledek {pnl:+.2f} {out['symbol'].split('/')[1].split(':')[0]} po poplatcích".replace(".", ",") if pnl is not None else
                           " – stop se vykonal na burze, výsledek v deníku demo obchodů"))
                print(dmsg)
                if tg:
                    notify.telegram(dmsg)
            except Exception as exc:
                print(f"demo uzavření selhalo: {exc}", file=sys.stderr)
                if tg:
                    notify.telegram(f"⚠️ Demo OKX: {pos['symbol']} {side} se nepodařilo uzavřít ({exc.__class__.__name__}) – zkontroluj demo účet.")
    state.data["open"] = still_open
    state.save()


def strategy_health(cfg, frames, now, days=182):
    """Jak by strategie dopadly za posledních `days` dní na živých datech (backtest po nákladech) vs. dlouhodobý průměr."""
    costs = cfg.get("costs", {})
    cost_pct = costs.get("fee_pct", 0) + costs.get("slippage_pct", 0)
    probs = load_probabilities(cfg)
    since = pd.Timestamp(now) - pd.Timedelta(days=days)
    parts = []
    for strat in cfg_strategies(cfg):
        p = strategy_params(strat)
        rs = []
        for (sym, tf), df in (frames or {}).items():
            if tf != strat["timeframe"] or df is None or len(df) < 250:
                continue
            rs += [t["r"] for t in backtest(df, p, "both", cost_pct, setup=strat["setup"]) if t["time"] >= since]
        if not rs and not frames:
            continue
        long_run = (probs.get(strat["name"]) or {}).get("all", {}).get("avg_r")
        s = sum(rs)
        warn = " ⚠️" if len(rs) >= 8 and s / len(rs) < 0 else ""
        lr = f", dlouhodobě Ø {long_run:+.2f} R/obch.".replace(".", ",", 1) if long_run is not None else ""
        name = setups.NAMES_CS.get(strat["setup"], strat["setup"]).split(" (")[0]
        parts.append(f"{name} {s:+.1f} R / {len(rs)} obch.".replace(".", ",", 1) + lr + warn)
    return ("Zdraví strategií (6 měs., na živých datech): " + " · ".join(parts)) if parts else ""


def positions_overview(state, prices, since=None, max_lines=8):
    """📋 Otevřené papírové pozice (aktuální R, stop, zrcadlo na demu) a uzavřené od `since` (R, výsledek na demu)."""
    def num(x):
        return f"{x:+.2f}".replace(".", ",")
    lines = []
    opened = state.data.get("open", [])
    if opened:
        lines.append(f"📋 Otevřené ({len(opened)}):")
        for pos in opened[:max_lines]:
            s = pos["setup"]
            sign = 1 if s["direction"] == "long" else -1
            risk = abs(s["entry"] - s["stop"]) or None
            px = (prices.get(pos["symbol"]) or (None,))[0]
            now_r = f", teď {notify.fmt(px)} ({num(sign * (px - s['entry']) / risk)} R)" if px and risk else ""
            stop = "vstup (po T1)" if pos.get("t1_notified") else notify.fmt(s["stop"])
            demo = " · 🧪 demo" if (pos.get("demo") or {}).get("status") == "open" else ""
            lines.append(f"• {pos['symbol']} {s['direction'].upper()}{' 1H' if pos.get('mtf') else ''} "
                         f"({pos.get('strategy')}) "
                         f"vstup {notify.fmt(s['entry'])}{now_r}, stop {stop}{demo}")
        if len(opened) > max_lines:
            lines.append(f"• … a dalších {len(opened) - max_lines}")
    recent = [c for c in state.data.get("closed", []) if c.get("closed_at") and (since is None or c["closed_at"] >= since)]
    if recent:
        lines.append(f"📕 Uzavřené od minulé zprávy ({len(recent)}):")
        for c in recent[-max_lines:]:
            demo = (f" · 🧪 demo {num(c['demo_pnl'])} {c.get('demo_ccy', '')}".rstrip()
                    if c.get("demo_pnl") is not None else "")
            lines.append(f"• {c['symbol']} {c['direction'].upper()} {num(c['r'])} R ({c['result']}){demo}")
    return lines


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
    closed = state.data.get("closed", [])
    lines.append(f"Papírově: otevřené {len(state.data.get('open', []))}, uzavřené {len(closed)}"
                 + (f", Σ {sum(c['r'] for c in closed):+.2f} R" if closed else ""))
    try:
        lines += positions_overview(state, status.get("prices") or {}, hb["last"])
    except Exception as exc:
        print(f"přehled pozic selhal: {exc}", file=sys.stderr)
    if status.get("errors"):
        lines.append("⚠️ Problém s daty: " + "; ".join(f"{k} – {v}" for k, v in status["errors"].items()))
    try:                                                              # výkon částí je v 📊 týdenním přehledu (scanner/weekly.py)
        if (cfg.get("demo") or {}).get("enabled"):
            n_demo = sum(1 for p in state.data.get("open", []) if (p.get("demo") or {}).get("status") == "open")
            lines.append(f"Demo OKX: {'připojeno' if demo_broker(cfg) else 'nepřipojeno (' + ((_DEMO['error'] or (0, 'chybí klíče'))[1]) + ')'}"
                         f", otevřené pozice {n_demo}")
    except Exception as exc:
        print(f"stav dema selhal: {exc}", file=sys.stderr)
    try:
        up = sessions.upcoming_line(now, hours)
        if up:
            lines.append(up)
        if (cfg.get("events") or {}).get("enabled"):
            nxt = [e for e in events_mod.upcoming(now, 2)[0] if e["impact"] == "High"]
            if nxt:
                lines.append("📅 Nejbližší: " + events_mod.event_line(nxt[0], events_mod.load_stats()))
    except Exception as exc:
        print(f"kontext burz selhal: {exc}", file=sys.stderr)
    rules_txt = ", ".join(f"{setups.NAMES_CS.get(st['setup'], st['setup'])} {st['timeframe']}" for st in cfg_strategies(cfg))
    lines.append(f"Hlídám: {rules_txt}. Další zpráva o stavu za {hours} h.")
    text = "\n".join(lines)
    ok = (send or notify.telegram)(text)
    if ok:
        state.data["heartbeat"] = {"last": now.isoformat(), "scans": 0, "setups": 0, "errors": 0}
    state.save()
    return text


def _write_factsheet(cfg, rec):
    """Datový list k signálu pro AI desk (research/factsheets/). Vrátí relativní cestu, nebo None."""
    if not cfg.get("factsheet", False) or rec["source"] != "crypto":
        return None
    try:
        from research import factsheet
        sheet = factsheet.build(rec["symbol"], cfg.get("exchange", "kraken"), signal=rec)
        name = rec["id"].replace("|", "_").replace("/", "-").replace(":", "")
        path = FACTSHEETS / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sheet, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
        return str(path.relative_to(HERE.parent))
    except Exception as exc:
        print(f"Datový list se nepovedl: {exc}", file=sys.stderr)
        return None


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
