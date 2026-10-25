"""Carry z fundingu – syntetický funding (Hyperliquid je ze sandboxu blokovaný)."""
import pandas as pd
import pytest

from research import carry


def hours(rate, days=60):
    idx = pd.date_range("2026-01-01", periods=days * 24, freq="1h", tz="UTC")
    return pd.Series(rate, index=idx)


def test_constant_positive_funding_earns_after_costs():
    f = hours(0.0000125)                                      # ≈ 10,95 % p.a. > práh 10 %
    r = carry.backtest(f)
    gross = 0.0000125 * 24 * 365 / carry.CAPITAL_PER_NOTIONAL * 100
    assert r["round_trips"] == 1 and r["time_in_pct"] > 80
    assert 0 < r["apr_on_capital_pct"] < gross


def test_negative_funding_never_enters():
    r = carry.backtest(hours(-0.00001))
    assert r["round_trips"] == 0 and r["apr_on_capital_pct"] == 0


def test_hysteresis_exit_when_funding_turns_negative():
    f = pd.concat([hours(0.00002, 30), hours(-0.00002, 30).set_axis(
        pd.date_range("2026-01-31", periods=30 * 24, freq="1h", tz="UTC"))])
    r = carry.backtest(f)
    assert r["round_trips"] == 1 and r["time_in_pct"] < 70


def test_funding_history_pagination():
    calls = []
    def post(p):
        calls.append(p["startTime"])
        t0 = p["startTime"]
        n = 500 if len(calls) == 1 else 3
        return [{"time": t0 + i * 3_600_000, "fundingRate": "0.00001"} for i in range(n)]
    s = carry.funding_history("BTC", pd.Timestamp("2026-01-01", tz="UTC").to_pydatetime(), post=post, pause=0)
    assert len(calls) == 2 and len(s) == 503 and s.iloc[0] == pytest.approx(0.00001)


def test_carry_update_paper_cycle(tmp_path):
    from datetime import datetime, timedelta, timezone
    from scanner.scan import State, carry_line, carry_update
    cfg = {"carry": {"enabled": True, "coins": ["BTC"], "enter_apr": 10, "exit_apr": 0}, "notify": {"telegram": True}}
    state = State(tmp_path / "s.json")
    sent = []
    d0 = datetime(2026, 10, 1, 0, 10, tzinfo=timezone.utc)
    m = carry_update(cfg, state, d0, current={"BTC": {"apr_7d_pct": 12.0}}, history=lambda c, s: pd.Series(dtype=float), send=sent.append)
    assert len(m) == 1 and "vstup BTC" in m[0] and "BTC" in state.data["carry"]["positions"]
    assert carry_update(cfg, state, d0 + timedelta(hours=3), current={"BTC": {"apr_7d_pct": 12.0}}) == []   # jednou denně
    def hist(c, since):                                                  # 24 h po 0,00002 → 0,048 % pozice
        idx = pd.date_range(pd.Timestamp(since) + pd.Timedelta(hours=1), periods=24, freq="1h")
        return pd.Series(0.00002, index=idx)
    d1 = d0 + timedelta(days=1)
    carry_update(cfg, state, d1, current={"BTC": {"apr_7d_pct": 8.0}}, history=hist, send=sent.append)
    acc = state.data["carry"]["positions"]["BTC"]["accrued_pct"]
    assert acc == pytest.approx(0.00002 * 24 / 1.5 * 100 - carry.COST_ROUND_TRIP / 2 / 1.5 * 100)
    assert "otevřeno BTC" in carry_line(state)
    d2 = d1 + timedelta(days=1)
    m = carry_update(cfg, state, d2, current={"BTC": {"apr_7d_pct": -2.0}}, history=hist, send=sent.append)
    assert "výstup BTC" in m[0] and state.data["carry"]["positions"] == {} and len(state.data["carry"]["closed"]) == 1
    assert len(sent) == 2
