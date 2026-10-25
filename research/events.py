#!/usr/bin/env python3
"""Kalendář událostí a zprávy – Fed, inflace, trh práce, hlasování a regulace, geopolitika, zprávy k mincím.

Zdroje (zdarma, bez klíče; ze sandboxu jsou blokované, běží v GitHub Actions):
  • FOMC – pevný seznam z kalendáře Fedu (FOMC_DECISIONS, ověřeno, viz FOMC_SOURCE),
  • ekonomický kalendář ForexFactory (týden + příští týden): CPI, PCE, NFP, HDP, projevy Fedu, ECB, BoJ …
    s časem, očekáváním (forecast) a minulou hodnotou,
  • expirace opcí Deribit (poslední pátek v měsíci 08:00 UTC – spočítané),
  • titulky zpráv z RSS: CoinDesk, Cointelegraph, Google News (k mincím z watchlistu + geopolitika,
    regulace/hlasování, Fed/inflace). Titulky se jen roztřídí podle klíčových slov – výklad dělá AI agent.

Jak silně události hýbou kryptem, je změřené v reports/events.md (statistiky v research/events_stats.json).

Použití:
    python3 research/events.py                 # nadcházející události 7 dní + titulky (JSON)
    python3 research/events.py --coin SOL
"""
import argparse
import json
import re
import time as _time
import xml.etree.ElementTree as ET
from datetime import datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "scanner" / "cache"
STATS = ROOT / "research" / "events_stats.json"
NY = ZoneInfo("America/New_York")
PRAGUE = ZoneInfo("Europe/Prague")
DAYS_CS = ["po", "út", "st", "čt", "pá", "so", "ne"]
UA = {"User-Agent": "Mozilla/5.0 (trading-team research)"}
FAIL_TTL = 600                                                            # po výpadku zdroje další pokus za 10 min

# Den rozhodnutí FOMC (druhý den zasedání), prohlášení 14:00 New York, tisková konference 14:30.
FOMC_SOURCE = "federalreserve.gov/monetarypolicy/fomccalendars.htm (2027: tisková zpráva Fedu 5. 9. 2025; termíny jsou předběžné)"
FOMC_DECISIONS = [
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08",
]
FOMC_SEP = {"2026-03-18", "2026-06-17", "2026-09-16", "2026-12-09"}   # s ekonomickými projekcemi („dot plot“)

FF_URLS = ["https://nfs.faireconomy.media/ff_calendar_thisweek.json",
           "https://nfs.faireconomy.media/ff_calendar_nextweek.json"]
FF_COUNTRIES = {"USD": "USA", "EUR": "eurozóna", "CNY": "Čína", "JPY": "Japonsko", "GBP": "Británie"}

COIN_NAMES = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "XRP Ripple", "ADA": "cardano",
              "LINK": "chainlink", "AVAX": "avalanche crypto", "DOGE": "dogecoin", "BNB": "BNB binance coin"}
NEWS_TOPICS = {
    "geopolitika": "markets (war OR tariffs OR sanctions OR ceasefire OR missile OR escalation)",
    "regulace a hlasování": "crypto (SEC OR CFTC OR bill OR Senate OR Congress OR stablecoin OR \"ETF approval\" OR regulation)",
    "Fed a inflace": "(\"Federal Reserve\" OR Powell OR FOMC OR inflation OR CPI OR \"rate cut\") markets",
}
RSS_FEEDS = {"CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
             "Cointelegraph": "https://cointelegraph.com/rss"}

# třídění titulků podle klíčových slov (jen pomůcka pro agenta, ne hodnocení)
TAGS = {
    "regulace": r"\b(sec|cftc|regulat\w*|bill|senate|congress|house vote|vote[sd]?|law|lawsuit|court|ban|license|mica)\b",
    "etf": r"\betfs?\b|inflows?|outflows?",
    "fed/makro": r"\b(fed|fomc|powell|inflation|cpi|pce|jobs report|payrolls|rate cut|rate hike|yields?|recession)\b",
    "geopolitika": r"\b(war|tariffs?|sanctions?|missile|attack|ceasefire|china|russia|iran|israel|ukraine|taiwan|election)\b",
    "bezpečnost": r"\b(hack\w*|exploit\w*|stolen|drain\w*|breach)\b",
    "burzy": r"\b(listing|lists|delist\w*|coinbase|binance|kraken|robinhood)\b",
}
POSITIVE = (r"\b(approv\w*|surge\w*|soar\w*|rall\w*|record|inflows?|adopt\w*|partnership|launch\w*|upgrade\w*|bullish|"
            r"wins?|passes|passed|rises?|rising|jumps?|gains?|climbs?|rebound\w*|breaks? above)\b")
NEGATIVE = (r"\b(reject\w*|plunge\w*|crash\w*|slump\w*|outflows?|hack\w*|exploit\w*|lawsuit|sue[sd]?|ban\w*|delist\w*|"
            r"bearish|fraud|probe|selloff|sell-off|falls?|drops?|tumbles?|slides?|sinks?|liquidat\w*|falls? below)\b")


def prague(ts):
    loc = ts.astimezone(PRAGUE)
    return f"{DAYS_CS[loc.weekday()]} {loc:%d.%m. %H:%M}"


def _get(url, timeout=8):
    import requests
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r


def cached(name, ttl_s, fetch):
    """Výsledek fetch() uložený v scanner/cache na ttl_s – zdroje nechceme volat každou minutu."""
    path = CACHE / f"events_{name}.json"
    try:
        if path.exists() and _time.time() - path.stat().st_mtime < ttl_s:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    fail = CACHE / f"events_{name}.fail"
    try:
        if fail.exists() and _time.time() - fail.stat().st_mtime < FAIL_TTL:
            return {"rows": [], "items": [], "errors": ["zdroj nedostupný – další pokus do 10 min"]}
    except Exception:
        pass
    data = fetch()
    if data.get("errors") and not (data.get("rows") or data.get("items")):
        try:                                                              # výpadek: nezkoušet každou minutu znovu
            CACHE.mkdir(parents=True, exist_ok=True)
            fail.write_text(datetime.now(timezone.utc).isoformat())
        except Exception:
            pass
        return data
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception:
        pass
    return data


# --- události ------------------------------------------------------------------------------
def fomc_events(start, end):
    out = []
    for d in FOMC_DECISIONS:
        ts = datetime.combine(datetime.fromisoformat(d).date(), time(14, 0), NY).astimezone(timezone.utc)
        if start <= ts < end:
            out.append({"time": ts, "title": "FOMC – rozhodnutí Fedu o sazbách" + (" + projekce" if d in FOMC_SEP else ""),
                        "country": "USA", "impact": "High", "kind": "fomc", "source": FOMC_SOURCE})
    return out


def deribit_expiries(start, end):
    out = []
    y, m = start.year, start.month
    while datetime(y, m, 1, tzinfo=timezone.utc) <= end:
        d = datetime(y + (m == 12), m % 12 + 1, 1, 8, tzinfo=timezone.utc) - timedelta(days=1)
        while d.weekday() != 4:
            d -= timedelta(days=1)
        if start <= d < end:
            q = m in (3, 6, 9, 12)
            out.append({"time": d, "title": f"{'Čtvrtletní' if q else 'Měsíční'} expirace opcí BTC/ETH (Deribit)",
                        "country": "krypto", "impact": "Medium", "kind": "expiry", "source": "Deribit – poslední pátek 08:00 UTC"})
        y, m = y + (m == 12), m % 12 + 1
    return out


def parse_ff(rows, start, end, impacts=("High",)):
    out = []
    for r in rows or []:
        if r.get("impact") not in impacts or r.get("country") not in FF_COUNTRIES:
            continue
        try:
            ts = datetime.fromisoformat(r["date"]).astimezone(timezone.utc)
        except (KeyError, ValueError):
            continue
        title = r.get("title", "")
        if not (start <= ts < end) or r["country"] == "USD" and re.search(r"FOMC|Federal Funds Rate", title):
            continue                                                      # FOMC máme z kalendáře Fedu
        out.append({"time": ts, "title": r.get("title", ""), "country": FF_COUNTRIES[r["country"]],
                    "impact": r["impact"], "kind": "macro", "forecast": r.get("forecast") or None,
                    "previous": r.get("previous") or None, "source": "ForexFactory (nfs.faireconomy.media)"})
    return out


def fetch_ff():
    rows, errors = [], []
    for u in FF_URLS:
        try:
            rows += _get(u).json()
        except Exception as exc:
            errors.append(f"{u.rsplit('/', 1)[-1]}: {exc.__class__.__name__}")
    return {"rows": rows, "errors": errors, "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def upcoming(now=None, days=7, ff=None, impacts=("High",)):
    """Seřazené události od teď do now+days. ff = výstup fetch_ff (None = stáhne/z cache)."""
    now = now or datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    if ff is None:
        try:
            ff = cached("ff", 3 * 3600, fetch_ff)
        except Exception as exc:
            ff = {"rows": [], "errors": [str(exc)]}
    evs = fomc_events(now, end) + deribit_expiries(now, end) + parse_ff(ff.get("rows"), now, end, impacts)
    evs.sort(key=lambda e: e["time"])
    return evs, ff.get("errors", [])


# --- zprávy --------------------------------------------------------------------------------
def parse_rss(xml_text, source, max_items=40):
    items = []
    root = ET.fromstring(xml_text)
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = it.findtext("pubDate")
        try:
            ts = parsedate_to_datetime(pub).astimezone(timezone.utc) if pub else None
        except (TypeError, ValueError):
            ts = None
        src = it.findtext("source") or source
        if title:
            items.append({"title": title, "link": link, "time": ts.isoformat() if ts else None, "source": src})
        if len(items) >= max_items:
            break
    return items


def title_key(title):
    """Klíč pro deduplikaci – bez „ - Zdroj“ na konci (Google News) a bez interpunkce."""
    return re.sub(r"\W+", "", re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", title).lower())[:80]


def tag(title):
    t = title.lower()
    tags = [k for k, rx in TAGS.items() if re.search(rx, t)]
    pos, neg = len(re.findall(POSITIVE, t)), len(re.findall(NEGATIVE, t))
    tone = "pozitivní" if pos > neg else "negativní" if neg > pos else "neutrální"
    return tags, tone


def mentions(title, coin):
    t = title.lower()
    names = {coin.lower()} | set(COIN_NAMES.get(coin, "").lower().split()) - {"crypto", "coin"}
    return any(re.search(rf"\b{re.escape(n)}\b", t) for n in names if n)


_AMOUNT = r"(?:\s*(?:million|billion|trillion|mln|bn|m|b)\b|\s*%)"


def price_levels(title):
    """Cenové úrovně v titulku: „$1.40“, „$85K“, „1.4 resistance“ – ne objemy ($500 million) ani procenta."""
    out = []
    for m in re.finditer(r"(\$)?\s?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?([kK])?(?!\d)", title):
        dollar, num, k = m.group(1), m.group(2), m.group(3)
        rest = title[m.end():m.end() + 12]
        if re.match(_AMOUNT, rest, re.I) or (not dollar and "." not in num and not k):
            continue                                      # objem, procento, nebo holé celé číslo (rok, počet)
        v = float(num.replace(",", "")) * (1000 if k else 1)
        if v > 0:
            out.append(v)
    return out


def stale_price(title, price, tol_pct=6.0):
    """True = titulek mluví o cenách, které jsou všechny daleko od aktuální ceny (stará zpráva nebo spekulace)."""
    lv = [v for v in price_levels(title) if 0.2 < v / price < 5] if price else []
    return bool(lv) and all(abs(v / price - 1) * 100 > tol_pct for v in lv)


_STOP = {"the", "and", "for", "with", "after", "amid", "as", "to", "of", "in", "on", "at", "is", "are", "its", "this",
         "that", "from", "by", "price", "crypto", "news", "today", "why", "how", "what", "will", "could", "may"}


def _words(title):
    t = re.sub(r"\s+[-–|]\s+[^-–|]{2,40}$", "", title.lower())
    return {w for w in re.findall(r"[a-z]{3,}", t) if w not in _STOP}


def is_rehash(item, items, coin, min_gap_h=12, min_sim=0.5):
    """True = stejné téma k minci vyšlo už aspoň `min_gap_h` hodin dřív (přepis staré zprávy s novým datem)."""
    ts = datetime.fromisoformat(item["time"])
    w = _words(item["title"])
    for o in items:
        if o is item or not o.get("time") or not mentions(o["title"], coin):
            continue
        if datetime.fromisoformat(o["time"]) > ts - timedelta(hours=min_gap_h):
            continue
        ow = _words(o["title"])
        if w and ow and len(w & ow) / len(w | ow) >= min_sim:
            return True
    return False


def google_news(query):
    return f"https://news.google.com/rss/search?q={quote_plus(query + ' when:2d')}&hl=en-US&gl=US&ceid=US:en"


def fetch_news(coins):
    feeds = dict(RSS_FEEDS)
    for c in coins:
        feeds[f"Google News: {c}"] = google_news(COIN_NAMES.get(c, c) + " crypto")
    for topic, q in NEWS_TOPICS.items():
        feeds[f"Google News: {topic}"] = google_news(q)
    items, errors = [], []
    for name, url in feeds.items():
        try:
            for x in parse_rss(_get(url).text, name):
                x["feed"] = name
                items.append(x)
        except Exception as exc:
            errors.append(f"{name}: {exc.__class__.__name__}")
    return {"items": items, "errors": errors, "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def news_digest(raw, coin=None, now=None, hours=48, limit=12):
    """Titulky za posledních `hours` hodin: k minci, k tématům (geopolitika, regulace, Fed), krypto obecně."""
    now = now or datetime.now(timezone.utc)
    seen, out = set(), {"coin": [], "geopolitika": [], "regulace a hlasování": [], "Fed a inflace": [], "krypto": []}
    for x in raw.get("items", []):
        key = title_key(x["title"])
        if key in seen:
            continue
        if x.get("time") and datetime.fromisoformat(x["time"]) < now - timedelta(hours=hours):
            continue
        seen.add(key)
        tags, tone = tag(x["title"])
        row = {"title": x["title"], "time": prague(datetime.fromisoformat(x["time"])) if x.get("time") else None,
               "source": x.get("source"), "link": x.get("link"), "tags": tags, "tone": tone}
        feed = x.get("feed", "")
        if coin and (mentions(x["title"], coin) or feed == f"Google News: {coin}"):
            out["coin"].append(row)
        elif feed.startswith("Google News: ") and feed[13:] in NEWS_TOPICS:
            out[feed[13:]].append(row)
        else:
            out["krypto"].append(row)
    out = {k: sorted(v, key=lambda r: r["time"] or "", reverse=True)[:limit] for k, v in out.items()}
    out["note"] = "tone/tags = jen klíčová slova v titulku, ne analýza; výklad a „co je naceněno“ dělá agent."
    return out


# --- statistiky a výstupy -------------------------------------------------------------------
def load_stats(path=STATS):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def fomc_effect(df, decisions=None, hours=4):
    """Rozkmit (high/low) v `hours` hodinách po rozhodnutí FOMC vs. stejná hodina UTC v jiné pracovní dny."""
    import numpy as np
    import pandas as pd
    evs = [e["time"] for e in fomc_events(df.index[0].to_pydatetime(), df.index[-1].to_pydatetime())] \
        if decisions is None else decisions
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    rng = lambda i: h[i:i + hours].max() / l[i:i + hours].min() - 1          # noqa: E731
    days = {e.date() for e in evs}
    a, pre = [], []
    for e in evs:
        i = df.index.searchsorted(pd.Timestamp(e))
        if hours <= i and i + hours <= len(df):
            a.append(rng(i))
            pre.append(rng(i - 24) if i >= 24 else np.nan)
    if len(a) < 5:
        return {"n": len(a)}
    hrs = {e.hour for e in evs}
    base = [rng(i) for i in range(len(df) - hours)
            if df.index[i].weekday() < 5 and df.index[i].hour in hrs and df.index[i].date() not in days]
    base_pre = np.nanmean([h[i:i + hours].max() / l[i:i + hours].min() - 1 for i in range(len(df) - hours)])
    return {"n": len(a), "hours": hours, "range_x_vs_same_hour": round(float(np.mean(a) / np.mean(base)), 2),
            "range_before_x": round(float(np.nanmean(pre) / base_pre), 2)}


def event_line(e, stats=None):
    st = (stats or {}).get("fomc", {}).get("range_x_vs_same_hour") if e["kind"] == "fomc" else None
    extra = []
    if e.get("forecast"):
        extra.append(f"očekávání {e['forecast']}")
    if e.get("previous"):
        extra.append(f"minule {e['previous']}")
    if st:
        extra.append(f"hist. {str(st).replace('.', ',')}× rozkmit 4 h")
    return f"{prague(e['time'])} {e['title']} ({e['country']})" + (f" – {', '.join(extra)}" if extra else "")


def context_line(now=None, hours=24, events=None, stats=None):
    """Řádek do Telegramu: nejbližší důležitá událost do `hours` h (FOMC, CPI, NFP …)."""
    now = now or datetime.now(timezone.utc)
    evs = events if events is not None else upcoming(now, 2)[0]
    stats = load_stats() if stats is None else stats
    near = [e for e in evs if e["impact"] == "High" and now <= e["time"] <= now + timedelta(hours=hours)]
    if not near:
        return ""
    e = near[0]
    more = f" (+{len(near) - 1} další)" if len(near) > 1 else ""
    return f"📅 {event_line(e, stats)}{more}"


def section_events(coin=None, now=None, days=7, ff=None, news=None, coins=None):
    """Sekce datového listu: kalendář na 7 dní + titulky za 48 h (mince, geopolitika, regulace, Fed)."""
    now = now or datetime.now(timezone.utc)
    stats = load_stats()
    evs, ff_err = upcoming(now, days, ff, impacts=("High", "Medium"))
    if news is None:
        news = cached("news_" + "_".join(sorted(coins or [coin or "BTC"])), 30 * 60, lambda: fetch_news(coins or [coin or "BTC"]))
    return {"source": "kalendář Fedu, ForexFactory, Deribit, RSS (CoinDesk, Cointelegraph, Google News)",
            "as_of": now.isoformat(timespec="seconds"),
            "calendar": [{**{k: v for k, v in e.items() if k != "time"}, "prague": prague(e["time"]),
                          "in_hours": round((e["time"] - now).total_seconds() / 3600, 1)} for e in evs],
            "calendar_errors": ff_err, "news": news_digest(news, coin, now), "news_errors": news.get("errors", []),
            "stats": stats.get("fomc"),
            "note": (f"FOMC: hist. rozkmit 4 h po rozhodnutí {(stats.get('fomc') or {}).get('range_x_vs_same_hour', '?')}× "
                     "vůči stejné hodině jiné dny (reports/events.md); směr se jako signál nepoužívá. "
                     "Výsledek dat vs. očekávání (forecast) hodnotí agent.")}


def build_stats(frames):
    """frames: {coin: hodinové svíčky} → průměr přes mince (každá stejná váha)."""
    import numpy as np
    per = {c: fomc_effect(df) for c, df in frames.items() if df is not None and len(df) > 24 * 120}
    ok = [v for v in per.values() if v.get("n", 0) >= 5]
    pooled = {k: round(float(np.mean([v[k] for v in ok])), 2) for k in ("range_x_vs_same_hour", "range_before_x")} if ok else {}
    return {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fomc": {**pooled, "n_meetings": max((v["n"] for v in ok), default=0), "coins": per}}


def report_md(stats):
    f = stats["fomc"]
    rows = [f"| {c} | {v.get('n', 0)} | {v.get('range_x_vs_same_hour', 0):.2f}× | {v.get('range_before_x', 0):.2f}× |"
            for c, v in f["coins"].items()]
    return "\n".join([
        f"# Kalendář událostí a krypto ({stats['generated'][:10]})", "",
        "## FOMC (rozhodnutí Fedu, 14:00 New York)", "",
        f"{f.get('n_meetings', 0)} zasedání 2024–2026, hodinové svíčky. Rozkmit = high/low okna. Kontrola = stejná hodina "
        "UTC v jiné pracovní dny (americká seance je živější i bez Fedu, proto ne obyčejný průměr).", "",
        "| Mince | Zasedání | Rozkmit 4 h po rozhodnutí vs. stejná hodina jindy | 4 h den předem vs. běžné 4 h |", "|---|---|---|---|",
        *rows, "",
        f"Průměr: **{f.get('range_x_vs_same_hour', 0):.2f}×** po rozhodnutí, {f.get('range_before_x', 0):.2f}× den předem. "
        "Po Fedu tedy výrazně větší knoty (riziko pro stop), den předem běžný trh. Směr po FOMC se neměří jako signál – "
        f"{f.get('n_meetings', 0)} zasedání je na to málo.", "",
        "## Ostatní", "",
        "- Měsíční expirace opcí Deribit (poslední pátek 08:00 UTC): rozkmit 4 h ≈ 0,9× běžného – měřitelný vliv nemá.",
        "- CPI, PCE, NFP a další data: historická data vydání nejsou zdarma ke stažení, proto se zatím neměří. Desk je "
        "bere z kalendáře ForexFactory (čas, očekávání, minulá hodnota) a hodnotí je jako riziko knotu.",
        "- Zprávy: titulky z CoinDesk, Cointelegraph a Google News (mince z watchlistu, geopolitika, regulace a "
        "hlasování, Fed a inflace) se jen roztřídí podle klíčových slov; význam a „co je naceněno“ hodnotí events-analyst.",
        "", "Zdroj termínů FOMC: " + FOMC_SOURCE + ".", "", "Nejde o finanční poradenství.", ""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coin", default="BTC")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--stats", action="store_true", help="přepočítat research/events_stats.json + reports/events.md")
    ap.add_argument("--cache-dir", type=Path, default=CACHE)
    a = ap.parse_args()
    if a.stats:
        import sys
        import yaml
        sys.path.insert(0, str(ROOT))
        from scanner import evaluate as ev
        cfg = yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text(encoding="utf-8"))
        frames = {t["symbol"].split("/")[0]: ev.load_history(t["symbol"], "crypto", "1h", 730, cfg.get("exchange", "kraken"),
                                                             a.cache_dir) for t in cfg["tickers"] if t["source"] == "crypto"}
        stats = build_stats(frames)
        STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (ROOT / "reports" / "events.md").write_text(report_md(stats), encoding="utf-8")
        print(f"OK: {STATS}")
        return
    print(json.dumps(section_events(a.coin, days=a.days), ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
