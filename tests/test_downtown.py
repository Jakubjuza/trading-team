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
