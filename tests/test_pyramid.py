"""🔺 Pyramida – přikupování, posun stopu, uzavření a oddělení od hlavních pozic."""
import json

import pandas as pd
import pytest

from scanner import pyramid
from scanner.scan import State, setup_id
from scanner.rules import Setup

P = {**pyramid.DEFAULTS, "enabled": True}


def frame(rows, start="2026-01-02"):
    idx = pd.date_range(start, periods=len(rows), freq="1D", tz="UTC")
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"], index=idx)


POS = {"id": "x", "symbol": "BTC/USDT", "timeframe": "1d", "strategy": "donchian_1d", "direction": "long",
       "entry": 100.0, "stop": 96.0, "atr": 2.0, "hold_time": "2026-01-01T00:00:00+00:00", "notified_units": 1}


def test_adds_units_and_raises_stop_then_stops_out():
    after = frame([(100, 102.5, 99.5, 102), (102, 104.5, 101.5, 104), (104, 105, 99, 100)])
    res = pyramid.simulate(POS, after, P, 0.0)
    assert [u[1] for u in res["units"]] == [100.0, 102.0, 104.0]          # +1 ATR a +2 ATR
    assert res["closed"] and res["reason"] == "stop"
    # stop po 3. kusu = 104 − 2×2 = 100, trailing 104 − 6 = 98 → stop 100; kus = 0,5 R / 4
    unit = 0.5 / 4
    assert res["exit"] == 100.0 and res["r"] == pytest.approx(unit * ((100 - 100) + (100 - 102) + (100 - 104)))


def test_short_mirror_and_time_exit():
    pos = {**POS, "direction": "short", "entry": 100.0, "stop": 104.0}
    after = frame([(100, 100.5, 97.5, 98)] + [(98, 98.5, 97.6, 98)] * 25)
    res = pyramid.simulate(pos, after, {**P, "max_hold_bars": 20}, 0.0)
    assert len(res["units"]) == 2 and res["reason"] == "time" and res["bars"] == 20
    assert res["r"] == pytest.approx(0.5 / 4 * ((100 - 98) + (98 - 98)))


def test_open_has_own_limits_and_messages(tmp_path):
    state = State(tmp_path / "s.json")
    cfg = {"pyramid": {"enabled": True}, "notify": {"telegram": False}}
    sent = []
    def cand(sym, d="long"):
        t = pd.Timestamp("2026-01-01", tz="UTC")
        s = Setup(direction=d, kind="donchian_breakout", entry=100.0, stop=96.0, targets=[108.0, 116.0], level=99.0,
                  range_high=99.0, range_low=90.0, breakout_time=t, retest_time=t, hold_time=t, rr=[2.0, 4.0],
                  meta={"atr": 2.0})
        return (sym, "crypto", "1d", None, s, {"name": "donchian_1d", "min_rr": 1.0})
    c = [cand(f"{x}/USDT") for x in ("BTC", "ETH", "SOL")]
    msgs = pyramid.open_new(cfg, state, c, "2026-01-02", setup_id, send=sent.append)
    assert len(state.data["pyramid"]["open"]) == 2 and len(msgs) == 2       # max. 2 na strategii a směr
    assert "1. kus" in msgs[0] and "102" in msgs[0] and "106" in msgs[0]
    assert pyramid.open_new(cfg, state, c, "2026-01-02", setup_id, send=sent.append) == []   # žádné duplikáty
    assert "open" not in state.data                                          # hlavní pozice nedotčené


def test_update_notifies_adds_and_logs_close(tmp_path):
    state = State(tmp_path / "s.json")
    state.data["pyramid"] = {"open": [dict(POS)], "closed": [], "seen": {}, "per_day": {}}
    cfg = {"pyramid": {"enabled": True}, "notify": {"telegram": False}}
    df = frame([(100, 101, 99, 100), (100, 102.5, 99.5, 102)], start="2026-01-01")
    msgs = pyramid.update(cfg, state, {("BTC/USDT", "1d"): df}, 0.0, send=lambda m: None)
    assert len(msgs) == 1 and "2. kus" in msgs[0] and state.data["pyramid"]["open"][0]["notified_units"] == 2
    df2 = pd.concat([df, frame([(102, 102, 97, 97)], start="2026-01-03")])
    msgs = pyramid.update(cfg, state, {("BTC/USDT", "1d"): df2}, 0.0, send=lambda m: None)
    assert "uzavřena" in msgs[-1] and state.data["pyramid"]["open"] == []
    rec = json.loads(pyramid.OUTCOMES.read_text().splitlines()[-1])
    assert rec["units"] == 2 and rec["reason"] == "stop"
    assert "uzavřené 1" in pyramid.heartbeat_line(state)
