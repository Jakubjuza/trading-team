"""Příkazy z Telegramu (/pozice)."""
import time

from scanner import commands
from scanner.scan import State

CFG = {"account_size": 10000, "risk_pct": 0.5, "pyramid": {"unit_r": 0.5, "add_atr": 1.0}}


def state_with_positions(tmp_path):
    st = State(tmp_path / "s.json")
    st.data["open"] = [{"symbol": "BTC/USDT", "setup": {"direction": "long", "entry": 100.0, "stop": 95.0}, "demo": {"status": "open"}}]
    st.data["pyramid"] = {"open": [{"symbol": "ETH/USDT", "direction": "short", "entry": 50.0, "stop": 52.0, "atr": 1.0,
                                    "notified_units": 2, "stop_now": 51.0}]}
    st.data["ensemble"] = {"cash": 4000.0, "start_equity": 5000.0, "qty": {"SOL": 10.0}, "avg": {"SOL": 100.0},
                           "equity": [["2026-10-26", 5000.0]], "demo_qty": {}}
    return st


def test_report_shows_all_parts(tmp_path):
    st = state_with_positions(tmp_path)
    prices = {"BTC/USDT": (105.0, ""), "ETH/USDT": (48.0, ""), "SOL/USDT": (110.0, "")}
    txt = commands.positions_report(CFG, st, prices)
    assert "BTC/USDT LONG: vstup 100,00, teď 105,00 (+1,00 R ≈ +50 USD), stop 95,00 · 🧪 demo" in txt
    # pyramida short: kusy 50 a 49, cena 48 → 0,25 × (2 + 1) = +0,75 R
    assert "ETH/USDT SHORT: 2 kus(y)" in txt and "(+0,75 R)" in txt
    assert "Ensemble: hodnota 5 100 USD (+2,0 %)" in txt and "SOL: 1 100 USD, +10,0 % od nákupu" in txt


def test_poll_answers_only_own_chat_and_fresh_messages(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    st = state_with_positions(tmp_path)
    now = int(time.time())
    updates = {"result": [
        {"update_id": 1, "message": {"chat": {"id": 7}, "date": now, "text": "/pozice"}},          # cizí chat
        {"update_id": 2, "message": {"chat": {"id": 42}, "date": now - 3600, "text": "/pozice"}},  # stará zpráva
        {"update_id": 3, "message": {"chat": {"id": 42}, "date": now, "text": "/pozice@MujBot"}},
        {"update_id": 4, "message": {"chat": {"id": 42}, "date": now, "text": "/pomoc"}}]}
    sent = []
    out = commands.poll(CFG, st, {"BTC/USDT": (100.0, "")}, get=lambda p: updates, send=sent.append)
    assert len(out) == 2 and out[0].startswith("📋 Pozice teď") and out[1].startswith("Příkazy:")
    assert st.data["telegram"]["offset"] == 5 and sent == out
