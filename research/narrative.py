#!/usr/bin/env python3
"""📡 Radar vyprávění – sílí na trhu býčí, nebo medvědí vyprávění, a potvrzuje ho cena? Bez AI, měřeno dopředu.

Postup (podle toho, jak trh čte uživatel):
  1. sběr     titulky a příspěvky z veřejných zdrojů (média, analytici a on-chain výzkum, burzy, komunita,
              veřejné kanály Telegramu); každý zdroj se zkouší zvlášť, výpadek se jen zapíše,
  2. třídění  podle frází vyprávění („bear market“, „bottom is in“, „breaks below“ …) → býčí +1 / medvědí −1 / nic,
  3. shoda    za posledních `window_hours` (72 h): vážený poměr býčích a medvědích zpráv, kolik RŮZNÝCH zdrojů
              říká totéž a jestli shoda roste proti `baseline_days` (14 dní),
  4. cena     potvrzení na BTC 1H → 4H → 1D: close na správné straně středu Bollingerova pásma (SMA20) a prolomená
              úroveň (minimum / maximum 20 předchozích svíček) v posledních 5 svíčkách,
  5. měření   každá zpráva i každý signál se zapíše s cenou BTC a po 7 a 30 dnech se vyhodnotí, jestli cena šla
              daným směrem → úspěšnost každého zdroje (komu věřit) a radaru jako celku.

Radar je popis a podklad pro desk, ne vstupní signál: strategie se mění jen po testu (CLAUDE.md). X/Twitter nemá
veřejné rozhraní bez placeného API a Threads také ne – tyhle zdroje se nečtou automaticky.

Použití:
    python3 research/narrative.py --check     # zkusí všechny zdroje, vypíše stav a aktuální shodu (GitHub Actions)
"""
import argparse
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research import events as ev  # noqa: E402

LOG = ROOT / "research" / "narrative_log.jsonl"          # zatříděné zprávy (commit ze skeneru)
CALLS = ROOT / "research" / "narrative_calls.jsonl"      # signály radaru a jejich vyhodnocení
SOURCES_OUT = ROOT / "research" / "narrative_sources.json"  # úspěšnost zdrojů (čte AI desk a mentor)

# název → (druh, URL, váha). Váha: analytici 1,5 · média 1 · komunita 0,5 · Telegram 1. Ověřeno během „radar“
# 26. 10. 2026 z GitHub Actions; nefungovaly (HTTP chyba): Glassnode Insights RSS, Bybit API oznámení, r/CryptoCurrency.
SOURCES = {
    "CoinDesk": ("rss", "https://www.coindesk.com/arc/outboundfeeds/rss/", 1.0),
    "Cointelegraph": ("rss", "https://cointelegraph.com/rss", 1.0),
    "The Block": ("rss", "https://www.theblock.co/rss.xml", 1.0),
    "Decrypt": ("rss", "https://decrypt.co/feed", 1.0),
    "Bitcoin Magazine": ("rss", "https://bitcoinmagazine.com/feed", 1.0),
    "CryptoSlate": ("rss", "https://cryptoslate.com/feed/", 1.0),
    "Blockworks": ("rss", "https://blockworks.co/feed", 1.0),
    "Analytici (Google News)": ("rss", ev.google_news("bitcoin (analyst OR analysts OR trader OR strategist) "
                                                      "(bear OR bull OR bottom OR top OR rally OR crash)"), 1.5),
    "Reddit r/BitcoinMarkets": ("rss", "https://www.reddit.com/r/BitcoinMarkets/.rss", 0.5),
}
# kandidáti veřejných kanálů Telegramu pro --check (do configu jen ty, které se ověří)
TG_CANDIDATES = ["WatcherGuru", "wublockchainenglish", "cointelegraph", "glassnode"]
TG_WEIGHT = 1.0

# fráze vyprávění: (regex, váha). Celé fráze mají přednost před jednotlivými slovy (počítají se první a vymažou se).
FLIPS = [  # „konec bear marketu“ = býčí, „konec bull runu“ = medvědí, „konec odlivů“ = býčí
    (r"\b(bear market|crypto winter|bear trend|downtrend)\W+(\w+\W+){0,2}?(over|ending|ended|done)\b", +2),
    (r"\bend of (the )?(bear market|crypto winter|downtrend)\b", +2),
    (r"\b(bull (market|run)|uptrend|rally)\W+(\w+\W+){0,2}?(over|ending|ended|done|dead)\b", -2),
    (r"\bend of (the )?(bull (market|run)|uptrend|rally)\b", -2),
    (r"\b(break|breaks|broke|end|ends|ended|snap|snaps|snapped)\b[^.]{0,25}\boutflow streak\b", +1),
    (r"\b(break|breaks|broke|end|ends|ended|snap|snaps|snapped)\b[^.]{0,25}\binflow streak\b", -1),
]
NEGATION = r"\b(not|no|never|won'?t|unlikely to|may not|could not|cannot|can'?t)\s+(\w+\s+)?\w+"
BULL = [
    (r"\b(the )?bottom (is|may be|could be) in\b|\bis the bottom in\b|\bbottom(ed| confirmed)\b|\bmarket bottom\b|\bcycle low\b", 2),
    (r"\bbull (market|run|cycle)\b|\bnew uptrend\b", 2),
    (r"\b(all[- ]time high|record high|new ath|ath)\b", 1),
    (r"\bbullish\b|\bgolden cross\b|\bhigher highs?\b", 1),
    (r"\b(rall(y|ies|ied)|surg(e|es|ed|ing)|soar(s|ed|ing)?|jump(s|ed)?|climb(s|ed)?|rebound(s|ed)?|recover(s|y|ed)?)\b", 1),
    (r"\b(break(s|ing)? above|breakout|reclaim(s|ed)?|flip(s|ped)? resistance)\b", 1),
    (r"\b(inflows?|accumulat\w*|buy the dip|short squeeze)\b", 1),
]
BEAR = [
    (r"\bbear (market|trend|cycle)\b|\bcrypto winter\b", 2),
    (r"\b(the )?top (is|may be|could be) in\b|\bis the top in\b|\bcycle top\b|\btopped\b|\bmarket top\b", 2),
    (r"\bbearish\b|\bdeath cross\b|\blower lows?\b|\b(more|further) downside\b", 1),
    (r"\b(crash(es|ed)?|plung(e|es|ed)|slump(s|ed)?|tumbl(e|es|ed)|sink(s|ing)?|sank|sell-?off|dump(s|ed)?)\b", 1),
    (r"\b(break(s|ing)? below|breakdown|los(es|t|ing) support|falls? below|drops? below)\b", 1),
    (r"\b(outflows?|liquidat\w*|capitulat\w*|recession)\b", 1),
]
MARKET = r"\b(bitcoin|btc|crypto|cryptocurrenc\w*|altcoins?|ether(eum)?|eth|stablecoins?|solana|xrp|digital assets?)\b"


def classify(text):
    """Směr vyprávění textu: (+1 býčí / −1 medvědí / 0, skóre). Otázka („Is the bottom in?“) má poloviční váhu."""
    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    if not re.search(MARKET, t):
        return 0, 0.0
    score = 0.0
    for rx, w in FLIPS:
        if re.search(rx, t):
            score += w
            t = re.sub(rx, " ", t)
    t = re.sub(NEGATION, " ", t)                                    # „may not crash“ – zapřené slovo se nepočítá
    for rx, w in BULL:
        if re.search(rx, t):
            score += w
    for rx, w in BEAR:
        if re.search(rx, t):
            score -= w
    if "?" in text:
        score *= 0.5
    return (1 if score >= 1 else -1 if score <= -1 else 0), score


# --- sběr ------------------------------------------------------------------------------------------
def parse_telegram(page, channel, max_items=30):
    """Veřejný náhled kanálu t.me/s/<kanál>: text a čas zpráv (HTML bez knihoven)."""
    items = []
    for block in re.findall(r'<div class="tgme_widget_message_wrap.*?</time>', page, re.S):
        m = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        tm = re.search(r'<time[^>]*datetime="([^"]+)"', block)
        if not m:
            continue
        text = html.unescape(re.sub(r"<br\s*/?>", " ", m.group(1)))
        text = re.sub(r"<[^>]+>", "", text).strip()
        if text:
            ts = datetime.fromisoformat(tm.group(1)).astimezone(timezone.utc).isoformat() if tm else None
            items.append({"title": text[:280], "time": ts, "source": f"Telegram @{channel}"})
    return items[-max_items:]


def parse_atom(xml_text, source, max_items=40):
    """Atom (Reddit, některé blogy): <entry><title>, <updated>/<published>."""
    import xml.etree.ElementTree as ET
    ns = "{http://www.w3.org/2005/Atom}"
    out = []
    for e in ET.fromstring(xml_text).iter(f"{ns}entry"):
        title = (e.findtext(f"{ns}title") or "").strip()
        ts = e.findtext(f"{ns}published") or e.findtext(f"{ns}updated")
        try:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat() if ts else None
        except ValueError:
            t = None
        if title:
            out.append({"title": title, "time": t, "source": source})
        if len(out) >= max_items:
            break
    return out


def parse_bybit(data):
    rows = ((data or {}).get("result") or {}).get("list") or []
    out = []
    for r in rows:
        ts = r.get("dateTimestamp") or r.get("publishTime")
        t = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).isoformat() if ts else None
        out.append({"title": f"{r.get('title', '')} {r.get('description', '')}".strip()[:280], "time": t,
                    "source": "Bybit oznámení"})
    return out


def fetch_all(channels=(), get=None):
    """Všechny zdroje; vrací (zprávy, stav zdrojů). get(url) → text (pro testy)."""
    get = get or (lambda url: ev._get(url, timeout=10).text)
    items, status = [], {}
    todo = dict(SOURCES)
    for ch in channels:
        todo[f"Telegram @{ch}"] = ("telegram", f"https://t.me/s/{ch}", TG_WEIGHT)
    for name, (kind, url, w) in todo.items():
        try:
            raw = get(url)
            if kind == "rss":
                got = ev.parse_rss(raw, name) or parse_atom(raw, name)
                for x in got:
                    x["source"] = name                                   # Google News vrací původní médium
            elif kind == "bybit":
                got = parse_bybit(json.loads(raw))
            else:
                got = parse_telegram(raw, url.rsplit("/", 1)[-1])
            for x in got:
                x["w"] = w
            items += got
            status[name] = f"ok ({len(got)})"
        except Exception as exc:
            status[name] = f"chyba: {exc.__class__.__name__}"
    return items, status


# --- shoda -----------------------------------------------------------------------------------------
def tag_items(items, now, price=None, known=None):
    """Zatřídí nové zprávy (bez duplicit podle zdroje a titulku); vrací jen nové záznamy."""
    known = set(known or ())
    out = []
    for x in items:
        key = f"{x['source']}|{ev.title_key(x['title'])}"
        if key in known:
            continue
        known.add(key)
        d, s = classify(x["title"])
        t = x.get("time") or now.isoformat()
        try:
            if datetime.fromisoformat(t) < now - timedelta(days=3):
                continue                                                 # staré zprávy z archivu kanálu
        except ValueError:
            t = now.isoformat()
        out.append({"k": key, "t": t, "src": x["source"], "w": x.get("w", 1.0), "d": d, "s": round(s, 1),
                    "title": x["title"][:160], "p": price})
    return out


def consensus(items, now, window_h=72, baseline_days=14, min_sources=4, net_thr=0.25, rising=0.15):
    """Shoda za okno vs. základ. net −1…+1 (vážený, vyhlazený), zdroje = počet různých zdrojů na každé straně."""
    def stats(lo, hi):
        sel = [x for x in items if x["d"] and lo <= datetime.fromisoformat(x["t"]) < hi]
        bull = sum(x["w"] for x in sel if x["d"] > 0)
        bear = sum(x["w"] for x in sel if x["d"] < 0)
        return {"n": len(sel), "bull": round(bull, 1), "bear": round(bear, 1),
                "net": round((bull - bear) / (bull + bear + 1), 2),
                "src_bull": len({x["src"] for x in sel if x["d"] > 0}),
                "src_bear": len({x["src"] for x in sel if x["d"] < 0})}
    win = stats(now - timedelta(hours=window_h), now + timedelta(minutes=1))
    base = stats(now - timedelta(days=baseline_days), now - timedelta(hours=window_h))
    span = (now - min((datetime.fromisoformat(x["t"]) for x in items), default=now)).days
    have_base = span >= baseline_days * 0.5 and base["n"] >= 10
    zone = "smíšené"
    if win["net"] >= net_thr and win["src_bull"] >= min_sources:
        zone = "býčí shoda"
    elif win["net"] <= -net_thr and win["src_bear"] >= min_sources:
        zone = "medvědí shoda"
    trend = None
    if have_base:
        diff = win["net"] - base["net"]
        trend = "sílí býčí" if diff >= rising else "sílí medvědí" if diff <= -rising else "beze změny"
    return {"zone": zone, "window": win, "base": base if have_base else None, "trend": trend,
            "dir": 1 if zone == "býčí shoda" else -1 if zone == "medvědí shoda" else 0}


# --- potvrzení cenou -------------------------------------------------------------------------------
def tf_confirm(df, direction, lookback=20, recent=5):
    """2 = cena na správné straně středu Bollingerova pásma + prolomená úroveň v posledních `recent` svíčkách,
    1 = jen správná strana pásma (drží se nahoře / dole), 0 = nepotvrzuje."""
    if df is None or len(df) < lookback + recent + 1 or not direction:
        return 0
    c, h, l = df["Close"].values, df["High"].values, df["Low"].values
    mid = c[-20:].mean()
    side = c[-1] > mid if direction > 0 else c[-1] < mid
    if not side:
        return 0
    prior = slice(-(lookback + recent), -recent)
    broke = h[-recent:].max() > h[prior].max() if direction > 0 else l[-recent:].min() < l[prior].min()
    return 2 if broke else 1


def confirmation(frames_btc, direction):
    """{1h, 4h, 1d: 0/1/2} a stupeň = kolik timeframů po sobě (od 1H) plně potvrzuje."""
    res = {tf: tf_confirm(frames_btc.get(tf), direction) for tf in ("1h", "4h", "1d")}
    stage = 0
    for tf in ("1h", "4h", "1d"):
        if res[tf] == 2:
            stage += 1
        else:
            break
    return res, stage


# --- měření ---------------------------------------------------------------------------------------
def evaluate(items, scores, price, now, horizons=(7, 30)):
    """Zprávy staré ≥ 7 / 30 dní: šla cena BTC směrem zprávy? Průběžně sčítá úspěšnost zdrojů."""
    for x in items:
        if not x["d"] or not x.get("p") or not price:
            continue
        age = (now - datetime.fromisoformat(x["t"])).days
        for hz in horizons:
            key = f"e{hz}"
            if age >= hz and key not in x:
                hit = (price - x["p"]) * x["d"] > 0
                x[key] = int(hit)
                s = scores.setdefault(x["src"], {})
                s[f"n{hz}"] = s.get(f"n{hz}", 0) + 1
                s[f"hit{hz}"] = s.get(f"hit{hz}", 0) + int(hit)
    return scores


def source_table(scores, min_n=10):
    rows = []
    for src, s in scores.items():
        n, hit = s.get("n7", 0), s.get("hit7", 0)
        n30, hit30 = s.get("n30", 0), s.get("hit30", 0)
        rows.append((src, n, hit / n if n else None, n30, hit30 / n30 if n30 else None))
    rows.sort(key=lambda r: (r[1] < min_n, -(r[2] or 0)))
    return rows


# --- skener ---------------------------------------------------------------------------------------
ARROW = {1: "🟢 býčí", -1: "🔴 medvědí", 0: "⚪ smíšené"}
TFMARK = {2: "✅", 1: "〰️", 0: "⏳"}


def message(c, conf, stage, samples=(), scores=None):
    w = c["window"]
    lines = [f"📡 Radar vyprávění: {c['zone']} (posledních 72 h: býčí {w['bull']} / medvědí {w['bear']}, "
             f"zdrojů {w['src_bull']} / {w['src_bear']}, net {w['net']:+.2f})"]
    if c["trend"]:
        lines.append(f"Vývoj proti 14 dnům: {c['trend']} (základ net {c['base']['net']:+.2f}).")
    else:
        lines.append("Vývoj proti 14 dnům: zatím sbírám data.")
    if c["dir"]:
        lines.append("Cena BTC potvrzuje: " + " · ".join(f"{tf.upper()} {TFMARK[v]}" for tf, v in conf.items())
                     + f" (stupeň {stage}/3; ✅ prolomená úroveň + správná strana Bollingerova pásma, 〰️ jen pásmo)")
    for x in samples[:3]:
        lines.append(f"• {x['src']}: {x['title'][:110]}")
    if scores:
        top = [r for r in source_table(scores) if r[1] >= 10][:3]
        if top:
            lines.append("Úspěšnost zdrojů (směr BTC za 7 dní): " + ", ".join(f"{r[0]} {r[2] * 100:.0f} % (n={r[1]})"
                                                                         for r in top))
    lines.append("Popis vyprávění, ne signál ke vstupu. Nejde o finanční poradenství.")
    return "\n".join(lines)


def update(cfg, state, frames, now, dry_run=False, fetch=None, send=None):
    """Skener: jednou za `fetch_minutes` sběr + shoda + potvrzení; zpráva jen při změně stupně. Vrací zprávu nebo None."""
    nc = cfg.get("narrative") or {}
    if not nc.get("enabled"):
        return None
    st = state.data.setdefault("narrative", {"items": [], "scores": {}})
    last = st.get("fetched")
    if last and now - datetime.fromisoformat(last) < timedelta(minutes=nc.get("fetch_minutes", 60)):
        return None
    from scanner.data import closed_only, resample
    h1 = frames.get(("BTC/USDT", "1h"))
    d1 = frames.get(("BTC/USDT", "1d"))
    btc = {}
    if h1 is not None and len(h1):
        h1 = closed_only(h1, "1h", now)
        btc["1h"], btc["4h"] = h1, closed_only(resample(h1, "4h"), "4h", now)
    if d1 is not None and len(d1):
        btc["1d"] = closed_only(d1, "1d", now)
    price = float(btc["1h"]["Close"].iloc[-1]) if "1h" in btc and len(btc["1h"]) else None
    raw, status = (fetch or fetch_all)(nc.get("telegram_channels") or [])
    st["fetched"] = now.isoformat()
    st["status"] = status
    keep_from = now - timedelta(days=nc.get("keep_days", 35))
    neutral_from = now - timedelta(days=4)                              # neutrální jen kvůli duplicitám
    st["items"] = [x for x in st["items"]
                   if datetime.fromisoformat(x["t"]) >= (keep_from if x["d"] else neutral_from)]
    new = tag_items(raw, now, price, known=[x["k"] for x in st["items"]])
    st["items"] += new
    evaluate(st["items"], st["scores"], price, now)
    c = consensus(st["items"], now, nc.get("window_hours", 72), nc.get("baseline_days", 14), nc.get("min_sources", 4),
                  nc.get("net_threshold", 0.25), nc.get("rising", 0.15))
    conf, stage = confirmation(btc, c["dir"])
    samples = sorted([x for x in st["items"] if c["dir"] and x["d"] == c["dir"]], key=lambda x: x["t"])[-3:]
    st["last"] = {"as_of": now.isoformat(), "zone": c["zone"], "dir": c["dir"], "trend": c["trend"], "stage": stage,
                  "conf": conf, "window": c["window"], "base": c["base"], "price": price}
    prev = st.get("signal") or {"dir": 0, "stage": 0}
    sig = {"dir": c["dir"], "stage": stage if c["dir"] else 0}
    msg = None
    rising = c["trend"] in ("sílí býčí", "sílí medvědí") and (c["trend"] == "sílí býčí") == (c["dir"] > 0)
    day = now.date().isoformat()
    sent_today = st.get("sent_day") == day and st.get("sent_n", 0) >= nc.get("max_alerts_per_day", 2)
    changed = sig["dir"] != prev["dir"] or sig["stage"] > prev["stage"]
    if changed and sig["dir"] and sig["stage"] >= 1 and (rising or c["trend"] is None) and not sent_today:
        msg = message(c, conf, stage, samples, st["scores"])
        st["sent_n"] = st.get("sent_n", 0) + 1 if st.get("sent_day") == day else 1
        st["sent_day"] = day
        call = {"t": now.isoformat(), "dir": sig["dir"], "stage": sig["stage"], "p": price, "zone": c["zone"],
                "net": c["window"]["net"], "trend": c["trend"]}
        st.setdefault("calls", []).append(call)
        if not dry_run:
            _append(CALLS, {"type": "call", **call})
    st["signal"] = sig
    for call in st.get("calls", []):                                    # vyhodnocení signálů radaru
        age = (now - datetime.fromisoformat(call["t"])).days
        for hz in (7, 30):
            if age >= hz and f"r{hz}" not in call and price and call.get("p"):
                call[f"r{hz}"] = round((price / call["p"] - 1) * 100 * call["dir"], 2)
                if not dry_run:
                    _append(CALLS, {"type": "eval", "call_t": call["t"], "horizon_d": hz, "r_pct_dir": call[f"r{hz}"]})
    state.save()
    if not dry_run:
        for x in new:
            if x["d"]:                                                   # do repozitáře jen zprávy se směrem
                _append(LOG, {k: v for k, v in x.items() if k != "k"})
        out = json.dumps({"scores": st["scores"]}, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        try:                                                             # jen při změně (jinak by byl commit každou hodinu)
            if not SOURCES_OUT.exists() or SOURCES_OUT.read_text(encoding="utf-8") != out:
                SOURCES_OUT.write_text(out, encoding="utf-8")
        except Exception:
            pass
    if msg:
        print(msg)
        if not dry_run:
            (send or _telegram)(msg)
    return msg


def report(state):
    """/radar – aktuální stav radaru, zdroje a úspěšnost."""
    st = state.data.get("narrative") or {}
    last = st.get("last")
    if not last:
        return "📡 Radar vyprávění ještě neběžel (skener ho počítá jednou za hodinu)."
    c = {"zone": last["zone"], "window": last["window"], "base": last["base"], "trend": last["trend"], "dir": last["dir"]}
    items = st.get("items", [])
    side = last["dir"] or (1 if last["window"]["bull"] >= last["window"]["bear"] else -1)
    samples = sorted([x for x in items if x["d"] == side], key=lambda x: x["t"])[-3:]
    text = message(c, last.get("conf") or {}, last.get("stage", 0), samples, st.get("scores"))
    ok = sum(1 for v in (st.get("status") or {}).values() if v.startswith("ok"))
    text += f"\nZdroje: {ok}/{len(st.get('status') or {})} dostupných, zpráv v paměti {len(items)}. Spočítáno {last['as_of'][:16]}."
    calls = [x for x in st.get("calls", []) if "r7" in x]
    if calls:
        r = np.array([x["r7"] for x in calls])
        text += f"\nSignály radaru: {len(calls)} vyhodnocených, Ø pohyb BTC ve směru za 7 dní {r.mean():+.1f} %, " \
                f"úspěšnost {(r > 0).mean() * 100:.0f} %."
    return text


def _append(path, rec):
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _telegram(text):
    from scanner import notify
    return notify.telegram(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="zkusit zdroje a vypsat aktuální shodu")
    ap.add_argument("--channels", default="", help="veřejné kanály Telegramu oddělené čárkou")
    a = ap.parse_args()
    import yaml
    cfg = yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text())
    chans = [c for c in a.channels.split(",") if c] or (cfg.get("narrative") or {}).get("telegram_channels") or []
    chans = list(dict.fromkeys(chans + TG_CANDIDATES))
    now = datetime.now(timezone.utc)
    raw, status = fetch_all(chans)
    print("Zdroje:")
    for k, v in status.items():
        print(f"  {k}: {v}")
    items = tag_items(raw, now)
    print(f"\nZpráv za 3 dny: {len(items)}, býčích {sum(x['d'] > 0 for x in items)}, "
          f"medvědích {sum(x['d'] < 0 for x in items)}")
    c = consensus(items, now)
    print(json.dumps(c, ensure_ascii=False, indent=1))
    per = {}
    for x in items:
        p = per.setdefault(x["src"], [0, 0, 0])
        p[0] += 1
        p[1] += x["d"] > 0
        p[2] += x["d"] < 0
    print("\nPodle zdroje (zpráv / býčích / medvědích):")
    for k, (n, b, s) in sorted(per.items(), key=lambda kv: -kv[1][0]):
        print(f"  {k}: {n} / {b} / {s}")
    print("\nUkázky:")
    for d in (1, -1):
        for x in [x for x in items if x["d"] == d][:6]:
            print(f"  {'+' if d > 0 else '−'} [{x['src']}] {x['title'][:120]}")


if __name__ == "__main__":
    main()
