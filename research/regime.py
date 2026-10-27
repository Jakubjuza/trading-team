"""Režim trhu pro jednu minci z denních svíček – vždy z PŘEDCHOZÍHO uzavřeného dne (žádný pohled do budoucnosti).

    panika   – denní ATR v % ceny je v horních 20 % za posledních 365 dní (stejná myšlenka jako filtr paniky skeneru)
    býčí     – close nad EMA 200 a EMA 50 roste
    medvědí  – close pod EMA 200 a EMA 50 klesá
    boční    – všechno ostatní

Použití: `regime_series(daily_df)` vrátí řadu štítků s indexem = den, PRO KTERÝ štítek platí (tj. den po výpočtu).
"""
import numpy as np
import pandas as pd

LABELS = ("býčí", "medvědí", "boční", "panika")


def regime_series(daily):
    c = daily["Close"]
    e200 = c.ewm(span=200, adjust=False, min_periods=200).mean()
    e50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
    tr = pd.concat([daily["High"] - daily["Low"], (daily["High"] - c.shift()).abs(), (daily["Low"] - c.shift()).abs()],
                   axis=1).max(axis=1)
    atr_pct = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean() / c
    rank = atr_pct.rolling(365, min_periods=120).rank(pct=True)
    rising = e50 > e50.shift(1)
    lab = np.where(c > e200, np.where(rising, "býčí", "boční"), np.where(~rising, "medvědí", "boční"))
    lab = pd.Series(lab, index=daily.index, dtype=object)
    lab[rank >= 0.8] = "panika"
    lab[e200.isna() | e50.shift(1).isna()] = None
    lab.index = lab.index + pd.Timedelta("1D")                         # platí až pro následující den
    return lab


def at(series, times):
    """Štítek režimu pro dané časy svíček (podle dne jejich začátku)."""
    idx = pd.DatetimeIndex(times)
    return series.reindex(idx.floor("1D")).to_numpy(dtype=object)
