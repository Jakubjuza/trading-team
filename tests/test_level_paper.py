import json

import numpy as np
import pandas as pd
import yaml

from scanner import level_paper as lv

CFG = yaml.safe_load(open("scanner/config.yaml"))
P = next(s for s in CFG["strategies"] if s["name"] == "donchian_1d")["params"]


def _frames(direction="short"):
    """Denní pád pod EMA200, dnes 1H prorazí 20denní minimum v 1H downtrendu."""
    days = pd.date_range("2025-01-01", periods=400, freq="1D", tz="UTC")
    c = np.r_[np.linspace(200, 150, 380), np.linspace(150, 140, 20)]
    w = np.linspace(0.03, 0.01, 400)                                   # volatilita klesá → ne panika
    d1 = pd.DataFrame({"Open": c, "High": c * (1 + w), "Low": c * (1 - w), "Close": c, "Volume": 1.0}, index=days)
    today = days[-1] + pd.Timedelta(days=1)
    hours = pd.date_range(today - pd.Timedelta(hours=100), today + pd.Timedelta(hours=60), freq="1h", tz="UTC")
    hc = np.linspace(142, 130, len(hours))
    h1 = pd.DataFrame({"Open": hc, "High": hc * 1.001, "Low": hc * 0.999, "Close": hc, "Volume": 1.0}, index=hours)
    return d1, h1, today


def test_find_entry_short_at_level():
    d1, h1, today = _frames()
    e = lv.find_entry(d1, h1, today, P)
    level = d1["Low"].iloc[-P["channel"]:].min()
    assert e and e["dir"] == "short" and abs(e["level"] - level) < 1e-9
    assert e["entry"] <= level and e["stop"] > e["entry"] * 1.014
    assert e["time"] >= today


def test_update_opens_and_closes(tmp_path):
    d1, h1, today = _frames()

    class S:
        data = {}

        def save(self):
            pass

    st = S()
    now = today + pd.Timedelta(hours=10, minutes=1)
    fetch = lambda coin, tf, bars: (h1[h1.index + pd.Timedelta(hours=1) <= now] if tf == "1h" else d1)  # noqa: E731
    cfg = {**CFG, "level_entry": {"enabled": True, "coins": ["BTC"]}}
    msgs = lv.update(cfg, st, now, dry_run=True, fetch=fetch)
    assert st.data["level"]["open"] and any("🎯" in m for m in msgs)
    assert lv.update(cfg, st, now, dry_run=True, fetch=fetch) == []           # stejná hodina → nic
    later = today + pd.Timedelta(hours=59)
    fetch2 = lambda coin, tf, bars: (h1 if tf == "1h" else d1)  # noqa: E731
    lv.update(cfg, st, later, dry_run=True, fetch=fetch2)
    recs = [json.loads(x) for x in lv.LOG.read_text().splitlines()]
    assert recs[0]["event"] == "open"
