"""🧭 Ensemble a 📊 týdenní přehled."""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from scanner import ensemble, weekly
from scanner.scan import State

CFG = {"account_size": 10000, "risk_pct": 0.5, "timezone": "Europe/Prague", "notify": {"telegram": False},
       "ensemble": {"enabled": True}, "weekly_report": {"enabled": True, "weekday": 0, "hour": 8}}


def trend(n=400, slope=0.004, start=100.0, seed=1):
    rng = np.random.default_rng(seed)
    c = start * np.exp(np.cumsum(slope + rng.normal(0, 0.02, n)))
    idx = pd.date_range("2025-01-01", periods=n, freq="1D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c}, index=idx)


def test_signal_full_in_uptrend_zero_in_downtrend():
    assert ensemble.signal(trend(slope=0.01), [10, 20, 40, 80, 160]) == 1.0
    assert ensemble.signal(trend(slope=-0.01), [10, 20, 40, 80, 160]) == 0.0


def test_update_rebalances_once_per_day_and_reports_entries(tmp_path):
    state = State(tmp_path / "s.json")
    frames = {("BTC/USDT", "1d"): trend(slope=0.01), ("ETH/USDT", "1d"): trend(slope=-0.01, seed=2)}
    sent = []
    msg = ensemble.update(CFG, state, frames, 0.15, send=sent.append)
    st = state.data["ensemble"]
    assert "BTC 0 →" in msg and "ETH" not in msg and st["qty"].get("BTC", 0) > 0 and "ETH" not in st["qty"]
    w = st["weights"]["BTC"]
    assert 0 < w <= 0.5 and st["cash"] < 5000
    assert ensemble.update(CFG, state, frames, 0.15, send=sent.append) is None      # stejný den – nic
    assert len(st["equity"]) == 1 and len(sent) == 1


def test_weekly_report_lists_all_parts(tmp_path):
    state = State(tmp_path / "s.json")
    now = datetime(2026, 11, 2, 8, 30, tzinfo=timezone.utc)                          # pondělí
    state.data["closed"] = [{"strategy": "donchian_1d", "r": 1.5, "closed_at": "2026-10-30T00:00:00+00:00"},
                            {"strategy": "pullback_1d+mtf", "r": -1.0, "closed_at": "2026-10-29T00:00:00+00:00"},
                            {"strategy": "pullback_1d", "r": -1.0, "closed_at": "2026-10-01T00:00:00+00:00"}]
    state.data["pyramid"] = {"open": [], "closed": [{"r": 3.2, "closed_at": "2026-10-31T00:00:00+00:00"}]}
    state.data["ensemble"] = {"start_equity": 5000, "weights": {"BTC": 0.1},
                              "equity": [["2026-10-20", 5000], ["2026-10-27", 5100], ["2026-11-01", 5202]]}
    log = tmp_path / "demo.jsonl"
    log.write_text(json.dumps({"event": "close", "id": "x", "pnl_usdt": 12.5, "closed": "2026-10-30T00:00:00+00:00"}) + "\n")
    sent = []
    msg = weekly.maybe_send(CFG, state, now, health_fn=lambda: "Zdraví strategií: OK", demo_log=log, send=sent.append)
    assert msg.startswith("📊 Týdenní přehled") and "Jádro (denní signály): týden 1 obch. +1,50 R · celkem 2 obch. +0,50 R" in msg
    assert "Vstup z 1H (papír): týden 1 obch. -1,00 R" in msg and "Pyramida" in msg and "+3,20 R" in msg
    assert "Ensemble (papír): týden +4,0 % · celkem +4,0 %" in msg and "Demo OKX: týden 1 obch. +12,50 USDC" in msg
    assert "Zdraví strategií: OK" in msg and "týden +277 USD" in msg
    assert weekly.maybe_send(CFG, state, now, send=sent.append) is None              # jednou za týden
