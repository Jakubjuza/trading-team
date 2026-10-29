"""🧠 Kontext trhu u signálu – „vnímá to trh jako člověk, nebo jen slepě bere průraz?“

Stejný kód počítá metriky v backtestu (research/experiments/context_gate.py) i živě (scanner/lab_paper.py),
takže papír a test měří totéž. Vše je známé na close signální svíčky; denní metriky jsou z PŘEDCHOZÍHO uzavřeného
dne, Strach a chamtivost den zpožděně. Žádný pohled do budoucnosti.

Metriky (kladná hodnota = „v souladu se směrem obchodu“ tam, kde dává směr smysl):
  trend_d    denní trend mince ve směru obchodu: close nad EMA200, nad EMA50, EMA50 roste  (−1,5 … +1,5) × směr
  btc_d      totéž pro BTC (altcoiny jdou za BTC)
  er_d       denní efektivita pohybu (Kaufman ER, 20 dní): 1 = čistý trend, 0 = chaos tam a zpět
  adx_d      denní ADX(14) – síla trendu bez ohledu na směr
  chop_d     denní Choppiness index(14): vysoko = boční pila
  rpos_d     poloha v rozpětí 30 dní ve směru obchodu: +1 = kupuju na vrcholu rozpětí (long), −1 = u dna
  er_tf      efektivita pohybu na timeframu signálu (50 svíček)
  ft_tf      FOLLOW-THROUGH: z posledních 30 průrazů 20svíčkového maxima/minima (oba směry) na tomhle timeframu
             a minci, kolik pokračovalo aspoň 0,5 ATR dál za 6 svíček. Nízko = průrazy jsou jen sweepy likvidity.
  squeeze    ATR(14) / průměrné ATR za 100 svíček: nízko = trh se před signálem uklidnil (napětí), vysoko = už letí
  clv        kde se signální svíčka zavřela ve svém rozpětí ve směru obchodu (+1 = na samém konci, −1 = knot proti)
  vol        objem signální svíčky / průměr 20 svíček
  ext        vzdálenost close od EMA20 v ATR ve směru obchodu (přetažení)
  fng        Strach a chamtivost ve směru obchodu: (F&G − 50) / 50 × směr (long při chamtivosti = +)
  fng_chg    změna F&G za 7 dní ve směru obchodu
"""
import numpy as np
import pandas as pd

FEATURES = ("trend_d", "btc_d", "er_d", "adx_d", "chop_d", "rpos_d", "er_tf", "ft_tf", "squeeze", "clv", "vol", "ext",
            "fng", "fng_chg")

CS = {"trend_d": "denní trend mince", "btc_d": "denní trend BTC", "er_d": "trendovost (denní)", "adx_d": "síla trendu ADX",
      "chop_d": "boční pila (chop)", "rpos_d": "poloha v rozpětí 30 dní", "er_tf": "trendovost na TF signálu",
      "ft_tf": "pokračování průrazů", "squeeze": "uklidnění před signálem", "clv": "zavření svíčky",
      "vol": "objem průrazu", "ext": "přetažení od EMA20", "fng": "nálada (strach/chamtivost)", "fng_chg": "změna nálady"}

FT_LOOKBACK, FT_HORIZON, FT_EVENTS, FT_MIN_ATR = 20, 6, 30, 0.5


# ---------------------------------------------------------------- pomocné
def _atr(df, n=14):
    c = df["Close"]
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - c.shift()).abs(), (df["Low"] - c.shift()).abs()], axis=1).max(axis=1)
    return tr, tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def _er(close, n):
    c = pd.Series(close, dtype=float)
    net = (c - c.shift(n)).abs()
    path = c.diff().abs().rolling(n, min_periods=n).sum()
    return (net / path.replace(0, np.nan)).to_numpy()


def _adx(df, n=14):
    h, l = df["High"], df["Low"]
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    tr, _ = _atr(df, n)
    a = 1 / n
    trs = tr.ewm(alpha=a, adjust=False, min_periods=n).mean()
    pdi = 100 * pdm.ewm(alpha=a, adjust=False, min_periods=n).mean() / trs
    mdi = 100 * mdm.ewm(alpha=a, adjust=False, min_periods=n).mean() / trs
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=a, adjust=False, min_periods=n).mean()


def _chop(df, n=14):
    tr, _ = _atr(df, 1)
    rng = df["High"].rolling(n, min_periods=n).max() - df["Low"].rolling(n, min_periods=n).min()
    return 100 * np.log10(tr.rolling(n, min_periods=n).sum() / rng.replace(0, np.nan)) / np.log10(n)


def _trend_score(daily):
    c = daily["Close"]
    e200 = c.ewm(span=200, adjust=False, min_periods=200).mean()
    e50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
    s = (c > e200).astype(float) + (c > e50).astype(float) + (e50 > e50.shift(1)).astype(float) - 1.5
    return s.where(e200.notna() & e50.shift(1).notna())


# ---------------------------------------------------------------- denní kontext (bez směru)
def daily_frame(daily, btc_daily=None, fng=None):
    """Denní metriky s indexem = den, PRO KTERÝ platí (výpočet z předchozího uzavřeného dne)."""
    c = daily["Close"]
    hi30, lo30 = daily["High"].rolling(30, min_periods=30).max(), daily["Low"].rolling(30, min_periods=30).min()
    out = pd.DataFrame({
        "trend_d": _trend_score(daily),
        "er_d": _er(c.to_numpy(float), 20),
        "adx_d": _adx(daily),
        "chop_d": _chop(daily),
        "rpos_d": 2 * (c - lo30) / (hi30 - lo30).replace(0, np.nan) - 1,
    }, index=daily.index)
    out["btc_d"] = _trend_score(btc_daily).reindex(out.index) if btc_daily is not None else np.nan
    out.index = out.index + pd.Timedelta("1D")
    if fng is not None:                       # fng už má index = den, pro který platí (research/lab.fng_series)
        f = fng.reindex(out.index).ffill()
        out["fng"] = (f - 50) / 50
        out["fng_chg"] = (f - f.shift(7)) / 50
    else:
        out["fng"] = np.nan
        out["fng_chg"] = np.nan
    return out


# ---------------------------------------------------------------- follow-through průrazů
def follow_through(o, h, l, c, atr, lookback=FT_LOOKBACK, horizon=FT_HORIZON, events=FT_EVENTS, min_atr=FT_MIN_ATR):
    """Pro každou svíčku podíl posledních `events` průrazů, které pokračovaly ≥ min_atr ATR za `horizon` svíček.

    Průraz = každá svíčka, která zavře nad max. high předchozích `lookback` svíček (nebo pod min.). Výsledek průrazu na svíčce j je známý
    až na close svíčky j + horizon, teprve od té chvíle se započítá. Vrací pole délky len(c) (NaN, dokud není 10 průrazů).
    """
    n = len(c)
    hs, ls = pd.Series(h), pd.Series(l)
    hi = hs.rolling(lookback, min_periods=lookback).max().shift(1).to_numpy()
    lo = ls.rolling(lookback, min_periods=lookback).min().shift(1).to_numpy()
    up = c > hi                                    # každá svíčka, která zavře za maximem/minimem předchozích N
    dn = c < lo
    idx = np.flatnonzero(up | dn)
    idx = idx[idx + horizon < n]
    if not len(idx):
        return np.full(n, np.nan)
    d = np.where(up[idx], 1.0, -1.0)
    fut = c[idx + horizon]
    ok = (d * (fut - c[idx]) >= min_atr * atr[idx]).astype(float)
    known = idx + horizon
    rate = pd.Series(ok).rolling(events, min_periods=10).mean().to_numpy()
    pos = np.searchsorted(known, np.arange(n), side="right") - 1          # poslední průraz s už známým výsledkem
    out = np.full(n, np.nan)
    m = pos >= 0
    out[m] = rate[pos[m]]
    return out


# ---------------------------------------------------------------- metriky na timeframu signálu
class TfContext:
    """Metriky jedné mince na jednom timeframu (bez směru); směr se přidá v `at`."""

    def __init__(self, df, dctx):
        self.df = df
        o, h, l, c, v = (df[k].to_numpy(float) for k in ("Open", "High", "Low", "Close", "Volume"))
        _, atr_s = _atr(df)
        atr = atr_s.to_numpy()
        self.er_tf = _er(c, 50)
        self.ft_tf = follow_through(o, h, l, c, atr)
        self.squeeze = atr / atr_s.rolling(100, min_periods=50).mean().to_numpy()
        rng = np.where(h - l > 0, h - l, np.nan)
        self.clv = 2 * (c - l) / rng - 1
        self.vol = v / pd.Series(v).rolling(20, min_periods=20).mean().shift(1).to_numpy()
        e20 = df["Close"].ewm(span=20, adjust=False, min_periods=20).mean().to_numpy()
        self.ext = (c - e20) / atr
        self.day = dctx.reindex(df.index.floor("1D"))

    def at(self, idx, d):
        """Slovník metrik pro indexy svíček `idx` a směr d (+1 long, −1 short)."""
        idx = np.asarray(idx, np.int64)
        dd = self.day.iloc[idx]
        return {
            "trend_d": d * dd["trend_d"].to_numpy(float),
            "btc_d": d * dd["btc_d"].to_numpy(float),
            "er_d": dd["er_d"].to_numpy(float),
            "adx_d": dd["adx_d"].to_numpy(float),
            "chop_d": dd["chop_d"].to_numpy(float),
            "rpos_d": d * dd["rpos_d"].to_numpy(float),
            "er_tf": self.er_tf[idx],
            "ft_tf": self.ft_tf[idx],
            "squeeze": self.squeeze[idx],
            "clv": d * self.clv[idx],
            "vol": self.vol[idx],
            "ext": d * self.ext[idx],
            "fng": d * dd["fng"].to_numpy(float),
            "fng_chg": d * dd["fng_chg"].to_numpy(float),
        }


# ---------------------------------------------------------------- model brány (parametry z backtestu)
def score(model, feats):
    """Skóre kontextu: Σ váha × standardizovaná metrika (chybějící metrika = 0, tj. průměr). Vrací pole."""
    n = len(np.atleast_1d(feats[FEATURES[0]]))
    s = np.zeros(n)
    for f, w in model["weights"].items():
        if not w:
            continue
        mu, sd = model["norm"][f]
        x = (np.atleast_1d(np.asarray(feats[f], float)) - mu) / sd
        s += w * np.clip(np.nan_to_num(x, nan=0.0), -3, 3)
    return s


def is_range(model, feats):
    """Boční kontext podle předem stanovených mezí (pro strategie typu „návrat do rozpětí“)."""
    rc = model["range"]
    ft = np.asarray(feats["ft_tf"], float)
    er = np.asarray(feats["er_d"], float)
    return (ft < rc["ft_tf_max"]) & (er < rc["er_d_max"])


def reasons(model, feats, k=3):
    """Nejsilnější důvody pro a proti u jednoho signálu (pro zprávu na Telegram)."""
    parts = []
    for f, w in model["weights"].items():
        if not w:
            continue
        mu, sd = model["norm"][f]
        x = float(np.atleast_1d(feats[f])[0])
        if not np.isfinite(x):
            continue
        parts.append((w * np.clip((x - mu) / sd, -3, 3), f))
    parts.sort()
    neg = [CS[f] for v, f in parts[:k] if v < -0.25]
    pos = [CS[f] for v, f in parts[::-1][:k] if v > 0.25]
    return pos, neg


def describe(model, feats):
    """Jednořádkový popis kontextu signálu pro Telegram (popis, ne signál)."""
    g = lambda k: float(np.atleast_1d(feats[k])[0])                    # noqa: E731
    ft, er, tr = g("ft_tf"), g("er_d"), g("trend_d")
    kind = "boční základna" if bool(is_range(model, feats)[0]) else "trh už trenduje"
    bits = []
    if np.isfinite(ft):
        bits.append(f"průrazy pokračují {ft:.0%}")
    if np.isfinite(er):
        bits.append(f"denní trendovost {er:.2f}")
    if np.isfinite(tr):
        bits.append("denní trend " + ("po směru" if tr > 0 else "proti směru" if tr < 0 else "neutrální"))
    return f"🧠 Kontext: {kind} · " + " · ".join(bits)
