import numpy as np
import pandas as pd

from research import ai_lab as al
from research.experiments import strategy_atlas as atlas


def _frames():
    out = {}
    idx = pd.date_range("2022-06-01", "2026-03-01", freq="1h", tz="UTC", inclusive="left")
    rng = np.random.default_rng(3)
    btc = rng.normal(0, 0.006, len(idx))
    for k, c in enumerate(al.COINS):
        ret = 0.6 * btc + rng.normal(0, 0.006, len(idx)) if c != "BTC" else btc
        cl = 100 * np.exp(np.cumsum(ret))
        o = np.r_[cl[0], cl[:-1]]
        df = pd.DataFrame({"Open": o, "High": np.maximum(o, cl) * 1.002, "Low": np.minimum(o, cl) * 0.998, "Close": cl,
                           "Volume": rng.lognormal(10, .4, len(idx))}, index=idx)
        z = atlas.Ind(df)
        z.d200 = (np.arange(len(idx)) // 500 % 2).astype(float)
        out[c] = z
    return out


def test_strategies_and_evolution(monkeypatch):
    fr = _frames()
    F = al.features(fr)
    assert set(al.FEATS) <= set(F["ETH"].columns)
    t1 = al.a1_echo(fr, F)
    t2 = al.a2_quiet(fr, F)
    assert all(t["exit"] >= t["entry"] for t in t1 + t2)
    r3, hrs = al.a3_hours(fr, F)
    r4 = al.a4_rotation(fr, F)
    assert len(r3) > 100 and len(r4) > 100 and set(hrs) == set(al.COINS)
    monkeypatch.setattr(al, "POP", 12)
    monkeypatch.setattr(al, "GENS", 2)
    monkeypatch.setattr(al, "TOP_K", 5)
    ev = al.evolve(fr, F)
    assert ev["tested"] > 0 and len(ev["top"]) <= 5
    assert "když" in al.genome_text(ev["top"][0]["genome"])


def test_running_trade_not_counted():
    fr = _frames()
    z = fr["BTC"]
    m = np.zeros(len(z.c), bool)
    m[-3] = True
    ii, xx, rr = al.trades_from(z, m, 1, 2.0, 0.0, 32)
    assert al.to_list(z, "BTC", 1, ii, xx, rr) == []
