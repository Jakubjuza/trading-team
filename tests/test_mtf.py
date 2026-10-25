"""Vstup z nižších TF (1D signál → 4H směr → 1H zóna → 1H spouštěč) – syntetická data."""
from datetime import timedelta

import pandas as pd
import pytest

from scanner import mtf
from scanner.scan import State, mtf_entries, update_paper_positions

T0 = pd.Timestamp("2026-03-10", tz="UTC")


def hourly(window_rows, base=200):
    rows = [(100 + 0.1 * i, 100.2 + 0.1 * i, 99.9 + 0.1 * i, 100.1 + 0.1 * i) for i in range(base)]   # růst před signálem
    rows += window_rows
    idx = pd.date_range(T0 - pd.Timedelta(hours=base), periods=len(rows), freq="1h", tz="UTC")
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"], index=idx).assign(Volume=1.0)


DIP_AND_TURN = [(120, 120.2, 118.5, 118.8), (118.8, 120.6, 118.7, 120.5)]


def test_trigger_long_entry_and_swing_stop():
    h1 = hourly(DIP_AND_TURN)
    r = mtf.find_trigger("long", h1, T0, daily_stop=112, targets=[130, 140], atr=3.0)
    assert r["status"] == "entry" and r["time"] == T0 + pd.Timedelta(hours=1) and r["entry"] == 120.5
    assert r["stop"] == pytest.approx(min(118.5 - 0.3, 120.5 * 0.985))            # swing − 0,1 ATR, min. 1,5 %


def test_trigger_waits_stops_and_skips():
    assert mtf.find_trigger("long", hourly([(120, 120.3, 119.9, 120.2)]), T0, 112, [130, 140], 3.0) is None
    crash = hourly([(120, 120.1, 111.0, 111.5)])
    assert mtf.find_trigger("long", crash, T0, 112, [130, 140], 3.0)["status"] == "stopped"
    assert mtf.find_trigger("long", hourly(DIP_AND_TURN), T0, 112, [120.0, 140], 3.0)["status"] == "skipped"


def test_scanner_opens_mtf_paper_position_and_expires(tmp_path):
    cfg = {"timeframe": "1h", "notify": {"telegram": True}, "mtf_entry": {"enabled": True, "wait_hours": 72}}
    setup = {"direction": "long", "entry": 121.0, "stop": 112.0, "targets": [130.0, 140.0], "rr": [1.0, 2.1],
             "hold_time": (T0 - pd.Timedelta(days=1)).isoformat(), "meta": {"atr": 3.0}}
    state = State(tmp_path / "s.json")
    state.data["mtf_pending"] = [{"id": "BTC|1d|long|x", "symbol": "BTC/USDT", "strategy": "pullback_1d", "setup": setup,
                                  "exit": {"split": 0.5, "trail_atr": 3.0, "max_hold_bars": 20}, "t0": T0.isoformat()}]
    sent = []
    msgs = mtf_entries(cfg, state, {("BTC/USDT", "1h"): hourly(DIP_AND_TURN)}, T0 + timedelta(hours=2), send=sent.append)
    assert msgs[0].startswith("📍 Vstup z nižších TF (papírově): BTC/USDT LONG") and sent == msgs
    pos = state.data["open"][0]
    assert pos["strategy"] == "pullback_1d+mtf" and pos["mtf"] and pos["exit"]["max_hold_bars"] == 480
    assert state.data["mtf_pending"] == []
    # stop zasažen na hodinovém grafu → 📕 s označením varianty
    h1 = hourly(DIP_AND_TURN + [(120.5, 120.6, 117.0, 117.5)])
    update_paper_positions({"notify": {"telegram": False}}, state, {("BTC/USDT", "1h"): h1}, 0.15)
    assert state.data["open"] == [] and state.data["closed"][0]["result"] == "stop"
    # bez spouštěče do 72 h → vyprší
    state.data["mtf_pending"] = [
        {"id": "ETH|x", "symbol": "ETH/USDT", "strategy": "donchian_1d", "setup": setup, "exit": {}, "t0": T0.isoformat()}]
    flat = hourly([(120, 120.3, 119.9, 120.2)] * 3)
    msgs = mtf_entries(cfg, state, {("ETH/USDT", "1h"): flat}, T0 + timedelta(hours=73), send=lambda m: None)
    assert msgs[0].startswith("⌛ Vstup z nižších TF nenastal: ETH/USDT LONG") and state.data["mtf_pending"] == []
