import numpy as np
import pandas as pd

from research.experiments import brain_study as bs


def _data():
    idx = pd.date_range("2019-01-01", "2026-06-30", freq="D", tz="UTC")
    ph = pd.Series(np.where(np.arange(len(idx)) // 90 % 2 == 0, "A", "B"), index=idx)
    rng = np.random.default_rng(1)
    a = np.where(ph == "A", 0.004, -0.004) + rng.normal(0, 0.01, len(idx))
    b = rng.normal(0.0005, 0.01, len(idx))
    return pd.DataFrame({"x": a, "y": b}, index=idx), ph


def test_weights_never_zero_and_favour_phase():
    df, ph = _data()
    months = bs.months_of(df.index)
    plan = bs.gates(df, ph, months)
    m = months[-1]
    assert plan[m]["A"]["x"] == bs.UP and plan[m]["B"]["x"] == bs.DOWN
    assert all(v > 0 for p in plan[m].values() for v in p.values())
    r, tilt = bs.run_plan(df, ph, plan)
    base = df.mean(axis=1)[r.index]
    assert r.sum() > base.sum() and tilt.any()


def test_no_lookahead():
    df, ph = _data()
    m = pd.Timestamp("2022-01-01", tz="UTC")
    p1 = bs.gates(df, ph, [m])
    df2 = df.copy()
    df2.loc[df2.index >= m, "x"] = -0.05
    assert bs.gates(df2, ph, [m]) == p1


def test_domes_quadrants():
    df, ph = _data()
    df["z"] = df["x"] * 3
    dome, st, _, _ = bs.assign_domes(df, {})
    assert set(dome.values()) <= set(bs.DOMES)


def test_shuffle_keeps_length():
    _, ph = _data()
    sp = bs.shuffled_phase(ph, np.random.default_rng(0))
    assert len(sp) == len(ph) and set(sp.unique()) == set(ph.unique())
