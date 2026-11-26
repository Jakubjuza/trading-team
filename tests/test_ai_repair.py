import json

import numpy as np
import pandas as pd

from research import ai_lab as al
from research import ai_repair as rp
from research.experiments import strategy_atlas as atlas
from tests.test_ai_lab import _frames


def _extra():
    idx = pd.date_range("2022-06-01", "2026-03-01", freq="1h", tz="UTC", inclusive="left")
    rng = np.random.default_rng(7)
    out = {}
    for c in ["LTC", "DOT", "ATOM"]:
        cl = 50 * np.exp(np.cumsum(rng.normal(0, 0.007, len(idx))))
        o = np.r_[cl[0], cl[:-1]]
        df = pd.DataFrame({"Open": o, "High": np.maximum(o, cl) * 1.002, "Low": np.minimum(o, cl) * 0.998, "Close": cl,
                           "Volume": rng.lognormal(10, .4, len(idx))}, index=idx)
        z = atlas.Ind(df)
        z.d200 = (np.arange(len(idx)) // 700 % 2).astype(float)
        out[c] = z
    return out


def _world(monkeypatch):
    fr = _frames()
    F = al.features(fr)
    thr = al.is_thresholds(fr, F)
    monkeypatch.setattr(rp, "load_extra", lambda cache, idx=None: _extra())
    return rp.World.build(fr, F, thr, "/nikde")


def test_originals_match_ai_lab(monkeypatch):
    fr = _frames()
    F = al.features(fr)
    a = al.a1_echo(fr, F)
    b = rp.run_spec(rp.ORIG["a1"], fr, F)
    assert [t["r"] for t in a] == [t["r"] for t in b]
    assert np.allclose(al.a4_rotation(fr, F).to_numpy(), rp.run_spec(rp.ORIG["a4"], fr, F).to_numpy())
    assert np.allclose(al.a3_hours(fr, F)[0].to_numpy(), rp.run_spec(rp.ORIG["a3"], fr, F).to_numpy())
    assert [t["r"] for t in al.a2_quiet(fr, F)] == [t["r"] for t in rp.run_spec(rp.ORIG["a2"], fr, F)]


def test_time_test_all_kinds(monkeypatch):
    w = _world(monkeypatch)
    assert set(w.tf) == {"2h", "4h"} and len(w.extra) == 3
    g = {"conds": [("r1z", ">", 0.5)], "dir": 1, "hold": 4, "stop": 2.0}
    for spec in (rp.ORIG["a1"], rp.ORIG["a3"], rp.ORIG["a4"], {"kind": "genome", "genome": g}):
        tt = w.time_test(spec)
        assert set(tt["checks"]) == {"years", "regimes", "tf", "coins"} and isinstance(tt["pass"], bool)
        assert tt["years"] and tt["coins"]["n_coins"] == 3
        json.dumps(tt, default=str)
        assert rp.tt_lines(tt, rp.kind_type(spec))


def test_repair_one_attempt(monkeypatch, tmp_path):
    w = _world(monkeypatch)
    monkeypatch.setitem(rp.GRIDS, "a1", rp.GRIDS["a1"][:4])
    x = rp.repair(w, "a1", "Ozvěna BTC", rp.ORIG["a1"], "2026-11-26")
    assert x["n_variants"] == 4 and x["of"] == "a1" and "time_test" in x
    g = {"conds": [("r1z", ">", 0.5), ("rsi14", "<", 0.7)], "dir": 1, "hold": 4, "stop": 2.0}
    assert len(rp.neighbours(g)) > 20
    monkeypatch.setattr(rp, "neighbours", lambda g: [g, {**g, "hold": 8}, {**g, "stop": 3.0}])
    y = rp.repair(w, "r18", "Kolo 18 · vše", {"kind": "genome", "genome": g}, "2026-11-26")
    assert y["type"] == "r"
    monkeypatch.setattr(rp, "OUT", tmp_path / "r.json")
    monkeypatch.setattr(rp, "OUT_MD", tmp_path / "r.md")
    D = {"repairs": [x, y], "updated": "x", "extra_coins": list(w.extra)}
    (tmp_path / "r.json").write_text(json.dumps(D, default=str))
    rp.write_md(D)
    assert "Ozvěna BTC" in (tmp_path / "r.md").read_text()
    aj = {"strategies": [{"id": "a1", "pass": False}, {"id": "a2", "pass": False}, {"id": "ga", "pass": True}]}
    rounds = {"rounds": [{"n": 18, "added": None, "focus": "vše", "repair_genome": g}, {"n": 12, "added": None, "focus": "x", "repair_genome": g}]}
    assert [j[0] for j in rp.todo(aj, rounds)] == ["a2"]          # a1 i r18 už pokus měly, kolo 12 je před Testem v čase


def test_round_with_time_test(monkeypatch, tmp_path):
    fr = _frames()
    F = al.features(fr)
    monkeypatch.setattr(al, "POP", 10)
    monkeypatch.setattr(al, "GENS", 2)
    monkeypatch.setattr(al, "TOP_K", 5)
    monkeypatch.setattr(al, "TT_FROM_ROUND", 1)
    monkeypatch.setattr(al, "ROUNDS", tmp_path / "r.json")
    calls = []
    R = al.run_round(fr, F, None, None, lambda g: calls.append(g) or {"pass": False})
    r = R["rounds"][-1]
    assert r["repair_genome"] is not None and r["added"] is None
    assert r["time_tested"] == len(calls)
