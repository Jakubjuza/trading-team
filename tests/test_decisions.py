import json
from datetime import datetime, timezone
from types import SimpleNamespace

from scanner import scan


def test_log_decision_writes_reason(tmp_path):
    p = tmp_path / "d.jsonl"
    s = SimpleNamespace(direction="long", entry=100.5, stop=95.0, rr=[1.8, 3.0])
    now = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
    scan.log_decision(now, "BTC/USDT", "1d", "donchian_1d", s, "vyřazen", "R:R 0.8 < 1.0", path=p)
    rec = json.loads(p.read_text().strip())
    assert rec["decision"] == "vyřazen" and rec["reason"].startswith("R:R") and rec["symbol"] == "BTC/USDT"


def test_log_decision_dry_run_writes_nothing(tmp_path):
    p = tmp_path / "d.jsonl"
    s = SimpleNamespace(direction="short", entry=1.0, stop=1.1, rr=[1.2])
    scan.log_decision(datetime.now(timezone.utc), "ETH/USDT", "1d", "x", s, "signál", "ok", dry_run=True, path=p)
    assert not p.exists()
