"""Testy kalendáře světových burz a měření jejich vlivu."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from research import sessions as s

UTC = timezone.utc


def test_open_times_follow_local_dst():
    # ASX 10:00 Sydney: v říjnu (letní čas AEDT, UTC+11) = 23:00 UTC předchozího dne
    asx = s.opens("Sydney (ASX)", datetime(2026, 10, 25, tzinfo=UTC), datetime(2026, 10, 27, tzinfo=UTC))
    assert asx[0] == datetime(2026, 10, 25, 23, 0, tzinfo=UTC)
    # NYSE 9:30 New York: do 1. 11. letní čas (13:30 UTC), potom zimní (14:30 UTC)
    ny = s.opens("New York (NYSE)", datetime(2026, 10, 30, tzinfo=UTC), datetime(2026, 11, 3, tzinfo=UTC))
    assert [t.hour * 60 + t.minute for t in ny] == [13 * 60 + 30, 14 * 60 + 30]       # pá 30. 10., po 2. 11.
    assert all(t.weekday() < 5 for t in ny)                                  # o víkendu zavřeno
    # CME neděle 17:00 Chicago
    cme = s.opens("CME (neděle)", datetime(2026, 10, 24, tzinfo=UTC), datetime(2026, 10, 27, tzinfo=UTC))
    assert cme == [datetime(2026, 10, 25, 22, 0, tzinfo=UTC)]


def test_session_now_weekend_and_weekday():
    sun = s.session_now(datetime(2026, 10, 25, 12, 0, tzinfo=UTC))
    assert sun["weekend_cme_closed"] and sun["open_now"] == ["žádná velká burza (jen krypto)"]
    assert [e["open"] for e in sun["next_24h"]][:2] == ["CME (neděle)", "Sydney (ASX)"]
    assert sun["next_24h"][1]["prague"] == "po 00:00"                         # Praha už v zimním čase
    tue = s.session_now(datetime(2026, 10, 27, 15, 0, tzinfo=UTC))
    assert set(tue["open_now"]) == {"Londýn (LSE)", "New York (NYSE)"} and not tue["weekend_cme_closed"]


def _hourly(start="2026-01-01", days=200, seed=0, spike_hour=None):
    idx = pd.date_range(start, periods=days * 24, freq="1h", tz="UTC")
    rng = np.random.default_rng(seed)
    vol = np.full(len(idx), 0.002)
    if spike_hour is not None:
        vol[(idx.hour >= spike_hour) & (idx.hour < spike_hour + 4)] = 0.008
    c = 100 * np.exp(np.cumsum(rng.normal(0, vol)))
    o = np.r_[100, c[:-1]]
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c) * 1.001, "Low": np.minimum(o, c) * 0.999,
                         "Close": c, "Volume": 1.0}, index=idx)


def test_open_effect_detects_volatility_at_open():
    df = _hourly(spike_hour=14)                                              # NYSE v zimě 14:30 UTC → svíčka 15:00
    ny = s.open_effect(df, "New York (NYSE)", 2)
    ldn = s.open_effect(df, "Londýn (LSE)", 2)
    assert ny["vol_ratio"] > 1.5 and ldn["vol_ratio"] < 1.0
    assert abs(ny["t_stat"]) < 3                                             # náhodná data → žádný směr


def test_cme_gap_and_current_gap():
    df = _hourly(start="2026-06-01", days=150)
    g = s.cme_gaps(df, min_gap_pct=0.0)
    assert g["n"] >= 15 and 0 <= g["p_filled"] <= 1 and 0 <= g["p_random_level"] <= 1
    now = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)                           # úterý
    h1 = df[df.index < pd.Timestamp(now)]
    cur = s.current_gap(h1, now)
    fri = h1["Open"][h1.index >= pd.Timestamp("2026-10-23 21:00", tz="UTC")].iloc[0]  # pá 16:00 Chicago (CDT = UTC−5)
    assert cur["friday_close"] == round(float(fri), 6) and isinstance(cur["filled"], bool)


def test_context_line_uses_stats():
    stats = {"pooled": {"opens_4h": {"New York (NYSE)": {"vol_ratio": 1.46}, "Sydney (ASX)": {"vol_ratio": 1.06},
                                     "CME (neděle)": {"vol_ratio": 1.47}}}}
    line = s.context_line(datetime(2026, 10, 27, 10, 0, tzinfo=UTC), "BTC", stats)
    assert "New York" in line and "1,5×" in line and "út 14:30" in line
    assert s.context_line(datetime(2026, 10, 27, 20, 0, tzinfo=UTC), "BTC", stats) == ""    # nic silného do 6 h
    assert "víkend" in s.context_line(datetime(2026, 10, 24, 10, 0, tzinfo=UTC), "BTC", stats)
    assert "CME futures" in s.upcoming_line(datetime(2026, 10, 25, 20, 0, tzinfo=UTC), 4, stats)


def test_section_sessions_without_candles():
    sec = s.section_sessions(None, datetime(2026, 10, 25, 20, 0, tzinfo=UTC), "BTC",
                             {"coins": {"BTC": {"opens_4h": {"CME (neděle)": {"vol_ratio": 1.5, "avg_ret_pct": 0.0}}}}})
    assert sec["next_24h"][0]["hist_vol_4h_x"] == 1.5 and "cme_gap" not in sec
