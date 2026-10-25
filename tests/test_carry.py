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
