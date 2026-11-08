import pandas as pd

from research import city_accounts as ca


def T(e, x, r, coin="BTC"):
    return {"entry": e, "exit": x, "coin": coin, "dir": 1, "r": r}


def test_compounding_and_stats():
    tr = [T("2024-01-01", "2024-01-05", 2.0), T("2024-02-01", "2024-02-03", -1.0), T("2024-03-01", "2024-03-02", -1.0)]
    a = ca.account(tr, end="2024-03-10")
    eq = 1000 * 1.02 * 0.99 * 0.99
    assert abs(a["equity"] - round(eq, 2)) < 0.02
    assert a["n_trades"] == 3 and a["win_pct"] == 33.3 and a["lose_streak"] == 2
    assert a["deposited"] == 1000 and a["wipes"] == 0 and a["liquidations"] == 0
    assert abs(a["best_trade"] - 20.0) < 1e-6
    assert a["max_dd_pct"] < 0 and a["peak_equity"] >= 1020
    assert a["years"] == {"2024": round((eq / 1000 - 1) * 100, 1)}
    assert a["curve"][-1][1] == a["equity"]


def test_concurrent_sizes_use_equity_at_entry():
    tr = [T("2024-01-01", "2024-01-10", 1.0), T("2024-01-02", "2024-01-03", 1.0, "ETH")]
    a = ca.account(tr)
    # obě vstupují při účtu 1000 → každý +10
    assert abs(a["equity"] - 1020.0) < 1e-6


def test_empty_account():
    a = ca.account([], start="2026-11-01")
    assert a["n_trades"] == 0 and a["equity"] == 1000 and a["curve"] == []


def test_returns_account():
    idx = pd.date_range("2024-01-01", periods=4, freq="D", tz="UTC")
    a = ca.returns_account(pd.Series([0.01, -0.02, 0.01, 0.0], index=idx))
    assert abs(a["equity"] - round(1000 * 1.01 * 0.98 * 1.01, 2)) < 0.02
    assert a["n_trades"] is None and a["win_pct"] == 50.0


def test_id_time():
    assert ca._id_time({"id": "ETH/USDT|1d|short|donchian_breakout|2026-10-29T00:00:00+00:00", "closed_at": "x"}).startswith("2026-10-29")


def test_lab_backtest_trades_smoke():
    from tests.test_combo_study import _frame
    z = _frame()
    s = {"id": "x", "family": "donchian", "params": "20", "tf": "4h", "filter": "none", "exit": "trail", "dir": "long"}
    tr = ca.lab_backtest_trades(s, {"BTC": z})
    assert tr and all(t["exit"] >= t["entry"] for t in tr)
    a = ca.account(tr)
    assert a["n_trades"] == len(tr) and len(a["curve"]) > 2
