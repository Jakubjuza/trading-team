#!/usr/bin/env python3
"""Export desku jako jednoho agenta pro Agentárium → reports/agentarium/trading-desk.json.

Datový model podle zadání Agentária (Agent): popis, broker, verze, backtest (orientační), live, obchody.
  • backtest: denní hodnota papírového účtu 10 000 USD do dne spuštění verze – jádro (donchian_1d + pullback_1d,
    riziko 0,5 % na obchod, R připsané v den uzavření) + 🔺 pyramida (P2) + 🧭 ensemble (50 % kapitálu), stejně jako
    tyto části běží papírově. Signály a portfolio z research/experiments/pyramid.py, ensemble z experiments/ensemble.py.
    Kombinace všech tří částí jako celek předem testovaná nebyla (testy: reports/pyramid.md, reports/portfolio_review.md).
  • live: research/equity_log.jsonl – denní snímek papírového účtu (`paper`) a spotového DEMO účtu OKX (`demo`).
    Ani jedno není ověření od brokera s reálnými penězi; JSON to nese v `verification`.
Metriky (výnos, propad, Sharpe, úroveň…) si web počítá z dat sám; tady jsou jen vstupy.

    python3 research/export_agentarium.py [scanner/cache]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "experiments"))
OUT = ROOT / "reports" / "agentarium" / "trading-desk.json"
VERSION = "1.0"
LIVE_START = "2026-10-27"          # verze 1.0: od tohoto dne se zapisuje denní snímek účtu (scanner/equity.py)
ACCOUNT = 10000.0


def backtest_series(cache):
    sys.argv = [sys.argv[0], str(cache)]
    import ensemble as E   # noqa: E402  (research/experiments)
    import pyramid as P    # noqa: E402
    cfg = yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text())
    risk = cfg.get("risk_pct", 0.5) / 100
    frames = {c: E.load(c) for c in E.COINS}
    idx = frames["BTC"].index
    rets = pd.DataFrame({c: f["Close"].pct_change() for c, f in frames.items()}).reindex(idx)
    w = pd.DataFrame(0.0, index=idx, columns=E.COINS)
    for c, f in frames.items():
        vol = f["Close"].pct_change().rolling(30).std() * np.sqrt(365)
        w[c] = (E.coin_signal(f) * np.minimum(1, 0.40 / vol) / len(E.COINS)).reindex(idx).fillna(0)
    turnover = w.diff().abs().sum(axis=1).fillna(0)
    ens = (w.shift(1) * rets.fillna(0)).sum(axis=1) - turnover * E.COST
    df = P.build()
    trades = []
    daily = pd.Series(0.0, index=idx)
    for var, part in (("P0", "jádro"), ("P2", "pyramida")):
        for x in P.portfolio(df[df["var"] == var]).itertuples():
            d = x.exit.normalize()
            if d in daily.index:
                daily[d] += risk * x.r
            trades.append({"t": x.exit.date().isoformat(), "opened": x.time.date().isoformat(), "symbol": f"{x.coin}/USDT",
                           "side": "buy" if x.dir == "long" else "sell", "r": round(float(x.r), 3),
                           "pnl": round(float(x.r) * risk * ACCOUNT, 2), "part": part, "strategy": x.strategy})
    total = daily + 0.5 * ens
    start = idx[200]
    end = pd.Timestamp(LIVE_START, tz="UTC")
    total = total[(total.index >= start) & (total.index < end)]
    eq = ACCOUNT * (1 + total).cumprod()
    series = [{"t": d.date().isoformat(), "equity": round(float(v), 2)} for d, v in eq.items()]
    trades = sorted([t for t in trades if start.date().isoformat() <= t["t"] < LIVE_START], key=lambda t: t["t"])
    return series, trades


def live_series():
    from scanner.equity import read
    rows = [r for r in read() if r.get("t", "") >= LIVE_START]
    paper = [{"t": r["t"], "equity": r["paper"]} for r in rows if r.get("paper") is not None]
    demo = [{"t": r["t"], "equity": r["demo"]} for r in rows if r.get("demo") is not None]
    return paper, demo, (rows[-1].get("demo_ccy") if rows else "USDC")


def live_trades():
    out = []
    for path, part in ((ROOT / "research" / "outcomes.jsonl", "jádro"), (ROOT / "research" / "pyramid_outcomes.jsonl", "pyramida")):
        if not path.exists():
            continue
        cfg = yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text())
        risk_usd = cfg.get("account_size", 10000) * cfg.get("risk_pct", 0.5) / 100
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("r") is None or (r.get("closed_at") or "")[:10] < LIVE_START:
                continue
            out.append({"t": r["closed_at"][:10], "symbol": r.get("symbol"), "side": "buy" if r.get("direction") == "long" else "sell",
                        "r": r["r"], "pnl": round(r["r"] * risk_usd, 2), "part": part, "strategy": r.get("strategy")})
    return sorted(out, key=lambda t: t["t"])


def build(cache=ROOT / "scanner" / "cache"):
    bt, bt_trades = backtest_series(cache)
    paper, demo, demo_ccy = live_series()
    lt = live_trades()
    hold = [(pd.Timestamp(t["t"]) - pd.Timestamp(t["opened"])).days for t in bt_trades]
    months = max(1.0, (pd.Timestamp(bt[-1]["t"]) - pd.Timestamp(bt[0]["t"])).days / 30.44)
    return {
        "id": "trading-desk", "name": "Trading desk", "createdBy": "platform", "sample": False,
        "tagline": "Tým AI agentů na trendy v kryptu",
        "style": "Trend following (denní graf)",
        "description": ("Tým agentů, který hlídá 8 kryptoměn a obchoduje průrazy a návraty v trendu na denním grafu. "
                        "Ke každému signálu jádra se přidává pyramida (přikupuje do vydělávající pozice) a vedle běží "
                        "trendová alokace jen long s řízením volatility. Často prohrává malé obchody a vydělává na "
                        "několika velkých. Strategie se mění jen po předem stanoveném testu."),
        "market": "Krypto (BTC, ETH, SOL, XRP, ADA, LINK, AVAX, DOGE)", "broker": "OKX (demo účet)",
        "model": "Claude", "version": VERSION, "liveStart": LIVE_START,
        "verification": {"live": "paper", "demo": "okx-demo",
                         "note": ("Živá křivka je papírový účet, který počítá sám skener desku (signály a ceny z burzy), "
                                  "a vedle něj simulovaný DEMO účet OKX. Neověřuje ji broker s reálnými penězi."),
                         "demoCurrency": demo_ccy},
        "expectedAnnualReturn": round(((bt[-1]["equity"] / bt[0]["equity"]) ** (365 / max(1, len(bt))) - 1) * 100, 1),
        "expectedNote": "roční výnos backtestu (orientační, po nákladech)",
        "tradesPerMonth": round(len(bt_trades) / months, 1),
        "winRate": round(100 * sum(t["r"] > 0 for t in bt_trades) / max(1, len(bt_trades))),
        "avgHoldDays": round(float(np.mean(hold)), 1) if hold else None,
        "statsSource": "backtest",
        "minHorizonMonths": 12, "priceCzk": 0,
        "backtest": bt, "live": paper, "demo": demo,
        "trades": lt, "backtestTrades": bt_trades,
        "sources": ["reports/pyramid.md", "reports/portfolio_review.md", "reports/setup_library.md"],
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    agent = build(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(agent, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT}: backtest {len(agent['backtest'])} dní ({agent['backtest'][0]['t']} – {agent['backtest'][-1]['t']}), "
          f"{len(agent['backtestTrades'])} obchodů v backtestu, živě {len(agent['live'])} dní, "
          f"roční výnos backtestu {agent['expectedAnnualReturn']} %, úspěšnost {agent['winRate']} %, "
          f"{agent['tradesPerMonth']} obchodů/měsíc, Ø držení {agent['avgHoldDays']} dní")


if __name__ == "__main__":
    main()
