"""🌡️ Index nálady trhu (research/mood.py)."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from research import mood
from scanner import commands
from scanner.scan import State


def frame(trend, n=600, start="2025-01-01"):
    idx = pd.date_range(start, periods=n, freq="D", tz="UTC")
    rng = np.random.default_rng(1)
    c = 100 * np.exp(np.cumsum(trend + rng.normal(0, 0.02, n)))
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c, "Volume": 1.0}, index=idx)


def test_zones_and_scores():
    assert mood.zone(1) == "silně medvědí" and mood.zone(40) == "medvědí" and mood.zone(55) == "neutrální"
    assert mood.zone(61) == "býčí" and mood.zone(100) == "silně býčí"
    assert mood.score_funding(-10) == 0 and mood.score_funding(10) == 50 and mood.score_funding(30) == 100
    assert mood.score_stables(5) == 100 and mood.score_stables(-9) == 0
    dg = {"krypto": [{"tone": "pozitivní"}] * 6 + [{"tone": "negativní"}] * 2, "note": "x"}
    assert mood.score_news(dg)[0] == 75
    assert mood.score_news({"krypto": [{"tone": "neutrální"}] * 9})[0] is None       # málo tónovaných titulků


def test_combine_reweights_missing_components():
    assert mood.combine({"trend": 100.0, "makro": 0.0}) == round(100 * 20 / 35)
    assert mood.combine({"trend": 100.0, "makro": None, "fear_greed": float("nan")}) == 100
    assert mood.combine({}) is None
    assert mood.combine({"trend": 0.0}) == 1                                      # škála 1–100


def test_trend_up_scores_higher_than_trend_down():
    up = mood.price_history({"BTC": frame(0.004), "ETH": frame(0.004)}).iloc[-100:].mean()
    dn = mood.price_history({"BTC": frame(-0.004), "ETH": frame(-0.004)}).iloc[-100:].mean()
    assert up["trend"] > 70 > 30 > dn["trend"]
    assert up["šíře trhu"] > dn["šíře trhu"]


def test_no_lookahead():
    """Hodnota indexu v den t se nezmění, když přidáme budoucí svíčky."""
    full = {"BTC": frame(0.001), "ETH": frame(-0.001)}
    cut = {k: v.iloc[:450] for k, v in full.items()}
    a = mood.price_history(full).iloc[449]
    b = mood.price_history(cut).iloc[-1]
    pd.testing.assert_series_equal(a, b, check_names=False)


def fake(index, zone_name=None):
    return lambda daily: {"index": index, "zone": zone_name or mood.zone(index), "as_of": "2026-10-26T07:00:00+00:00",
                          "components": {"trend": {"score": float(index), "detail": "BTC test"}}}


def test_daily_update_once_per_day_and_alert_only_on_zone_change(tmp_path):
    cfg = {"timezone": "Europe/Prague", "mood": {"enabled": True, "hour": 8}}
    st = State(tmp_path / "s.json")
    frames = {("BTC/USDT", "1d"): frame(0.0)}
    sent = []
    early = datetime(2026, 10, 26, 5, 0, tzinfo=timezone.utc)                    # 6:00 Praha – ještě ne
    assert mood.daily_update(cfg, st, frames, early, send=sent.append, compute=fake(50)) is None and "day" not in st.data.get("mood", {})
    t = datetime(2026, 10, 26, 8, 0, tzinfo=timezone.utc)
    assert mood.daily_update(cfg, st, frames, t, send=sent.append, compute=fake(50)) is None   # první den bez zprávy
    assert mood.daily_update(cfg, st, frames, t, send=sent.append, compute=fake(20)) is None   # stejný den znovu ne
    t2 = datetime(2026, 10, 27, 8, 0, tzinfo=timezone.utc)
    assert mood.daily_update(cfg, st, frames, t2, send=sent.append, compute=fake(55)) is None  # stejné pásmo
    t3 = datetime(2026, 10, 28, 8, 0, tzinfo=timezone.utc)
    msg = mood.daily_update(cfg, st, frames, t3, send=sent.append, compute=fake(35))
    assert sent == [msg] and "neutrální (55) → medvědí (35)" in msg and "trend: 55 → 35" in msg
    assert [d for d, _ in st.data["mood"]["history"]] == ["2026-10-26", "2026-10-27", "2026-10-28"]


def test_nalada_command(tmp_path):
    st = State(tmp_path / "s.json")
    assert "ještě není" in commands.mood_report(st)
    st.data["mood"] = {"last": fake(30)(None), "history": [["2026-10-%02d" % d, 50 - d] for d in range(1, 10)]}
    txt = commands.mood_report(st)
    assert txt.startswith("🌡️ Nálada trhu: 30/100 – medvědí") and "• trend (20 %): 30 – BTC test" in txt
    assert "před 7 dny 48" in txt and "Spočítáno 2026-10-26" in txt
