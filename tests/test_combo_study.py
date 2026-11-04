"""Studie kombinací (research/experiments/combo_study.py): parametry, filtry, pravidlo průchodu, registr, papír."""
import numpy as np
import pandas as pd
import pytest

from research import registry
from research.experiments import combo_study as cs
from research.experiments import strategy_atlas as atlas

M = atlas.MAIN


def _frame(seed=1, start="2021-01-01", end="2026-01-01", tf="4h"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq=tf, tz="UTC", inclusive="left")
    ret = rng.normal(0.0003, 0.02, len(idx)) + 0.004 * np.sin(np.arange(len(idx)) / 60)
    c = 100 * np.exp(np.cumsum(ret))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.01, len(idx)))
    l = np.minimum(o, c) * (1 - rng.uniform(0, 0.01, len(idx)))
    v = rng.lognormal(10, 0.5, len(idx))
    df = pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c, "Volume": v}, index=idx)
    z = atlas.Ind(df)
    n = len(idx)
    z.flt = {"d200": (np.arange(n) // 200 % 2).astype(float), "d50": (np.arange(n) // 90 % 2).astype(float)}
    z.reg = np.array([("býčí", "medvědí", "boční", "panika")[(i // 150) % 4] for i in range(n)], dtype=object)
    z.ns = z.df.index.as_unit("ns").asi8.astype(np.int64)
    z.fng = 50 + 40 * np.sin(np.arange(n) / 37)
    return z


@pytest.fixture(scope="module")
def z():
    return _frame()


def test_params_roundtrip_and_label():
    s = cs.make_params("ma_cross", "ema/20/100/cross", [("vol", 1.5), ("reg", "trend")])
    assert s == "ma_cross:ema/20/100/cross+vol:1.5+reg:trend"
    fam, p, f = cs.parse_params(s)
    assert fam == "ma_cross" and p == ("ema", 20, 100, "cross") and f == [("vol", 1.5), ("reg", "trend")]
    assert cs.parse_params("boll_break:20/2.0")[1] == (20, 2.0)
    e = {"family": "combo", "params": s, "tf": "4h", "filter": "none", "exit": "trail", "dir": "long"}
    assert "|" not in s and registry.sid(e).startswith("combo|")
    assert registry.label(e).startswith("Kombinace: Protnutí průměrů ema 20 100 cross + objem×1,5")


def test_neighbors():
    assert cs.neighbors("vol", 1.5) == [1.0, 2.0]
    assert cs.neighbors("vol", 1) == [1.5]            # „vol:1“ z textu registru
    assert cs.neighbors("rsi", 45) == [50]
    assert cs.neighbors("reg", "trend") == [] and cs.neighbors("macd", "sig") == []


def test_filters_are_mirrored_and_subset(z):
    for kind, val in [("rsi", 50), ("macd", "sig"), ("ema", 100), ("fng", 45), ("d", 200)]:
        L, S = cs.filter_mask(z, kind, val, 1), cs.filter_mask(z, kind, val, -1)
        assert L.dtype == bool and len(L) == len(z.c)
        assert not (L & S).any() or kind == "ema"     # long a short se nepřekrývají
    ent, _ = atlas.family_signals(z, "donchian", (20,), 1)
    ent2, _ = cs.combo_signals(z, "donchian:20+vol:1.5", 1)
    assert set(ent2) <= set(ent) and len(ent2) < len(ent)
    ok = cs.filter_mask(z, "vol", 1.5, 1)
    assert ok[ent2].all()
    assert not cs.filter_mask(z, "reg", "trend", 1)[z.reg != "býčí"].any()


def test_fng_filter_without_data_blocks():
    z2 = _frame(seed=2, end="2021-06-01")
    del z2.fng
    assert not cs.filter_mask(z2, "fng", 45, 1).any()
    assert cs.needs_fng("donchian:20+fngg:55") and not cs.needs_fng("donchian:20+vol:1.5")


def _row(**k):
    base = {f"{M}_is_n": 300, f"{M}_oos_n": 80, f"{M}_is_r": 0.2, f"{M}_oos_r": 0.3, f"{M}_hold_r": 0.2,
            f"{M}_rnd_oos_p95": 0.1, f"{M}_rnd_hold_p95": 0.1, f"{M}_oos_t": 2.5, "oos_gain": 0.1, "is_gain": 0.05}
    base.update({(f"{M}_{a}" if not a.endswith("gain") else a): b for a, b in k.items()})
    return base


def test_basic_pass_rule():
    assert cs.basic_pass(_row())
    assert not cs.basic_pass(_row(oos_gain=0.04))           # neporazí spouštěč o 0,05 R
    assert not cs.basic_pass(_row(oos_t=1.9))
    assert not cs.basic_pass(_row(is_n=149))
    assert not cs.basic_pass(_row(hold_r=0.05))             # pod p95 náhody
    assert not cs.basic_pass(_row(is_r=-0.01))
    assert "OOS t < 2" in cs.fail_reason(_row(oos_t=1.0))


def test_robust_neighbors():
    r = _row() | {"params": "donchian:20+vol:1.5"}
    good = {"donchian:20+vol:1": {"oos_gain": 0.02}, "donchian:20+vol:2": {"oos_gain": 0.01}}
    assert cs.robust(r, good)[0]
    bad = {"donchian:20+vol:1": {"oos_gain": 0.02}, "donchian:20+vol:2": {"oos_gain": -0.03}}
    ok, why = cs.robust(r, bad)
    assert not ok and "vol:2" in why
    assert not cs.robust(r, {"donchian:20+vol:1": {"oos_gain": 0.02}})[0]       # sousední nespočteno
    cat = _row() | {"params": "donchian:20+reg:trend"}
    assert cs.robust(cat, {})[0]
    assert not cs.robust(cat | {"is_gain": -0.01}, {})[0]                       # kategorický bez IS zlepšení


def _cand(params, oos_t=3.0, hold_t=2.5, tf="4h"):
    return {"params": params, "tf": tf, "exit": "trail", "dir": "long", f"{M}_is_r": 0.2, f"{M}_oos_r": 0.3,
            f"{M}_hold_r": 0.2, f"{M}_oos_t": oos_t, f"{M}_hold_t": hold_t, f"{M}_is_n": 300, f"{M}_oos_n": 80,
            f"{M}_hold_n": 60, "base_oos_r": 0.1, "maxdd_r": 10.0, "per_month": 3.0,
            "regime_stats": {"býčí": {"n": 40, "mean_r": 0.3}}, "regimes": ["býčí"]}


def test_register_limits_and_replacement():
    other = {"id": "macd|12/26/9/signal|4h|none|opp|long", "family": "macd", "status": "papír", "params": "12/26/9/signal"}
    reg = {"strategies": [dict(other)]}
    ch = cs.register([_cand("donchian:20+vol:1.5"), _cand("donchian:20+vol:2"), _cand("donchian:20+vol:1")],
                     reg, "2026-11-04", 1)
    combos = [s for s in reg["strategies"] if s["family"] == "combo"]
    assert len(ch) == 2 and len(combos) == 2                                   # nejvýš 2 nové za běh
    assert all(s["status"] == "papír" and s["history"][0]["reason"].startswith("combo_study:") for s in combos)
    assert reg["strategies"][0] == other                                      # necombo beze změny
    assert cs.register([_cand("donchian:20+vol:1.5")], reg, "2026-11-04", 2) == []   # už je v registru
    # naplnit limit 10
    for i in range(4):
        cs.register([_cand(f"donchian:{i}+vol:1", oos_t=2.2 + i * 0.1), _cand(f"donchian:{i}+vol:2", oos_t=2.2 + i * 0.1)],
                    reg, "2026-11-04", 3 + i)
    assert len([s for s in registry.active(reg) if s["family"] == "combo"]) == 10
    assert cs.register([_cand("roc:20+vol:1", oos_t=2.0, hold_t=2.0)], reg, "2026-11-05", 9) == []   # slabší → nic
    ch = cs.register([_cand("roc:20+vol:1", oos_t=4.0, hold_t=4.0)], reg, "2026-11-05", 10)
    assert len(ch) == 1 and "nahradila" in ch[0]
    act = [s for s in registry.active(reg) if s["family"] == "combo"]
    assert len(act) == 10
    gone = [s for s in reg["strategies"] if s["status"] == "vyřazeno"]
    assert len(gone) == 1 and gone[0]["history"][-1]["reason"].startswith("combo_study: nahrazeno")


def test_lab_paper_dispatch(z):
    from scanner import lab_paper
    s = {"family": "combo", "params": "donchian:20+rsi:50", "dir": "long", "exit": "trail"}
    a, _ = lab_paper._signals(z, s, 1)
    b, _ = cs.combo_signals(z, "donchian:20+rsi:50", 1)
    assert np.array_equal(a, b) and len(a)
    assert lab_paper._needs_fng({"family": "combo", "params": "donchian:20+fng:30"})
    assert not lab_paper._needs_fng({"family": "macd", "params": "12/26/9/signal"})
    i = int(a[len(a) // 2])
    assert lab_paper._simulate(z, s, i)["entry_i"] == i + 1


def test_run_part_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "OUT", tmp_path / "combo")
    monkeypatch.setattr(cs, "STATE", tmp_path / "combo_state.json")
    monkeypatch.setattr(atlas, "N_RAND", 3)
    frames = {"AAA": _frame(3), "BBB": _frame(4)}
    adir = tmp_path / "atlas"
    adir.mkdir()
    pd.DataFrame([{"tf": "4h", "family": "donchian", "params": "20", "filter": "none", "exit": "trail", "dir": "long",
                   f"{M}_is_n": 400, f"{M}_is_r": 0.1, f"{M}_is_t": 2.0},
                  {"tf": "4h", "family": "donchian", "params": "20", "filter": "d200", "exit": "trail", "dir": "long",
                   f"{M}_is_n": 400, f"{M}_is_r": 0.5, f"{M}_is_t": 5.0},
                  {"tf": "4h", "family": "macd", "params": "12/26/9/signal", "filter": "none", "exit": "opp", "dir": "short",
                   f"{M}_is_n": 50, f"{M}_is_r": 0.1, f"{M}_is_t": 3.0}]).to_csv(adir / "4h.csv.gz", index=False)
    saved = []
    real_save = cs.save_state
    monkeypatch.setattr(cs, "save_state", lambda st: (saved.append(
        [p.get("status") for p in st["parts"]]), real_save(st)))
    st = {"next": cs.parts().index(("pair", "4h", "A")), "total_tests": 0, "parts": []}
    st, part, res, cands = cs.run_part(None, st, frames=frames, atlas_dir=adir)
    assert saved[0] == ["běží"]                                               # mřížka zapsána před výsledky
    assert [t["family"] for t in part["grid"]["triggers"]] == ["donchian"]    # jen bez filtru, IS ≥ 300
    assert part["n_combos"] == 11 and part["n_tests"] == 12 and st["total_tests"] == 12
    assert len(res) == 11 and {"oos_gain", "is_gain", "basic", "robust", "passed", "why"} <= set(res.columns)
    assert (cs.OUT / f"part_{part['no']:03d}.csv.gz").exists()
    assert st["next"] == cs.parts().index(("pair", "4h", "A")) + 1
    # deep stejného TF vezme páry z uloženého dílu
    meta, combos = cs.grid_for("deep", "4h", None, st)
    assert all(len(f) == 2 for _, f in combos)
    monkeypatch.setattr(cs, "REPORT", tmp_path / "combo_study.md")
    monkeypatch.setattr(registry, "PATH", tmp_path / "registry.json")
    txt = cs.report(st)
    assert "Studie kombinací" in txt and "Top 10" in txt
