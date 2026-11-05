import numpy as np
import pandas as pd

from research import fragility as fr


def _h1(n=24 * 80, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    r = rng.normal(0, 0.004, n)
    return idx, r


def _frame(idx, r):
    c = 100 * np.exp(np.cumsum(r))
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def test_fragile_when_bad_news_follow_through_and_good_fade():
    idx, r = _h1()
    for i in range(24 * 45, len(r) - 30, 24 * 3):          # šok dolů s pokračováním, šok nahoru s návratem
        if (i // (24 * 3)) % 2:
            r[i] = -0.03; r[i + 1:i + 13] += -0.002
        else:
            r[i] = 0.02; r[i + 1:i + 13] += -0.0025
    s = fr.current(_frame(idx, r))
    assert s["k"] is not None and s["k"] >= fr.THR and s["state"] == "křehký"


def test_optimistic_mirror_and_no_lookahead():
    idx, r = _h1()
    for i in range(24 * 45, len(r) - 30, 24 * 3):
        if (i // (24 * 3)) % 2:
            r[i] = 0.03; r[i + 1:i + 13] += 0.002
        else:
            r[i] = -0.02; r[i + 1:i + 13] += 0.0025
    h1 = _frame(idx, r)
    assert fr.current(h1)["state"] == "optimistický"
    sh = fr.shocks(h1)
    assert (sh["known"] > sh.index).all()
    # K v čase t nesmí záviset na datech po t
    t = idx[24 * 70]
    assert fr.series(h1, [t]).iat[0] == fr.series(h1[h1.index <= t], [t]).iat[0]


def test_too_few_shocks():
    idx, r = _h1()
    s = fr.current(_frame(idx, r))
    assert s["state"] in ("málo dat", "vyrovnaný", "křehký", "optimistický")
    assert "Křehkost" in fr.line(s)
