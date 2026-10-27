"""Atlas strategií – 15 rodin pravidlových strategií na 7 timeframech, long i short, s poplatky MEXC.

Stanoveno PŘEDEM (27. 10. 2026), po spuštění se nic neladí:

  Data: OKX spot USDT, 8 mincí (BTC ETH SOL XRP ADA LINK AVAX DOGE). Hodinové svíčky od 1/2019 (z nich 2H, 4H, 6H,
        12H, 1D), 15M svíčky od 1/2022. Ceny OKX a MEXC se u těchto párů liší zanedbatelně.
  Rodiny a varianty (signál pro long, short je zrcadlo; „výstup signálem“ = opp):
    ma_cross     SMA/EMA, rychlý {5..50} × pomalý {30..200}, signál cross / confirm / pullback   (192)
    price_ma     close protne SMA/EMA {10,20,50,100,200}                                          (10)
    donchian     close nad max. předchozích N {10,20,40,55,100}; výstup pod min. N/2               (5)
    boll_break   close nad horní Bollinger (n {20,50}, k {2,2.5}); výstup pod střed                (4)
    boll_fade    close zpět nad dolní Bollinger; výstup nad střed                                  (4)
    rsi_revert   RSI(2) nahoru přes 10 / 5, RSI(14) přes 30 / 25; výstup RSI(2) > 70, RSI(14) > 50 (4)
    rsi_mom      RSI(14) nahoru přes 50 / 55 / 60; výstup pod 50                                   (3)
    macd         (12,26,9) (5,35,5) (19,39,9) × protnutí signální / nulové linie                   (6)
    roc          změna za N {10,20,50,100} svíček přejde nad 0                                     (4)
    supertrend   (10, 2) (10, 3) (20, 3) – otočení směru                                           (3)
    stoch        %K(14) protne %D(3) zespodu pod 20 / 30; výstup protnutí shora nad 80 / 70        (2)
    keltner      close nad EMA20 + m × ATR, m {1,5; 2; 2,5}; výstup pod EMA20                      (3)
    vol_break    průraz max. N {20,55} s objemem ≥ v × průměr 20 {1,5; 2,5}; výstup pod min. N/2  (4)
    candle       inside bar průraz / pohlcení (engulfing); výstup close pod EMA20                  (2)
    sweep        propíchnutí min. N {20,55} a close zpět nad ním; výstup nad střed kanálu          (2)
  Na každou variantu: timeframe {15M,1H,2H,4H,6H,12H,1D} × filtr {none, d200, d50} × výstup {opp, trail, target,
  opp_stop} × směr {long, short} = 41 664 kombinací. Filtry a výstupy jako v ma_grid.py.
  Poplatky na stranu: MEXC futures taker 0,02 % + skluz 0,03 % = **0,05 % (hlavní scénář, rozhoduje)**;
  MEXC spot taker 0,05 % + skluz 0,03 % = 0,08 %; MEXC maker 0 % bez skluzu = 0 % (optimistická mez – limitní
  příkaz se nemusí vyplnit); 0,15 % (dřívější testy). Funding futures není započten.
  Rozdělení: IS < 2024-01-01 ≤ OOS < 2025-07-01 ≤ HOLDOUT. Každá kombinace má vlastní náhodné srovnání
  (10 opakování, stejná mince, směr, filtr, výstup i signál výstupu, podobný počet obchodů).
  Výběr (hlavní scénář poplatků): kombinace s IS ≥ 150 a OOS ≥ 50 obchody; podle IS t-statistiky 50 nejlepších na
  směr ze VŠECH rodin a timeframů. PROJDE: Ø R > 0 v IS, OOS i HOLDOUT, OOS i HOLDOUT nad 95. percentilem vlastní
  náhody, OOS t ≥ 2. Navíc se spočítá, kolik ze VŠECH kombinací splní totéž (bez pořadí v IS) – a kolik by to mělo
  být čistě náhodou; to jsou jen kandidáti na papírové ověření, ne důkaz.

    python3 research/experiments/strategy_atlas.py run 4h scanner/cache        # jeden timeframe → reports/atlas/4h.csv.gz
    python3 research/experiments/strategy_atlas.py report reports/atlas        # souhrn → reports/strategy_atlas.md
    python3 research/experiments/strategy_atlas.py run 4h scanner/cache --quick
"""
import sys
import time
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

ROOT = Path(__file__).resolve().parents[2]
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
SPLIT_OOS, SPLIT_HOLD = pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")
COSTS = {"mexc_fut": 0.0005, "mexc_spot": 0.0008, "maker": 0.0, "old": 0.0015}
MAIN = "mexc_fut"
FILTERS = ["none", "d200", "d50"]
EXITS = {"opp": (0.0, 0.0, 0.0, True, 300), "trail": (2.0, 3.0, 0.0, False, 100),
         "target": (2.0, 0.0, 3.0, False, 50), "opp_stop": (1.5, 0.0, 0.0, True, 300)}
DIRS = {"short": -1, "long": 1}
N_RAND = 10
OHLCV = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}


def variants():
    v = []
    for kind in ("sma", "ema"):
        for f in (5, 10, 20, 30, 40, 50):
            for s in (30, 50, 60, 100, 150, 200):
                if f < s:
                    for sig in ("cross", "confirm", "pullback"):
                        v.append(("ma_cross", (kind, f, s, sig)))
    v += [("price_ma", (k, n)) for k in ("sma", "ema") for n in (10, 20, 50, 100, 200)]
    v += [("donchian", (n,)) for n in (10, 20, 40, 55, 100)]
    v += [("boll_break", (n, k)) for n in (20, 50) for k in (2.0, 2.5)]
    v += [("boll_fade", (n, k)) for n in (20, 50) for k in (2.0, 2.5)]
    v += [("rsi_revert", p) for p in ((2, 10), (2, 5), (14, 30), (14, 25))]
    v += [("rsi_mom", (t,)) for t in (50, 55, 60)]
    v += [("macd", (a, b, c, m)) for (a, b, c) in ((12, 26, 9), (5, 35, 5), (19, 39, 9)) for m in ("signal", "zero")]
    v += [("roc", (n,)) for n in (10, 20, 50, 100)]
    v += [("supertrend", p) for p in ((10, 2.0), (10, 3.0), (20, 3.0))]
    v += [("stoch", p) for p in ((20, 80), (30, 70))]
    v += [("keltner", (m,)) for m in (1.5, 2.0, 2.5)]
    v += [("vol_break", (n, x)) for n in (20, 55) for x in (1.5, 2.5)]
    v += [("candle", (k,)) for k in ("inside", "engulf")]
    v += [("sweep", (n,)) for n in (20, 55)]
    return v


# ---------------------------------------------------------------- data
def fetch(coin, tf, start, cache):
    path = cache / f"okx_{coin}_{tf}_from{start[:4]}.csv"
    if path.exists() and (time.time() - path.stat().st_mtime) < 6 * 3600:
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    import ccxt
    ex = ccxt.okx({"enableRateLimit": True})
    step = {"1h": 3_600_000, "15m": 900_000}[tf]
    since = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end = int(datetime.now(timezone.utc).timestamp() * 1000)
    rows, empty, errs = [], 0, 0
    while since < end:
        try:
            batch = ex.fetch_ohlcv(f"{coin}/USDT", tf, since=since, limit=100)
        except Exception as exc:
            errs += 1
            print(f"  {coin} {tf} {pd.Timestamp(since, unit='ms')}: {exc.__class__.__name__}", flush=True)
            if errs > 50:
                break
            time.sleep(3)
            continue
        if not batch:
            empty += 1
            since += 100 * step
            if empty > 3000:
                break
            continue
        rows += batch
        nxt = batch[-1][0] + step
        since = nxt if nxt > since else since + 100 * step
    df = pd.DataFrame(rows, columns=["t", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("t")
    df.index = pd.to_datetime(df.pop("t"), unit="ms", utc=True)
    df = df.sort_index()
    cache.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def resample(base, tf):
    tf = {"1d": "1D"}.get(tf, tf)
    df = base[list(OHLCV)].resample(tf).agg(OHLCV).dropna() if tf not in ("1h", "15m") else base[list(OHLCV)].dropna()
    return df[df.index + pd.Timedelta(tf) <= datetime.now(timezone.utc)]


def daily_regimes(base):
    d = resample(base, "1d")
    e200 = d["Close"].ewm(span=200, adjust=False, min_periods=200).mean()
    e50 = d["Close"].ewm(span=50, adjust=False, min_periods=50).mean()
    bull = (d["Close"] > e200).where(e200.notna())
    up = (e50 > e50.shift(1)).where(e50.shift(1).notna())
    bull.index = bull.index + pd.Timedelta("1D")
    up.index = up.index + pd.Timedelta("1D")
    return bull, up


# ---------------------------------------------------------------- indikátory
class Ind:
    """Líně počítané indikátory jedné mince na jednom timeframu."""

    def __init__(self, df):
        self.df = df
        self.c = df["Close"].to_numpy(float)
        self.o = df["Open"].to_numpy(float)
        self.h = df["High"].to_numpy(float)
        self.l = df["Low"].to_numpy(float)
        self.v = df["Volume"].to_numpy(float)
        self._ = {}
        cl = df["Close"]
        tr = pd.concat([df["High"] - df["Low"], (df["High"] - cl.shift()).abs(), (df["Low"] - cl.shift()).abs()], axis=1).max(axis=1)
        self.atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean().to_numpy()

    def get(self, key, fn):
        if key not in self._:
            self._[key] = fn()
        return self._[key]

    def ma(self, kind, n):
        s = self.df["Close"]
        return self.get(("ma", kind, n), lambda: (s.rolling(n, min_periods=n).mean() if kind == "sma"
                                                    else s.ewm(span=n, adjust=False, min_periods=n).mean()).to_numpy())

    def hi(self, n):   # max. high předchozích n svíček (bez aktuální)
        return self.get(("hi", n), lambda: self.df["High"].rolling(n, min_periods=n).max().shift(1).to_numpy())

    def lo(self, n):
        return self.get(("lo", n), lambda: self.df["Low"].rolling(n, min_periods=n).min().shift(1).to_numpy())

    def sd(self, n):
        return self.get(("sd", n), lambda: self.df["Close"].rolling(n, min_periods=n).std(ddof=0).to_numpy())

    def rsi(self, n):
        def f():
            d = self.df["Close"].diff()
            up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
            dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
            return (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(100).where(up.notna()).to_numpy()
        return self.get(("rsi", n), f)

    def macd(self, a, b, c):
        def f():
            s = self.df["Close"]
            line = s.ewm(span=a, adjust=False, min_periods=b).mean() - s.ewm(span=b, adjust=False, min_periods=b).mean()
            return line.to_numpy(), line.ewm(span=c, adjust=False, min_periods=c).mean().to_numpy()
        return self.get(("macd", a, b, c), f)

    def stoch(self):
        def f():
            hh = self.df["High"].rolling(14, min_periods=14).max()
            ll = self.df["Low"].rolling(14, min_periods=14).min()
            k = 100 * (self.df["Close"] - ll) / (hh - ll).replace(0, np.nan)
            return k.to_numpy(), k.rolling(3, min_periods=3).mean().to_numpy()
        return self.get(("stoch",), f)

    def supertrend(self, n, m):
        def f():
            tr = np.maximum.reduce([self.h - self.l, np.abs(self.h - np.r_[np.nan, self.c[:-1]]),
                                    np.abs(self.l - np.r_[np.nan, self.c[:-1]])])
            atr = pd.Series(tr).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()
            return _supertrend(self.h, self.l, self.c, atr, m)
        return self.get(("st", n, m), f)

    def vavg(self, n):
        return self.get(("vavg", n), lambda: self.df["Volume"].rolling(n, min_periods=n).mean().shift(1).to_numpy())


@njit(cache=True)
def _supertrend(h, l, c, atr, m):
    n = len(c)
    trend = np.zeros(n)
    up = np.full(n, np.nan)
    dn = np.full(n, np.nan)
    for i in range(n):
        if not (atr[i] > 0):
            continue
        mid = (h[i] + l[i]) / 2
        bu, bd = mid - m * atr[i], mid + m * atr[i]
        if i > 0 and trend[i - 1] != 0:
            if c[i - 1] > up[i - 1]:
                bu = max(bu, up[i - 1])
            if c[i - 1] < dn[i - 1]:
                bd = min(bd, dn[i - 1])
        up[i], dn[i] = bu, bd
        if i == 0 or trend[i - 1] == 0:
            trend[i] = 1.0
        elif trend[i - 1] > 0:
            trend[i] = -1.0 if c[i] < up[i - 1] else 1.0
        else:
            trend[i] = 1.0 if c[i] > dn[i - 1] else -1.0
    return trend


def xup(a, b):
    a = np.asarray(a, float)
    b = np.broadcast_to(np.asarray(b, float), a.shape)
    now = a > b
    prev = np.r_[False, (a[:-1] <= b[:-1])]
    ok = ~(np.isnan(a) | np.isnan(b)) & np.r_[False, ~(np.isnan(a[:-1]) | np.isnan(b[:-1]))]
    return now & prev & ok


def xdn(a, b):
    return xup(-np.asarray(a, float), -np.broadcast_to(np.asarray(b, float), np.shape(a)))


def first(cond):
    cond = np.asarray(cond, bool)
    return cond & ~np.r_[False, cond[:-1]]


def family_signals(z, fam, p, d):
    """Vrátí (vstupy: indexy svíček se signálem na close, výstupní signál: bool pole)."""
    c, h, l, o = z.c, z.h, z.l, z.o
    L = d > 0
    up = xup if L else xdn
    dn = xdn if L else xup
    if fam == "ma_cross":
        kind, f, s, sig = p
        fast, slow = z.ma(kind, f), z.ma(kind, s)
        ok = ~(np.isnan(fast) | np.isnan(slow))
        side = ((fast > slow) if L else (fast < slow)) & ok
        if sig == "cross":
            ent = first(side) & np.r_[False, ok[:-1]]
        elif sig == "confirm":
            ent = first(side & ((c > np.fmax(fast, slow)) if L else (c < np.fmin(fast, slow))))
        else:
            ent = side & np.r_[False, side[:-1]] & np.r_[False, ((c < fast) if L else (c > fast))[:-1]] & ((c > fast) if L else (c < fast))
        other = ((fast < slow) if L else (fast > slow)) & ok
        return np.flatnonzero(ent), first(other)
    if fam == "price_ma":
        m = z.ma(*p)
        return np.flatnonzero(up(c, m)), dn(c, m)
    if fam in ("donchian", "vol_break"):
        n = p[0]
        hi, lo = z.hi(n), z.lo(n)
        brk = first((c > hi) if L else (c < lo))
        if fam == "vol_break":
            brk &= z.v > p[1] * z.vavg(20)
        ex = (c < z.lo(max(2, n // 2))) if L else (c > z.hi(max(2, n // 2)))
        return np.flatnonzero(brk), first(ex)
    if fam in ("boll_break", "boll_fade"):
        n, k = p
        mid, sd = z.ma("sma", n), z.sd(n)
        upb, lob = mid + k * sd, mid - k * sd
        if fam == "boll_break":
            return np.flatnonzero(xup(c, upb) if L else xdn(c, lob)), (xdn(c, mid) if L else xup(c, mid))
        return np.flatnonzero(xup(c, lob) if L else xdn(c, upb)), (xup(c, mid) if L else xdn(c, mid))
    if fam == "rsi_revert":
        n, t = p
        r = z.rsi(n)
        exit_lvl = 70 if n == 2 else 50
        if L:
            return np.flatnonzero(xup(r, t)), xup(r, exit_lvl)
        return np.flatnonzero(xdn(r, 100 - t)), xdn(r, 100 - exit_lvl)
    if fam == "rsi_mom":
        r = z.rsi(14)
        if L:
            return np.flatnonzero(xup(r, p[0])), xdn(r, 50)
        return np.flatnonzero(xdn(r, 100 - p[0])), xup(r, 50)
    if fam == "macd":
        a, b, cc, mode = p
        line, sig = z.macd(a, b, cc)
        ref = sig if mode == "signal" else np.zeros_like(line)
        return np.flatnonzero(up(line, ref)), dn(line, ref)
    if fam == "roc":
        n = p[0]
        roc = c / np.r_[np.full(n, np.nan), c[:-n]] - 1
        return np.flatnonzero(up(roc, 0.0)), dn(roc, 0.0)
    if fam == "supertrend":
        tr = z.supertrend(*p)
        want = 1.0 if L else -1.0
        prev = np.r_[0.0, tr[:-1]]
        return np.flatnonzero((tr == want) & (prev == -want)), (tr == -want) & (prev == want)
    if fam == "stoch":
        lo_z, hi_z = p
        k, dd = z.stoch()
        kp = np.r_[np.nan, k[:-1]]
        if L:
            return np.flatnonzero(xup(k, dd) & (kp < lo_z)), xdn(k, dd) & (kp > hi_z)
        return np.flatnonzero(xdn(k, dd) & (kp > hi_z)), xup(k, dd) & (kp < lo_z)
    if fam == "keltner":
        mid = z.ma("ema", 20)
        band = mid + (1 if L else -1) * p[0] * z.atr
        return np.flatnonzero(up(c, band)), dn(c, mid)
    if fam == "candle":
        e20 = z.ma("ema", 20)
        ex = xdn(c, e20) if L else xup(c, e20)
        h1, l1, h2, l2 = np.r_[np.nan, h[:-1]], np.r_[np.nan, l[:-1]], np.r_[np.nan, np.nan, h[:-2]], np.r_[np.nan, np.nan, l[:-2]]
        o1, c1 = np.r_[np.nan, o[:-1]], np.r_[np.nan, c[:-1]]
        if p[0] == "inside":
            inside = (h1 <= h2) & (l1 >= l2)
            ent = inside & ((c > h2) if L else (c < l2))
        else:
            ent = ((c1 < o1) & (c > o) & (c >= o1) & (o <= c1)) if L else ((c1 > o1) & (c < o) & (c <= o1) & (o >= c1))
        return np.flatnonzero(ent), ex
    if fam == "sweep":
        n = p[0]
        hi, lo = z.hi(n), z.lo(n)
        mid = (hi + lo) / 2
        if L:
            return np.flatnonzero((l < lo) & (c > lo)), xup(c, mid)
        return np.flatnonzero((h > hi) & (c < hi)), xdn(c, mid)
    if fam == "fng":                                                   # Strach a chamtivost (z.fng, den zpožděně)
        mode, lvl = p
        f = z.fng
        lv = lvl if L else 100 - lvl
        if mode == "into":                                             # vstup do extrému (long do strachu, short do chamtivosti)
            ent = xdn(f, lv) if L else xup(f, lv)
        else:                                                          # konec extrému (návrat ze strachu / z chamtivosti)
            ent = xup(f, lv) if L else xdn(f, lv)
        return np.flatnonzero(ent), (xup(f, 50) if L else xdn(f, 50))
    raise ValueError(fam)


# ---------------------------------------------------------------- simulace (bez nákladů; náklady se odečtou potom)
@njit(cache=True)
def simulate(o, h, l, c, atr, entries, opp, d, stop_atr, trail_atr, tgt_atr, use_opp, max_hold):
    n = len(o)
    m = len(entries)
    out_i = np.empty(m, np.int64)
    out_x = np.empty(m, np.int64)
    out_g = np.empty(m)
    out_rf = np.empty(m)
    k = 0
    last_exit = -1
    for j in range(m):
        i = entries[j]
        e = i + 1
        if e >= n or e <= last_exit:
            continue
        a = atr[i]
        if not (a > 0):
            continue
        px = o[e]
        risk = (stop_atr if stop_atr > 0 else 2.0) * a
        stop = px - d * stop_atr * a if stop_atr > 0 else np.nan
        tgt = px + d * tgt_atr * a if tgt_atr > 0 else np.nan
        best = px
        xp = np.nan
        xb = -1
        end = min(n, e + max_hold)
        t = e
        while t < end:
            if stop_atr > 0:
                if d > 0:
                    if o[t] <= stop:
                        xp = o[t]
                    elif l[t] <= stop:
                        xp = stop
                else:
                    if o[t] >= stop:
                        xp = o[t]
                    elif h[t] >= stop:
                        xp = stop
                if xp == xp:
                    xb = t
                    break
            if tgt_atr > 0:
                if d > 0 and h[t] >= tgt:
                    xp = o[t] if o[t] > tgt else tgt
                    xb = t
                    break
                if d < 0 and l[t] <= tgt:
                    xp = o[t] if o[t] < tgt else tgt
                    xb = t
                    break
            if use_opp and opp[t]:
                if t + 1 < n:
                    xp = o[t + 1]
                    xb = t + 1
                else:
                    xp = c[t]
                    xb = t
                break
            if trail_atr > 0 and atr[t] > 0:
                if d > 0:
                    if c[t] > best:
                        best = c[t]
                    ns = best - trail_atr * atr[t]
                    if ns > stop:
                        stop = ns
                else:
                    if c[t] < best:
                        best = c[t]
                    ns = best + trail_atr * atr[t]
                    if ns < stop:
                        stop = ns
            t += 1
        if xb < 0:
            xb = end - 1
            xp = c[xb]
        out_i[k] = e
        out_x[k] = xb
        out_g[k] = d * (xp / px - 1.0)
        out_rf[k] = risk / px
        k += 1
        last_exit = xb
    return out_i[:k], out_x[:k], out_g[:k], out_rf[:k]


def split_masks(ns):
    a, b = SPLIT_OOS.value, SPLIT_HOLD.value
    return {"is": ns < a, "oos": (ns >= a) & (ns < b), "hold": ns >= b}


def stats_for(g, rf, ns, cost):
    r = (g - 2 * cost) / rf
    out = {}
    for nm, m in split_masks(ns).items():
        x = r[m]
        n = len(x)
        mean = x.mean() if n else np.nan
        sd = x.std(ddof=1) if n > 1 else np.nan
        out[f"{nm}_n"] = n
        out[f"{nm}_r"] = mean
        out[f"{nm}_t"] = mean / (sd / np.sqrt(n)) if n > 1 and sd > 0 else np.nan
        out[f"{nm}_pct"] = ((g[m] - 2 * cost).mean() * 100) if n else np.nan
        out[f"{nm}_win"] = (x > 0).mean() if n else np.nan
    return out, r


def max_dd(r, xt):
    if not len(r):
        return np.nan
    eq = np.cumsum(r[np.argsort(xt, kind="stable")])
    return float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max())


# ---------------------------------------------------------------- běh jednoho timeframu
def run(tf, cache, quick=False, var=None, attach=None, name=None):
    """var = vlastní seznam variant, attach(coin, z) = doplní další data (např. sentiment), name = jméno výstupu."""
    t0 = time.time()
    base_tf, start = ("15m", "2022-01-01") if tf == "15m" else ("1h", "2019-01-01")
    data = {}
    for coin in COINS:
        b = fetch(coin, base_tf, start, cache)
        if len(b) < 500:
            print(f"{coin}: málo dat ({len(b)}), vynecháno", flush=True)
            continue
        data[coin] = b
        print(f"{coin} {base_tf}: {len(b)} svíček {b.index[0]:%Y-%m-%d} → {b.index[-1]:%Y-%m-%d}", flush=True)
    regime_src = {c: (fetch(c, "1h", "2019-01-01", cache) if tf == "15m" else b) for c, b in data.items()}
    prep = {}
    for coin, b in data.items():
        df = resample(b, tf)
        z = Ind(df)
        bull, up50 = daily_regimes(regime_src[coin])
        day = df.index.floor("1D")
        z.flt = {"d200": bull.reindex(day).to_numpy(float), "d50": up50.reindex(day).to_numpy(float)}
        z.ns = df.index.as_unit("ns").asi8.astype(np.int64)
        if attach is not None:
            attach(coin, z)
        prep[coin] = z
    span_m = max(1.0, np.mean([(b.index[-1] - b.index[0]).days for b in data.values()]) / 30.4)
    V = var if var is not None else variants()
    if quick:
        V = [v for i, v in enumerate(V) if i % 12 == 0]
    rng = np.random.default_rng(20261027 + sum(map(ord, tf)))
    rows = []
    okcache = {}
    for (fam, p), flt, ex, (dname, d) in product(V, FILTERS, EXITS, DIRS.items()):
        sa, ta, ga, uo, mh = EXITS[ex]
        G, RF, NS, XT = [], [], [], []
        RG = [[] for _ in range(N_RAND)]
        RR = [[] for _ in range(N_RAND)]
        RN = [[] for _ in range(N_RAND)]
        for coin, z in prep.items():
            ent, opp = family_signals(z, fam, p, d)
            opp = np.asarray(opp, bool)
            if flt != "none":
                ent = ent[z.flt[flt][ent] == (1.0 if d > 0 else 0.0)]
            ii, xx, gg, rf = simulate(z.o, z.h, z.l, z.c, z.atr, ent.astype(np.int64), opp, d, sa, ta, ga, uo, mh)
            G.append(gg); RF.append(rf); NS.append(z.ns[ii]); XT.append(z.ns[xx])
            if not len(gg):
                continue
            key = (coin, d, flt)
            if key not in okcache:
                ok = ~np.isnan(z.atr) & (np.arange(len(z.c)) > 200)
                if flt != "none":
                    ok &= z.flt[flt] == (1.0 if d > 0 else 0.0)
                okcache[key] = np.flatnonzero(ok)
            cand = okcache[key]
            if not len(cand):
                continue
            k = int(len(gg) * 1.4) + 1
            for rep in range(N_RAND):
                re = np.unique(cand[rng.integers(0, len(cand), size=k)])
                i2, _, g2, r2 = simulate(z.o, z.h, z.l, z.c, z.atr, re.astype(np.int64), opp, d, sa, ta, ga, uo, mh)
                RG[rep].append(g2); RR[rep].append(r2); RN[rep].append(z.ns[i2])
        g, rf, ns, xt = np.concatenate(G), np.concatenate(RF), np.concatenate(NS), np.concatenate(XT)
        row = {"tf": tf, "family": fam, "params": "/".join(map(str, p)), "filter": flt, "exit": ex, "dir": dname,
               "per_month": len(g) / span_m}
        rnd = [(np.concatenate(RG[k]), np.concatenate(RR[k]), np.concatenate(RN[k])) for k in range(N_RAND) if RG[k]]
        for cname, cost in COSTS.items():
            st, r = stats_for(g, rf, ns, cost)
            row.update({f"{cname}_{k}": v for k, v in st.items()})
            if cname == MAIN:
                row["maxdd_r"] = max_dd(r, xt)
                row["sum_r"] = float(r.sum())
            for nm in ("is", "oos", "hold"):
                vals = []
                for g2, r2, n2 in rnd:
                    m = split_masks(n2)[nm]
                    vals.append(((g2[m] - 2 * cost) / r2[m]).mean() if m.any() else np.nan)
                vals = np.array(vals, float)
                fin = np.isfinite(vals)
                row[f"{cname}_rnd_{nm}_med"] = np.median(vals[fin]) if fin.any() else np.nan
                row[f"{cname}_rnd_{nm}_p95"] = np.quantile(vals[fin], .95) if fin.any() else np.nan
        rows.append(row)
    out = ROOT / "reports" / "atlas"
    out.mkdir(parents=True, exist_ok=True)
    name = name or tf
    pd.DataFrame(rows).to_csv(out / f"{name}.csv.gz", index=False, float_format="%.5f")
    periods = {c: f"{b.index[0]:%m/%Y}" for c, b in data.items()}
    (out / f"{name}.meta").write_text(f"{name}: {len(rows)} kombinací, {time.time() - t0:.0f} s, data od " +
                                    ", ".join(f"{c} {v}" for c, v in periods.items()), encoding="utf-8")
    print(f"{tf}: {len(rows)} kombinací za {time.time() - t0:.0f} s", flush=True)


# ---------------------------------------------------------------- souhrnný report
FAM_CS = {"fng": "strach a chamtivost", "ma_cross": "protnutí 2 průměrů", "price_ma": "cena × průměr", "donchian": "Donchian průraz",
          "boll_break": "Bollinger průraz", "boll_fade": "Bollinger návrat", "rsi_revert": "RSI návrat",
          "rsi_mom": "RSI momentum", "macd": "MACD", "roc": "momentum ROC", "supertrend": "Supertrend",
          "stoch": "Stochastic", "keltner": "Keltner průraz", "vol_break": "průraz s objemem",
          "candle": "svíčkové vzory", "sweep": "sweep & reclaim"}
TF_ORDER = ["15m", "1h", "2h", "4h", "6h", "12h", "1d"]


def f2(x, d=2):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{d}f}".replace(".", ",")


def pct(x):
    return f"{x:.0%}" if np.isfinite(x) else "–"


def report(parts):
    parts = Path(parts)
    res = pd.concat([pd.read_csv(f) for f in sorted(parts.glob("*.csv.gz"))], ignore_index=True)
    metas = [m.read_text(encoding="utf-8") for m in sorted(parts.glob("*.meta"))]
    M = MAIN
    name = lambda r: f"{r['tf']} {FAM_CS.get(r['family'], r['family'])} {r['params']} · {r['filter']} · {r['exit']}"

    def passes(df, c=M):
        return ((df[f"{c}_is_r"] > 0) & (df[f"{c}_oos_r"] > 0) & (df[f"{c}_hold_r"] > 0)
                & (df[f"{c}_oos_r"] > df[f"{c}_rnd_oos_p95"]) & (df[f"{c}_hold_r"] > df[f"{c}_rnd_hold_p95"])
                & (df[f"{c}_oos_t"] >= 2))

    elig = res[(res[f"{M}_is_n"] >= 150) & (res[f"{M}_oos_n"] >= 50)].copy()
    picks = elig.sort_values(f"{M}_is_t", ascending=False).groupby("dir").head(50).copy()
    picks["pass"] = passes(picks)
    L = ["# Atlas strategií – 15 rodin, 7 timeframů, poplatky MEXC (27. 10. 2026)\n"]
    L.append("Otázka: je mezi běžnými pravidlovými strategiemi na kterémkoli timeframu něco, co po poplatcích MEXC "
             "vydělává spolehlivěji než náhoda? Metoda stanovená předem je v hlavičce `research/experiments/strategy_atlas.py`.\n")
    L.append(f"- **{len(res):,} kombinací**".replace(",", " ") + " (15 rodin, 248 variant × 7 timeframů × 3 filtry × "
             "4 výstupy × long/short), 8 mincí.")
    for m in metas:
        L.append(f"- {m}")
    L.append("- Poplatky na stranu: **MEXC futures taker 0,02 % + skluz 0,03 % = 0,05 % (rozhoduje)**; MEXC spot "
             "taker 0,08 %; maker 0 % (optimistická mez); 0,15 % (dřívější testy). Funding nezapočten. Poplatky MEXC "
             "podle [MEXC, 11/2025](https://www.mexc.com/ru-RU/crypto-pulse/article/mexc-trading-fees-complete-guide-39643).")
    L.append("- IS do 12/2023 (15M od 1/2022), OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. R = výsledek po poplatcích / "
             "riziko (vzdálenost stopu; bez stopu 2 ATR).\n")

    L.append("## 1. Mají rodiny strategií výhodu? (hlavní scénář poplatků)\n")
    L.append("„Nad náhodou“ = podíl kombinací, jejichž Ø R v daném období je nad mediánem jejich vlastních náhodných "
             "vstupů (bez výhody by to bylo ~50 %). „Obě nad p95“ = OOS i HOLDOUT nad 95. percentilem náhody "
             "(čistou náhodou ~0,25 %).\n")
    L.append("| Rodina | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Obě nad p95 | Medián OOS R | Medián HOLDOUT R |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for (fam, dname), g in res.groupby(["family", "dir"]):
        both = ((g[f"{M}_oos_r"] > g[f"{M}_rnd_oos_p95"]) & (g[f"{M}_hold_r"] > g[f"{M}_rnd_hold_p95"])).mean()
        L.append(f"| {FAM_CS.get(fam, fam)} | {dname} | {len(g)} | {pct((g[f'{M}_oos_r'] > 0).mean())} | "
                 f"{pct((g[f'{M}_hold_r'] > 0).mean())} | {pct((g[f'{M}_oos_r'] > g[f'{M}_rnd_oos_med']).mean())} | "
                 f"{pct((g[f'{M}_hold_r'] > g[f'{M}_rnd_hold_med']).mean())} | {both:.1%}".replace(".", ",") + " | "
                 f"{f2(g[f'{M}_oos_r'].median())} | {f2(g[f'{M}_hold_r'].median())} |")

    L.append("\n## 2. Podle timeframu (všechny rodiny dohromady)\n")
    L.append("| TF | Směr | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Medián OOS R | Medián obchodů/měs. |")
    L.append("|---|---|---|---|---|---|---|---|")
    for tf in TF_ORDER:
        for dname in ("long", "short"):
            g = res[(res.tf == tf) & (res.dir == dname)]
            if not len(g):
                continue
            L.append(f"| {tf} | {dname} | {pct((g[f'{M}_oos_r'] > 0).mean())} | {pct((g[f'{M}_hold_r'] > 0).mean())} | "
                     f"{pct((g[f'{M}_oos_r'] > g[f'{M}_rnd_oos_med']).mean())} | "
                     f"{pct((g[f'{M}_hold_r'] > g[f'{M}_rnd_hold_med']).mean())} | {f2(g[f'{M}_oos_r'].median())} | "
                     f"{g.per_month.median():.0f} |")

    L.append("\n## 3. Kolik dělají poplatky\n")
    L.append("Podíl všech kombinací s kladným Ø R v OOS a v HOLDOUT podle výše poplatků:\n")
    L.append("| Poplatky na stranu | OOS > 0 long | OOS > 0 short | HOLDOUT > 0 long | HOLDOUT > 0 short | Projde pravidlem (ze všech) |")
    L.append("|---|---|---|---|---|---|")
    for cname, lab in (("maker", "0 % (maker, optimisticky)"), ("mexc_fut", "0,05 % (MEXC futures taker)"),
                       ("mexc_spot", "0,08 % (MEXC spot taker)"), ("old", "0,15 % (dřívější testy)")):
        lg, sh = res[res.dir == "long"], res[res.dir == "short"]
        e = res[(res[f"{cname}_is_n"] >= 150) & (res[f"{cname}_oos_n"] >= 50)]
        L.append(f"| {lab} | {pct((lg[f'{cname}_oos_r'] > 0).mean())} | {pct((sh[f'{cname}_oos_r'] > 0).mean())} | "
                 f"{pct((lg[f'{cname}_hold_r'] > 0).mean())} | {pct((sh[f'{cname}_hold_r'] > 0).mean())} | "
                 f"{int(passes(e, cname).sum())} z {len(e)} |")

    L.append("\n## 4. Výběr podle předem stanoveného pravidla (50 nejlepších podle IS t-statistiky na směr)\n")
    L.append("| Směr | Kombinace | IS n / Ø R | OOS n / Ø R | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Obch./měs. | Prošlo |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in picks.iterrows():
        L.append(f"| {r['dir']} | {name(r)} | {int(r[f'{M}_is_n'])} / {f2(r[f'{M}_is_r'])} | {int(r[f'{M}_oos_n'])} / "
                 f"{f2(r[f'{M}_oos_r'])} | {f2(r[f'{M}_oos_t'], 1)} | {f2(r[f'{M}_rnd_oos_p95'])} | "
                 f"{int(r[f'{M}_hold_n'])} / {f2(r[f'{M}_hold_r'])} | {f2(r[f'{M}_rnd_hold_p95'])} | {r['maxdd_r']:.0f} | "
                 f"{r['per_month']:.0f} | {'✅' if r['pass'] else '❌'} |")
    passed = picks[picks["pass"]]

    L.append("\n## 5. Všechny kombinace, které splní kritéria (bez pořadí v IS) – kandidáti, ne důkaz\n")
    cand = elig[passes(elig)].copy()
    exp = len(elig) * 0.05 * 0.05 * 0.3
    L.append(f"Splní je **{len(cand)}** z {len(elig)} způsobilých kombinací. Čistou náhodou by to bylo řádově "
             f"{exp:.0f} (OOS i HOLDOUT nad p95 ≈ 0,25 %, k tomu t ≥ 2 a kladné IS). Kombinace v rámci rodiny "
             "jsou si podobné, takže skutečně nezávislých nálezů je méně.\n")
    if len(cand):
        cand["score"] = np.minimum(cand[f"{M}_oos_t"], cand[f"{M}_hold_r"] / cand[f"{M}_rnd_hold_p95"].abs().clip(lower=.05))
        L.append("| Směr | Kombinace | IS Ø R | OOS n / Ø R / t | HOLDOUT n / Ø R | Max. propad R | Obch./měs. | Ø % na obchod (OOS) |")
        L.append("|---|---|---|---|---|---|---|---|")
        for _, r in cand.sort_values(f"{M}_oos_t", ascending=False).head(40).iterrows():
            L.append(f"| {r['dir']} | {name(r)} | {f2(r[f'{M}_is_r'])} | {int(r[f'{M}_oos_n'])} / {f2(r[f'{M}_oos_r'])} / "
                     f"{f2(r[f'{M}_oos_t'], 1)} | {int(r[f'{M}_hold_n'])} / {f2(r[f'{M}_hold_r'])} | {r['maxdd_r']:.0f} | "
                     f"{r['per_month']:.0f} | {f2(r[f'{M}_oos_pct'])} |")
        L.append("\nPodle rodiny a timeframu: " + "; ".join(
            f"{FAM_CS.get(k[0], k[0])} {k[1]} {k[2]}: {v}" for k, v in
            cand.groupby(["family", "tf", "dir"]).size().sort_values(ascending=False).head(15).items()) + ".\n")

    L.append("## Závěr\n")
    if len(passed):
        L.append(f"✅ **Předem stanovené pravidlo splnilo {len(passed)} kombinací:** "
                 + "; ".join(f"{r['dir']} {name(r)}" for _, r in passed.iterrows())
                 + ". Další krok je papírové ověření vedle skeneru, ne ostré zapnutí.")
    else:
        L.append("❌ **Předem stanovené pravidlo nesplnila žádná kombinace.**")
    notes = ROOT / "reports" / "strategy_atlas_notes.md"             # ruční ověření a interpretace (report je nepřepíše)
    if notes.exists():
        L.append("\n" + notes.read_text(encoding="utf-8").strip())
    L.append("\nCelá tabulka: `reports/atlas/<timeframe>.csv.gz` (všechny scénáře poplatků i náhodná srovnání).\n")
    L.append("Nejde o finanční poradenství.")
    (ROOT / "reports" / "strategy_atlas.md").write_text("\n".join(L), encoding="utf-8")
    print("Report: reports/strategy_atlas.md")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], Path(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else ROOT / "scanner" / "cache",
            quick="--quick" in sys.argv)
    else:
        report(sys.argv[2] if len(sys.argv) > 2 else ROOT / "reports" / "atlas")
