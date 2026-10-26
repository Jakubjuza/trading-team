"""Testy radaru vyprávění: třídění zpráv, zdroje, shoda, potvrzení cenou a průchod skeneru (bez sítě)."""
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from research import narrative as nr
from scanner.scan import State

UTC = timezone.utc
NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)


def test_classify_phrases_flips_and_questions():
    assert nr.classify("Bitcoin enters bear market as ETF outflows grow")[0] == -1
    assert nr.classify("Analysts say the bottom is in for BTC")[0] == 1
    assert nr.classify("Crypto bear market is over, says strategist")[0] == 1          # konec bear marketu = býčí
    assert nr.classify("Is the bull run over? Bitcoin slips")[0] == -1
    assert nr.classify("Is the bottom in for bitcoin?") == (1, 1.0)                     # otázka = poloviční váha
    assert nr.classify("BTC breaks below support as liquidations mount")[0] == -1
    assert nr.classify("Apple unveils new iPhone with record sales")[0] == 0          # mimo trh krypta
    assert nr.classify("Bitcoin price today: steady near $90K")[0] == 0
    # chyby nalezené na skutečných titulcích 26. 10. 2026
    assert nr.classify("Galaxy Digital Says Bitcoin Bear Market Is Officially Over")[0] == 1
    assert nr.classify("Bitcoin ETFs break 2-week outflow streak with $301M comeback")[0] == 1
    assert nr.classify("Quantum computing fears may not crash Bitcoin, says analyst")[0] == 0
    assert nr.classify("Brazil's Stock Market Crashes After Upset Victory")[0] == 0     # není o kryptu
    assert nr.classify("Strategist warns BTC could drop below $70,000")[0] == -1


def test_parsers():
    tg = ('<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message_text '
          'js-message_text" dir="auto">BTC <b>bear market</b> confirmed<br/>more downside</div>'
          '<a class="tgme_widget_message_date"><time datetime="2026-10-27T10:00:00+00:00" class="time"></time>')
    items = nr.parse_telegram(tg, "kanal")
    assert items == [{"title": "BTC bear market confirmed more downside", "time": "2026-10-27T10:00:00+00:00",
                      "source": "Telegram @kanal"}]
    atom = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Is the bottom in? BTC</title>'
            '<updated>2026-10-27T09:00:00Z</updated></entry></feed>')
    assert nr.parse_atom(atom, "Reddit")[0]["time"] == "2026-10-27T09:00:00+00:00"
    by = {"result": {"list": [{"title": "New listing", "description": "XYZ", "dateTimestamp": 1793095200000}]}}
    assert nr.parse_bybit(by)[0]["title"] == "New listing XYZ"


def test_fetch_all_survives_failing_source(monkeypatch):
    monkeypatch.setattr(nr, "SOURCES", {
        "A": ("rss", "rss://a", 1.0), "B": ("rss", "atom://b", 0.5), "C": ("bybit", "api://c", 0.5),
        "D": ("rss", "down://d", 1.0)})
    rss = ('<rss><channel><item><title>Bitcoin crash deepens</title>'
           '<pubDate>Tue, 27 Oct 2026 08:00:00 GMT</pubDate></item></channel></rss>')
    atom = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>BTC rally</title>'
            '<updated>2026-10-27T09:00:00Z</updated></entry></feed>')

    def get(url):
        if url.startswith("down"):
            raise TimeoutError
        return {"rss": rss, "atom": atom, "api": json.dumps({"result": {"list": []}}),
                "https": '<div class="tgme_widget_message_wrap"></div>'}[url.split(":")[0]]
    items, status = nr.fetch_all(["kanal"], get=get)
    assert status["A"] == "ok (1)" and status["B"] == "ok (1)" and status["C"] == "ok (0)"
    assert status["D"].startswith("chyba") and status["Telegram @kanal"] == "ok (0)"
    assert {x["source"] for x in items} == {"A", "B"} and {x["w"] for x in items} == {1.0, 0.5}


def _item(src, d, hours_ago, w=1.0):
    return {"k": f"{src}{hours_ago}{d}", "t": (NOW - timedelta(hours=hours_ago)).isoformat(), "src": src, "w": w,
            "d": d, "s": float(d), "title": "x", "p": 100.0}


def test_consensus_zone_needs_sources_and_trend_needs_history():
    few = [_item("A", -1, 1), _item("A", -1, 2), _item("B", -1, 3)]
    assert nr.consensus(few, NOW)["zone"] == "smíšené"                          # 2 zdroje nestačí
    bear = [_item(s, -1, 5) for s in "ABCDE"] + [_item("F", 1, 6)]
    c = nr.consensus(bear, NOW)
    assert c["zone"] == "medvědí shoda" and c["dir"] == -1 and c["trend"] is None
    base = [_item(s, 1, 24 * d) for d in range(4, 12) for s in "AB"]           # dřív převládalo býčí
    c = nr.consensus(bear + base, NOW)
    assert c["trend"] == "sílí medvědí" and c["base"]["net"] > 0


def _frame(n, step, freq, end):
    idx = pd.date_range(end=end, periods=n, freq=freq, tz="UTC")
    close = 100 + step * np.arange(n, dtype=float)
    return pd.DataFrame({"Open": close, "High": close + 0.5, "Low": close - 0.5, "Close": close, "Volume": 1.0},
                        index=idx)


def test_tf_confirm_and_stages():
    down = _frame(60, -1.0, "1h", "2026-10-27 10:00")
    up = _frame(60, 1.0, "1h", "2026-10-27 10:00")
    assert nr.tf_confirm(down, -1) == 2 and nr.tf_confirm(down, 1) == 0 and nr.tf_confirm(up, 1) == 2
    flat = down.copy()
    flat.iloc[-5:, :4] = flat["Close"].iloc[-25:-5].min() + 1                    # pod středem, bez nového minima
    assert nr.tf_confirm(flat, -1) == 1
    conf, stage = nr.confirmation({"1h": down, "4h": down, "1d": up}, -1)
    assert conf == {"1h": 2, "4h": 2, "1d": 0} and stage == 2


def test_update_alerts_once_and_scores_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(nr, "CALLS", tmp_path / "calls.jsonl")
    monkeypatch.setattr(nr, "SOURCES_OUT", tmp_path / "src.json")
    cfg = {"narrative": {"enabled": True, "fetch_minutes": 60}}
    state = State(tmp_path / "state.json")
    h1 = _frame(600, -0.1, "1h", "2026-10-27 11:00")
    frames = {("BTC/USDT", "1h"): h1, ("BTC/USDT", "1d"): _frame(60, -1.0, "1D", "2026-10-26")}
    raw = [{"title": f"Bitcoin bear market deepens, says {s}", "time": (NOW - timedelta(hours=2)).isoformat(),
            "source": s, "w": 1.0} for s in "ABCDE"]
    sent = []
    msg = nr.update(cfg, state, frames, NOW, fetch=lambda ch: (raw, {"A": "ok (5)"}), send=sent.append)
    assert msg and "medvědí shoda" in msg and "1H ✅" in msg and sent == [msg]
    assert len((tmp_path / "log.jsonl").read_text().splitlines()) == 5
    assert nr.update(cfg, state, frames, NOW + timedelta(minutes=30), fetch=lambda ch: (raw, {})) is None
    again = nr.update(cfg, state, frames, NOW + timedelta(hours=2), fetch=lambda ch: (raw, {}), send=sent.append)
    assert again is None and len(sent) == 1                                     # stejný stupeň = bez zprávy
    later = NOW + timedelta(days=8)                                             # cena mezitím klesla → zásah
    frames[("BTC/USDT", "1h")] = _frame(600, -0.1, "1h", later.strftime("%Y-%m-%d %H:00")) - 50
    nr.update(cfg, state, frames, later, fetch=lambda ch: ([], {}))
    sc = state.data["narrative"]["scores"]
    assert sc["A"]["n7"] == 1 and sc["A"]["hit7"] == 1
    assert state.data["narrative"]["calls"][0]["r7"] > 0
    assert "radar" in nr.report(state).lower() and "Signály radaru: 1" in nr.report(state)


def test_disabled_does_nothing(tmp_path):
    assert nr.update({"narrative": {"enabled": False}}, State(tmp_path / "s.json"), {}, NOW) is None
