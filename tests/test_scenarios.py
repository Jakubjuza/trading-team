"""Scénáře na delších timeframech – bez sítě, syntetická data."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from research import scenarios as sc


def daily(n=900, drift=0.0, vol=0.03, seed=3, start="2022-01-01"):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(drift, vol, n)))
    o = np.r_[100, c[:-1]]
    idx = pd.date_range(start, periods=n, freq="1D", tz="UTC")
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c) * 1.01, "Low": np.minimum(o, c) * 0.99, "Close": c}, index=idx)


def test_regime_uses_only_closed_weeks_and_months():
    d = daily()
    lab = sc.regime_series(d)
    cut = d.iloc[:700]
    lab_cut = sc.regime_series(cut)
    # režim do dne 699 se nezmění, když přidáme budoucí data (žádný pohled do budoucnosti)
    assert (lab.iloc[:700].dropna() == lab_cut.dropna()).all()
    assert lab.dropna().str.match(r"týden [↑↓] · měsíc [↑↓]").all()


def test_weekly_drops_incomplete_week_and_closed_days():
    d = daily(n=100, start="2026-07-01")                         # poslední den = čt 8. 10. 2026
    assert d.index[-1].dayofweek == 3
    w = sc.weekly(d)
    assert w.index[-1] < d.index[-1]                             # rozpracovaný týden pryč
    now = d.index[-1] + pd.Timedelta(hours=12)                   # dnešní svíčka rozpracovaná
    assert sc.closed_days(d, now).index[-1] == d.index[-2]


def test_z_quantiles_center_and_scenario_math():
    frames = {"A": daily(seed=1), "B": daily(seed=2, drift=0.002)}
    zq, n = sc.z_quantiles(frames, 28, center=True)
    assert zq[0.5] == pytest.approx(0.0) and zq[0.1] < 0 < zq[0.9] and n > 1000
    rng = sc.scenario_range(frames["A"], zq, 28)
    price = frames["A"]["Close"].iloc[-1]
    assert rng["základní (medián)"] == pytest.approx(price, rel=1e-6)
    assert rng["medvědí (10 %)"] < price < rng["býčí (90 %)"]
    sig = sc.vol_series(frames["A"]).iloc[-1]
    assert rng["býčí (90 %)"] == pytest.approx(price * np.exp(zq[0.9] * sig * np.sqrt(28)), rel=1e-6)


def test_quick_range_from_stats_and_outlook_lines():
    stats = {"z": {"4 týdny": {"q10": -1.3, "q50": 0.0, "q90": 1.8}, "13 týdnů": {"q10": -1.2, "q50": 0.0, "q90": 1.9}}}
    d = daily(n=600)
    r = sc.quick_range(d, "4 týdny", stats)
    assert r and r["medvědí (10 %)"] < d["Close"].iloc[-1] < r["býčí (90 %)"]
    assert sc.quick_range(d.iloc[:10], "4 týdny", stats) is None
    lines = sc.outlook_lines({"BTC": d}, ["BTC"], "13 týdnů", stats)
    assert lines[0].startswith("BTC ") and "13 týdnů:" in lines[0] and ("týden ↑" in lines[0] or "týden ↓" in lines[0])


def test_cycle_peaks_within_24_months():
    idx = pd.date_range("2016-01-01", "2026-10-01", freq="1D", tz="UTC")
    c = pd.Series(100.0, index=idx)
    c["2017-12-16"] = 1000                                       # vrchol cyklu 2016
    c["2021-11-08"] = 2000                                       # vrchol cyklu 2020
    c["2024-03-13"] = 2500                                       # vyšší, ale až 46 měsíců po halvingu 2020
    d = pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c})
    peaks = {p["halving"]: p["peak_date"] for p in sc.cycle(d)["cycle_peaks"]}
    assert peaks["2016-07-09"] == "2017-12-16" and peaks["2020-05-11"] == "2021-11-08"
