import json

import numpy as np
import pandas as pd

from research import context
from scanner import lab_paper


def _ohlcv(n, freq="1h", seed=0, start="2025-01-01"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(pd.Timestamp(start, tz="UTC"), periods=n, freq=freq)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * 1.003
    l = np.minimum(o, c) * 0.997
    return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c, "Volume": rng.lognormal(5, .3, n)}, index=idx)


def _daily(h1):
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    return h1.resample("1D").agg(agg).dropna()


def test_follow_through_does_not_look_ahead():
    df = _ohlcv(3000, seed=1)
    a = context.follow_through(*(df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close")),
                               np.full(len(df), 1.0))
    cut = 2000
    df2 = df.copy()
    df2.iloc[cut + 1:, :4] *= 1.5                                      # budoucnost se změní
    b = context.follow_through(*(df2[k].to_numpy(float) for k in ("Open", "High", "Low", "Close")),
                               np.full(len(df2), 1.0))
    assert np.allclose(a[:cut + 1], b[:cut + 1], equal_nan=True)
    assert np.nanmin(a) >= 0 and np.nanmax(a) <= 1


def test_follow_through_counts_continued_breakouts():
    n = 400
    c = np.r_[np.full(50, 100.0), 100 + np.arange(n - 50) * 1.0]      # čistý trend: každý průraz pokračuje
    ft = context.follow_through(c, c + .1, c - .1, c, np.full(n, 0.5))
    assert ft[-1] == 1.0


def test_tf_context_uses_previous_day_only():
    h1 = _ohlcv(24 * 400, seed=2)
    d = _daily(h1)
    dctx = context.daily_frame(d, d, None)
    tc = context.TfContext(h1, dctx)
    i = len(h1) - 5
    f1 = tc.at([i], 1)
    h1b = h1.copy()
    day = h1.index[i].floor("1D")
    h1b.loc[h1b.index >= day, ["Open", "High", "Low", "Close"]] *= 2  # dnešek (ještě neuzavřený den) se změní
    db = _daily(h1b)
    tcb = context.TfContext(h1b, context.daily_frame(db, db, None))
    f2 = tcb.at([i], 1)
    for k in ("trend_d", "er_d", "adx_d", "chop_d", "rpos_d", "btc_d"):
        assert np.allclose(f1[k], f2[k], equal_nan=True), k
    assert np.allclose(tc.at([i], -1)["trend_d"], -f1["trend_d"], equal_nan=True)


def _model(pass_=True):
    w = {f: 0 for f in context.FEATURES}
    w["ft_tf"] = 1
    w["trend_d"] = 1
    norm = {f: (0.0, 1.0) for f in context.FEATURES}
    norm["ft_tf"] = (0.5, 0.1)
    return {"weights": w, "norm": norm, "threshold": 0.0, "gate": {"pass": pass_},
            "range": {"ft_tf_max": 0.45, "er_d_max": 0.3}}


def _feats(ft=0.6, trend=1.0, er=0.5):
    f = {k: np.array([0.0]) for k in context.FEATURES}
    f.update({"ft_tf": np.array([ft]), "trend_d": np.array([trend]), "er_d": np.array([er])})
    return f


def test_score_and_reasons():
    m = _model()
    assert context.score(m, _feats(ft=0.7, trend=1.0))[0] > 0
    assert context.score(m, _feats(ft=0.3, trend=-1.5))[0] < 0
    pos, neg = context.reasons(m, _feats(ft=0.3, trend=1.5))
    assert "denní trend mince" in pos and "pokračování průrazů" in neg
    nan = _feats()
    nan["ft_tf"] = np.array([np.nan])                                 # chybějící metrika = průměr, ne pád
    assert np.isfinite(context.score(m, nan)[0])


def test_decide_gate_limit_and_range():
    m = _model()
    trend_s = {"id": "a", "dir": "long"}
    range_s = {"id": "b", "dir": "long", "context": "range"}
    ok, *_ = lab_paper.decide(m, trend_s, _feats(ft=0.7, trend=1.0), [], 3, "BTC")
    assert ok
    ok, why, *_ = lab_paper.decide(m, trend_s, _feats(ft=0.2, trend=-1.5), [], 3, "BTC")
    assert not ok and "slabý kontext" in why
    ok, *_ = lab_paper.decide(_model(pass_=False), trend_s, _feats(ft=0.2, trend=-1.5), [], 3, "BTC")
    assert ok                                                         # neprošlá brána jen měří
    ok, why, *_ = lab_paper.decide(m, trend_s, _feats(), [{"coin": "BTC", "dir": "long"}], 3, "BTC")
    assert not ok and "stejného směru" in why
    opn = [{"coin": c, "dir": "long"} for c in ("ETH", "SOL", "XRP")]
    ok, why, *_ = lab_paper.decide(m, trend_s, _feats(), opn, 3, "BTC")
    assert not ok and "limit 3" in why
    ok, *_ = lab_paper.decide(m, range_s, _feats(ft=0.3, er=0.2), [], 3, "BTC")
    assert ok
    ok, why, *_ = lab_paper.decide(m, range_s, _feats(ft=0.7, er=0.2), [], 3, "BTC")
    assert not ok and "boční" in why
    ok, *_ = lab_paper.decide(None, range_s, None, [], 3, "BTC")
    assert not ok                                                     # bez modelu se boční strategie neobchoduje


class _State:
    def __init__(self):
        self.data = {}

    def save(self):
        pass


def test_update_routes_blocked_signal_to_shadow(tmp_path, monkeypatch):
    """Celý průchod laboratoře: signál, který limit nepustí, jde do stínového deníku a bez zprávy."""
    h1 = _ohlcv(1200, seed=3, start="2025-06-01")
    d1 = _daily(_ohlcv(24 * 400, seed=3, start="2024-06-01"))
    now = h1.index[-1] + pd.Timedelta("1h")

    def fake_candles(ex, coin, tf, now_, bars=1000):
        return d1 if tf == "1d" else h1

    monkeypatch.setattr(lab_paper, "candles", fake_candles)
    monkeypatch.setattr(lab_paper, "load_model", lambda path=None: None)
    # strategie, která signalizuje na každé svíčce: přepíšeme family_signals
    last = len(h1) - 1
    monkeypatch.setattr(lab_paper.atlas, "family_signals",
                        lambda z, fam, p, d: (np.array([len(z.c) - 1]), np.zeros(len(z.c), bool)))
    reg = {"strategies": [{"id": "x|1|1h|none|trail|long", "label": "Test · 1H long", "family": "donchian",
                           "params": "100", "tf": "1h", "filter": "none", "exit": "trail", "dir": "long",
                           "status": "papír", "regimes": [], "backtest": {"oos_r": 0.2}}]}
    cfg = {"lab": {"enabled": True, "max_same_dir": 1},
           "tickers": [{"symbol": "BTC/USDT", "source": "crypto"}, {"symbol": "ETH/USDT", "source": "crypto"}],
           "notify": {"telegram": False}}
    st = _State()
    sent = []
    msgs = lab_paper.update(cfg, st, now=now, reg=reg, ex=object(), send=sent.append)
    assert len(st.data["lab"]["open"]) == 1 and len(st.data["lab"]["shadow"]) == 1
    assert "limit 1" in st.data["lab"]["shadow"][0]["skip"]
    assert len(msgs) == 1 and len(sent) == 1                          # stínový signál bez zprávy
    shadow = [json.loads(x) for x in lab_paper.SHADOW.read_text().splitlines()]
    assert shadow[0]["event"] == "signal" and shadow[0]["coin"] == "ETH"
    assert last == len(h1) - 1
