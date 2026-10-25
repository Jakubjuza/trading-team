"""Demo OKX – falešná burza místo sítě; ověřuje, jaké příkazy odcházejí a že bez demo režimu se nic nepošle."""
import json

import pytest

from scanner import demo


class FakeOKX:
    def __init__(self, pos_mode="net_mode", demo_header=True):
        self.headers = {"x-simulated-trading": "1"} if demo_header else {}
        self.orders, self.cancels, self.leverage = [], [], []
        self.pos_mode = pos_mode
        self.tp_filled = 0.0

    def private_get_account_config(self):
        return {"data": [{"posMode": self.pos_mode}]}

    def load_markets(self):
        return {}

    def market(self, sym):
        return {"contractSize": 0.01, "limits": {"amount": {"min": 1}}}

    def amount_to_precision(self, sym, x):
        return str(int(x))

    def set_leverage(self, lev, sym, params):
        self.leverage.append((lev, sym, params))

    def create_order(self, sym, typ, side, amount, price, params):
        oid = f"o{len(self.orders) + 1}"
        self.orders.append({"id": oid, "symbol": sym, "type": typ, "side": side, "amount": amount, "price": price, "params": params})
        if typ == "market" and "stopLossPrice" not in params:
            px = 101.0 if not params.get("reduceOnly") else 110.0
            return {"id": oid, "average": px, "filled": amount, "fee": {"cost": 0.05}}
        return {"id": oid}

    def fetch_order(self, oid, sym):
        o = next(o for o in self.orders if o["id"] == oid)
        return {"id": oid, "status": "closed" if self.tp_filled else "open", "filled": self.tp_filled,
                "average": o["price"], "price": o["price"], "fee": {"cost": 0.02}}

    def cancel_order(self, oid, sym, params=None):
        self.cancels.append((oid, params or {}))


POS = {"id": "BTC/USDT|1d|long|x", "symbol": "BTC/USDT", "strategy": "donchian_1d",
       "setup": {"direction": "long", "entry": 100.0, "stop": 95.0, "targets": [110.0, 120.0]}}


def test_refuses_without_demo_header():
    with pytest.raises(RuntimeError):
        demo.DemoBroker({"demo": {}}, ex=FakeOKX(demo_header=False))


def test_open_sends_market_stop_and_half_t1():
    ex = FakeOKX()
    b = demo.DemoBroker({"demo": {"leverage": 2}}, ex=ex)
    rec = b.open(POS, {"qty": 0.05})                                   # 0,05 BTC / 0,01 = 5 kontraktů
    assert rec["status"] == "open" and rec["contracts"] == 5 and rec["symbol"] == "BTC/USDT:USDT"
    entry, sl, tp = ex.orders
    assert entry["type"] == "market" and entry["side"] == "buy" and entry["params"]["tdMode"] == "isolated"
    assert sl["params"]["stopLossPrice"] == 95.0 and sl["params"]["reduceOnly"] and sl["side"] == "sell" and sl["amount"] == 5
    assert tp["type"] == "limit" and tp["price"] == 110.0 and tp["amount"] == 2 and tp["params"]["reduceOnly"]
    assert rec["slippage_pct"] == pytest.approx(1.0) and ex.leverage[0][0] == 2
    assert json.loads(demo.LOG.read_text().splitlines()[-1])["event"] == "open"


def test_hedged_account_marks_orders():
    ex = FakeOKX(pos_mode="long_short_mode")
    demo.DemoBroker({"demo": {}}, ex=ex).open(POS, {"qty": 0.05})
    assert all(o["params"].get("hedged") for o in ex.orders) and ex.leverage[0][2]["posSide"] == "long"


def test_move_stop_and_close_with_partial_t1():
    ex = FakeOKX()
    b = demo.DemoBroker({"demo": {}}, ex=ex)
    rec = b.open(POS, {"qty": 0.05})
    ex.tp_filled = 2.0                                                  # T1 vybral 2 kontrakty
    rec = b.move_stop(POS, rec, 100.0)
    assert ex.cancels[-1] == ("o2", {"trigger": True})
    assert ex.orders[-1]["params"]["stopLossPrice"] == 100.0 and ex.orders[-1]["amount"] == 3
    out = b.close(POS, rec, "time", paper_r=1.2)
    last = ex.orders[-1]
    assert last["type"] == "market" and last["side"] == "sell" and last["amount"] == 3 and last["params"]["reduceOnly"]
    # PnL: 2 kontr. × (110 − 101) × 0,01 + 3 × (110 − 101) × 0,01 − poplatky
    assert out["pnl_usdt"] == pytest.approx(5 * 9 * 0.01 - (0.05 + 0.02 + 0.05), abs=0.01)


def test_scanner_mirrors_signal_to_demo(tmp_path):
    from datetime import datetime, timezone
    import scanner.scan as sc
    from tests.test_setups import Cache, cfg_multi, flat, frame
    ex = FakeOKX()
    sc._DEMO["broker"] = demo.DemoBroker({"demo": {}}, ex=ex)
    cfg = cfg_multi(demo={"enabled": True, "variant": "daily"})
    d1 = frame(flat(30) + [(100, 103.5, 99.8, 103)], freq="1D")
    state = sc.State(tmp_path / "s.json")
    sc.scan_once(cfg, Cache({"1d": d1, "1h": frame(flat(40))}), state, now=datetime(2026, 2, 6, tzinfo=timezone.utc))
    pos = state.data["open"][0]
    assert pos["demo"]["status"] == "open" and ex.orders[0]["side"] == "buy"
    stop = pos["setup"]["stop"]
    nxt = __import__("pandas").concat([d1, frame([(103, 103.2, stop - 1, stop - 0.5)], freq="1D",
                                                 start=d1.index[-1] + __import__("pandas").Timedelta(days=1))])
    sc.update_paper_positions(cfg, state, {("BTC/USDT", "1d"): nxt}, 0.15)
    assert state.data["open"] == [] and any(e["event"] == "close" for e in map(json.loads, demo.LOG.read_text().splitlines()))
