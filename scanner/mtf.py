"""Vstup z nižších timeframů pro denní signál (1D směr → 4H potvrzení → 1H zóna → 1H spouštěč).

Pravidlo (otestované v research/experiments/mtf_entry.py, reports/mtf_entry.md):
  • 4H: poslední UZAVŘENÁ 4h svíčka zavřela ve směru obchodu vůči EMA20 (4H),
  • 1H zóna: cena se po signálu dotkla EMA20 (1H) – návrat proti směru,
  • 1H spouštěč: hodinová svíčka zavře zpět za EMA20 a zároveň za high (long) / low (short) předchozí svíčky,
  • stop za swingem posledních 6 hodinových svíček − 0,1 denního ATR, min. 1,5 % od vstupu, nejvýš původní denní stop,
  • cíle = ceny T1/T2 z denního signálu; když už je cena za T1, vstup se nebere,
  • když cena před spouštěčem zasáhne denní stop, signál propadá; čeká se nejvýš `wait_hours`.
"""
import numpy as np
import pandas as pd


def resample_4h(h1):
    return h1.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()


def find_trigger(direction, h1, t0, daily_stop, targets, atr, wait_hours=72, ema_len=20, swing_bars=6,
                 min_stop_pct=1.5, ema1=None, h4=None, ema4=None, upper_hours=4):
    """h1 = uzavřené hodinové svíčky (index = začátek svíčky). t0 = uzavření denní svíčky signálu.
    Obecně: h1 = timeframe spouštěče, h4 = vyšší timeframe potvrzení s délkou svíčky `upper_hours` (výchozí 4H/1H).
    Vrací {"status": "entry", "time", "entry", "stop"} | {"status": "stopped"} | {"status": "skipped"} | None (čeká)."""
    long = direction == "long"
    ema1 = ema1 if ema1 is not None else h1["Close"].ewm(span=ema_len, adjust=False).mean()
    h4 = h4 if h4 is not None else resample_4h(h1)
    ema4 = ema4 if ema4 is not None else h4["Close"].ewm(span=ema_len, adjust=False).mean()
    win = h1[(h1.index >= t0) & (h1.index < t0 + pd.Timedelta(hours=wait_hours))]
    touched, prev = False, None
    for t, row in win.iterrows():
        if (long and row["Low"] <= daily_stop) or (not long and row["High"] >= daily_stop):
            return {"status": "stopped", "time": t}
        e = ema1.get(t)
        if e is None or np.isnan(e):
            prev = row
            continue
        if (long and row["Low"] <= e) or (not long and row["High"] >= e):
            touched = True
        closed4 = ema4[ema4.index <= t - pd.Timedelta(hours=upper_hours)]       # poslední UZAVŘENÁ svíčka vyššího TF
        trend_ok = False
        if len(closed4):
            c4 = h4["Close"].get(closed4.index[-1])
            trend_ok = c4 is not None and ((long and c4 > closed4.iloc[-1]) or (not long and c4 < closed4.iloc[-1]))
        trig = prev is not None and touched and trend_ok and (
            (long and row["Close"] > e and row["Close"] > prev["High"]) or
            (not long and row["Close"] < e and row["Close"] < prev["Low"]))
        if trig:
            entry = float(row["Close"])
            if (long and targets[0] <= entry) or (not long and targets[0] >= entry):
                return {"status": "skipped", "time": t}
            swing = h1[h1.index <= t].iloc[-swing_bars:]
            sw = swing["Low"].min() - 0.1 * atr if long else swing["High"].max() + 0.1 * atr
            min_d = entry * min_stop_pct / 100
            sw = min(sw, entry - min_d) if long else max(sw, entry + min_d)
            stop = max(sw, daily_stop) if long else min(sw, daily_stop)
            return {"status": "entry", "time": t, "entry": entry, "stop": float(stop)}
        prev = row
    return None
