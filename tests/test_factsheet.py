"""Testy datového listu – výpočty na syntetických datech, odpovědi API napodobené (sandbox je blokuje)."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from research import factsheet as fs


def _candles(n=400, start=100.0, drift=0.0, seed=1, freq="1h"):
    rng = np.random.default_rng(seed)
    c = start * np.exp(np.cumsum(rng.normal(drift, 0.004, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * 1.002
    l = np.minimum(o, c) * 0.998
    idx = pd.date_range("2026-09-01", periods=n, freq=freq, tz="UTC")
    return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c, "Volume": rng.uniform(100, 200, n)}, index=idx)


def test_structure_detects_uptrend_and_downtrend():
    up = fs.structure_tf(_candles(drift=0.002))
    down = fs.structure_tf(_candles(drift=-0.002))
    assert up["trend"] == "up" and up["dist_ema200_pct"] > 0
    assert down["trend"] == "down" and down["dist_ema200_pct"] < 0
    assert 0 <= up["range20_pos_pct"] <= 100 and 0 < up["rsi14"] < 100


def test_volume_profile_poc_at_heavy_volume():
    df = _candles(200)
    df.loc[df.index[50:60], "Volume"] = 50_000                        # obří objem v jednom místě
    zone = (df["Low"].iloc[50:60].min(), df["High"].iloc[50:60].max())
    vp = fs.volume_profile(df)
    assert zone[0] - 1 <= vp["poc"] <= zone[1] + 1
    assert vp["val"] <= vp["poc"] <= vp["vah"]


def test_liquidity_pools_equal_highs():
    df = _candles(120, drift=0.0, seed=3)
    for i in (30, 60, 90):                                            # tři stejná maxima nad cenou
        df.iloc[i, df.columns.get_loc("High")] = 130.0
    price = float(df["Close"].iloc[-1])
    pools = fs.liquidity_pools(df, price)
    assert any(abs(p["price"] - 130.0) < 0.3 and p["touches"] >= 2 for p in pools["above"])


def test_orderbook_depth_and_imbalance():
    book = {"bids": [[99.9, 10], [99.5, 10], [98.0, 100]], "asks": [[100.1, 5], [100.5, 5], [102.5, 50]]}
    ob = fs.section_orderbook(book)
    assert ob["mid"] == 100.0 and ob["spread_bps"] == pytest.approx(20.0)
    d = ob["depth_1pct"]
    assert d["bid_usd"] == pytest.approx(99.9 * 10 + 99.5 * 10, rel=1e-6)
    assert d["imbalance"] > 0                                          # víc nákupů v ±1 %
    assert ob["walls"]["bids"][0]["price"] == 98.0


def test_derivatives_hyperliquid_parsing():
    def post(p):
        if p["type"] == "metaAndAssetCtxs":
            return [{"universe": [{"name": "ETH"}, {"name": "BTC"}]},
                    [{}, {"funding": "0.0000125", "openInterest": "25000", "markPx": "80000", "prevDayPx": "80800",
                          "premium": "0.0001", "dayNtlVlm": "1200000000"}]]
        return [{"fundingRate": "0.00001"}] * 48
    d = fs.section_derivatives("BTC", post)
    assert d["funding_annual_pct"] == pytest.approx(0.0000125 * 24 * 365 * 100, abs=0.1)   # ≈ 10,9 %
    assert d["open_interest_usd"] == 25000 * 80000
    assert d["price_change_24h_pct"] == pytest.approx(-0.99, abs=0.01)
    assert "error" in fs.section_derivatives("DOGE", post)


def test_options_deribit_max_pain_pc_and_skew():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    rows = []
    for exp, days in (("25OCT26", 1), ("27NOV26", 34)):
        for k in (70000, 75000, 80000, 85000, 90000):
            for cp in ("C", "P"):
                iv = 50 + (k < 80000 and cp == "P") * 8 - (k > 80000 and cp == "C") * 2
                oi = 300 if (k == 75000) else 100
                rows.append({"instrument_name": f"BTC-{exp}-{k}-{cp}", "open_interest": oi, "mark_iv": iv,
                             "underlying_price": 80000})
    def get(url, params):
        if "book_summary" in url:
            return {"result": rows}
        return {"result": {"data": [[0, 0, 0, 0, 48.0], [1, 0, 0, 0, 52.0]]}}
    o = fs.section_options("BTC", get, now)
    assert o["put_call_oi"] == pytest.approx(1.0)
    assert o["skew_25d_approx_30d"] > 0                                 # puty dražší
    assert o["max_pain_nearest"] == 75000                               # strike s největším OI
    assert o["implied_move_7d_pct"] == pytest.approx(o["atm_iv_30d"] * (7 / 365) ** 0.5, abs=0.01)
    assert o["dvol"] == 52.0 and o["dvol_7d_change"] == 4.0


def test_section_error_is_captured():
    def boom(p):
        raise ConnectionError("blocked")
    d = fs.section_derivatives("BTC", boom)
    assert "error" in d and "blocked" in d["error"]


def test_build_end_to_end_with_mocks(monkeypatch):
    frames = {"1h": _candles(400), "4h": _candles(300, freq="4h"), "1d": _candles(250, freq="1D")}

    class Ex:
        def fetch_order_book(self, s, limit=500):
            p = float(frames["1h"]["Close"].iloc[-1])
            return {"bids": [[p * 0.999, 3], [p * 0.99, 10]], "asks": [[p * 1.001, 2], [p * 1.01, 8]]}

    monkeypatch.setattr(fs, "section_derivatives", lambda coin: {"source": "mock", "funding_annual_pct": 5.0})
    monkeypatch.setattr(fs, "section_options", lambda coin: {"source": "mock"})
    monkeypatch.setattr(fs, "section_macro", lambda daily: {"source": "mock", "regime": "neutrální"})
    monkeypatch.setattr(fs, "section_history", lambda sym, d, strategy=None: {"source": "mock"})
    monkeypatch.setattr(fs.events, "section_events", lambda coin: {"source": "mock", "calendar": []})
    monkeypatch.setattr(fs.onchain, "section_onchain", lambda coin: {"source": "mock"})
    monkeypatch.setattr(fs.scenarios, "section_scenarios", lambda coin: {"source": "mock"})
    sheet = fs.build("BTC/USDT", signal={"setup": {"direction": "long"}}, frames=frames, ex=Ex())
    for k in ("structure", "levels", "orderflow", "orderbook", "derivatives", "options", "macro", "scenarios", "onchain", "events", "sessions", "history"):
        assert k in sheet and "error" not in sheet[k], (k, sheet[k])
    assert set(sheet["structure"]) >= {"1h", "4h", "1d"}
    assert sheet["levels"]["volume_profile_7d"]["poc"] is not None


# --- napojení: verdikty, Telegram, měření --------------------------------------
def test_verdict_groups_compare_approved_vs_rejected():
    from scanner.evaluate import verdict_groups
    sigs = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
    res = [{"result": "T2", "r": 2.0}, {"result": "stop", "r": -1.1}, {"result": "stop", "r": -1.0}, {"result": "open", "r": 0}]
    v = {"a": {"grade": "A"}, "b": {"grade": "NO_TRADE"}, "d": {"grade": "B"}}
    g = verdict_groups(sigs, res, v)
    assert [x["r"] for x in g["schváleno (A/B)"]] == [2.0]                 # otevřený "d" se nepočítá
    assert [x["r"] for x in g["zamítnuto (C/NO_TRADE)"]] == [-1.1]
    assert [x["r"] for x in g["bez verdiktu"]] == [-1.0]


def test_format_verdict_for_telegram():
    from research.send_verdicts import format_verdict
    txt = format_verdict({"symbol": "BTC/USDT", "direction": "short", "grade": "B",
                          "summary": ["1. a", "2. b", "3. c", "4. d", "5. e"], "vetoes": ["FOMC 28. 10."]})
    assert txt.startswith("🧠 Desk verdikt: BTC/USDT SHORT – 🟡 B")
    assert "5. e" in txt and "Veto: FOMC" in txt and "finanční poradenství" in txt


def test_scanner_writes_factsheet_path(tmp_path, monkeypatch):
    import json as _json
    import scanner.scan as sc
    from tests.test_rules import _cfg, _FakeCache, load, POSITIVE
    from datetime import datetime, timezone
    monkeypatch.setattr("research.factsheet.build", lambda sym, ex, signal=None: {"symbol": sym, "signal": signal})
    monkeypatch.setattr(sc, "FACTSHEETS", sc.HERE.parent / "research" / "factsheets" / "_pytest")
    cfg = _cfg(factsheet=True)
    try:
        sc.scan_once(cfg, _FakeCache(load(POSITIVE[3][0])), sc.State(tmp_path / "s.json"),
                     now=datetime(2026, 8, 27, 12, 5, tzinfo=timezone.utc))
        rec = _json.loads(sc.SIGNALS.read_text().splitlines()[-1])
        assert rec["factsheet"].startswith("research/factsheets/_pytest/") and (sc.HERE.parent / rec["factsheet"]).exists()
    finally:
        import shutil
        shutil.rmtree(sc.HERE.parent / "research" / "factsheets" / "_pytest", ignore_errors=True)
