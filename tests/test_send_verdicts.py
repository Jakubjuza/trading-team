import json

from research import send_verdicts as sv


def test_verdict_gets_usd_orders_from_signal(tmp_path, monkeypatch):
    sid = "ETH/USDT|1d|short|donchian_breakout|2026-10-29T00:00:00+00:00"
    sig = {"id": sid, "setup": {"direction": "short", "entry": 2254.22, "stop": 2435.25, "targets": [1892.16, 1530.10]},
           "size": {"qty": 0.5}, "exit": {"split": 0.5}}
    path = tmp_path / "signals.jsonl"
    path.write_text("not json\n" + json.dumps(sig) + "\n")
    real = sv.find_signal
    monkeypatch.setattr(sv, "find_signal", lambda s: real(s, path))
    txt = sv.format_verdict({"signal_id": sid, "symbol": "ETH/USDT", "direction": "short", "grade": "C", "summary": ["1. x"]})
    assert "📋 Příkazy (USD):" in txt
    assert "limit SELL $2 251,97" in txt                       # max. 0,10 % pod plánovaným vstupem
    assert "stop-limit BUY – spouštěcí $2 435,25, limit $2 442,56" in txt
    assert "limit BUY T1 $1 892,16 (50 %) · T2 $1 530,10 (zbytek)" in txt
    assert txt.endswith("Nejde o finanční poradenství.")


def test_verdict_without_signal_has_no_orders(monkeypatch):
    monkeypatch.setattr(sv, "find_signal", lambda s: None)
    assert "Příkazy" not in sv.format_verdict({"signal_id": "manual:BTC:1", "symbol": "BTC/USDT", "grade": "B"})
