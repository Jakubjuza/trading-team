"""Mřížka klouzavých průměrů – všechny kombinace (hypotéza uživatele: short podle MA 30 × MA 60 na 4H).

Stanoveno PŘEDEM (27. 10. 2026), nic se po spuštění neladí:

  Data: hodinové svíčky OKX (spot USDT) od 1. 1. 2019 (nebo od začátku obchodování mince), 8 mincí
        BTC ETH SOL XRP ADA LINK AVAX DOGE. Vyšší timeframy vznikají přeskupením hodinových svíček.
  Mřížka (27 648 kombinací):
    timeframe   1H, 2H, 4H, 6H, 12H, 1D
    průměr      SMA, EMA
    dvojice     rychlý {5,10,20,30,40,50} × pomalý {30,50,60,100,150,200}, rychlý < pomalý (32 dvojic)
    signál      cross    – rychlý protne pomalý (short dolů, long nahoru)
                confirm  – rychlý pod pomalým A close pod oběma (první svíčka, kdy obojí platí)
                pullback – v režimu rychlý < pomalý cena vystoupí nad rychlý a další close zpět pod něj
    filtr       none | d200 (denní close vs. denní EMA 200, předchozí uzavřený den)
                | d50 (sklon denní EMA 50 ve směru obchodu, předchozí uzavřený den)
    výstup      opp       – opačné protnutí průměrů (bez stopu, max. 300 svíček)
                trail     – stop 2 ATR, trailing 3 ATR od nejlepšího close, max. 100 svíček
                target    – stop 2 ATR, cíl 3 ATR (1,5 R), max. 50 svíček
                opp_stop  – stop 1,5 ATR + opačné protnutí, max. 300 svíček
    směr        short, long (zrcadlově)
  Obchod: signál na close svíčky i, vstup na open svíčky i+1; na jedné minci jen jeden obchod dané kombinace
  naráz. Stop a cíl se kontrolují uvnitř svíčky (stop dřív než cíl), gap přes stop = vyplnění na open.
  Náklady 0,15 % na stranu (poplatek + skluz). Funding u shortu na perpu NENÍ započten (shorty ho v kryptu
  většinou dostávají, ale ne vždy). R = výsledek po nákladech / riziko (vzdálenost stopu; u „opp“ 2 ATR).
  Rozdělení podle času vstupu:  IS < 2024-01-01 ≤ OOS < 2025-07-01 ≤ HOLDOUT (do dneška).
  Náhoda: každá kombinace má vlastní srovnání – náhodné vstupy na svíčkách, kde filtr povoluje obchod, na stejné
  minci, stejným směrem, se stejným výstupem i opačným signálem a podobným počtem obchodů (10 opakování).
  Výběr (jediné rozhodovací pravidlo): z kombinací s IS ≥ 150 obchody a OOS ≥ 50 se podle IS t-statistiky
  vezme 25 nejlepších pro každý směr. PROJDE jen ta, která má Ø R > 0 v IS, OOS i HOLDOUT, v OOS i HOLDOUT
  je nad 95. percentilem náhody a OOS t-statistika ≥ 2. Nic dalšího (nejlepší podle OOS apod.) není výběr,
  jen ilustrace přeučení. Do skeneru by šla jen kombinace, která projde, a ani pak ne bez papírového ověření.

    python3 research/experiments/ma_grid.py scanner/cache            # stáhne data (poprvé), spočítá, zapíše report
    python3 research/experiments/ma_grid.py scanner/cache --quick    # malá mřížka na kontrolu
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
except ImportError:                                              # bez numba to jde, jen pomaleji
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

ROOT = Path(__file__).resolve().parents[2]
SP = Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ROOT / "scanner" / "cache")
QUICK = "--quick" in sys.argv
OUT = ROOT / "reports" / "ma_grid.md"
CSV = ROOT / "reports" / "ma_grid_all.csv.gz"
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
START = "2019-01-01"
COST = 0.0015
SPLIT_OOS, SPLIT_HOLD = pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")
OHLC = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}

TFS = ["1h", "2h", "4h", "6h", "12h", "1d"]
MAS = ["sma", "ema"]
FAST, SLOW = [5, 10, 20, 30, 40, 50], [30, 50, 60, 100, 150, 200]
PAIRS = [(f, s) for f in FAST for s in SLOW if f < s]
SIGNALS = ["cross", "confirm", "pullback"]
FILTERS = ["none", "d200", "d50"]
EXITS = {  # stop_atr, trail_atr, target_atr, opposite_cross, max_hold
    "opp": (0.0, 0.0, 0.0, True, 300),
    "trail": (2.0, 3.0, 0.0, False, 100),
    "target": (2.0, 0.0, 3.0, False, 50),
    "opp_stop": (1.5, 0.0, 0.0, True, 300),
}
DIRS = {"short": -1, "long": 1}
N_RAND = 10                                                       # náhodné vstupy na kombinaci
if QUICK:
    TFS, PAIRS = ["4h", "1d"], [(10, 50), (30, 60), (50, 200)]


# ---------------------------------------------------------------- data
def fetch_1h(coin):
    path = SP / f"okx_{coin}_1h_from2019.csv"
    if path.exists() and (time.time() - path.stat().st_mtime) < 6 * 3600:
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    import ccxt
    ex = ccxt.okx({"enableRateLimit": True})
    step = 3_600_000
    since = int(pd.Timestamp(START, tz="UTC").timestamp() * 1000)
    end = int(datetime.now(timezone.utc).timestamp() * 1000)
    rows, empty = [], 0
    while since < end:
        try:
            batch = ex.fetch_ohlcv(f"{coin}/USDT", "1h", since=since, limit=100)
        except Exception as exc:                                  # krátký výpadek API – zkusit znovu
            print(f"  {coin} {pd.Timestamp(since, unit='ms')}: {exc.__class__.__name__}, znovu", flush=True)
            time.sleep(3)
            continue
        if not batch:
            empty += 1
            since += 100 * step                                   # mince ještě neobchodovala / díra v datech
            if empty > 2000:
                break
            continue
        rows += batch
        nxt = batch[-1][0] + step
        since = nxt if nxt > since else since + 100 * step
    df = pd.DataFrame(rows, columns=["t", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("t")
    df.index = pd.to_datetime(df.pop("t"), unit="ms", utc=True)
    df = df.sort_index()
    SP.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def frames(h1, tf):
    tf = {"1d": "1D"}.get(tf, tf)
    df = h1[list(OHLC)].resample(tf).agg(OHLC).dropna() if tf != "1h" else h1[list(OHLC)].dropna()
    now = datetime.now(timezone.utc)
    return df[df.index + pd.Timedelta(tf) <= now]                    # jen uzavřené svíčky


def daily_regimes(h1):
    """Denní filtry z PŘEDCHOZÍHO uzavřeného dne: close nad EMA200, EMA50 roste."""
    d = frames(h1, "1D")
    ema200 = d["Close"].ewm(span=200, adjust=False, min_periods=200).mean()
    ema50 = d["Close"].ewm(span=50, adjust=False, min_periods=50).mean()
    bull200 = (d["Close"] > ema200).where(ema200.notna())
    up50 = (ema50 > ema50.shift(1)).where(ema50.shift(1).notna())
    # hodnota dne D je známá až po jeho konci → platí pro svíčky dne D+1
    bull200.index = bull200.index + pd.Timedelta("1D")
    up50.index = up50.index + pd.Timedelta("1D")
    return bull200, up50


def align(series, index):
    """Denní řadu (platnou od začátku dne) přiřadí svíčkám podle dne jejich začátku."""
    day = index.floor("1D")
    return series.reindex(day).to_numpy(dtype=float)


# ---------------------------------------------------------------- simulace
@njit(cache=True)
def simulate(o, h, l, c, atr, entries, opp, d, stop_atr, trail_atr, tgt_atr, use_opp, max_hold, cost):
    n = len(o)
    m = len(entries)
    out_i = np.empty(m, np.int64)
    out_x = np.empty(m, np.int64)
    out_r = np.empty(m)
    out_p = np.empty(m)
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
        net = d * (xp / px - 1.0) - 2.0 * cost
        out_i[k] = e
        out_x[k] = xb
        out_p[k] = net
        out_r[k] = net / (risk / px)
        k += 1
        last_exit = xb
    return out_i[:k], out_x[:k], out_r[:k], out_p[:k]


def ma(close, kind, n):
    if kind == "sma":
        return close.rolling(n, min_periods=n).mean().to_numpy()
    return close.ewm(span=n, adjust=False, min_periods=n).mean().to_numpy()


def signals(c, fast, slow, d, sig):
    ok = ~(np.isnan(fast) | np.isnan(slow))
    side = (fast < slow) if d < 0 else (fast > slow)
    side &= ok
    prev = np.r_[False, side[:-1]]
    if sig == "cross":
        ent = side & ~prev & np.r_[False, ok[:-1]]
    elif sig == "confirm":
        beyond = (c < np.fmin(fast, slow)) if d < 0 else (c > np.fmax(fast, slow))
        cond = side & beyond
        ent = cond & ~np.r_[False, cond[:-1]]
    else:  # pullback: cena se vrátí přes rychlý průměr proti trendu a další close zpět ve směru
        was_against = np.r_[False, ((c > fast) if d < 0 else (c < fast))[:-1]]
        back = (c < fast) if d < 0 else (c > fast)
        ent = side & np.r_[False, side[:-1]] & was_against & back
    other = (fast > slow) if d < 0 else (fast < slow)
    other &= ok
    opp = other & ~np.r_[False, other[:-1]]
    return np.flatnonzero(ent), opp


def split_masks(times):
    a, b = SPLIT_OOS.value, SPLIT_HOLD.value
    return {"is": times < a, "oos": (times >= a) & (times < b), "hold": times >= b}


def stats(r, p, times):
    out = {}
    a, b = SPLIT_OOS.value, SPLIT_HOLD.value                     # times = ns od epochy (int64)
    for name, mask in (("is", times < a), ("oos", (times >= a) & (times < b)),
                       ("hold", times >= b), ("all", np.ones(len(r), bool))):
        x = r[mask]
        n = len(x)
        mean = x.mean() if n else np.nan
        sd = x.std(ddof=1) if n > 1 else np.nan
        gains, losses = x[x > 0].sum(), -x[x < 0].sum()
        out.update({f"{name}_n": n, f"{name}_r": mean, f"{name}_ci": 1.96 * sd / np.sqrt(n) if n > 1 else np.nan,
                    f"{name}_t": mean / (sd / np.sqrt(n)) if n > 1 and sd > 0 else np.nan,
                    f"{name}_sum": x.sum(), f"{name}_win": (x > 0).mean() if n else np.nan,
                    f"{name}_pf": gains / losses if losses > 0 else np.nan,
                    f"{name}_pct": p[mask].mean() * 100 if n else np.nan})
    return out


def max_dd(r, xt):
    if not len(r):
        return np.nan
    eq = np.cumsum(r[np.argsort(xt, kind="stable")])
    return float((np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max())


# ---------------------------------------------------------------- běh
def main():
    t0 = time.time()
    data = {}
    for coin in COINS:
        h1 = fetch_1h(coin)
        print(f"{coin}: {len(h1)} hodinových svíček {h1.index[0]:%Y-%m-%d} → {h1.index[-1]:%Y-%m-%d}", flush=True)
        data[coin] = h1
    periods = {c: (h.index[0], h.index[-1]) for c, h in data.items()}

    rows = []
    rng = np.random.default_rng(20261027)
    span_months = max(1.0, sum((b - a).days for a, b in periods.values()) / 8 / 30.4)
    for tf in TFS:
        prep = {}
        for coin, h1 in data.items():
            df = frames(h1, tf)
            close = df["Close"]
            tr = pd.concat([df["High"] - df["Low"], (df["High"] - close.shift()).abs(),
                            (df["Low"] - close.shift()).abs()], axis=1).max(axis=1)
            atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean().to_numpy()
            bull200, up50 = daily_regimes(h1)
            prep[coin] = {
                "o": df["Open"].to_numpy(float), "h": df["High"].to_numpy(float), "l": df["Low"].to_numpy(float),
                "c": close.to_numpy(float), "atr": atr, "idx": df.index, "ns": df.index.as_unit("ns").asi8.astype(np.int64),
                "ma": {(k, n): ma(close, k, n) for k in MAS for n in set(FAST) | set(SLOW)},
                "d200": align(bull200, df.index), "d50": align(up50, df.index),
            }
        okmask = {}
        for kind, (f, s), sig, flt, ex, (dname, d) in product(MAS, PAIRS, SIGNALS, FILTERS, EXITS, DIRS.items()):
            stop_atr, trail_atr, tgt_atr, use_opp, max_hold = EXITS[ex]
            R, P, IT, XT = [], [], [], []
            RR = [[] for _ in range(N_RAND)]
            RT = [[] for _ in range(N_RAND)]
            for coin, z in prep.items():
                ent, opp = signals(z["c"], z["ma"][(kind, f)], z["ma"][(kind, s)], d, sig)
                if flt != "none":
                    ent = ent[z[flt][ent] == (1.0 if d > 0 else 0.0)]
                ii, xx, rr, pp = simulate(z["o"], z["h"], z["l"], z["c"], z["atr"], ent.astype(np.int64), opp, d,
                                          stop_atr, trail_atr, tgt_atr, use_opp, max_hold, COST)
                R.append(rr); P.append(pp)
                IT.append(z["ns"][ii]); XT.append(z["ns"][xx])
                # náhoda pro TUTO kombinaci: stejná mince, směr, filtr, výstup i opačný signál, podobný počet obchodů
                key = (coin, d, flt, s)
                if key not in okmask:
                    ok = ~np.isnan(z["atr"]) & ~np.isnan(z["ma"][("sma", s)])
                    if flt != "none":
                        ok &= z[flt] == (1.0 if d > 0 else 0.0)
                    okmask[key] = np.flatnonzero(ok)
                cand = okmask[key]
                if len(rr) and len(cand):
                    k = int(len(rr) * 1.4) + 1
                    for rep in range(N_RAND):
                        re = np.unique(cand[rng.integers(0, len(cand), size=k)])
                        i2, _, r2, _ = simulate(z["o"], z["h"], z["l"], z["c"], z["atr"], re.astype(np.int64), opp, d,
                                                stop_atr, trail_atr, tgt_atr, use_opp, max_hold, COST)
                        RR[rep].append(r2); RT[rep].append(z["ns"][i2])
            r, p = np.concatenate(R), np.concatenate(P)
            it, xt = np.concatenate(IT), np.concatenate(XT)
            row = {"tf": tf, "ma": kind, "fast": f, "slow": s, "signal": sig, "filter": flt, "exit": ex, "dir": dname}
            row.update(stats(r, p, it))
            row["maxdd_r"] = max_dd(r, xt)
            row["per_month"] = len(r) / span_months
            rs = {"is": [], "oos": [], "hold": []}
            for rep in range(N_RAND):
                if not RR[rep]:
                    continue
                r2, t2 = np.concatenate(RR[rep]), np.concatenate(RT[rep])
                for nm, m in split_masks(t2).items():
                    rs[nm].append(r2[m].mean() if m.any() else np.nan)
            for nm, v in rs.items():
                v = np.array(v, float)
                row[f"rnd_{nm}_med"] = np.nanmedian(v) if np.isfinite(v).any() else np.nan
                row[f"rnd_{nm}_p95"] = np.nanquantile(v, .95) if np.isfinite(v).any() else np.nan
            rows.append(row)
        print(f"{tf}: hotovo, {len(rows)} kombinací, {time.time() - t0:.0f} s", flush=True)

    res = pd.DataFrame(rows)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(CSV, index=False, float_format="%.5f")
    write_report(res, periods, time.time() - t0)
    print(f"Report: {OUT}")


# ---------------------------------------------------------------- report
def f2(x, d=2):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.{d}f}".replace(".", ",")


def write_report(res, periods, secs):
    res = res.assign(oos95=res.rnd_oos_p95, hold95=res.rnd_hold_p95)
    elig = res[(res.is_n >= 150) & (res.oos_n >= 50)].copy()
    picks = (elig.sort_values("is_t", ascending=False).groupby("dir").head(25)).copy()
    picks["pass"] = ((picks.is_r > 0) & (picks.oos_r > 0) & (picks.hold_r > 0) & (picks.oos_r > picks.oos95)
                     & (picks.hold_r > picks.hold95) & (picks.oos_t >= 2))
    name = lambda r: f"{r['tf']} {r['ma'].upper()} {r['fast']}/{r['slow']} · {r['signal']} · {r['filter']} · {r['exit']}"
    L = []
    L.append("# Mřížka klouzavých průměrů – všechny kombinace (27. 10. 2026)\n")
    L.append("Otázka: dá se short (a long) vést podle protnutí dvou klouzavých průměrů, např. MA 30 × MA 60 na 4H, "
             "lépe než dnešní denní strategie s filtrem EMA 200? Metoda stanovená předem je v hlavičce skriptu "
             "`research/experiments/ma_grid.py`; nic se po spuštění neladilo.\n")
    L.append(f"- **{len(res):,} kombinací**".replace(",", " ") + " (6 timeframů × SMA/EMA × 32 dvojic délek × 3 signály × "
             "3 filtry × 4 výstupy × long/short), 8 mincí, hodinová data OKX"
             + "; " + ", ".join(f"{c} od {a:%m/%Y}" for c, (a, b) in periods.items()) + ".")
    L.append("- Náklady 0,15 % na stranu, funding u shortů nezapočten. R = výsledek / riziko (u výstupu „opp“ 2 ATR).")
    L.append("- IS do 12/2023, OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. Výpočet trval "
             f"{secs / 60:.0f} min.\n")

    L.append("## 1. Celá rodina: mají průměry vůbec nějakou výhodu?\n")
    L.append("Podíl kombinací s kladným Ø R a medián Ø R; „náhoda“ = medián Ø R náhodných vstupů, které má každá "
             "kombinace vlastní (stejná mince, směr, filtr, výstup i opačný signál, podobný počet obchodů, "
             "10 opakování).\n")
    L.append("| Směr | TF | Kombinací | IS > 0 | OOS > 0 | HOLDOUT > 0 | Medián OOS R | Náhoda OOS R | Medián HOLDOUT R | Náhoda HOLDOUT R | Obchodů/měs. (medián) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for (dname, tf), g in res.groupby(["dir", "tf"], sort=False):
        L.append(f"| {dname} | {tf} | {len(g)} | {(g.is_r > 0).mean():.0%} | {(g.oos_r > 0).mean():.0%} | "
                 f"{(g.hold_r > 0).mean():.0%} | {f2(g.oos_r.median())} | {f2(g.rnd_oos_med.median())} | "
                 f"{f2(g.hold_r.median())} | {f2(g.rnd_hold_med.median())} | {g.per_month.median():.0f} |")

    L.append("\n## 2. Co rozhoduje (medián OOS R podle jedné volby, ostatní volby smíchané)\n")
    for col in ["exit", "filter", "signal", "ma"]:
        t = res.groupby([col, "dir"]).oos_r.median().unstack()
        L.append(f"**{col}:** " + "; ".join(f"{k}: short {f2(v.get('short'))}, long {f2(v.get('long'))}"
                                             for k, v in t.iterrows()) + "  ")
    L.append("")

    L.append("## 3. Výběr podle předem stanoveného pravidla (25 nejlepších podle IS t-statistiky na směr)\n")
    L.append("| Směr | Kombinace | IS n / Ø R | OOS n / Ø R ± CI | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Prošlo |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in picks.iterrows():
        L.append(f"| {r.dir} | {name(r)} | {r.is_n} / {f2(r.is_r)} | {r.oos_n} / {f2(r.oos_r)} ± {f2(r.oos_ci).lstrip('+')} | "
                 f"{f2(r.oos_t, 1)} | {f2(r.oos95)} | {r.hold_n} / {f2(r.hold_r)} | {f2(r.hold95)} | {r.maxdd_r:.0f} | "
                 f"{'✅' if r['pass'] else '❌'} |")
    passed = picks[picks["pass"]]

    L.append("\n## 4. Vaše hypotéza: MA 30 × MA 60 na 4H\n")
    L.append("| Průměr | Směr | Signál | Filtr | Výstup | IS n / Ø R | OOS n / Ø R | HOLDOUT n / Ø R | Obchodů/měs. |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    h = res[(res.tf == "4h") & (res.fast == 30) & (res.slow == 60)].sort_values(["dir", "ma", "signal", "filter", "exit"])
    for _, r in h.iterrows():
        L.append(f"| {r['ma'].upper()} | {r['dir']} | {r['signal']} | {r['filter']} | {r['exit']} | {r.is_n} / {f2(r.is_r)} | "
                 f"{r.oos_n} / {f2(r.oos_r)} | {r.hold_n} / {f2(r.hold_r)} | {r.per_month:.0f} |")
    hs = h[h.dir == "short"]
    L.append(f"\nShort MA 30 × 60 na 4H: {len(hs)} variant, kladné OOS {(hs.oos_r > 0).sum()}, kladné HOLDOUT "
             f"{(hs.hold_r > 0).sum()}, kladné ve všech třech obdobích {((hs.is_r > 0) & (hs.oos_r > 0) & (hs.hold_r > 0)).sum()}.\n")

    L.append("## 5. Pro srovnání: nejlepší podle OOS (vybráno zpětně = ukázka přeučení, NE výběr)\n")
    L.append("| Směr | Kombinace | IS Ø R | OOS n / Ø R | HOLDOUT n / Ø R |")
    L.append("|---|---|---|---|---|")
    for _, r in elig.sort_values("oos_r", ascending=False).groupby("dir").head(5).iterrows():
        L.append(f"| {r.dir} | {name(r)} | {f2(r.is_r)} | {r.oos_n} / {f2(r.oos_r)} | {r.hold_n} / {f2(r.hold_r)} |")
    keep = elig.sort_values("oos_r", ascending=False).groupby("dir").head(5)
    L.append(f"\nZ těchto zpětně nejlepších zůstalo kladných v HOLDOUT {(keep.hold_r > 0).sum()} z {len(keep)}.\n")

    L.append("## Závěr\n")
    if len(passed):
        L.append(f"✅ **Kritéria splnilo {len(passed)} kombinací:** " + "; ".join(f"{r.dir} {name(r)}" for _, r in passed.iterrows())
                 + ". Další krok je papírové ověření vedle skeneru, ne ostré zapnutí.")
    else:
        L.append("❌ **Žádná kombinace nesplnila předem stanovená kritéria.** Skener se nemění.")
    L.append("\nCelá tabulka všech kombinací včetně jejich náhodných srovnání: `reports/ma_grid_all.csv.gz`.\n")
    L.append("Nejde o finanční poradenství.")
    OUT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
