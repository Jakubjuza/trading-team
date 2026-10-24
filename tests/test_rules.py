"""Testy pravidel setupu na reálných historických datech (fixtury z yfinance) + logika skeneru.

Pozitivní fixtury končí hold svíčkou, negativní pokrývají breakout + retest_window + 2 svíčky.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scanner import broker, rules  # noqa: E402
from scanner.data import CandleCache, closed_only  # noqa: E402
from scanner.scan import State, scan_once  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
P = rules.DEFAULTS
TOL = P["tolerance_pct"] / 100


def load(name):
    df = pd.read_csv(FIX / name, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


# --- pozitivní historické případy -------------------------------------------
POSITIVE = [
    ("pos_AAPL_1d_long_20241126.csv", "long", "2024-11-26"),
    ("pos_MSFT_1d_long_20241202.csv", "long", "2024-12-02"),
    ("pos_SPY_1d_short_20250310.csv", "short", "2025-03-10"),
    ("pos_BTC_1h_long_20260827.csv", "long", "2026-08-27 08:00"),
]


@pytest.mark.parametrize("fname,direction,breakout", POSITIVE)
def test_positive_historical_setup(fname, direction, breakout):
    df = load(fname)
    found = rules.latest_setup(df, "both")
    assert len(found) == 1, f"čekán právě 1 čerstvý setup, nalezeno {len(found)}"
    s = found[0]
    assert s.direction == direction
    assert s.breakout_time == pd.Timestamp(breakout, tz="UTC")

    # nezávislé ověření pravidel přímo z dat
    b = df.index.get_loc(s.breakout_time)
    r = df.index.get_loc(s.retest_time)
    h = len(df) - 1
    win = df.iloc[b - P["range_lookback"]:b]
    c, hi, lo = df["Close"], df["High"], df["Low"]
    if direction == "long":
        lvl = win["High"].max()
        assert c.iloc[b] > lvl >= c.iloc[b - 1]                    # první close nad range high
        assert lo.iloc[r] <= lvl * (1 + TOL)                         # návrat do 0,3 %
        assert c.iloc[r] >= lvl * (1 - TOL)                          # retest nezavřel pod
        assert c.iloc[h] > lvl and lo.iloc[h] >= lvl * (1 - TOL)     # hold
        assert s.stop < s.entry < s.targets[0] < s.targets[1]
    else:
        lvl = win["Low"].min()
        assert c.iloc[b] < lvl <= c.iloc[b - 1]
        assert hi.iloc[r] >= lvl * (1 - TOL)
        assert c.iloc[r] <= lvl * (1 + TOL)
        assert c.iloc[h] < lvl and hi.iloc[h] <= lvl * (1 + TOL)
        assert s.stop > s.entry > s.targets[0] > s.targets[1]
    assert s.level == pytest.approx(lvl)
    assert s.entry == pytest.approx(c.iloc[h])
    for t, rr in zip(s.targets, s.rr):
        assert rr == pytest.approx(abs(t - s.entry) / abs(s.entry - s.stop), abs=0.01)
    # stop aspoň min_stop_atr*ATR od vstupu
    assert abs(s.entry - s.stop) >= P["min_stop_atr"] * s.meta["atr"] - 1e-9


# --- negativní historické případy -------------------------------------------
NEGATIVE = [
    ("neg_AAPL_1d_retest_closed_below_20251020.csv", "2025-10-20"),  # retest zavřel pod hladinou
    ("neg_MSFT_1d_hold_failed_20250122.csv", "2025-01-22"),          # svíčka po retestu hladinu neudržela
    ("neg_AAPL_1d_no_retest_20250919.csv", "2025-09-19"),            # cena se do 0,3 % nevrátila
]


@pytest.mark.parametrize("fname,breakout", NEGATIVE)
def test_negative_historical_no_setup(fname, breakout):
    df = load(fname)
    bts = pd.Timestamp(breakout, tz="UTC")
    b = df.index.get_loc(bts)
    lvl = df.iloc[b - P["range_lookback"]:b]["High"].max()
    assert df["Close"].iloc[b] > lvl >= df["Close"].iloc[b - 1], "fixtura musí obsahovat skutečný breakout"
    assert not [s for s in rules.find_setups(df, "both") if s.breakout_time == bts]
    # ani průběžně (skener volá latest_setup po každé svíčce)
    for end in range(b + 1, len(df) + 1):
        assert not [s for s in rules.latest_setup(df.iloc[:end], "both") if s.breakout_time == bts]


# --- syntetické hraniční případy --------------------------------------------
def _synthetic(direction="long", retest_low=100.2, hold_close=101.0, width=2.0):
    """20 svíček range 100-width .. 100, breakout, retest, hold."""
    rows = [(99.5, 100.0, 100 - width, 99.5)] * 20
    rows += [(99.6, 99.9, 99.4, 99.8)]                 # close <= RH
    rows += [(99.8, 101.5, 99.7, 101.2)]               # breakout
    rows += [(101.2, 101.3, retest_low, 100.6)]        # retest
    rows += [(100.6, hold_close + 0.2, 100.1, hold_close)]  # hold
    df = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"])
    df["Volume"] = 1000.0
    df.index = pd.date_range("2026-01-01", periods=len(df), freq="1h", tz="UTC")
    if direction == "short":
        df = df.copy()
        o, h, l, c = (200 - df[k] for k in ("Open", "High", "Low", "Close"))
        df["Open"], df["High"], df["Low"], df["Close"] = o, l, h, c
    return df


def test_synthetic_long_and_short_mirror():
    assert [s.direction for s in rules.latest_setup(_synthetic("long"))] == ["long"]
    assert [s.direction for s in rules.latest_setup(_synthetic("short"))] == ["short"]


def test_synthetic_retest_not_close_enough():
    assert rules.latest_setup(_synthetic(retest_low=100.5)) == []      # 0,5 % nad hladinou > 0,3 %


def test_synthetic_range_too_wide():
    assert rules.latest_setup(_synthetic(width=12.0)) == []           # range 12 % > max_range_pct 8 %


def test_direction_filter():
    assert rules.latest_setup(_synthetic("long"), "short") == []


# --- velikost pozice, cache, deduplikace, broker ----------------------------
def test_position_size_risk_and_cash_cap():
    s = rules.latest_setup(load(POSITIVE[0][0]))[0]
    size = rules.position_size(s, 10000, 1.0, fractional=False)
    assert size["risk_usd"] <= 100
    assert size["notional"] <= 10000
    btc = rules.latest_setup(load(POSITIVE[3][0]))[0]
    size = rules.position_size(btc, 10000, 1.0, fractional=True)
    assert size["notional"] <= 10000                                   # u těsného stopu omezí hotovost


def test_cache_fetches_only_new_candles(tmp_path):
    full = load(POSITIVE[3][0])
    calls = []

    def fake(symbol, tf, since):
        calls.append(since)
        return full[full.index >= pd.Timestamp(since)].iloc[:40] if len(calls) == 1 else full[full.index >= pd.Timestamp(since)]

    cache = CandleCache(tmp_path, history_bars=40, fetchers={"crypto": fake})
    now = full.index[-1].to_pydatetime() + pd.Timedelta(hours=1)
    first = cache.update("crypto", "BTC/USDT", "1h", now=now)
    second = cache.update("crypto", "BTC/USDT", "1h", now=now)
    assert len(calls) == 2
    assert pd.Timestamp(calls[1]) == full.index[-1]                   # druhé volání stahuje až od poslední svíčky
    assert second.index[-1] == full.index[-1]
    assert not second.index.duplicated().any()


def test_closed_only_drops_running_candle():
    df = load(POSITIVE[3][0])
    now = df.index[-1].to_pydatetime() + pd.Timedelta(minutes=30)     # poslední svíčka běží
    assert closed_only(df, "1h", now).index[-1] == df.index[-2]


class _FakeCache:
    def __init__(self, df):
        self.df = df

    def update(self, source, symbol, tf, now=None):
        return self.df


def _cfg(**kw):
    cfg = {"tickers": [{"symbol": "BTC/USDT", "source": "crypto"}], "timeframe": "1h", "direction": "both",
           "account_size": 10000, "risk_pct": 1.0, "min_rr": 2.0, "max_setups_per_day": 3, "timezone": "Europe/Prague",
           "rules": dict(P), "notify": {"telegram": False, "chart": False}, "paper_trading": False, "live_trading": False}
    cfg.update(kw)
    return cfg


def test_dedupe_same_setup_not_sent_twice(tmp_path):
    state = State(tmp_path / "state.json")
    cache = _FakeCache(load(POSITIVE[3][0]))
    now = datetime(2026, 8, 27, 12, 5, tzinfo=timezone.utc)
    assert len(scan_once(_cfg(), cache, state, now=now)) == 1
    assert len(scan_once(_cfg(), cache, state, now=now)) == 0         # podruhé se nepošle
    assert len(json.loads((tmp_path / "state.json").read_text())["sent"]) == 1


def test_min_rr_and_daily_limit(tmp_path):
    cache = _FakeCache(load(POSITIVE[1][0]))                           # MSFT, R:R T1 = 1,5
    now = datetime(2024, 12, 5, tzinfo=timezone.utc)
    assert scan_once(_cfg(), cache, State(tmp_path / "a.json"), now=now) == []
    assert len(scan_once(_cfg(min_rr=1.0), cache, State(tmp_path / "b.json"), now=now)) == 1
    assert scan_once(_cfg(min_rr=1.0, max_setups_per_day=0), cache, State(tmp_path / "c.json"), now=now) == []


def test_broker_paper_by_default_and_live_blocked(tmp_path):
    order = {"symbol": "BTC/USDT", "side": "buy", "qty": 0.01, "entry": 1, "stop": 0.9, "targets": [1.2]}
    rec = broker.place_order(order, {"live_trading": False}, paper_log=tmp_path / "p.json")
    assert rec["mode"] == "paper"
    with pytest.raises(broker.LiveTradingDisabled):
        broker.place_order(order, {"live_trading": True}, paper_log=tmp_path / "p.json")
    with pytest.raises(NotImplementedError):
        broker.place_order(order, {"live_trading": True}, confirm=True, paper_log=tmp_path / "p.json")
