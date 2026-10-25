#!/usr/bin/env python3
"""Datový list (fact sheet) pro krypto ticker – měřitelná data bez AI.

Agenti desku čtou tato čísla místo odhadů z webu. Každá sekce má `source` a `as_of`;
když zdroj není dostupný, sekce obsahuje jen `error` (agent pak ví, že data chybí).

Sekce:
  structure   – trend 1h/4h/1d (EMA 20/50/200, RSI, ATR %, pozice v range, swingy)
  levels      – předchozí den/týden high/low, volume profile (POC, VAH, VAL), liquidity pools, kulatá čísla
  orderflow   – relativní objem, odhad delta (CVD) ze svíček
  orderbook   – hloubka ±0,5/1/2 %, nerovnováha, největší zdi (ccxt)
  derivatives – funding (aktuální, 24h, 7d, anualizovaný), open interest, prémie (Hyperliquid)
  options     – DVOL, ATM IV, skew, put/call OI, max pain, implikovaný pohyb (Deribit; jen BTC/ETH)
  macro       – VIX, DXY, US10Y, QQQ, zlato; korelace s QQQ a DXY (yfinance)
  history     – jak dopadl stejný typ setupu na tomto tickeru (backtest, po nákladech)

Použití:
    python3 research/factsheet.py BTC/USDT [--signal scanner/signals.jsonl:ID] [--out research/factsheets/x.json]
"""
import argparse
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

HL_URL = "https://api.hyperliquid.xyz/info"
DERIBIT = "https://www.deribit.com/api/v2/public"
MACRO = {"VIX": "^VIX", "DXY": "DX-Y.NYB", "US10Y": "^TNX", "QQQ": "QQQ", "GOLD": "GC=F"}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe(fn):
    """Sekce nikdy neshodí celý list – chyba se zapíše do sekce."""
    def wrap(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as exc:
            return {"error": f"{exc.__class__.__name__}: {str(exc)[:160]}", "as_of": now_iso()}
    wrap.__name__ = fn.__name__
    return wrap


def r(x, n=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)


# --- výpočty ze svíček ---------------------------------------------------------
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def pivots(df, k=3):
    """Swing high/low: extrém v okně ±k svíček."""
    h, l = df["High"], df["Low"]
    pos = pd.Series(np.arange(len(df)), index=df.index)

    def dedupe(ser):                       # sousední svíčky se stejným extrémem = jeden swing
        keep, last = [], -10**9
        for t, v in ser.items():
            if pos[t] - last > k:
                keep.append(t)
                last = pos[t]
        return ser.loc[keep]
    ph = dedupe(h[(h == h.rolling(2 * k + 1, center=True).max())].dropna())
    pl = dedupe(l[(l == l.rolling(2 * k + 1, center=True).min())].dropna())
    return ph, pl


def structure_tf(df):
    c = df["Close"]
    e20, e50, e200 = ema(c, 20).iloc[-1], ema(c, 50).iloc[-1], ema(c, 200).iloc[-1] if len(c) >= 200 else np.nan
    last = c.iloc[-1]
    if not math.isnan(e200) and last > e50 > e200:
        trend = "up"
    elif not math.isnan(e200) and last < e50 < e200:
        trend = "down"
    else:
        trend = "mixed"
    prev = df["Close"].shift(1)
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    hi20, lo20 = df["High"].iloc[-20:].max(), df["Low"].iloc[-20:].min()
    ph, pl = pivots(df)
    swings = "?"
    if len(ph) >= 2 and len(pl) >= 2:
        hh, hl = ph.iloc[-1] > ph.iloc[-2], pl.iloc[-1] > pl.iloc[-2]
        swings = {(True, True): "HH+HL (rostoucí)", (False, False): "LH+LL (klesající)"}.get((hh, hl), "smíšené")
    return {"close": r(last, 6), "trend": trend, "ema20": r(e20, 6), "ema50": r(e50, 6), "ema200": r(e200, 6),
            "dist_ema200_pct": r((last / e200 - 1) * 100) if not math.isnan(e200) else None,
            "rsi14": r(rsi(c).iloc[-1], 1), "atr_pct": r(atr / last * 100),
            "range20_pos_pct": r((last - lo20) / (hi20 - lo20) * 100 if hi20 > lo20 else 50, 1),
            "swings": swings, "bars": len(df), "last_bar": df.index[-1].isoformat()}


def volume_profile(df, bins=40, value_area=0.7):
    """Objem rozprostřený rovnoměrně mezi low–high každé svíčky → POC, VAH, VAL."""
    lo, hi = df["Low"].min(), df["High"].max()
    edges = np.linspace(lo, hi, bins + 1)
    vol = np.zeros(bins)
    for l, h, v in zip(df["Low"].values, df["High"].values, df["Volume"].values):
        i0, i1 = np.searchsorted(edges, l, "right") - 1, np.searchsorted(edges, h, "left")
        i0, i1 = max(i0, 0), max(min(i1, bins), i0 + 1)
        vol[i0:i1] += v / (i1 - i0)
    poc = int(vol.argmax())
    inc, total, a, b = vol[poc], vol.sum(), poc, poc
    while total > 0 and inc / total < value_area and (a > 0 or b < bins - 1):
        left = vol[a - 1] if a > 0 else -1
        right = vol[b + 1] if b < bins - 1 else -1
        if right >= left:
            b += 1
            inc += vol[b]
        else:
            a -= 1
            inc += vol[a]
    mid = (edges[:-1] + edges[1:]) / 2
    return {"poc": r(mid[poc], 6), "vah": r(edges[b + 1], 6), "val": r(edges[a], 6)}


def liquidity_pools(df, price, tol_pct=0.15, k=3, max_n=4):
    """Shluky „equal highs/lows“ (≥2 swingy do tol %) – místa, kde leží stopy a likvidace."""
    ph, pl = pivots(df, k)
    out = {"above": [], "below": []}
    for side, ser in (("above", ph), ("below", pl)):
        vals = sorted(ser.values)
        clusters, cur = [], []
        for v in vals:
            if cur and abs(v / np.mean(cur) - 1) * 100 > tol_pct:
                clusters.append(cur)
                cur = []
            cur.append(v)
        if cur:
            clusters.append(cur)
        for cl in clusters:
            lvl = float(np.mean(cl))
            if len(cl) >= 2 and ((side == "above" and lvl > price) or (side == "below" and lvl < price)):
                out[side].append({"price": r(lvl, 6), "touches": len(cl), "dist_pct": r((lvl / price - 1) * 100)})
        out[side] = sorted(out[side], key=lambda x: abs(x["dist_pct"]))[:max_n]
    return out


def round_numbers(price, n=2):
    step = 10 ** math.floor(math.log10(price)) / 2
    base = math.floor(price / step) * step
    return [r(base - i * step, 6) for i in range(n)][::-1] + [r(base + (i + 1) * step, 6) for i in range(n)]


@safe
def section_structure(frames):
    return {"source": "ccxt OHLCV", "as_of": now_iso(),
            **{tf: structure_tf(df) for tf, df in frames.items() if df is not None and len(df) > 30}}


@safe
def section_levels(h1):
    price = float(h1["Close"].iloc[-1])
    day = h1.resample("1D").agg({"High": "max", "Low": "min"}).dropna()
    week = h1.resample("W-MON", label="left", closed="left").agg({"High": "max", "Low": "min"}).dropna()
    last7 = h1[h1.index > h1.index[-1] - pd.Timedelta(days=7)]
    return {"source": "ccxt OHLCV 1h", "as_of": now_iso(), "price": r(price, 6),
            "prev_day": {"high": r(day["High"].iloc[-2], 6), "low": r(day["Low"].iloc[-2], 6)} if len(day) > 1 else None,
            "prev_week": {"high": r(week["High"].iloc[-2], 6), "low": r(week["Low"].iloc[-2], 6)} if len(week) > 1 else None,
            "volume_profile_7d": volume_profile(last7) if len(last7) > 20 else None,
            "liquidity_pools": liquidity_pools(h1.iloc[-300:], price),
            "round_numbers": round_numbers(price)}


@safe
def section_orderflow(h1):
    v = h1["Volume"]
    rng = (h1["High"] - h1["Low"]).replace(0, np.nan)
    delta = (v * (2 * (h1["Close"] - h1["Low"]) / rng - 1)).fillna(0)        # odhad: kde v rozpětí svíčka zavřela
    day = v.iloc[-24:].sum()
    week_avg = v.iloc[-24 * 7:].sum() / 7 if len(v) >= 24 * 7 else np.nan
    return {"source": "ccxt OHLCV 1h (delta je odhad ze svíček, ne tick data)", "as_of": now_iso(),
            "rel_volume_last_bar": r(v.iloc[-1] / v.iloc[-21:-1].mean()),
            "rel_volume_24h_vs_7d": r(day / week_avg) if week_avg else None,
            "delta_24h_pct_of_volume": r(delta.iloc[-24:].sum() / day * 100, 1) if day else None,
            "delta_7d_pct_of_volume": r(delta.iloc[-168:].sum() / v.iloc[-168:].sum() * 100, 1)}


# --- order book ------------------------------------------------------------------
@safe
def section_orderbook(book, price=None):
    bids, asks = book["bids"], book["asks"]
    mid = price or (bids[0][0] + asks[0][0]) / 2
    out = {"source": "ccxt order book", "as_of": now_iso(), "mid": r(mid, 6),
           "spread_bps": r((asks[0][0] - bids[0][0]) / mid * 1e4, 1)}
    for pct in (0.5, 1, 2):
        b = sum(p * q for p, q, *_ in bids if p >= mid * (1 - pct / 100))
        a = sum(p * q for p, q, *_ in asks if p <= mid * (1 + pct / 100))
        out[f"depth_{pct}pct"] = {"bid_usd": r(b, 0), "ask_usd": r(a, 0), "imbalance": r((b - a) / (b + a), 3) if b + a else None}
    near_b = [(p, p * q) for p, q, *_ in bids if p >= mid * 0.97]
    near_a = [(p, p * q) for p, q, *_ in asks if p <= mid * 1.03]
    out["walls"] = {"bids": [{"price": r(p, 6), "usd": r(u, 0)} for p, u in sorted(near_b, key=lambda x: -x[1])[:3]],
                    "asks": [{"price": r(p, 6), "usd": r(u, 0)} for p, u in sorted(near_a, key=lambda x: -x[1])[:3]]}
    out["note"] = "jen jedna burza; spoofing a skryté příkazy nejsou vidět"
    return out


# --- deriváty: Hyperliquid -----------------------------------------------------------
def hl_post(payload, post=None):
    post = post or (lambda p: requests.post(HL_URL, json=p, timeout=15).json())
    return post(payload)


@safe
def section_derivatives(coin, post=None):
    meta, ctxs = hl_post({"type": "metaAndAssetCtxs"}, post)
    names = [u["name"] for u in meta["universe"]]
    if coin not in names:
        return {"error": f"{coin} na Hyperliquid není", "as_of": now_iso()}
    ctx = ctxs[names.index(coin)]
    start = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000)
    hist = hl_post({"type": "fundingHistory", "coin": coin, "startTime": start}, post) or []
    rates = [float(h["fundingRate"]) for h in hist]
    f_now = float(ctx["funding"])
    mark, prev = float(ctx["markPx"]), float(ctx.get("prevDayPx") or 0)
    oi = float(ctx["openInterest"])
    return {"source": "Hyperliquid (perp DEX)", "as_of": now_iso(),
            "funding_hourly_pct": r(f_now * 100, 5), "funding_annual_pct": r(f_now * 24 * 365 * 100, 1),
            "funding_24h_avg_annual_pct": r(np.mean(rates[-24:]) * 24 * 365 * 100, 1) if rates else None,
            "funding_7d_avg_annual_pct": r(np.mean(rates) * 24 * 365 * 100, 1) if rates else None,
            "open_interest_usd": r(oi * mark, 0), "premium_pct": r(float(ctx.get("premium") or 0) * 100, 4),
            "day_volume_usd": r(float(ctx.get("dayNtlVlm") or 0), 0),
            "price_change_24h_pct": r((mark / prev - 1) * 100) if prev else None,
            "note": "funding > ~30 % p.a. = přeplněné longy, záporný = přeplněné shorty; OI bez historie (jen snímek)"}


# --- opce: Deribit -------------------------------------------------------------------
def deribit_get(path, params, get=None):
    get = get or (lambda u, p: requests.get(u, params=p, timeout=15).json())
    return get(f"{DERIBIT}/{path}", params)["result"]


def _parse_instr(name):
    _, exp, strike, cp = name.split("-")
    return datetime.strptime(exp, "%d%b%y").replace(hour=8, tzinfo=timezone.utc), float(strike), cp


@safe
def section_options(currency, get=None, now=None):
    now = now or datetime.now(timezone.utc)
    rows = deribit_get("get_book_summary_by_currency", {"currency": currency, "kind": "option"}, get)
    opts = []
    for x in rows:
        exp, k, cp = _parse_instr(x["instrument_name"])
        opts.append({"exp": exp, "k": k, "cp": cp, "oi": float(x.get("open_interest") or 0),
                     "iv": x.get("mark_iv"), "S": float(x.get("underlying_price") or 0)})
    df = pd.DataFrame(opts)
    df = df[df["exp"] > now + timedelta(hours=12)]
    S = float(df["S"].median())
    exps = sorted(df["exp"].unique())
    near = exps[0]
    m30 = min(exps, key=lambda e: abs((e - now).days - 30))

    def atm_iv(e):
        d = df[(df["exp"] == e) & df["iv"].notna()]
        d = d.iloc[(d["k"] - S).abs().argsort()[:4]]
        return float(d["iv"].mean())

    def iv_at(e, k, cp):
        d = df[(df["exp"] == e) & (df["cp"] == cp) & df["iv"].notna()]
        return float(d.iloc[(d["k"] - k).abs().argsort()[:1]]["iv"].iloc[0])

    nd = df[df["exp"] == near]
    strikes = sorted(nd["k"].unique())
    pain = {s: sum(max(0, s - k) * oi for k, oi in zip(nd[nd.cp == "C"]["k"], nd[nd.cp == "C"]["oi"]))
            + sum(max(0, k - s) * oi for k, oi in zip(nd[nd.cp == "P"]["k"], nd[nd.cp == "P"]["oi"])) for s in strikes}
    iv30 = atm_iv(m30)
    calls, puts = df[df.cp == "C"]["oi"].sum(), df[df.cp == "P"]["oi"].sum()
    out = {"source": "Deribit (veřejné API)", "as_of": now_iso(), "underlying": r(S, 2),
           "atm_iv_nearest": r(atm_iv(near), 1), "atm_iv_30d": r(iv30, 1),
           "skew_25d_approx_30d": r(iv_at(m30, S * 0.9, "P") - iv_at(m30, S * 1.1, "C"), 1),
           "put_call_oi": r(puts / calls, 2) if calls else None,
           "nearest_expiry": near.isoformat(), "max_pain_nearest": r(min(pain, key=pain.get), 0) if pain else None,
           "nearest_expiry_oi": r(nd["oi"].sum(), 0),
           "implied_move_1d_pct": r(iv30 / math.sqrt(365), 2), "implied_move_7d_pct": r(iv30 * math.sqrt(7 / 365), 2),
           "note": "skew > 0 = puty dražší (strach z poklesu); implied move = 1σ podle IV"}
    try:
        end = int(now.timestamp() * 1000)
        dv = deribit_get("get_volatility_index_data", {"currency": currency, "start_timestamp": end - 8 * 86400_000,
                                                       "end_timestamp": end, "resolution": "3600"}, get)["data"]
        out["dvol"] = r(dv[-1][4], 1)
        out["dvol_7d_change"] = r(dv[-1][4] - dv[0][4], 1)
    except Exception:
        out["dvol"] = None
    return out


# --- makro ---------------------------------------------------------------------------
@safe
def section_macro(coin_daily=None, download=None):
    if download is None:
        import yfinance as yf
        download = lambda t: yf.download(t, period="90d", interval="1d", progress=False, auto_adjust=False)["Close"]
    closes = download(list(MACRO.values()))
    out = {"source": "yfinance (denní close)", "as_of": now_iso()}
    for name, t in MACRO.items():
        s = closes[t].dropna()
        out[name] = {"last": r(s.iloc[-1]), "chg_1d_pct": r((s.iloc[-1] / s.iloc[-2] - 1) * 100),
                     "chg_5d_pct": r((s.iloc[-1] / s.iloc[-6] - 1) * 100),
                     "above_ma50": bool(s.iloc[-1] > s.iloc[-50:].mean())}
    risk_on = out["QQQ"]["above_ma50"] and out["VIX"]["last"] < 20 and not out["DXY"]["above_ma50"]
    risk_off = (not out["QQQ"]["above_ma50"]) and out["VIX"]["last"] > 22
    out["regime"] = "risk-on" if risk_on else "risk-off" if risk_off else "neutrální"
    if coin_daily is not None and len(coin_daily) > 35:
        cr = coin_daily.pct_change()
        cr.index = cr.index.tz_localize(None).normalize()
        for name in ("QQQ", "DXY"):
            mr = closes[MACRO[name]].pct_change()
            mr.index = pd.to_datetime(mr.index).tz_localize(None).normalize()
            j = pd.concat([cr, mr], axis=1, join="inner").dropna().iloc[-30:]
            out[f"corr30d_{name}"] = r(j.corr().iloc[0, 1]) if len(j) > 10 else None
    return out


# --- historie setupu ---------------------------------------------------------------------
@safe
def section_history(symbol, direction=None, cfg=None, days=None, strategy=None):
    import yaml
    from scanner import evaluate as ev
    from scanner.calibrate import HISTORY_DAYS, strategies, strategy_params
    cfg = cfg or yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text())
    costs = cfg.get("costs", {})
    cost = costs.get("fee_pct", 0.1) + costs.get("slippage_pct", 0.05)
    strats = strategies(cfg)
    strat = next((s for s in strats if s["name"] == strategy), strats[0])
    days = days or min(HISTORY_DAYS.get(strat["timeframe"], 365), 365 if strat["timeframe"] == "1h" else 3650)
    df = ev.load_history(symbol, "crypto", strat["timeframe"], days)
    tr = ev.backtest(df, strategy_params(strat), "both", cost, setup=strat["setup"])
    out = {"source": f"backtest strategie {strat['name']} ({strat['setup']}, {strat['timeframe']}), {days} dní, po nákladech",
           "as_of": now_iso(), "all": ev.stats(tr)}
    for d in ("long", "short"):
        out[d] = ev.stats([t for t in tr if t["direction"] == d])
    sel = [t for t in tr if not direction or t["direction"] == direction][-10:]
    out["last_10_same_direction"] = [{"time": str(t["time"])[:16], "result": t["result"], "r": t["r"]} for t in sel]
    return out


# --- sestavení -------------------------------------------------------------------------------
def fetch_frames(symbol, exchange="kraken", ex=None):
    import ccxt
    ex = ex or getattr(ccxt, exchange)({"enableRateLimit": True})
    frames = {}
    for tf in ("1h", "4h", "1d"):
        rows = ex.fetch_ohlcv(symbol, timeframe=tf, limit=720)
        d = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
        d.index = pd.to_datetime(d.pop("ts"), unit="ms", utc=True)
        frames[tf] = d.iloc[:-1]                                        # poslední svíčka je rozpracovaná
    return frames, ex


def build(symbol, exchange="kraken", signal=None, frames=None, ex=None):
    coin = symbol.split("/")[0]
    sheet = {"symbol": symbol, "coin": coin, "generated": now_iso(), "signal": signal}
    try:
        if frames is None:
            frames, ex = fetch_frames(symbol, exchange)
    except Exception as exc:
        frames = {}
        sheet["candles_error"] = f"{exc.__class__.__name__}: {str(exc)[:160]}"
    h1 = frames.get("1h")
    sheet["structure"] = section_structure(frames) if frames else {"error": "bez svíček"}
    sheet["levels"] = section_levels(h1) if h1 is not None else {"error": "bez svíček"}
    sheet["orderflow"] = section_orderflow(h1) if h1 is not None else {"error": "bez svíček"}
    try:
        book = ex.fetch_order_book(symbol, limit=500) if ex else None
        sheet["orderbook"] = section_orderbook(book) if book else {"error": "order book nedostupný"}
    except Exception as exc:
        sheet["orderbook"] = {"error": f"{exc.__class__.__name__}: {str(exc)[:160]}"}
    sheet["derivatives"] = section_derivatives(coin)
    sheet["options"] = section_options(coin) if coin in ("BTC", "ETH") else {"note": "Deribit opce jen pro BTC a ETH"}
    sheet["macro"] = section_macro(frames.get("1d", pd.DataFrame()).get("Close") if frames else None)
    sheet["history"] = section_history(symbol, (signal or {}).get("setup", {}).get("direction"),
                                       strategy=(signal or {}).get("strategy"))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--exchange", default="kraken")
    ap.add_argument("--signal-json", help="JSON signálu (řádek ze scanner/signals.jsonl)")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    sig = json.loads(a.signal_json) if a.signal_json else None
    sheet = build(a.symbol, a.exchange, sig)
    text = json.dumps(sheet, ensure_ascii=False, indent=1, default=str)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n", encoding="utf-8")
        print(f"OK: {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
