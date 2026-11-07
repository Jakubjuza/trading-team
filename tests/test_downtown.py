import numpy as np
import pandas as pd

from research import downtown as D


def frame(closes, freq="4h", start="2023-01-01"):
    idx = pd.date_range(start, periods=len(closes), freq=freq, tz="UTC")
    c = np.asarray(closes, float)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c) * 1.001, "Low": np.minimum(o, c) * 0.999,
                         "Close": c, "Volume": 1.0}, index=idx)


def test_hodl3_liquidates_and_refills():
    # cena 100 → po 10 svíčkách pád o 40 % → páka 3× = likvidace, nový vklad
    closes = [100] * 10 + list(np.linspace(100, 60, 10)) + [60] * 10
    acc, curve, pos, idx = D.run("hodl3", {"BTC": frame(closes)}, "2023-01-01")
    assert acc.liqs == 1 and acc.wipes == 1
    assert acc.dep == 2 * D.START_CASH
    assert pos is not None            # po vkladu znovu long
    s = D.summarize(acc, curve, pos, idx)
    assert s["liquidations"] == 1 and s["net"] < -900


def test_hodl3_gain_matches_leverage():
    closes = [100] * 5 + list(np.linspace(100, 110, 20))
    acc, curve, pos, idx = D.run("hodl3", {"BTC": frame(closes)}, "2023-01-01")
    val = curve[-1][1]
    # +~10 % ceny × 3 = ~+30 % minus náklady a funding
    assert 1250 < val < 1310
    assert acc.liqs == 0


def test_stop_before_liquidation_ko50():
    # long po průrazu; stop 0,8 % je blíž než likvidace (~1,5 %) → stop, ne likvidace
    base = [100.0] * 230
    closes = base + [101.0, 101.5, 99.0, 99.0, 99.0]
    acc, curve, pos, idx = D.run("ko50", {"BTC": frame(closes, freq="1h")}, "2023-01-01")
    kinds = [t["kind"] for t in acc.trades]
    assert "stop" in kinds and "likvidace" not in kinds
    loss = [t for t in acc.trades if t["kind"] == "stop"][0]["pnl"]
    assert -600 < loss < -400          # ~0,8 % × 50 = −40 % marže + náklady


def test_gap_through_liquidation():
    base = [100.0] * 230
    closes = base + [101.0, 101.5, 95.0, 95.0]
    f = frame(closes, freq="1h")
    f.loc[f.index[-2], "Open"] = 95.0          # gap přes likvidační cenu
    acc, *_ = D.run("ko50", {"BTC": f}, "2023-01-01")
    assert acc.liqs == 1


def test_kronos_signal_threshold_and_one_bar_exit():
    closes = [100.0] * 20 + [100.0, 101.0, 101.0, 101.0]
    f = frame(closes, freq="2h")
    pred = pd.Series(0.0, index=f.index)
    pred.iloc[20] = 0.01            # čeká +1 % → long na open svíčky 21, zavřít na jejím close
    pred.iloc[22] = 0.002           # pod prahem 0,3 % → nic
    D.KRONOS.clear(); D.KRONOS["BTC"] = pred
    acc, curve, pos, idx = D.run("kronos10", {"BTC": f}, "2023-01-01")
    D.KRONOS.clear()
    tr = [t for t in acc.trades if t["kind"] != "vklad"]
    assert len(tr) == 1 and tr[0]["dir"] == 1 and tr[0]["kind"] == "čas"
    assert tr[0]["pnl"] > 0


def test_gate_blocks_entries_and_rotation_goes_to_cash():
    closes = [100] * 5 + list(np.linspace(100, 130, 30))
    acc, curve, pos, idx = D.run("hodl3", {"BTC": frame(closes)}, "2023-01-01", gate=lambda ix: np.zeros(len(ix), bool))
    assert pos is None and all(abs(v - D.START_CASH) < 1e-9 for _, v, _ in curve)


def test_sweep_moves_half_of_gain_to_vault():
    # hodl3 ×3 na trhu +60 %: účet se zdvojnásobí → při vypnutí brány (hotovost) se půlka zisku odloží
    closes = [100] * 5 + list(np.linspace(100, 160, 40)) + [160] * 10
    n = len(closes)
    gate = lambda ix: np.arange(len(ix)) < n - 8  # noqa: E731
    acc, curve, pos, idx = D.run("hodl3", {"BTC": frame(closes)}, "2023-01-01", gate=gate, sweep=0.5)
    assert acc.vault > 0
    assert abs(curve[-1][1] - (acc.eq + acc.vault)) < 1e-6


def test_dispatch_phase_uses_previous_day_only():
    from research import downtown_dispatch as X
    idx = pd.date_range("2022-01-01", periods=24 * 700, freq="1h", tz="UTC")
    c = np.r_[np.linspace(100, 200, 24 * 400), np.linspace(200, 120, 24 * 300)]
    btc = pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": 1.0}, index=idx)
    ph, feat = X.phases(btc)
    day = ph.index[50]
    # fáze dne D = výpočet z close dne D−1 (žádný pohled do budoucna)
    assert ph.loc[day, "trend"] == ("býk" if feat.loc[day - pd.Timedelta("1D"), "btc"] > feat.loc[day - pd.Timedelta("1D"), "sma200"] else "medvěd")


def test_dispatch_plan_learns_only_from_closed_trades():
    from research import downtown_dispatch as X
    t0 = pd.Timestamp("2024-01-01", tz="UTC")
    tr = pd.DataFrame({"opened": [t0 + pd.Timedelta(days=i) for i in range(20)],
                       "t": [t0 + pd.Timedelta(days=i + 1) for i in range(20)],
                       "r": [0.02, 0.01] * 10, "faze": "býk · trend · klid"})
    plan = X.make_plan({"rot5": tr}, pd.DatetimeIndex([t0 + pd.Timedelta(days=10), t0 + pd.Timedelta(days=40)]))
    assert plan[t0 + pd.Timedelta(days=10)] == {}                       # zatím jen 9 ukončených obchodů
    assert plan[t0 + pd.Timedelta(days=40)] == {"býk · trend · klid": ["rot5"]}
