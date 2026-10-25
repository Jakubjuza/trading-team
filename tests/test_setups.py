"""Testy knihovny setupů, tabulky pravděpodobností a skeneru s více strategiemi."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from scanner import calibrate, setups
from scanner.scan import State, approach_alerts, scan_once, update_paper_positions

NOFILTER = {"trend_ema": 0, "min_stop_pct": 0.0, "min_stop_atr": 0.0, "skip_weekends": False}


def frame(rows, freq="1h", start="2026-01-05", vol=None):
    df = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"])
    df["Volume"] = vol if vol is not None else 1000.0
    df.index = pd.date_range(start, periods=len(df), freq=freq, tz="UTC")
    return df


def flat(n, mid=100.0, half=1.0):
    return [(mid, mid + half, mid - half, mid)] * n


def mirror(df):
    m = df.copy()
    m["Open"], m["High"], m["Low"], m["Close"] = 200 - df["Open"], 200 - df["Low"], 200 - df["High"], 200 - df["Close"]
    return m


# --- donchian ------------------------------------------------------------------------
def test_donchian_long_short_and_negative():
    df = frame(flat(30) + [(100, 103.5, 99.8, 103)])
    s = setups.find("donchian_breakout", df, params=NOFILTER, last_only=True)
    assert [x.direction for x in s] == ["long"]
    assert s[0].stop == pytest.approx(103 - 2 * s[0].meta["atr"] - 0.1 * s[0].meta["atr"])
    assert [x.direction for x in setups.find("donchian_breakout", mirror(df), params=NOFILTER, last_only=True)] == ["short"]
    df_no = frame(flat(30) + [(100, 101.5, 99.8, 100.5)])               # close pod maximem kanálu
    assert setups.find("donchian_breakout", df_no, params=NOFILTER, last_only=True) == []


def test_donchian_trend_filter():
    rows = [(150, 151, 149, 150)] * 60 + flat(30) + [(100, 103.5, 99.8, 103)]
    df = frame(rows)
    assert setups.find("donchian_breakout", df, params={**NOFILTER, "trend_ema": 50}, last_only=True) == []


# --- pullback ------------------------------------------------------------------------
def _uptrend_pullback(final_close):
    rows = [(100 + i, 101 + i, 99.5 + i, 100.8 + i) for i in range(40)]       # silný růst
    rows += [(140, 140.5, 137, 137.5), (137.5, 138, 135.5, 136)]              # pokles k EMA
    rows += [(136, final_close + 0.5, 135.8, final_close)]                     # obratová svíčka
    return frame(rows)


PB = {**NOFILTER, "ema_fast": 5, "ema_mid": 10, "ema_slow": 20, "slope_bars": 3, "touch_tol_pct": 2.0, "lookback": 3}


def test_pullback_long_and_short():
    df = _uptrend_pullback(139.0)                                             # close nad high předchozí svíčky
    assert [x.direction for x in setups.find("pullback", df, params=PB, last_only=True)] == ["long"]
    assert [x.direction for x in setups.find("pullback", mirror(df), params=PB, last_only=True)] == ["short"]


def test_pullback_needs_reversal_candle():
    df = _uptrend_pullback(137.0)                                             # close pod high předchozí (138)
    assert setups.find("pullback", df, params=PB, last_only=True) == []


# --- sweep & reclaim ------------------------------------------------------------------------
def test_sweep_reclaim_long_and_negative():
    vol = [1000.0] * 25 + [3000.0]
    df = frame(flat(25) + [(99.5, 100.5, 96.5, 100.2)], vol=vol)            # knot pod 99, close zpět nad
    s = setups.find("sweep_reclaim", df, params=NOFILTER, last_only=True)
    assert [x.direction for x in s] == ["long"] and s[0].level == pytest.approx(99.0)
    df_close_below = frame(flat(25) + [(99.5, 100, 96.5, 98.0)], vol=vol)   # zavřel pod → žádný reclaim
    assert setups.find("sweep_reclaim", df_close_below, params=NOFILTER, last_only=True) == []
    df_low_vol = frame(flat(25) + [(99.5, 100.5, 96.5, 100.2)])             # bez objemu
    assert setups.find("sweep_reclaim", df_low_vol, params=NOFILTER, last_only=True) == []


# --- squeeze --------------------------------------------------------------------------------
def test_squeeze_breakout_long():
    rows = [(100, 100.2, 99.8, 100.1 if i % 2 else 99.9) for i in range(130)]
    rows.append((100, 103, 99.9, 102.5))
    vol = [1000.0] * 130 + [3000.0]
    s = setups.find("squeeze_breakout", frame(rows, vol=vol), params=NOFILTER, last_only=True)
    assert [x.direction for x in s] == ["long"]
    assert setups.find("squeeze_breakout", frame(rows), params=NOFILTER, last_only=True) == []   # bez objemu


# --- range fade -----------------------------------------------------------------------------
def test_range_fade_long_targets_mid_and_top():
    osc = [(100, 104, 96, 103) if i % 2 else (100, 104, 96, 97) for i in range(80)]
    drop = [(99, 99.2, 97, 97.2), (97.2, 97.4, 96.6, 96.8), (96.8, 97, 96.2, 96.4)]
    rows = osc + drop + [(96.4, 98.5, 96.0, 98.2)]                             # dotek dna + býčí svíčka
    p = {**NOFILTER, "adx_max": 100, "rsi_low": 50, "range_bars": 40}
    s = setups.find("range_fade", frame(rows), params=p, last_only=True)
    assert [x.direction for x in s] == ["long"]
    assert s[0].targets[0] == pytest.approx((s[0].range_high + s[0].range_low) / 2)


# --- společné ---------------------------------------------------------------------------------
def test_min_stop_pct_applies_to_all_setups():
    df = frame(flat(30) + [(100, 103.5, 99.8, 103)])
    s = setups.find("donchian_breakout", df, params={**NOFILTER, "stop_atr": 0.1, "min_stop_pct": 3.0}, last_only=True)[0]
    assert (s.entry - s.stop) / s.entry * 100 >= 3.0 - 1e-9


def test_find_all_vs_last_only_consistent():
    df = frame(flat(30) + [(100, 103.5, 99.8, 103)])
    allx = setups.find("donchian_breakout", df, params=NOFILTER)
    assert allx and allx[-1].meta["hold_index"] == len(df) - 1


def test_features_regime():
    df = frame([(100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(260)])
    f = setups.features(setups.Ctx(df), 259, "long")
    assert f["trend"] == "with" and f["volume"] == "normal" and f["vol"] in ("low", "mid", "high")
    assert setups.features(setups.Ctx(df), 259, "short")["trend"] == "against"


# --- pravděpodobnosti ------------------------------------------------------------------------
def _trades(n, p_t1, r_win, trend="with"):
    return [{"t1": i < n * p_t1, "r": r_win if i < n * p_t1 else -1.0, "trend": trend, "vol": "mid", "volume": "normal"}
            for i in range(n)]


def test_summarize_and_lookup():
    tr = _trades(100, 0.4, 2.0) + _trades(10, 0.9, 2.0, trend="against")
    table = calibrate.build_table(tr)
    st, key = calibrate.lookup(table)
    assert key == "*|*|*" and st["n"] == 110
    assert st["p_t1"] == pytest.approx(49 / 110, abs=1e-3)
    assert st["avg_r"] == pytest.approx((49 * 2 - 61) / 110, abs=1e-3)
    # jemná skupina s < 30 obchody se nepoužije → hrubší skupina
    st2, key2 = calibrate.lookup(table, {"trend": "against", "vol": "mid", "volume": "normal"}, detail=True)
    assert key2 == "*|*|*"
    st3, key3 = calibrate.lookup(table, {"trend": "with", "vol": "mid", "volume": "normal"}, detail=True)
    assert key3 == "with|mid|normal" and st3["p_t1"] == pytest.approx(0.4)


def test_calibration_report_counts():
    is_t = _trades(200, 0.3, 2.0)
    oos_t = _trades(100, 0.3, 2.0)
    cal = calibrate.calibration(is_t, oos_t)
    assert cal["n"] == 100 and cal["pred_p_t1"] == pytest.approx(0.3) and cal["actual_p_t1"] == pytest.approx(0.3)


# --- skener: více strategií, T1, „blíží se“ -----------------------------------------------------
class Cache:
    def __init__(self, frames):
        self.frames = frames

    def update(self, source, symbol, tf, now=None):
        return self.frames[tf]


def cfg_multi(**kw):
    c = {"tickers": [{"symbol": "BTC/USDT", "source": "crypto"}], "timeframe": "1h", "direction": "both",
         "account_size": 10000, "risk_pct": 0.5, "min_rr": 1.0, "max_setups_per_day": 5, "timezone": "Europe/Prague",
         "notify": {"telegram": False, "chart": False}, "paper_trading": False, "costs": {"fee_pct": 0.1, "slippage_pct": 0.05},
         "probabilities": "tests/fixtures/_none.json",
         "strategies": [{"name": "don_1d", "setup": "donchian_breakout", "timeframe": "1d", "params": NOFILTER,
                         "exit": {"split": 0.5, "trail_atr": 3.0, "max_hold_bars": 20}, "min_rr": 1.0,
                         "max_open_per_direction": 1}]}
    c.update(kw)
    return c


def test_scan_multi_strategy_signal_and_position(tmp_path):
    d1 = frame(flat(30) + [(100, 103.5, 99.8, 103)], freq="1D")
    h1 = frame(flat(40), freq="1h")
    state = State(tmp_path / "s.json")
    now = datetime(2026, 2, 6, tzinfo=timezone.utc)
    found = scan_once(cfg_multi(), Cache({"1d": d1, "1h": h1}), state, now=now)
    assert len(found) == 1 and found[0][1].kind == "donchian_breakout"
    assert state.data["open"][0]["strategy"] == "don_1d" and state.data["open"][0]["exit"]["trail_atr"] == 3.0
    assert scan_once(cfg_multi(), Cache({"1d": d1, "1h": h1}), state, now=now) == []      # deduplikace


def test_t1_milestone_notified_once(tmp_path):
    d1 = frame(flat(30) + [(100, 103.5, 99.8, 103)], freq="1D")
    state = State(tmp_path / "s.json")
    scan_once(cfg_multi(), Cache({"1d": d1, "1h": frame(flat(40))}), state, now=datetime(2026, 2, 6, tzinfo=timezone.utc))
    pos = state.data["open"][0]
    t1 = pos["setup"]["targets"][0]
    nxt = pd.concat([d1, frame([(103, t1 + 0.5, 102.9, t1)], freq="1D", start=d1.index[-1] + pd.Timedelta(days=1))])
    update_paper_positions(cfg_multi(), state, {("BTC/USDT", "1d"): nxt}, 0.15, dry_run=True)
    assert state.data["open"][0].get("t1_notified") is True
    update_paper_positions(cfg_multi(), state, {("BTC/USDT", "1d"): nxt}, 0.15, dry_run=True)
    assert len(state.data["open"]) == 1                                            # pořád otevřená, žádné opakování


def test_approach_alert_once_per_day(tmp_path):
    d1 = frame(flat(30, half=1.0), freq="1D")                                      # kanál 99–101
    h1 = frame(flat(5, mid=100.8, half=0.1))                                        # cena těsně pod 101
    state = State(tmp_path / "s.json")
    cfg = cfg_multi(approach_alerts={"enabled": True, "atr_distance": 0.5, "max_per_day": 4})
    frames = {("BTC/USDT", "1d"): d1, ("BTC/USDT", "1h"): h1}
    msgs = approach_alerts(cfg, state, frames, cfg["strategies"], datetime(2026, 2, 6, tzinfo=timezone.utc), "2026-02-06", True)
    assert len(msgs) == 1 and "LONG" in msgs[0] and "101" in msgs[0]
    assert approach_alerts(cfg, state, frames, cfg["strategies"], datetime(2026, 2, 6, tzinfo=timezone.utc), "2026-02-06", True) == []


def test_closed_position_logged_to_outcomes(tmp_path):
    import json
    import scanner.scan as sc
    d1 = frame(flat(30) + [(100, 103.5, 99.8, 103)], freq="1D")
    state = State(tmp_path / "s.json")
    scan_once(cfg_multi(), Cache({"1d": d1, "1h": frame(flat(40))}), state, now=datetime(2026, 2, 6, tzinfo=timezone.utc))
    stop = state.data["open"][0]["setup"]["stop"]
    nxt = pd.concat([d1, frame([(103, 103.2, stop - 1, stop - 0.5)], freq="1D", start=d1.index[-1] + pd.Timedelta(days=1))])
    update_paper_positions(cfg_multi(), state, {("BTC/USDT", "1d"): nxt}, 0.15, dry_run=False)
    rec = json.loads(sc.OUTCOMES.read_text().splitlines()[-1])
    assert rec["result"] == "stop" and rec["r"] < -1 and rec["strategy"] == "don_1d" and state.data["open"] == []


def test_approach_alert_uses_decimal_comma(tmp_path):
    d1 = frame(flat(30, half=1.0), freq="1D")
    h1 = frame(flat(5, mid=100.8, half=0.1))
    cfg = cfg_multi(approach_alerts={"enabled": True, "atr_distance": 0.5, "max_per_day": 4})
    msgs = approach_alerts(cfg, State(tmp_path / "s.json"), {("BTC/USDT", "1d"): d1, ("BTC/USDT", "1h"): h1},
                           cfg["strategies"], datetime(2026, 2, 6, tzinfo=timezone.utc), "2026-02-06", True)
    assert "0,20 %" in msgs[0]


def test_panic_filter_skips_high_volatility():
    rows = flat(260, half=1.0) + [(100, 108.0, 92.0, 100)] * 5 + [(100, 109.5, 99.8, 109)]   # panika: ATR vyletí
    df = frame(rows, freq="1D")
    assert setups.find("donchian_breakout", df, params=NOFILTER, last_only=True)                      # bez filtru signál
    p = {**NOFILTER, "panic_vol_rank": 0.8, "panic_window": 365}
    assert setups.find("donchian_breakout", df, params=p, last_only=True) == []
    calm = frame(flat(100) + flat(60, half=4.0) + flat(100) + [(100, 103.5, 99.8, 103)], freq="1D")  # dřív bouře, teď klid
    assert setups.find("donchian_breakout", calm, params=p, last_only=True)


def test_scenario_note_and_weekly_outlook(tmp_path, monkeypatch):
    import scanner.scan as sc_mod
    stats = {"z": {"4 týdny": {"q10": -1.3, "q50": 0.0, "q90": 1.8}, "13 týdnů": {"q10": -1.2, "q50": 0.0, "q90": 1.9}},
             "btc_cycle_peaks": [{"peak_after_months": 17.2}, {"peak_after_months": 18.0}]}
    monkeypatch.setattr(sc_mod.scenarios, "load_stats", lambda path=None: stats)
    rng = np.random.default_rng(1)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 600)))
    d1 = pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c, "Volume": 1.0},
                      index=pd.date_range("2025-03-01", periods=600, freq="1D", tz="UTC"))
    s = setups.Setup(kind="donchian_breakout", direction="long", breakout_time=d1.index[-1], retest_time=d1.index[-1],
                     hold_time=d1.index[-1], level=c[-1], range_high=c[-1], range_low=c[-1] * 0.9, entry=c[-1],
                     stop=c[-1] * 0.95, targets=[c[-1] * 1.1, c[-1] * 5], rr=[2.0, 80.0], meta={"atr": 1.0})
    note = sc_mod.scenario_note(s, d1)
    assert note.startswith("4 týdny 80 %:") and note.endswith("(T2 mimo pásmo)")
    cfg = {"timezone": "Europe/Prague", "outlook": {"enabled": True, "weekday": 0, "hour": 8}, "notify": {"telegram": True}}
    state = State(tmp_path / "s.json")
    sent = []
    mon = datetime(2026, 10, 26, 8, 30, tzinfo=timezone.utc)           # po 9:30 Praha
    msg = sc_mod.weekly_outlook(cfg, state, {("BTC/USDT", "1d"): d1}, mon, send=sent.append)
    assert msg.startswith("📆 Týdenní výhled") and "BTC " in msg and "měsíců po halvingu" in msg and sent == [msg]
    assert sc_mod.weekly_outlook(cfg, state, {("BTC/USDT", "1d"): d1}, mon, send=sent.append) is None   # jednou týdně
    tue = datetime(2026, 10, 27, 8, 30, tzinfo=timezone.utc)
    assert sc_mod.weekly_outlook(cfg, State(tmp_path / "s2.json"), {("BTC/USDT", "1d"): d1}, tue) is None


def test_mean_reversion_signals_and_strategy_health():
    import scanner.scan as sc_mod
    rows = [(100 + i * 0.5, 101 + i * 0.5, 99.5 + i * 0.5, 100.5 + i * 0.5) for i in range(240)]   # trend nahoru
    rows += [(220, 220.5, 214, 215), (215, 215.5, 209, 210)]                                       # prudký pokles
    df = frame(rows, freq="1D")
    s = setups.find("mean_reversion", df, params={**NOFILTER, "trend_ema": 200}, last_only=True)
    assert [x.direction for x in s] == ["long"] and s[0].stop < s[0].entry
    assert setups.find("mean_reversion", mirror(df), params={**NOFILTER, "trend_ema": 200}, last_only=True)[0].direction == "short"
    cfg = cfg_multi()
    line = sc_mod.strategy_health(cfg, {("BTC/USDT", "1d"): df}, df.index[-1].to_pydatetime())
    assert line.startswith("Zdraví strategií (6 měs., na živých datech): Donchian") and "obch." in line
