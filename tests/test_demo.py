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

    markets = {"BTC/USDT:USDT": {"symbol": "BTC/USDT:USDT", "base": "BTC", "id": "BTC-USDT-SWAP"}}

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


class FakeOKXSpot(FakeOKX):
    """Spot: nákup market (poplatek v BTC), stopy přes algo endpoint."""

    def __init__(self, usdt=5000.0, **kw):
        super().__init__(**kw)
        self.algos, self.cancelled_algos, self.usdt = [], [], usdt
        self.algo_gone = False

    def market(self, sym):
        return {"id": sym.replace("/", "-"), "limits": {"amount": {"min": 0.00001}}}

    def amount_to_precision(self, sym, x):
        return f"{int(x * 1e5) / 1e5:.5f}"

    def price_to_precision(self, sym, x):
        return f"{x:.1f}"

    def fetch_balance(self):
        return {"USDT": {"free": self.usdt}}

    def create_order(self, sym, typ, side, amount, price, params):
        oid = f"o{len(self.orders) + 1}"
        self.orders.append({"id": oid, "symbol": sym, "type": typ, "side": side, "amount": amount, "params": params})
        if side == "buy":
            return {"id": oid, "average": 101.0, "filled": amount, "fee": {"cost": 0.0001, "currency": "BTC"}}
        return {"id": oid, "average": 110.0, "filled": amount, "fee": {"cost": 0.05, "currency": "USDT"}}

    def private_post_trade_order_algo(self, req):
        self.algos.append(req)
        return {"data": [{"algoId": f"a{len(self.algos)}", "sCode": "0"}]}

    def private_post_trade_cancel_algos(self, reqs):
        self.cancelled_algos.append(reqs[0]["algoId"])
        return {"data": [{"sCode": "51000" if self.algo_gone else "0"}]}


SPOT = {"demo": {"market": "spot"}}


def test_spot_long_buys_and_places_cash_stop():
    ex = FakeOKXSpot()
    b = demo.make_broker(SPOT, ex=ex)
    assert isinstance(b, demo.SpotDemoBroker)
    rec = b.open(POS, {"qty": 0.01})
    buy = ex.orders[0]
    assert buy["symbol"] == "BTC/USDT" and buy["side"] == "buy" and buy["params"]["tgtCcy"] == "base_ccy"
    assert len(ex.orders) == 1 and not ex.leverage                      # žádný limit T1, žádná páka
    assert rec["contracts"] == pytest.approx(0.0099)                     # poplatek stržen v BTC
    algo = ex.algos[0]
    assert algo["tdMode"] == "cash" and algo["side"] == "sell" and algo["slTriggerPx"] == "95.0" and algo["sz"] == "0.00990"
    assert rec["entry_fee"] == pytest.approx(0.0101)


def test_spot_skips_shorts_and_missing_funds():
    ex = FakeOKXSpot(usdt=50)
    b = demo.make_broker(SPOT, ex=ex)
    short = {**POS, "setup": {**POS["setup"], "direction": "short", "stop": 105.0, "targets": [90.0, 80.0]}}
    assert b.open(short, {"qty": 0.01})["status"] == "skipped_short"
    assert b.open(POS, {"qty": 1.0})["status"] == "no_funds" and not ex.orders


def test_spot_t1_sells_half_and_close_computes_pnl():
    ex = FakeOKXSpot()
    b = demo.make_broker(SPOT, ex=ex)
    rec = b.open(POS, {"qty": 0.01})
    rec = b.move_stop(POS, rec, 100.0)
    assert ex.cancelled_algos == ["a1"] and ex.orders[1]["side"] == "sell" and ex.orders[1]["amount"] == pytest.approx(0.00495)
    assert ex.algos[1]["slTriggerPx"] == "100.0" and ex.algos[1]["sz"] == "0.00495"
    out = b.close(POS, rec, "time")
    assert ex.orders[2]["amount"] == pytest.approx(0.00495) and ex.cancelled_algos[-1] == "a2"
    assert out["pnl_usdt"] == pytest.approx(0.0099 * 9 - 0.0101 - 0.05 - 0.05, abs=0.01)


def test_spot_stop_already_executed_on_exchange():
    ex = FakeOKXSpot()
    b = demo.make_broker(SPOT, ex=ex)
    rec = b.open(POS, {"qty": 0.01})
    ex.algo_gone = True
    out = b.close(POS, rec, "stop")
    assert out["stopped_on_exchange"] and len(ex.orders) == 1 and out["pnl_usdt"] is None


def test_quote_override_maps_to_usdc_swap():
    ex = FakeOKX()
    ex.markets = {"BTC/USDC:USDC": {"symbol": "BTC/USDC:USDC", "base": "BTC", "id": "BTC-USDC-SWAP"}}
    rec = demo.DemoBroker({"demo": {"quote": "USDC"}}, ex=ex).open(POS, {"qty": 0.05})
    assert rec["symbol"] == "BTC/USDC:USDC" and ex.orders[0]["symbol"] == "BTC/USDC:USDC"
    assert demo.spot_symbol("ETH/USDT", "USDC") == "ETH/USDC" and demo.swap_symbol("ETH/USDT") == "ETH/USDT:USDT"


def test_resolve_prefers_eea_xperp_then_quote_swap():
    ex = FakeOKX()
    ex.markets = {"BTC/USD:USD-310328": {"symbol": "BTC/USD:USD-310328", "base": "BTC", "id": "BTC-USD_UM_XPERP-310328", "linear": True},
                  "BTC/USDT:USDT": {"symbol": "BTC/USDT:USDT", "base": "BTC", "id": "BTC-USDT-SWAP"},
                  "ADA/USDC:USDC": {"symbol": "ADA/USDC:USDC", "base": "ADA", "id": "ADA-USDC-SWAP"},
                  "SOL/USDT:USDT": {"symbol": "SOL/USDT:USDT", "base": "SOL", "id": "SOL-USDT-SWAP"}}
    b = demo.DemoBroker({"demo": {"quote": "USDC"}}, ex=ex)
    assert b.resolve("BTC/USDT") == "BTC/USD:USD-310328"
    assert b.resolve("ADA/USDT") == "ADA/USDC:USDC"
    assert b.resolve("SOL/USDT") is None and b.open({**POS, "symbol": "SOL/USDT"}, {"qty": 1})["status"] == "no_market"
