"""Testy kalendáře událostí, třídění zpráv a upozornění skeneru (bez sítě)."""
from datetime import datetime, timedelta, timezone

from research import events as ev
from scanner.scan import State, event_alerts

UTC = timezone.utc
NOW = datetime(2026, 10, 27, 7, 0, tzinfo=UTC)                     # út 8:00 Praha
FF = {"rows": [
    {"title": "CPI m/m", "country": "USD", "date": "2026-10-27T08:30:00-04:00", "impact": "High",
     "forecast": "0.3%", "previous": "0.4%"},
    {"title": "German Ifo", "country": "EUR", "date": "2026-10-27T04:00:00-04:00", "impact": "Medium"},
    {"title": "Some Low", "country": "USD", "date": "2026-10-27T10:00:00-04:00", "impact": "Low"},
    {"title": "AUD thing", "country": "AUD", "date": "2026-10-27T10:00:00-04:00", "impact": "High"},
    {"title": "FOMC Statement", "country": "USD", "date": "2026-10-28T14:00:00-04:00", "impact": "High"},
]}


def test_fomc_time_and_dst():
    f = ev.fomc_events(datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 12, 31, tzinfo=UTC))
    assert [e["time"] for e in f] == [datetime(2026, 10, 28, 18, 0, tzinfo=UTC),        # EDT
                                      datetime(2026, 12, 9, 19, 0, tzinfo=UTC)]         # EST
    assert ev.prague(f[0]["time"]) == "st 28.10. 19:00" and "projekce" in f[1]["title"]


def test_deribit_last_friday():
    e = ev.deribit_expiries(datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 12, 31, tzinfo=UTC))
    assert [x["time"].date().isoformat() for x in e] == ["2026-10-30", "2026-11-27", "2026-12-25"]
    assert e[-1]["title"].startswith("Čtvrtletní")


def test_upcoming_filters_and_dedupes_fomc():
    evs, err = ev.upcoming(NOW, 7, ff=FF)
    titles = [e["title"] for e in evs]
    assert "CPI m/m" in titles and "German Ifo" not in titles and "Some Low" not in titles
    assert "AUD thing" not in titles and "FOMC Statement" not in titles               # FOMC z kalendáře Fedu
    assert sum("FOMC" in t for t in titles) == 1 and titles == sorted(titles, key=titles.index)
    medium, _ = ev.upcoming(NOW, 7, ff=FF, impacts=("High", "Medium"))
    assert "German Ifo" in [e["title"] for e in medium]
    cpi = next(e for e in evs if e["title"] == "CPI m/m")
    assert ev.event_line(cpi) == "út 27.10. 13:30 CPI m/m (USA) – očekávání 0.3%, minule 0.4%"


def test_context_line_next_24h_only():
    evs, _ = ev.upcoming(NOW, 7, ff=FF)
    assert ev.context_line(NOW, 24, evs, stats={}).startswith("📅 út 27.10. 13:30 CPI m/m")
    assert ev.context_line(NOW + timedelta(days=3), 24, evs, stats={}) == ""


def test_tags_tone_mentions():
    tags, tone = ev.tag("SEC approves spot Solana ETF as inflows surge")
    assert "regulace" in tags and "etf" in tags and tone == "pozitivní"
    assert ev.tag("Hackers drain $200M from bridge")[1] == "negativní"
    assert ev.mentions("Solana hits record", "SOL") and ev.mentions("SOL price", "SOL")
    assert not ev.mentions("Solar panels", "SOL") and not ev.mentions("Bitcoin rallies", "ETH")


def test_parse_rss_and_digest():
    rss = """<rss><channel>
      <item><title>Ethereum ETF sees record inflows</title><link>https://x/1</link>
            <pubDate>Tue, 27 Oct 2026 06:00:00 GMT</pubDate><source>Reuters</source></item>
      <item><title>Ethereum ETF sees record inflows</title><link>https://x/1b</link>
            <pubDate>Tue, 27 Oct 2026 06:10:00 GMT</pubDate></item>
      <item><title>Old news</title><link>https://x/2</link><pubDate>Mon, 19 Oct 2026 06:00:00 GMT</pubDate></item>
    </channel></rss>"""
    items = [dict(x, feed="CoinDesk") for x in ev.parse_rss(rss, "CoinDesk")]
    assert len(items) == 3 and items[0]["source"] == "Reuters"
    d = ev.news_digest({"items": items}, "ETH", NOW)
    assert [r["title"] for r in d["coin"]] == ["Ethereum ETF sees record inflows"]          # duplikát a staré pryč
    assert d["coin"][0]["tone"] == "pozitivní"


def _cfg(**kw):
    c = {"tickers": [{"symbol": "ETH/USDT", "source": "crypto"}], "timezone": "Europe/Prague",
         "events": {"enabled": True, "digest_hour": 8, "pre_alert_minutes": 60, "news_max_per_day": 1}}
    c.update(kw)
    return c


def test_event_alerts_digest_pre_and_news(tmp_path):
    state = State(tmp_path / "s.json")
    evs, _ = ev.upcoming(NOW, 2, ff=FF)
    news = {"items": [
        {"title": "SEC approves Ethereum staking ETF", "time": (NOW - timedelta(minutes=30)).isoformat(), "source": "Reuters", "link": "l1"},
        {"title": "Ethereum hack drains exchange", "time": (NOW - timedelta(minutes=20)).isoformat(), "source": "X", "link": "l2"},
        {"title": "Ethereum price today", "time": (NOW - timedelta(minutes=10)).isoformat(), "source": "X", "link": "l3"},
        {"title": "Bitcoin ETF approved", "time": (NOW - timedelta(minutes=10)).isoformat(), "source": "X", "link": "l4"},
    ]}
    msgs = event_alerts(_cfg(), state, NOW, True, events=evs, news=news)
    assert msgs[0].startswith("📅 Kalendář dnes a zítra:") and "CPI m/m" in msgs[0] and "FOMC" in msgs[0]
    assert sum(m.startswith("📰") for m in msgs) == 1 and "staking ETF" in msgs[-1]      # limit 1/den, BTC není ve watchlistu
    assert not any(m.startswith("⚠️") for m in msgs)                                       # CPI je až za 5,5 h
    assert event_alerts(_cfg(), state, NOW, True, events=evs, news=news) == []            # nic dvakrát
    later = NOW + timedelta(hours=5)                                                       # 30 min před CPI
    pre = event_alerts(_cfg(), state, later, True, events=evs, news={"items": []})
    assert len(pre) == 1 and pre[0].startswith("⚠️ Za 30 min: út 27.10. 13:30 CPI m/m")
    assert event_alerts(_cfg(), state, later, True, events=evs, news={"items": []}) == []


def test_event_alerts_disabled(tmp_path):
    assert event_alerts({"tickers": [], "events": {"enabled": False}}, State(tmp_path / "s.json"), NOW, True) == []


def test_ff_fomc_duplicates_and_tone_words():
    rows = {"rows": [{"title": "Federal Funds Rate", "country": "USD", "date": "2026-10-28T14:00:00-04:00", "impact": "High"},
                     {"title": "FOMC Press Conference", "country": "USD", "date": "2026-10-28T14:30:00-04:00", "impact": "High"}]}
    evs, _ = ev.upcoming(NOW, 7, ff=rows)
    assert [e["kind"] for e in evs if "Fed" in e["title"] or "FOMC" in e["title"]] == ["fomc"]
    assert ev.tag("Bitcoin Falls Below $80,000 as U.S. Pulls Staff")[1] == "negativní"
    assert ev.tag("Solana jumps 8% after upgrade")[1] == "pozitivní"


def test_title_key_ignores_source_suffix():
    assert ev.title_key("Bitcoin or Gold: Which Is Better? - 24/7 Wall St.") == ev.title_key("Bitcoin or Gold: Which Is Better? - Yahoo Finance")
