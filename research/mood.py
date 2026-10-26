#!/usr/bin/env python3
"""🌡️ Index nálady trhu 1–100 (1 = silně medvědí, 100 = silně býčí) – měřitelná data bez AI.

Složky (každá 0–100, vážený průměr; chybějící složka se vynechá a váhy se přepočítají):
  trend        20 %  BTC nad SMA 50/200, SMA 50 nad SMA 200, 30denní výnos vůči poslednímu roku
  šíře trhu    15 %  podíl Donchian modelů v longu přes celý watchlist (stejné modely jako 🧭 ensemble)
  volatilita   10 %  100 − percentil 30denní volatility BTC v posledním roce (vysoká volatilita = strach)
  makro        15 %  Nasdaq (QQQ) nad SMA 50, VIX vůči poslednímu roku, dolar (DXY) pod SMA 50
  fear_greed   15 %  Crypto Fear & Greed Index (alternative.me)
  funding      10 %  průměrný funding BTC za 7 dní (Hyperliquid): −10 % p.a. = 0, +30 % p.a. = 100
  stablecoiny   5 %  změna oběhu stablecoinů za 30 dní (DefiLlama): −5 % = 0, +5 % = 100
  zprávy       10 %  tón titulků za 72 h (krypto, geopolitika, regulace, Fed) podle klíčových slov

Index popisuje, jaká nálada převládá – NENÍ to vstupní signál a strategie se podle něj nemění
(test na historii: reports/mood.md). Výklad událostí a geopolitiky dělá AI v týdenním reportu nálady.

Použití:
    python3 research/mood.py              # aktuální index (JSON)
    python3 research/mood.py --backtest   # historie cenových složek → reports/mood.md
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WEIGHTS = {"trend": 20, "šíře trhu": 15, "volatilita": 10, "makro": 15, "fear_greed": 15, "funding": 10,
           "stablecoiny": 5, "zprávy": 10}
WINDOWS = [10, 20, 40, 80, 160]
ZONES = [(20, "silně medvědí"), (40, "medvědí"), (60, "neutrální"), (80, "býčí"), (100, "silně býčí")]
MACRO = {"QQQ": "QQQ", "VIX": "^VIX", "DXY": "DX-Y.NYB"}
REPORT = ROOT / "reports" / "mood.md"
LOG = ROOT / "research" / "mood_log.jsonl"                           # denní hodnoty ze skeneru (commit v Actions)


def zone(x):
    return next(name for top, name in ZONES if x <= top)


def clamp(x, lo=0.0, hi=100.0):
    return float(min(hi, max(lo, x)))


def _naive(s):
    s = s.copy()
    s.index = pd.to_datetime(s.index)
    if s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    s.index = s.index.normalize()
    return s[~s.index.duplicated(keep="last")]


def _naive_df(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.index = df.index.normalize()
    return df[~df.index.duplicated(keep="last")]


def _pct_rank(s, n=365):
    return s.rolling(n, min_periods=n // 2).rank(pct=True)


# --- cenové složky (stejný kód pro dnešek i historii) ----------------------------------------------
def trend_series(btc):
    c = btc["Close"]
    s50, s200 = c.rolling(50).mean(), c.rolling(200).mean()
    parts = [(c > s200).astype(float), (c > s50).astype(float), (s50 > s200).astype(float),
             _pct_rank(c.pct_change(30))]
    out = pd.concat(parts, axis=1).mean(axis=1, skipna=False) * 100
    return out.where(s200.notna())


def donchian_state(df, n):
    hi, lo, cl = df["High"], df["Low"], df["Close"]
    up = (cl > hi.rolling(n).max().shift(1)).values
    dn = (cl < lo.rolling(n // 2).min().shift(1)).values
    out, s = np.empty(len(df)), 0.0
    for i, (u, d) in enumerate(zip(up, dn)):
        s = 1.0 if u else (0.0 if d else s)
        out[i] = s
    res = pd.Series(out, index=df.index)
    res.iloc[:n] = np.nan
    return res


def breadth_series(daily):
    per_coin = [pd.concat([donchian_state(df, n) for n in WINDOWS], axis=1).mean(axis=1, skipna=False)
                for df in daily.values() if df is not None and len(df) > max(WINDOWS)]
    if not per_coin:
        return pd.Series(dtype=float)
    return pd.concat(per_coin, axis=1).mean(axis=1) * 100            # mince bez historie se vynechají


def vol_series(btc):
    v = btc["Close"].pct_change().rolling(30).std()
    return (1 - _pct_rank(v)) * 100


def macro_series(closes):
    q, vix, dxy = (_naive(closes[k].dropna()) for k in ("QQQ", "VIX", "DXY"))
    parts = [(q > q.rolling(50).mean()).astype(float), 1 - _pct_rank(vix, 252), (dxy < dxy.rolling(50).mean()).astype(float)]
    return (pd.concat(parts, axis=1).ffill().mean(axis=1, skipna=False) * 100)


def price_history(daily, macro_closes=None):
    """Denní historie cenových složek (trend, šíře, volatilita, makro) – index bez mincí bez dat."""
    daily = {c: _naive_df(df) for c, df in daily.items() if df is not None and len(df)}
    btc = daily["BTC"]
    cols = {"trend": trend_series(btc), "šíře trhu": breadth_series(daily), "volatilita": vol_series(btc)}
    if macro_closes is not None:
        m = macro_series(macro_closes)
        cols["makro"] = m.reindex(btc.index, method="ffill")       # víkendy: poslední close burzy
    return pd.DataFrame(cols).reindex(btc.index)


def combine(scores):
    """Vážený průměr dostupných složek → index 1–100."""
    avail = {k: v for k, v in scores.items() if v is not None and not (isinstance(v, float) and np.isnan(v))}
    if not avail:
        return None
    w = sum(WEIGHTS[k] for k in avail)
    return int(round(clamp(sum(WEIGHTS[k] * v for k, v in avail.items()) / w, 1, 100)))


# --- živé složky (jen dnešní snímek) -------------------------------------------------------------
def score_funding(annual_pct):
    return clamp(50 + (annual_pct - 10) * 2.5)


def score_stables(chg_30d_pct):
    return clamp(50 + chg_30d_pct * 10)


def score_news(digest, min_n=5):
    rows = [r for k, v in digest.items() if k != "note" and isinstance(v, list) for r in v]
    pos = sum(r["tone"] == "pozitivní" for r in rows)
    neg = sum(r["tone"] == "negativní" for r in rows)
    if pos + neg < min_n:
        return None, pos, neg
    return clamp(50 + 50 * (pos - neg) / (pos + neg)), pos, neg


def _download_macro(days=500):
    import yfinance as yf
    df = yf.download(list(MACRO.values()), period=f"{days}d", interval="1d", progress=False, auto_adjust=False)["Close"]
    return {k: df[t] for k, t in MACRO.items()}


def current(daily, macro_closes=None, fetch=True):
    """Dnešní index: {index, zone, components: {název: {score, detail, source}}, as_of}."""
    comp = {}
    hist = price_history(daily, macro_closes)
    last = hist.iloc[-1]
    btc = _naive_df(daily["BTC"])["Close"]
    c, s50, s200 = btc.iloc[-1], btc.iloc[-50:].mean(), btc.iloc[-200:].mean()
    comp["trend"] = {"score": last.get("trend"), "source": "svíčky BTC",
                     "detail": f"BTC {'nad' if c > s200 else 'pod'} SMA 200, {'nad' if c > s50 else 'pod'} SMA 50, "
                               f"30 dní {(c / btc.iloc[-31] - 1) * 100:+.1f} %"}
    n_coins = sum(1 for df in daily.values() if df is not None and len(df) > max(WINDOWS))
    comp["šíře trhu"] = {"score": last.get("šíře trhu"), "source": "svíčky watchlistu",
                         "detail": f"{last.get('šíře trhu', 0):.0f} % Donchian modelů v longu ({n_coins} mincí)"}
    v30 = btc.pct_change().iloc[-30:].std() * np.sqrt(365) * 100
    comp["volatilita"] = {"score": last.get("volatilita"), "source": "svíčky BTC",
                          "detail": f"30denní volatilita BTC {v30:.0f} % p.a."}
    if macro_closes is not None and "makro" in hist:
        q, vix, dxy = (macro_closes[k].dropna() for k in ("QQQ", "VIX", "DXY"))
        comp["makro"] = {"score": last.get("makro"), "source": "yfinance",
                         "detail": f"Nasdaq {'nad' if q.iloc[-1] > q.iloc[-50:].mean() else 'pod'} SMA 50, VIX {vix.iloc[-1]:.1f}, "
                                   f"dolar {'pod' if dxy.iloc[-1] < dxy.iloc[-50:].mean() else 'nad'} SMA 50"}
    if fetch:
        from research import events, onchain
        from research.factsheet import section_derivatives
        try:
            fg = onchain.fear_greed()
            comp["fear_greed"] = {"score": float(fg["value"]), "source": "alternative.me",
                                  "detail": f"{fg['value']} ({fg.get('label')}), před týdnem {fg.get('week_ago')}"}
        except Exception as exc:
            comp["fear_greed"] = {"score": None, "error": exc.__class__.__name__}
        try:
            d = section_derivatives("BTC")
            f = d.get("funding_7d_avg_annual_pct")
            comp["funding"] = {"score": score_funding(f) if f is not None else None, "source": "Hyperliquid",
                               "detail": f"funding BTC 7 dní {f:+.1f} % p.a." if f is not None else d.get("error")}
        except Exception as exc:
            comp["funding"] = {"score": None, "error": exc.__class__.__name__}
        try:
            st = onchain.stablecoins()
            comp["stablecoiny"] = {"score": score_stables(st["chg_30d_pct"]), "source": "DefiLlama",
                                   "detail": f"oběh {st['total_usd_bn']} mld. USD, 30 dní {st['chg_30d_pct']:+.2f} %"}
        except Exception as exc:
            comp["stablecoiny"] = {"score": None, "error": exc.__class__.__name__}
        try:
            dg = events.news_digest(events.fetch_news(["BTC", "ETH"]), hours=72, limit=60)
            sc, pos, neg = score_news(dg)
            comp["zprávy"] = {"score": sc, "source": "Google News, RSS",
                              "detail": f"titulky 72 h: {pos} pozitivních, {neg} negativních (klíčová slova)"}
        except Exception as exc:
            comp["zprávy"] = {"score": None, "error": exc.__class__.__name__}
    for v in comp.values():
        if v.get("score") is not None:
            v["score"] = None if np.isnan(v["score"]) else round(float(v["score"]), 1)
    idx = combine({k: v.get("score") for k, v in comp.items()})
    week_ago = combine({k: hist[k].iloc[-8] for k in hist.columns if len(hist) > 8})
    return {"index": idx, "zone": zone(idx) if idx else None, "components": comp,
            "price_only_week_ago": week_ago, "price_only_now": combine({k: last.get(k) for k in hist.columns}),
            "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def bar(x, n=10):
    k = int(round(x / 100 * n))
    return "▰" * k + "▱" * (n - k)


def message(m, detail=True):
    if not m or m.get("index") is None:
        return "🌡️ Index nálady: data nedostupná."
    lines = [f"🌡️ Nálada trhu: {m['index']}/100 – {m['zone']} {bar(m['index'])}"]
    if m.get("price_only_week_ago") and m.get("price_only_now"):
        d = m["price_only_now"] - m["price_only_week_ago"]
        lines.append(f"Cenové složky za týden: {m['price_only_week_ago']} → {m['price_only_now']} ({d:+d}).")
    if detail:
        for k, v in m["components"].items():
            s = v.get("score")
            lines.append(f"• {k} ({WEIGHTS[k]} %): " + (f"{s:.0f} – {v.get('detail', '')}" if s is not None
                                                          else f"nedostupné ({(v.get('error') or v.get('detail') or '')[:50]})"))
    lines.append("Popis nálady, ne signál – historicky index budoucí vývoj nepředpovídal (reports/mood.md).")
    return "\n".join(lines)


def compact(m):
    return {"index": m["index"], "zone": m["zone"], "as_of": m["as_of"],
            "price_only_now": m.get("price_only_now"), "price_only_week_ago": m.get("price_only_week_ago"),
            "components": {k: {kk: v.get(kk) for kk in ("score", "detail", "error") if v.get(kk) is not None}
                           for k, v in m["components"].items()}}


def daily_update(cfg, state, frames, now, dry_run=False, send=None, compute=None):
    """Skener: jednou denně (od `hour` času Prahy) spočítá index; zpráva jen při změně pásma. Vrací zprávu nebo None."""
    mc = cfg.get("mood") or {}
    if not mc.get("enabled"):
        return None
    from zoneinfo import ZoneInfo
    from scanner.data import closed_only
    loc = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC")))
    day = loc.date().isoformat()
    st = state.data.setdefault("mood", {})
    if loc.hour < mc.get("hour", 8) or st.get("day") == day:
        return None
    daily = {sym.split("/")[0]: closed_only(df, "1d", now) for (sym, tf), df in frames.items()
             if tf == "1d" and df is not None and len(df)}
    if "BTC" not in daily:
        return None
    if compute is None:
        try:
            macro = _download_macro()
        except Exception:
            macro = None
        m = current(daily, macro)
    else:
        m = compute(daily)
    st["day"] = day
    if m.get("index") is None:
        state.save()
        return None
    prev = st.get("last")
    st["last"] = compact(m)
    st["history"] = (st.get("history", []) + [[day, m["index"]]])[-400:]
    state.save()
    if not dry_run and compute is None:
        try:
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"day": day, **compact(m)}, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass
    if not prev or prev.get("zone") == m["zone"] or not mc.get("alert_on_zone_change", True):
        return None
    msg = (f"🌡️ Nálada trhu se změnila: {prev['zone']} ({prev['index']}) → {m['zone']} ({m['index']}) {bar(m['index'])}\n"
           + "\n".join(movers(prev, m)) + "\nPodrobnosti: /nalada. Popis nálady, ne signál.")
    print(msg)
    from scanner import notify
    tg = send or (None if dry_run or not cfg.get("notify", {}).get("telegram", True) else notify.telegram)
    if tg:
        tg(msg)
    return msg


def movers(prev, m, n=3):
    """Složky, které se od minula pohnuly nejvíc."""
    out = []
    for k, v in m["components"].items():
        a, b = (prev.get("components") or {}).get(k, {}).get("score"), v.get("score")
        if a is not None and b is not None:
            out.append((abs(b - a), f"• {k}: {a:.0f} → {b:.0f} ({v.get('detail', '')})"))
    return [t for _, t in sorted(out, reverse=True)[:n]]


def history_line(state):
    h = (state.data.get("mood") or {}).get("history") or []
    if len(h) < 2:
        return ""
    def ago(days):
        return h[-1 - days][1] if len(h) > days else None
    parts = [f"před {d} dny {ago(d)}" for d in (7, 30) if ago(d) is not None]
    return ("Vývoj: " + ", ".join(parts) + ".") if parts else ""


# --- test na historii -------------------------------------------------------------------------
def backtest(daily, macro_closes, split="2022-01-01"):
    hist = price_history(daily, macro_closes).dropna()
    idx = hist.apply(lambda r: combine(r.to_dict()), axis=1)
    btc = _naive(daily["BTC"]["Close"]).reindex(idx.index)
    rows, out = [], {"from": str(idx.index[0].date()), "to": str(idx.index[-1].date()), "days": len(idx)}
    for h in (7, 30, 90):
        fwd = (btc.shift(-h) / btc - 1) * 100
        d = pd.DataFrame({"idx": idx, "fwd": fwd}).dropna()
        z = d["idx"].apply(zone)
        for part, sub in (("vše", d), ("do 2021", d[d.index < split]), ("od 2022", d[d.index >= split])):
            zz = z.loc[sub.index]
            rows.append({"h": h, "část": part, "korelace": round(sub["idx"].corr(sub["fwd"]), 3),
                         "průměr": round(sub["fwd"].mean(), 2),
                         **{name: (round(sub["fwd"][zz == name].mean(), 2), int((zz == name).sum()))
                            for _, name in ZONES}})
    out["rows"] = rows
    out["zone_days"] = {name: int((idx.apply(zone) == name).sum()) for _, name in ZONES}
    out["last"] = int(idx.iloc[-1])
    return out, idx


def report_md(bt, idx):
    L = ["# 🌡️ Index nálady trhu – test na historii", "",
         f"Cenové složky indexu (trend, šíře trhu, volatilita, makro = 60 % vah) spočítané den po dni "
         f"{bt['from']} – {bt['to']} ({bt['days']} dní), bez pohledu do budoucnosti. Fear & Greed, funding, stablecoiny "
         "a zprávy nemají dost dlouhou volně dostupnou historii, v testu chybí.", "",
         "Otázka: vypovídá index o tom, co BTC udělá dál (7 / 30 / 90 dní)? Průměrný budoucí výnos BTC v % podle pásma "
         "indexu (v závorce počet dní):", ""]
    L.append("| horizont | část | korelace | průměr | " + " | ".join(n for _, n in ZONES) + " |")
    L.append("|---|---|---|---|" + "---|" * len(ZONES))
    for r in bt["rows"]:
        L.append(f"| {r['h']} d | {r['část']} | {r['korelace']:+.3f} | {r['průměr']:+.2f} | "
                 + " | ".join(f"{r[n][0]:+.2f} ({r[n][1]})" if r[n][1] else "–" for _, n in ZONES) + " |")
    L += ["", "Dní v pásmech: " + ", ".join(f"{k} {v}" for k, v in bt["zone_days"].items()) + ".",
          f"Poslední hodnota cenových složek: {bt['last']}.", ""]
    oos = [r for r in bt["rows"] if r["část"] == "od 2022"]
    weak = all(abs(r["korelace"]) < 0.1 for r in oos)
    L += ["## Závěr", "",
          ("Od roku 2022 (mimo vzorek) je korelace indexu s budoucím výnosem BTC na všech horizontech pod 0,1 a pásma "
           "nejsou seřazená (býčí pásmo nemá vyšší budoucí výnos než medvědí). Do roku 2021 index vypadal užitečněji, "
           "ale to bylo hlavně jedno velké býčí období. Překrývající se okna navíc přeceňují počet nezávislých pozorování."
           if weak else "Mimo vzorek je vztah slabý – ověřit dalším testem, než se index použije k čemukoli dalšímu."),
          "",
          "**Index je popis nálady, ne signál.** Strategie, velikost pozic ani config se podle něj nemění.", "",
          "AI úprava v týdenním reportu (události a geopolitika, max. ±10 bodů) se loguje do research/mood_ai.jsonl; "
          "po ≥ 26 týdnech mentor ověří, jestli k měřenému indexu něco přidává.", ""]
    return "\n".join(L)


def load_daily(cache_dir=ROOT / "scanner" / "cache"):
    coins = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
    out = {}
    for c in coins:
        p = Path(cache_dir) / f"eval_crypto_{c}-USDT_1d_3650d.csv"
        if p.exists():
            df = pd.read_csv(p, index_col=0, parse_dates=True)
            out[c] = df
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    daily = load_daily()
    if a.backtest:
        macro = _download_macro(4000)
        bt, idx = backtest(daily, macro)
        print(json.dumps(bt, ensure_ascii=False, indent=1))
        REPORT.write_text(report_md(bt, idx), encoding="utf-8")
        return
    try:
        macro = _download_macro()
    except Exception:
        macro = None
    m = current(daily, macro, fetch=not a.no_fetch)
    print(json.dumps(m, ensure_ascii=False, indent=1, default=str))
    print(message(m))


if __name__ == "__main__":
    main()
