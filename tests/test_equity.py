"""Denní snímek hodnoty účtu (scanner/equity.py)."""
import json
from datetime import datetime, timezone

from scanner import equity
from scanner.scan import State

CFG = {"account_size": 10000, "risk_pct": 0.5}


def state(tmp_path):
    st = State(tmp_path / "s.json")
    st.data["closed"] = [{"r": 2.0}, {"r": -1.0}]
    st.data["open"] = [{"symbol": "BTC/USDT", "setup": {"direction": "short", "entry": 100.0, "stop": 110.0}}]
    st.data["pyramid"] = {"closed": [{"r": 3.0}], "open": [{"r_now": 0.5}]}
    st.data["ensemble"] = {"cash": 2000.0, "start_equity": 5000.0, "qty": {"SOL": 25.0}}
    return st


PRICES = {"BTC/USDT": (95.0, ""), "SOL/USDT": (130.0, "")}


def test_paper_equity_parts(tmp_path):
    eq, parts = equity.paper_equity(CFG, state(tmp_path), PRICES)
    # jádro: (2 − 1 + 0,5) R × 50 USD; pyramida (3 + 0,5) R × 50; ensemble 2000 + 25 × 130 − 5000
    assert parts == {"core": 75.0, "pyramid": 175.0, "ensemble": 250.0}
    assert eq == 10500.0


class FakeEx:
    def fetch_balance(self):
        return {"USDC": {"total": 1000.0}, "SOL": {"total": 2.0}, "XYZ": {"total": 5.0}, "info": "x"}


class FakeDemo:
    ex, quote = FakeEx(), "USDC"


def test_snapshot_once_per_day_with_demo(tmp_path):
    st, log = state(tmp_path), tmp_path / "eq.jsonl"
    t = datetime(2026, 10, 27, 0, 5, tzinfo=timezone.utc)
    rec = equity.snapshot(CFG, st, PRICES, t, demo=FakeDemo(), log=log)
    assert rec["t"] == "2026-10-27" and rec["paper"] == 10500.0 and rec["demo"] == 1260.0 and rec["demo_ccy"] == "USDC"
    assert equity.snapshot(CFG, st, PRICES, t.replace(hour=13), log=log) is None          # stejný den
    assert equity.snapshot(CFG, st, PRICES, datetime(2026, 10, 28, 0, 1, tzinfo=timezone.utc), log=log)["t"] == "2026-10-28"
    assert [json.loads(x)["t"] for x in log.read_text().splitlines()] == ["2026-10-27", "2026-10-28"]
    assert [r["t"] for r in equity.read(log)] == ["2026-10-27", "2026-10-28"]


def test_snapshot_skips_without_prices(tmp_path):
    assert equity.snapshot(CFG, state(tmp_path), {}, datetime(2026, 10, 27, tzinfo=timezone.utc), log=tmp_path / "x") is None


def test_scanner_imports_equity():
    """Regrese: snímek účtu ve skeneru padal na NameError, když import vypadl při slučování."""
    import scanner.scan
    assert scanner.scan.equity is equity
