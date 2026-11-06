#!/usr/bin/env python3
"""Downtown – divoké strategie na papíře (páka, likvidace, reinvestice). ODDĚLENÉ od desku.

Proč: uživatel (6. 11. 2026) chce vedle přísné laboratoře vidět i strategie, které testem neprojdou, ale můžou
hodně vydělat – a stejně tak účet smazat. Downtown NIKDY nesahá na skener, registr, riziko, demo ani peníze;
výsledky jsou jen papírové a slouží jako pozorování, ne jako signál.

Pravidla stanovená PŘEDEM (6. 11. 2026), po spuštění se neladí:

  Účet: každá strategie má vlastní papírový účet 1 000 USDT, perpetual futures, izolovaná marže, reinvestice.
  Vstup na open svíčky po signálu (signál na close), skluz 0,03 % a poplatek 0,05 % (MEXC futures, taker) na stranu,
  funding 0,01 % za 8 h z hodnoty pozice (longy platí, shorty dostávají).
  Likvidace: cena sáhne na entry × (1 ∓ (1/páka − 0,5 %)) → ztráta celé marže pozice. V jedné svíčce se nejdřív
  kontroluje likvidace a stop (horší případ), pak cíl; gap přes stop = vyplnění na open.
  Bankrot: když účet klesne pod 100 USDT (10 % startu), vloží se nových 1 000 USDT (počítá se „vloženo celkem“).
  Čistý výsledek = hodnota účtu − vloženo celkem.
  Zpětný test: svíčky OKX (spot USDT jako cenová řada), od 1. 1. 2023 do poslední uzavřené svíčky.
  Živý papír: totéž od LIVE_START, s novým účtem 1 000 USDT (indikátory se počítají i z dat před startem).

  Strategie (mince v pořadí BTC ETH SOL XRP ADA LINK AVAX DOGE; při více signálech naráz vyhrává první):
    scalp20    15m BTC/ETH/SOL · long RSI(2) < 10 nad EMA200, short RSI(2) > 90 pod EMA200 · cíl 0,4 %, stop 0,3 %,
               max 16 svíček · páka 20×, celá marže
    break25    1h 8 mincí · průraz 20svíčkového max/min ve směru EMA200 · stop 1 ATR, trailing 2 ATR, max 48 svíček
               · páka 25×, celá marže
    ko50       1h 8 mincí · jen long: close nad 24svíčkovým maximem a nad EMA200 · stop 0,8 %, cíl 3 %, max 24 svíček
               · páka 50×, celá marže
    marti10    1h BTC · long po červené svíčce s RSI(14) < 40 · cíl 1 %, stop 1 %, max 24 svíček · páka 10×,
               marže 1/64 účtu, po každé ztrátě dvojnásobná (max. celý účet), po zisku nebo 7. ztrátě zpět na 1/64
    dip15      1h 8 mincí · long po svíčce s propadem (close − open) < −3 ATR · cíl 1,5 ATR, stop 1,5 ATR, max 12
               svíček · páka 15×, celá marže
    rot5       4h 8 mincí · drží long mince s nejlepším výnosem za 24 h (6 svíček), když je kladný, jinak hotovost;
               přepíná na close · páka 5×, celá marže
    hodl3      4h BTC · stále long · páka 3×, celá marže (srovnání: co udělá „jen držet s pákou“)

    python3 research/downtown.py [cache_dir]        → research/downtown.json + reports/downtown.md
"""
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "research" / "downtown.json"
OUT_MD = ROOT / "reports" / "downtown.md"
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
BT_START = "2023-01-01"
LIVE_START = "2026-11-07"
WARMUP = "2022-10-01"           # indikátory (EMA200 na 15m/1h/4h) mají dost historie
START_CASH = 1000.0
FEE, SLIP, MM = 0.0005, 0.0003, 0.005
FUND_8H = 0.0001
BROKE = 100.0                   # pod 10 % startu je účet „mrtvý“ → nový vklad
TF_H = {"15m": 0.25, "1h": 1.0, "4h": 4.0}

STRATS = {
    "scalp20": {"name": "Scalper 15m ×20", "tf": "15m", "coins": ["BTC", "ETH", "SOL"], "lev": 20,
                "tag": "malé cíle, hodně obchodů", "rules": "RSI(2) < 10 nad EMA200 → long, > 90 pod EMA200 → short · cíl 0,4 %, stop 0,3 %, max 4 h"},
    "break25": {"name": "Průraz ×25", "tf": "1h", "coins": COINS, "lev": 25,
                "tag": "chytá rozjeté pohyby", "rules": "průraz 20h max/min ve směru EMA200 · stop 1 ATR, trailing 2 ATR, max 48 h"},
    "ko50": {"name": "Knock-out ×50", "tf": "1h", "coins": COINS, "lev": 50,
             "tag": "pohyb 1,5 % proti = likvidace", "rules": "jen long nad 24h maximem a EMA200 · stop 0,8 %, cíl 3 %, max 24 h"},
    "marti10": {"name": "Martingale ×10", "tf": "1h", "coins": ["BTC"], "lev": 10,
                "tag": "po ztrátě zdvojnásobí sázku", "rules": "long po červené svíčce s RSI(14) < 40 · cíl 1 %, stop 1 % · marže 1/64 účtu, po ztrátě ×2"},
    "dip15": {"name": "Lovec propadů ×15", "tf": "1h", "coins": COINS, "lev": 15,
              "tag": "kupuje do paniky", "rules": "long po svíčce s propadem větším než 3 ATR · cíl 1,5 ATR, stop 1,5 ATR, max 12 h"},
    "rot5": {"name": "Rotace hybnosti ×5", "tf": "4h", "coins": COINS, "lev": 5,
             "tag": "vždy v nejsilnější minci", "rules": "drží long mince s nejlepším výnosem za 24 h (když je kladný) · přepíná po 4 h"},
    "hodl3": {"name": "BTC ×3, jen drž", "tf": "4h", "coins": ["BTC"], "lev": 3,
              "tag": "srovnání bez obchodování", "rules": "stále long BTC s pákou 3× · po likvidaci nový účet a znovu long"},
}


# ---------------------------------------------------------------- data
def fetch(coin, tf, cache):
    """Hodinové / 15m svíčky OKX od WARMUP s průběžným doplňováním do cache (CSV)."""
    base = "15m" if tf == "15m" else "1h"
    path = Path(cache) / f"dt_okx_{coin}_{base}.csv"
    step = {"1h": 3_600_000, "15m": 900_000}[base]
    old = None
    since = int(pd.Timestamp(WARMUP, tz="UTC").timestamp() * 1000)
    if path.exists():
        old = pd.read_csv(path, index_col=0)
        old.index = pd.to_datetime(old.index, utc=True)
        if len(old):
            since = int(old.index[-1].timestamp() * 1000) + step
    import ccxt
    ex = ccxt.okx({"enableRateLimit": True})
    end = int(datetime.now(timezone.utc).timestamp() * 1000)
    rows, errs, empty = [], 0, 0
    while since < end:
        try:
            batch = ex.fetch_ohlcv(f"{coin}/USDT", base, since=since, limit=100)
        except Exception as exc:  # noqa: BLE001
            errs += 1
            print(f"  {coin} {base} {pd.Timestamp(since, unit='ms')}: {exc.__class__.__name__}", flush=True)
            if errs > 60:
                break
            time.sleep(3)
            continue
        if not batch:
            empty += 1
            since += 100 * step
            if empty > 50:
                break
            continue
        rows += batch
        nxt = batch[-1][0] + step
        since = nxt if nxt > since else since + 100 * step
    new = pd.DataFrame(rows, columns=["t", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("t")
    new.index = pd.to_datetime(new.pop("t"), unit="ms", utc=True)
    df = pd.concat([old, new]) if old is not None else new
    df = df[~df.index.duplicated(keep="last")].sort_index()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def resample(df, tf):
    if tf in ("15m", "1h"):
        out = df
    else:
        out = df.resample(tf).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    return out[out.index + pd.Timedelta(tf) <= datetime.now(timezone.utc)]


# ---------------------------------------------------------------- ukazatele
def atr(d, n=14):
    pc = d["Close"].shift(1)
    tr = pd.concat([d["High"] - d["Low"], (d["High"] - pc).abs(), (d["Low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def rsi(c, n):
    ch = c.diff()
    up = ch.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-ch.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def signals(sid, d):
    """Vrátí pole směru vstupu (+1/−1/0) na close každé svíčky (pro „target“ strategie skóre)."""
    c, o = d["Close"], d["Open"]
    ema = c.ewm(span=200, adjust=False, min_periods=200).mean()
    if sid == "scalp20":
        r = rsi(c, 2)
        return np.where((r < 10) & (c > ema), 1, np.where((r > 90) & (c < ema), -1, 0))
    if sid == "break25":
        hi, lo = d["High"].rolling(20).max().shift(1), d["Low"].rolling(20).min().shift(1)
        return np.where((c > hi) & (c > ema), 1, np.where((c < lo) & (c < ema), -1, 0))
    if sid == "ko50":
        hi = d["High"].rolling(24).max().shift(1)
        return np.where((c > hi) & (c > ema), 1, 0)
    if sid == "marti10":
        return np.where((c < o) & (rsi(c, 14) < 40), 1, 0)
    if sid == "dip15":
        a = atr(d).shift(1)
        return np.where((c - o) < -3 * a, 1, 0)
    raise KeyError(sid)


EXITS = {  # stop %, cíl %, stop ATR, cíl ATR, trailing ATR, max svíček
    "scalp20": (0.003, 0.004, None, None, None, 16),
    "break25": (None, None, 1.0, None, 2.0, 48),
    "ko50": (0.008, 0.03, None, None, None, 24),
    "marti10": (0.01, 0.01, None, None, None, 24),
    "dip15": (None, None, 1.5, 1.5, None, 12),
}


# ---------------------------------------------------------------- účet
class Account:
    def __init__(self, cash=START_CASH):
        self.eq, self.dep, self.liqs, self.wipes = cash, cash, 0, 0
        self.trades = []

    def refill(self, t):
        if self.eq < BROKE:
            self.wipes += 1
            self.dep += START_CASH
            self.eq += START_CASH
            self.trades.append({"t": t, "kind": "vklad", "pnl": 0.0})


def run(sid, frames, trade_from, cash=START_CASH):
    """Projde svíčky jedné strategie a vrátí účet, denní křivku a otevřenou pozici."""
    cfg = STRATS[sid]
    lev, tf, hours = cfg["lev"], cfg["tf"], TF_H[cfg["tf"]]
    coins = [c for c in cfg["coins"] if c in frames]
    idx = frames[coins[0]].index
    for c in coins[1:]:
        idx = idx.union(frames[c].index)
    F = {c: frames[c].reindex(idx) for c in coins}
    O = {c: F[c]["Open"].to_numpy(float) for c in coins}
    H = {c: F[c]["High"].to_numpy(float) for c in coins}
    L = {c: F[c]["Low"].to_numpy(float) for c in coins}
    C = {c: F[c]["Close"].to_numpy(float) for c in coins}
    A = {c: atr(F[c]).to_numpy(float) for c in coins}
    target = sid in ("rot5", "hodl3")
    if target:
        if sid == "rot5":
            score = pd.DataFrame({c: F[c]["Close"].pct_change(6) for c in coins}).to_numpy(float)
        else:
            score = np.ones((len(idx), 1))
    else:
        S = {c: np.asarray(signals(sid, F[c]), float) for c in coins}
    t_from = pd.Timestamp(trade_from, tz="UTC")
    start_i = int(np.searchsorted(idx.values, t_from.to_datetime64()))
    acc = Account(cash)
    pos = None
    marti_k = 0
    curve = []
    liq_mult = 1 / lev - MM
    fund = FUND_8H * hours / 8

    def close_pos(i, px, why):
        nonlocal pos, marti_k
        d, c = pos["dir"], pos["coin"]
        fill = px * (1 - d * SLIP)
        ret = d * (fill / pos["entry"] - 1)
        notional_exit = pos["notional"] * fill / pos["entry"]
        pnl = pos["notional"] * ret - notional_exit * FEE - pos["fund"]
        pnl = max(pnl, -pos["margin"])
        acc.eq += pnl
        acc.trades.append({"t": idx[i].isoformat(), "kind": why, "coin": c, "dir": d, "opened": pos["t0"],
                           "entry": round(pos["entry"], 6), "exit": round(fill, 6), "pnl": round(pnl, 2),
                           "ret_pct": round(100 * pnl / pos["margin"], 1)})
        if sid == "marti10":
            marti_k = 0 if pnl > 0 or marti_k >= 6 else marti_k + 1
        pos = None
        acc.refill(idx[i].isoformat())

    def liquidate(i):
        nonlocal pos, marti_k
        acc.liqs += 1
        acc.eq -= pos["margin"]
        acc.trades.append({"t": idx[i].isoformat(), "kind": "likvidace", "coin": pos["coin"], "dir": pos["dir"],
                           "opened": pos["t0"], "entry": round(pos["entry"], 6), "exit": round(pos["liq"], 6),
                           "pnl": round(-pos["margin"], 2), "ret_pct": -100.0})
        if sid == "marti10":
            marti_k = 0 if marti_k >= 6 else marti_k + 1
        pos = None
        acc.refill(idx[i].isoformat())

    def open_pos(i, c, d):
        nonlocal pos
        frac = min(1.0, 2 ** marti_k / 64) if sid == "marti10" else 1.0
        px = O[c][i]
        if not np.isfinite(px) or acc.eq < BROKE:
            return
        entry = px * (1 + d * SLIP)
        margin = acc.eq * frac
        notional = margin * lev
        acc.eq -= notional * FEE
        margin = min(margin, acc.eq)
        a = A[c][i - 1] if i > 0 else np.nan
        sp, tp, sa, ta, tr, mx = EXITS.get(sid, (None, None, None, None, None, 10 ** 9))
        stop = entry * (1 - d * sp) if sp else (entry - d * sa * a if sa and np.isfinite(a) else None)
        tgt = entry * (1 + d * tp) if tp else (entry + d * ta * a if ta and np.isfinite(a) else None)
        pos = {"coin": c, "dir": d, "entry": entry, "margin": margin, "notional": notional, "stop": stop, "tgt": tgt,
               "trail": (tr * a) if tr and np.isfinite(a) else None, "best": entry, "bars": 0, "max": mx, "fund": 0.0,
               "liq": entry * (1 - d * liq_mult), "t0": idx[i].isoformat(), "i0": i}

    for i in range(max(start_i, 1), len(idx)):
        # 1) rozhodnutí z close předchozí svíčky → vstup / přepnutí na open svíčky i
        j = i - 1
        if target:
            row = score[j]
            want = None
            if sid == "hodl3":
                want = (coins[0], 1)
            elif np.isfinite(row).any() and np.nanmax(row) > 0:
                want = (coins[int(np.nanargmax(row))], 1)
            if pos and (want is None or (pos["coin"], pos["dir"]) != want):
                close_pos(i, O[pos["coin"]][i], "přepnutí")
            if pos is None and want and j >= start_i - 1:
                open_pos(i, *want)
        elif pos is None:
            for c in coins:
                s = S[c][j]
                if s and np.isfinite(O[c][i]):
                    open_pos(i, c, int(s))
                    break
        # 2) průběh svíčky i
        if pos:
            c, d = pos["coin"], pos["dir"]
            o, h, l, cl = O[c][i], H[c][i], L[c][i], C[c][i]
            if not np.isfinite(cl):
                continue
            pos["fund"] += pos["notional"] * fund * d
            adverse = l if d > 0 else h
            fav = h if d > 0 else l
            hit = lambda lvl, x: lvl is not None and ((x <= lvl) if d > 0 else (x >= lvl))  # noqa: E731
            if hit(pos["liq"], o) or (hit(pos["liq"], adverse) and not (pos["stop"] is not None and d * (pos["stop"] - pos["liq"]) > 0)):
                liquidate(i)
            elif pos["stop"] is not None and hit(pos["stop"], o):
                close_pos(i, o, "stop")
            elif pos["stop"] is not None and hit(pos["stop"], adverse):
                close_pos(i, pos["stop"], "stop")
            elif pos["tgt"] is not None and (h >= pos["tgt"] if d > 0 else l <= pos["tgt"]):
                close_pos(i, pos["tgt"], "cíl")
            else:
                pos["bars"] += 1
                if pos["trail"]:
                    pos["best"] = max(pos["best"], cl) if d > 0 else min(pos["best"], cl)
                    ns = pos["best"] - d * pos["trail"]
                    pos["stop"] = ns if pos["stop"] is None else (max(pos["stop"], ns) if d > 0 else min(pos["stop"], ns))
                if pos["bars"] >= pos["max"]:
                    close_pos(i, cl, "čas")
        # 3) hodnota účtu na close
        val = acc.eq
        if pos and np.isfinite(C[pos["coin"]][i]):
            c, d = pos["coin"], pos["dir"]
            val += max(-pos["margin"], pos["notional"] * d * (C[c][i] / pos["entry"] - 1) - pos["fund"])
        curve.append((idx[i], val, acc.dep))
    return acc, curve, pos, idx


# ---------------------------------------------------------------- souhrn
def summarize(acc, curve, pos, idx):
    if not curve:
        return {"n_trades": 0, "equity": START_CASH, "deposited": START_CASH, "net": 0.0}
    cv = pd.DataFrame(curve, columns=["t", "val", "dep"]).set_index("t")
    # propad v rámci jednoho života účtu (vklad = nový začátek)
    life = (cv["dep"].diff().fillna(0) > 0).cumsum()
    peak = cv.groupby(life)["val"].cummax()
    dd = float((cv["val"] / peak - 1).min())
    trades = [x for x in acc.trades if x.get("kind") not in ("vklad",)]
    pnl = np.array([x["pnl"] for x in trades]) if trades else np.array([])
    daily = cv.resample("1D").last().dropna()

    def period_ret(freq):
        # výsledek období = změna (účet − vklady) / (účet na začátku + vklady v období) → nikdy pod −100 %
        e = cv.resample(freq).last().dropna()
        v0 = pd.concat([pd.Series([START_CASH], index=[cv.index[0]]), e["val"].iloc[:-1]]).to_numpy()
        d0 = pd.concat([pd.Series([START_CASH], index=[cv.index[0]]), e["dep"].iloc[:-1]]).to_numpy()
        pnl = (e["val"] - e["dep"]).to_numpy() - (v0 - d0)
        base = v0 + (e["dep"].to_numpy() - d0)
        return pd.Series(np.where(base > 0, pnl / base, np.nan), index=e.index)

    mret = period_ret("ME").dropna()
    yret = period_ret("YE")
    years = {str(t.year): (round(100 * float(v), 1) if np.isfinite(v) else None) for t, v in yret.items()}
    step = max(1, len(daily) // 160)
    pts = daily.iloc[::step]
    if len(daily) and pts.index[-1] != daily.index[-1]:
        pts = pd.concat([pts, daily.iloc[-1:]])
    out = {
        "start": cv.index[0].date().isoformat(), "end": cv.index[-1].isoformat(),
        "equity": round(float(cv["val"].iloc[-1]), 2), "deposited": round(float(cv["dep"].iloc[-1]), 2),
        "net": round(float(cv["val"].iloc[-1] - cv["dep"].iloc[-1]), 2),
        "net_pct": round(100 * float(cv["val"].iloc[-1] - cv["dep"].iloc[-1]) / float(cv["dep"].iloc[-1]), 1),
        "peak_equity": round(float(cv["val"].max()), 2), "max_dd_pct": round(100 * dd, 1),
        "liquidations": acc.liqs, "wipes": acc.wipes, "n_trades": len(trades),
        "win_pct": round(100 * float((pnl > 0).mean()), 1) if len(pnl) else None,
        "best_trade": round(float(pnl.max()), 2) if len(pnl) else None,
        "worst_trade": round(float(pnl.min()), 2) if len(pnl) else None,
        "best_month_pct": round(100 * float(mret.max()), 1) if len(mret) else None,
        "worst_month_pct": round(100 * float(mret.min()), 1) if len(mret) else None,
        "trades_per_month": round(len(trades) / max(1.0, (cv.index[-1] - cv.index[0]).days / 30.44), 1),
        "years": years,
        "curve": [[t.date().isoformat(), round(float(r.val), 2), round(float(r.dep), 2)] for t, r in pts.iterrows()],
        "last_trades": trades[-8:],
        "open": None,
    }
    if pos:
        out["open"] = {"coin": pos["coin"], "dir": pos["dir"], "entry": round(pos["entry"], 6), "since": pos["t0"],
                       "margin": round(pos["margin"], 2), "liq": round(pos["liq"], 6),
                       "stop": round(pos["stop"], 6) if pos["stop"] else None, "tgt": round(pos["tgt"], 6) if pos["tgt"] else None}
    return out


def eur(x):
    return "–" if x is None else f"{x:,.0f}".replace(",", " ")


def write_md(res, now):
    L = ["# Downtown – divoké strategie (jen papír)", "",
         f"Aktualizováno {now:%Y-%m-%d %H:%M} UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).",
         "Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,",
         "páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.", "",
         f"## Zpětný test od {BT_START}", "",
         "| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in res:
        b = s["backtest"]
        L.append(f"| {s['name']} | {s['lev']}× | {eur(b['deposited'])} | {eur(b['equity'])} | {eur(b['peak_equity'])} | {eur(b['net'])} ({b['net_pct']} %) | "
                 f"{b['max_dd_pct']} % | {b['liquidations']} | {b['wipes']} | {b['n_trades']} | {'–' if b['win_pct'] is None else str(b['win_pct']) + ' %'} | "
                 f"{b['best_month_pct']} % | {b['worst_month_pct']} % |")
    L += ["", "Roky (čistá křivka, % za rok):", ""]
    for s in res:
        L.append(f"- **{s['name']}**: " + ", ".join(f"{y}: {v} %" for y, v in s["backtest"]["years"].items()))
    L += ["", f"## Živý papír od {LIVE_START}", "",
          "| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |", "|---|---:|---:|---:|---:|---|"]
    for s in res:
        lv = s["live"]
        op = lv.get("open")
        ops = f"{op['coin']} {'long' if op['dir'] > 0 else 'short'} od {op['since'][:16]}" if op else "–"
        L.append(f"| {s['name']} | {eur(lv.get('equity'))} | {eur(lv.get('net'))} | {lv.get('n_trades', 0)} | {lv.get('liquidations', 0)} | {ops} |")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(cache="/tmp/dt_cache"):
    now = datetime.now(timezone.utc)
    raw = {}
    need = {(c, "15m" if s["tf"] == "15m" else "1h") for s in STRATS.values() for c in s["coins"]}
    for c, base in sorted(need):
        print(f"data {c} {base}", flush=True)
        raw[(c, base)] = fetch(c, base, cache)
    res = []
    for sid, cfg in STRATS.items():
        base = "15m" if cfg["tf"] == "15m" else "1h"
        frames = {c: resample(raw[(c, base)], cfg["tf"]) for c in cfg["coins"]}
        acc, cv, pos, idx = run(sid, frames, BT_START)
        bt = summarize(acc, cv, pos, idx)
        live = {"start": LIVE_START, "n_trades": 0, "equity": START_CASH, "deposited": START_CASH, "net": 0.0,
                "liquidations": 0, "wipes": 0, "curve": [], "last_trades": [], "open": None}
        if now >= pd.Timestamp(LIVE_START, tz="UTC"):
            acc2, cv2, pos2, idx2 = run(sid, frames, LIVE_START)
            if cv2:
                live = summarize(acc2, cv2, pos2, idx2)
                live["start"] = LIVE_START
        res.append({"id": sid, "name": cfg["name"], "tag": cfg["tag"], "rules": cfg["rules"], "lev": cfg["lev"],
                    "tf": cfg["tf"], "coins": cfg["coins"], "backtest": bt, "live": live, "updated": now.isoformat(timespec="minutes")})
        print(f"{sid}: čistě {bt['net']} USDT, likvidací {bt['liquidations']}, bankrotů {bt['wipes']}, obchodů {bt['n_trades']}", flush=True)
    OUT_JSON.write_text(json.dumps({"updated": now.isoformat(timespec="minutes"), "bt_start": BT_START, "live_start": LIVE_START,
                                    "start_cash": START_CASH, "costs": {"fee": FEE, "slip": SLIP, "funding_8h": FUND_8H, "mm": MM},
                                    "strategies": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(res, now)


if __name__ == "__main__":
    main(*(sys.argv[1:2] or []))
