#!/usr/bin/env python3
"""🏙️ Papírové účty pro Agentown – stejné statistiky jako Downtown i pro Laboratoř a jádro města.

Stanoveno PŘEDEM (8. 11. 2026), jen přepočet existujících výsledků, nic se neladí a na skener, riziko, demo ani peníze
to nesahá:
  • každá strategie má papírový účet 1 000 USDT, na každý obchod riskuje 1 % aktuálního (uzavřeného) účtu a reinvestuje;
    zisk/ztráta obchodu = velikost rizika × výsledek v R (R už je po poplatcích a skluzu z testu dané strategie),
  • bez páky, takže bankroty a likvidace nedávají smysl – místo nich se měří nejdelší série ztrát,
  • velikost pozice se řídí stopem (riziko 1 %), souběžné obchody na více mincích se sčítají,
  • Laboratoř: obchody celé historie atlasu (OKX, 8 mincí, od 2019 / 15M od 2022) přes stejné signály a výstupy jako
    papír (scanner/lab_paper.py), papír = uzavřené obchody z research/lab_trades.jsonl od přidání do registru,
  • jádro: donchian_1d a pullback_1d (varianta P0) a 🔺 pyramida (P2) z research/experiments/pyramid.py s limity desku,
    papír z research/outcomes.jsonl a research/pyramid_outcomes.jsonl; 🧭 ensemble = denní výnosy alokace
    z research/experiments/ensemble.py, papír z research/equity_log.jsonl (díl ensemblu z 5 000 USD přepočtený na 1 000).

Výstup research/city_accounts.json (čte ho denní úloha „Agentown – aktualizace z laboratoře“ → kolekce `accounts`).

    python3 research/city_accounts.py /tmp/cache scanner/cache
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "experiments"))
OUT = ROOT / "research" / "city_accounts.json"
START_CASH, RISK = 1000.0, 0.01
CORE_LIVE_START = "2026-10-27"
COINS8 = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]


# ---------------------------------------------------------------- účet
def _ts(x):
    t = pd.Timestamp(x)
    return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")


def daily_equity(trades, cash=START_CASH, risk=RISK):
    """Denní uzavřený účet (stejná pravidla jako account) – pro studie alokace."""
    tr = sorted(({**t, "entry": _ts(t["entry"]), "exit": _ts(t["exit"])} for t in trades), key=lambda t: t["entry"])
    ev = []
    for k, t in enumerate(tr):
        ev.append((t["entry"], 1, k, 1))
        ev.append((t["exit"], 0, k, 2 if t["exit"] <= t["entry"] else 0))
    ev.sort(key=lambda e: (e[0], e[3]))
    eq, size, pts = cash, {}, []
    for t, kind, k, _ in ev:
        if kind == 1:
            size[k] = eq * risk
        else:
            eq += size.pop(k) * tr[k]["r"]
            pts.append((t, eq))
    if not pts:
        return pd.Series(dtype=float)
    s = pd.Series([v for _, v in pts], index=pd.DatetimeIndex([t for t, _ in pts])).groupby(level=0).last()
    s = pd.concat([pd.Series([cash], index=[tr[0]["entry"]]), s]).groupby(level=0).last()
    return s.resample("1D").last().ffill()


def account(trades, start=None, end=None, cash=START_CASH, risk=RISK):
    """trades: dicty s entry, exit (čas), coin, dir (+1/−1), r. Vrátí souhrn ve tvaru Downtownu."""
    tr = sorted(({**t, "entry": _ts(t["entry"]), "exit": _ts(t["exit"])} for t in trades), key=lambda t: t["entry"])
    ev = []
    for k, t in enumerate(tr):
        ev.append((t["entry"], 1, k, 1))
        ev.append((t["exit"], 0, k, 2 if t["exit"] <= t["entry"] else 0))
    ev.sort(key=lambda e: (e[0], e[3]))               # ve stejný okamžik napřed uzavřít, pak otevřít (obchod v 1 svíčce až po vstupu)
    eq, size, pts, done = cash, {}, [], []
    for t, kind, k, _ in ev:
        if kind == 1:
            size[k] = eq * risk
        else:
            pnl = size.pop(k) * tr[k]["r"]
            eq += pnl
            pts.append((t, eq))
            done.append({**tr[k], "pnl": pnl, "ret_pct": risk * tr[k]["r"] * 100})
    s0 = _ts(start) if start else (tr[0]["entry"] if tr else None)
    e0 = _ts(end) if end else datetime.now(timezone.utc)
    return summarize(pts, done, s0, e0, cash)


def summarize(pts, done, start, end, cash=START_CASH, n_trades=None):
    base = {"start": start.date().isoformat() if start is not None else None, "end": pd.Timestamp(end).isoformat(),
            "deposited": cash, "liquidations": 0, "wipes": 0}
    if not pts:
        return {**base, "n_trades": 0 if n_trades is None else n_trades, "equity": cash, "net": 0.0, "net_pct": 0.0,
                "peak_equity": cash, "max_dd_pct": 0.0, "win_pct": None, "curve": [], "last_trades": [], "open": None,
                "years": {}, "lose_streak": 0}
    s = pd.Series([v for _, v in pts], index=pd.DatetimeIndex([t for t, _ in pts])).groupby(level=0).last()
    if start is not None:
        s = pd.concat([pd.Series([cash], index=[start]), s]).groupby(level=0).last()
    day = s.resample("1D").last().ffill()
    peak = day.cummax()
    dd = float(((day / peak) - 1).min() * 100)
    mon = day.resample("ME").last()
    mret = mon.pct_change()
    if len(mon):
        first = day.iloc[0] if len(day) else cash
        mret.iloc[0] = mon.iloc[0] / first - 1
    yr = day.resample("YE").last()
    yprev = yr.shift(1)
    yprev.iloc[0] = cash
    years = {str(i.year): round(float((v / p - 1) * 100), 1) for i, v, p in zip(yr.index, yr.values, yprev.values)}
    eq = float(day.iloc[-1])
    rs = [d["r"] for d in done]
    streak = best = 0
    for r in rs:
        streak = streak + 1 if r <= 0 else 0
        best = max(best, streak)
    months = max(1.0, (day.index[-1] - day.index[0]).days / 30.44)
    step = max(1, len(day) // 300)
    curve = day.iloc[::step]
    if curve.index[-1] != day.index[-1]:
        curve = pd.concat([curve, day.iloc[-1:]])
    out = {**base, "equity": round(eq, 2), "net": round(eq - cash, 2), "net_pct": round((eq / cash - 1) * 100, 1),
           "peak_equity": round(float(day.max()), 2), "max_dd_pct": round(dd, 1),
           "n_trades": len(done) if n_trades is None else n_trades,
           "win_pct": round(float(np.mean([r > 0 for r in rs]) * 100), 1) if rs else None,
           "best_trade": round(max(d["pnl"] for d in done), 2) if done else None,
           "worst_trade": round(min(d["pnl"] for d in done), 2) if done else None,
           "best_month_pct": round(float(mret.max() * 100), 1) if len(mret) else None,
           "worst_month_pct": round(float(mret.min() * 100), 1) if len(mret) else None,
           "trades_per_month": round(len(done) / months, 1) if done else None,
           "lose_streak": best, "years": years, "open": None,
           "curve": [[t.date().isoformat(), round(float(v), 2), cash] for t, v in curve.items()],
           "last_trades": [{"t": d["exit"].isoformat(), "kind": "win" if d["r"] > 0 else "loss", "coin": d.get("coin", ""),
                            "dir": d.get("dir", 1), "pnl": round(d["pnl"], 2), "ret_pct": round(d["ret_pct"], 2),
                            "r": round(float(d["r"]), 3)} for d in done[-12:]]}
    return out


def returns_account(rets, start=None, cash=START_CASH):
    """Účet z denních výnosů (ensemble – alokace, ne jednotlivé obchody)."""
    r = rets.dropna()
    if start is not None:
        r = r[r.index >= _ts(start)]
    if r.empty:
        return summarize([], [], _ts(start) if start else None, datetime.now(timezone.utc), cash)
    eq = cash * (1 + r).cumprod()
    pts = list(eq.items())
    res = summarize(pts, [], r.index[0] - pd.Timedelta("1D"), r.index[-1], cash, n_trades=None)
    res.update({"n_trades": None, "win_pct": round(float((r > 0).mean() * 100), 1), "win_basis": "dny",
                "trades_per_month": None, "best_trade": None, "worst_trade": None, "lose_streak": None, "last_trades": []})
    return res


# ---------------------------------------------------------------- data (doplnění cache jen o nové svíčky)
def patch_fetch():
    """atlas.fetch stahuje při starší cache celou historii znovu; tady se načte cache a doplní jen chybějící konec."""
    from research.experiments import strategy_atlas as atlas
    orig = atlas.fetch

    def fetch(coin, tf, start, cache):
        path = Path(cache) / f"okx_{coin}_{tf}_from{start[:4]}.csv"
        if not path.exists():
            return orig(coin, tf, start, cache)
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        if time.time() - path.stat().st_mtime < 3 * 3600:
            return df
        try:
            import ccxt
            ex = ccxt.okx({"enableRateLimit": True})
            step = {"1h": 3_600_000, "15m": 900_000}[tf]
            since, end, rows = int(df.index[-1].timestamp() * 1000) + step, time.time() * 1000, []
            while since < end:
                b = ex.fetch_ohlcv(f"{coin}/USDT", tf, since=since, limit=100)
                if not b:
                    break
                rows += b
                since = b[-1][0] + step
            if rows:
                add = pd.DataFrame(rows, columns=["t", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("t")
                add.index = pd.to_datetime(add.pop("t"), unit="ms", utc=True)
                df = pd.concat([df, add])
                df = df[~df.index.duplicated(keep="last")].sort_index()
                df.to_csv(path)
        except Exception as exc:
            print(f"  {coin} {tf}: doplnění selhalo ({exc.__class__.__name__}), beru cache", flush=True)
        return df
    atlas.fetch = fetch


# ---------------------------------------------------------------- laboratoř
def lab_backtest_trades(s, frames):
    from research.experiments import strategy_atlas as atlas
    from scanner import lab_paper
    d = 1 if s["dir"] == "long" else -1
    sa, ta, ga, uo, mh = atlas.EXITS[s["exit"]]
    out = []
    for coin, z in frames.items():
        ent, opp = lab_paper._signals(z, s, d)
        if s.get("filter", "none") != "none" and s["family"] != "combo":
            ent = ent[z.flt[s["filter"]][ent] == (1.0 if d > 0 else 0.0)]
        ii, xx, gg, rf = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, np.asarray(ent, np.int64), np.asarray(opp, bool), d,
                                        sa, ta, ga, uo, mh)
        r = (gg - 2 * atlas.COSTS[atlas.MAIN]) / rf
        idx = z.df.index
        for i, x, rr in zip(ii, xx, r):
            out.append({"entry": idx[i], "exit": idx[x], "coin": coin, "dir": d, "r": float(rr)})
    return out


def lab_paper_trades(path=ROOT / "research" / "lab_trades.jsonl"):
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        x = json.loads(line)
        if x.get("event") != "close" or x.get("r") is None:
            continue
        out.setdefault(x["sid"], []).append({"entry": x.get("signal_bar") or x["time"], "exit": x.get("exit_bar") or x["time"],
                                             "coin": x.get("coin", ""), "dir": 1 if x.get("dir") == "long" else -1,
                                             "r": float(x["r"])})
    return out


def lab_accounts(cache):
    from research import registry
    from research.experiments import combo_study
    reg = registry.load()
    rows = [s for s in reg["strategies"] if s.get("status") != "vyřazeno"]
    paper = lab_paper_trades()
    out, frames_by_tf = [], {}
    for s in rows:
        tf = s["tf"]
        try:
            if tf not in frames_by_tf:
                frames_by_tf[tf] = combo_study.frames_for(tf, cache)[0]
            bt = account(lab_backtest_trades(s, frames_by_tf[tf]))
        except Exception as exc:
            print(f"{s['id']}: zpětný test selhal ({exc.__class__.__name__}: {exc})", flush=True)
            bt = None
        lv = account(paper.get(s["id"], []), start=s.get("added") or CORE_LIVE_START)
        out.append({"id": "lab:" + s["id"], "kind": "lab", "ref": s["id"], "name": s.get("label") or s["id"],
                    "tf": tf, "coins": COINS8, "status": s.get("status"), "backtest": bt, "live": lv})
        print(f"{s['id']}: zpětný test {bt and bt['net']} USDT, papír {lv['net']} USDT ({lv['n_trades']} obch.)", flush=True)
    return out


# ---------------------------------------------------------------- jádro města
def _id_time(x):
    for part in str(x.get("id", "")).split("|"):
        if part[:2] == "20" and "T" in part:
            return part
    return x["closed_at"]


def core_paper(path, name=None):
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        x = json.loads(line)
        if name and x.get("strategy") != name:
            continue
        if x.get("r") is None or not x.get("closed_at"):
            continue
        out.append({"entry": _id_time(x), "exit": x["closed_at"], "coin": str(x.get("symbol", "")).split("/")[0],
                    "dir": 1 if x.get("direction") == "long" else -1, "r": float(x["r"])})
    return out


def core_backtests(scache):
    """Zpětné testy jádra: {"donchian"|"pullback"|"pyramida": obchody} a denní výnosy ensemblu (od 200. dne)."""
    sys.argv = [sys.argv[0], str(scache)]
    from scanner import evaluate as ev
    for c in COINS8:                                    # zajistí denní svíčky v cache (yfinance, jako skener)
        try:
            ev.load_history(f"{c}/USDT", "crypto", "1d", 3650, cache_dir=scache)
        except Exception as exc:
            print(f"{c} 1d: {exc.__class__.__name__}", flush=True)
    import pyramid as P  # noqa: E402
    import ensemble as E  # noqa: E402
    df = P.build()
    conv = lambda t: [{"entry": x.time, "exit": x.exit, "coin": x.coin, "dir": 1 if x.dir == "long" else -1,
                       "r": float(x.r)} for x in t.itertuples()]
    p0 = df[df["var"] == "P0"]
    trades = {"donchian": conv(P.portfolio(p0[p0["strategy"] == "donchian_1d"])),
              "pullback": conv(P.portfolio(p0[p0["strategy"] == "pullback_1d"])),
              "pyramida": conv(P.portfolio(df[df["var"] == "P2"]))}
    frames = {c: E.load(c) for c in E.COINS}
    idx = frames["BTC"].index
    rets = pd.DataFrame({c: f["Close"].pct_change() for c, f in frames.items()}).reindex(idx)
    w = pd.DataFrame(0.0, index=idx, columns=E.COINS)
    for c, f in frames.items():
        vol = f["Close"].pct_change().rolling(30).std() * np.sqrt(365)
        w[c] = (E.coin_signal(f) * np.minimum(1, 0.40 / vol) / len(E.COINS)).reindex(idx).fillna(0)
    ens = (w.shift(1) * rets.fillna(0)).sum(axis=1) - w.diff().abs().sum(axis=1).fillna(0) * E.COST
    return trades, ens.iloc[200:]


CORE_META = {"donchian": ("donchian_1d", "Věž Donchian · průraz denního kanálu", "outcomes.jsonl"),
             "pullback": ("pullback_1d", "Věž Pullback · návrat k trendu", "outcomes.jsonl"),
             "pyramida": (None, "Pyramida · přikupování (P2)", "pyramid_outcomes.jsonl")}


def core_accounts(scache):
    trades, ens = core_backtests(scache)
    out = []
    for sid, (name, tag, fn) in CORE_META.items():
        out.append({"id": "core:" + sid, "kind": "core", "ref": sid, "name": tag, "tf": "1d", "coins": COINS8,
                    "backtest": account(trades[sid]),
                    "live": account(core_paper(ROOT / "research" / fn, name), start=CORE_LIVE_START)})
    out.append({"id": "core:ensemble", "kind": "core", "ref": "ensemble", "name": "Ensemble · trendová alokace (jen long)",
                "tf": "1d", "coins": COINS8, "backtest": returns_account(ens), "live": ens_live()})
    for a in out:
        print(f"{a['id']}: zpětný test {a['backtest']['net']} USDT, papír {a['live']['net']} USDT", flush=True)
    return out


def ens_live(path=ROOT / "research" / "equity_log.jsonl", capital=5000.0):
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()] if path.exists() else []
    pts = []
    for x in rows:
        v = (x.get("parts") or {}).get("ensemble")
        if v is not None and x.get("t", "") >= CORE_LIVE_START:
            pts.append((_ts(x["t"]), START_CASH * (1 + float(v) / capital)))
    res = summarize(pts, [], _ts(CORE_LIVE_START), datetime.now(timezone.utc))
    res.update({"n_trades": None, "trades_per_month": None, "lose_streak": None})
    return res


def main():
    cache = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cache")
    scache = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "scanner" / "cache")
    patch_fetch()
    accounts = []
    for part in (lambda: lab_accounts(cache), lambda: core_accounts(scache)):
        try:
            accounts += part()
        except Exception as exc:
            print(f"část selhala: {exc.__class__.__name__}: {exc}", flush=True)
    accounts = [a for a in accounts if a.get("backtest")]
    if not accounts:
        print("žádný účet – nic se neukládá")
        return 1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
    for a in accounts:
        a["updated"] = now
    OUT.write_text(json.dumps({"updated": now, "start_cash": START_CASH, "risk_pct": RISK * 100,
                               "accounts": accounts}, ensure_ascii=False, separators=(",", ":"), default=str) + "\n",
                   encoding="utf-8")
    print(f"uloženo {len(accounts)} účtů → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
