"""📋 Export otevřených pozic pro Agentown (scanner/positions_export.py)."""
import json
from datetime import datetime, timedelta, timezone

from scanner import lab_report, positions_export as pe
from scanner.scan import State

CFG = {"account_size": 10000, "risk_pct": 0.5, "exit": {"split": 0.5}, "pyramid": {"unit_r": 0.5, "add_atr": 1.0}}
NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def _state(tmp_path, monkeypatch):
    monkeypatch.setattr(lab_report, "CACHE", tmp_path)                 # ceny laboratoře jen ze skeneru
    st = State(tmp_path / "s.json")
    st.data["open"] = [
        {"id": "c1", "symbol": "BTC/USDT", "timeframe": "1d", "strategy": "donchian_1d", "demo": {"status": "open"},
         "setup": {"direction": "long", "entry": 100.0, "stop": 95.0, "targets": [110.0, 120.0], "hold_time": "2026-11-15"}},
        {"id": "c2", "symbol": "ETH/USDT", "timeframe": "1d", "strategy": "pullback_1d", "t1_notified": True,
         "setup": {"direction": "short", "entry": 50.0, "stop": 52.0, "targets": [46.0, 42.0], "hold_time": "2026-11-14"}}]
    st.data["pyramid"] = {"open": [{"id": "p1", "symbol": "ETH/USDT", "direction": "short", "entry": 50.0, "stop": 52.0,
                                    "atr": 1.0, "notified_units": 2, "stop_now": 51.0}]}
    st.data["lab"] = {"open": [{"sid": "a", "label": "Bollinger průraz · 4H long", "coin": "SOL", "tf": "4h", "dir": "long",
                                "signal_bar": "2026-11-16T08:00:00+00:00", "signal_close": 100.0, "entry": 100.0,
                                "rf": 0.04, "stop": 96.0, "strategy": {"exit": "target"}}]}
    st.data["ensemble"] = {"cash": 4000.0, "start_equity": 5000.0, "qty": {"SOL": 10.0}, "avg": {"SOL": 100.0},
                           "equity": [["2026-10-26", 5000.0]]}
    prices = {"BTC/USDT": (105.0, ""), "ETH/USDT": (48.0, ""), "SOL/USDT": (102.0, "")}
    return st, prices


def test_core_loss_to_stop_and_gain_to_targets(tmp_path, monkeypatch):
    st, prices = _state(tmp_path, monkeypatch)
    doc = pe.build(CFG, st, prices, NOW)
    assert doc["risk_usd"] == 50.0
    btc, eth = doc["parts"][0]["positions"]
    # long 100 / stop 95: teď +1 R, ztráta −1 R = −50 USD, zisk 0,5 × 2 R + 0,5 × 4 R = 3 R = 150 USD
    assert (btc["r_now"], btc["r_loss"], btc["r_gain"]) == (1.0, -1.0, 3.0)
    assert (btc["usd_loss"], btc["usd_gain"], btc["demo"]) == (-50.0, 150.0, True)
    # short po T1: stop na vstupu, polovina vybrána na +2 R → nejhůř +1 R, teď 1 + 0,5 × 1 = 1,5 R
    assert eth["stop"] == 50.0 and eth["stop_orig"] == 52.0
    assert (eth["r_loss"], eth["r_now"], eth["r_gain"]) == (1.0, 1.5, 3.0)


def test_pyramid_and_lab(tmp_path, monkeypatch):
    st, prices = _state(tmp_path, monkeypatch)
    doc = pe.build(CFG, st, prices, NOW)
    pyr = doc["parts"][1]["positions"][0]
    # kusy 50 a 49, stop 51 → 0,25 × (−1 − 2) = −0,75 R; teď 0,25 × (2 + 1) = +0,75 R; cíl žádný
    assert (pyr["r_loss"], pyr["r_now"], pyr["r_gain"]) == (-0.75, 0.75, None)
    lab = doc["parts"][2]["positions"][0]
    # riziko 4 = 2 ATR → ATR 2, cíl 3 ATR = 106 → +1,5 R; stop 96 → −1 R
    assert lab["targets"] == [106.0] and (lab["r_loss"], lab["r_gain"]) == (-1.0, 1.5)
    assert doc["ensemble"]["value"] == 5020.0 and doc["prices"]["SOL"] == 102.0


def test_maybe_write_only_on_change_or_hourly(tmp_path, monkeypatch):
    st, prices = _state(tmp_path, monkeypatch)
    out = tmp_path / "positions.json"
    assert pe.maybe_write(CFG, st, prices, NOW, out)
    assert not pe.maybe_write(CFG, st, prices, NOW + timedelta(minutes=10), out)
    st.data["open"].pop()                                                # uzavřená pozice → zapsat hned
    assert pe.maybe_write(CFG, st, prices, NOW + timedelta(minutes=11), out)
    assert pe.maybe_write(CFG, st, prices, NOW + timedelta(minutes=70), out)
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["id"] == "state" and len(doc["parts"][0]["positions"]) == 1
