import json

import pandas as pd

from research import ai_lab as al
from research import future_lab as fl
from tests.test_ai_lab import _frames


def test_round_uses_only_data_before_round(monkeypatch):
    fr = _frames()
    F = al.features(fr)
    monkeypatch.setattr(fl, "POP", 10)
    monkeypatch.setattr(fl, "GENS", 2)
    monkeypatch.setattr(al, "TOP_K", 5)
    t = pd.Timestamp("2025-06-01", tz="UTC")
    r = fl.run_one(fr, F, "A", 1, t)
    assert r["is_end"].startswith("2024-06-01") and r["oos_end"].startswith("2025-06-01")
    assert all("hold" not in c for c in r["cands"])            # výsledky po kole se do výběru nedostanou
    assert al.IS_END == pd.Timestamp("2024-01-01", tz="UTC") and al.POP == 200   # globály AI Labu vrácené zpět
    json.dumps(r, default=str)


def _cand(t, conds=(("rsi14", ">", 0.8),), d=1):
    return {"genome": {"conds": [list(c) for c in conds], "dir": d, "hold": 8, "stop": 2.0},
            "is": {"n": 400, "mean_r": 0.1, "t": 2.0}, "oos": {"n": 200, "mean_r": 0.2, "t": t}}


def test_registry_a_adds_and_replaces(monkeypatch):
    monkeypatch.setattr(fl, "MAX_REG", 2)
    rounds = [{"n": i, "t": f"2025-0{i}-09T00:00:00+00:00", "focus": "vše", "tested": 1, "top_oos_ok": 3, "random_oos_ok": 0,
               "sane": True, "thr": {}, "cands": [_cand(t, (("rsi14", ">", q),))]}
              for i, (t, q) in enumerate([(3.0, .1), (2.6, .2), (2.8, .3), (2.5, .4)], start=1)]
    members, hist = fl.registry_a(rounds)
    assert [h["added"] for h in hist] == ["fa1", "fa2", "fa3", None]
    assert hist[2]["removed"] == "fa2" and members[1]["removed"].startswith("2025-03-09")


def test_registry_b_keeps_diverse_best():
    rounds = [{"n": 1, "focus": "vše", "thr": {}, "cands": [_cand(4.0), _cand(3.5, (("rsi14", ">", .3),)),
                                                             _cand(3.2, (("comp", "<", .2),))]}]
    reg, pool = fl.registry_b(rounds)
    assert pool == 3 and [m["oos"]["t"] for m in reg] == [4.0, 3.2]     # stejná sada znaků a směr jen jednou


def test_years_to_million():
    s, e = pd.Timestamp("2024-11-09", tz="UTC"), pd.Timestamp("2026-11-09", tz="UTC")
    assert fl.years_to_million({"equity": 4000.0}, s, e)["years"] == 10.0
    assert fl.years_to_million({"equity": 900.0}, s, e) is None
