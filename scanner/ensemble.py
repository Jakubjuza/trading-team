"""🧭 Ensemble – samostatná část: trendová alokace (Donchian ensemble s cílovou volatilitou), jen long.

Ověřeno v research/experiments/ensemble.py (reports/portfolio_review.md; podle Zarattini, Pagani, Barbon: Catching
Crypto Trends). Jednou denně po uzavření denní svíčky:
  • pro každou minci 5 modelů Donchian (okna `windows`): long od zavření nad max. High předchozích N dní do zavření pod
    min. Low předchozích N/2 dní; signál = podíl modelů v longu (0–1),
  • cílová váha = signál × min(1, `target_vol` / roční volatilita za 30 dní) / počet mincí,
  • papírová kniha s kapitálem `capital_frac` × account_size se přenastaví na cílové váhy (obchod jen při změně
    ≥ `min_rebalance` kapitálu), náklady z configu na obchodovaný objem,
  • `demo: true` → stejné změny zrcadlí na spotovém DEMO účtu OKX (páry v `demo.quote`, jen mince, které tam jsou).
Zprávy jen při vstupu do mince / výstupu z ní; výkon je v týdenní tabulce. Nic se neposílá na ostrý účet.
"""
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from scanner import notify

DEFAULTS = {"enabled": False, "windows": [10, 20, 40, 80, 160], "target_vol": 0.40, "capital_frac": 0.5,
            "min_rebalance": 0.01, "demo": False}


def params(cfg):
    return {**DEFAULTS, **(cfg.get("ensemble") or {})}


def signal(df, windows):
    """Podíl Donchian modelů v longu na poslední uzavřené svíčce."""
    hi, lo, cl = df["High"], df["Low"], df["Close"]
    states = []
    for n in windows:
        up = (cl > hi.rolling(n).max().shift(1)).values
        dn = (cl < lo.rolling(n // 2).min().shift(1)).values
        s = 0
        for u, d in zip(up, dn):
            s = 1 if u else (0 if d else s)
        states.append(s)
    return float(np.mean(states))


def target_weights(daily, p):
    w = {}
    for coin, df in daily.items():
        if df is None or len(df) < max(p["windows"]) + 31:
            continue
        vol = df["Close"].pct_change().iloc[-30:].std() * np.sqrt(365)
        w[coin] = signal(df, p["windows"]) * (min(1.0, p["target_vol"] / vol) if vol and vol > 0 else 0.0) / len(daily)
    return w


def update(cfg, state, frames, cost_pct, dry_run=False, send=None, demo=None):
    """Denní přenastavení papírové knihy (a případně dema). Vrací zprávu nebo None."""
    p = params(cfg)
    if not p["enabled"]:
        return None
    daily = {sym.split("/")[0]: df for (sym, tf), df in frames.items() if tf == "1d" and df is not None and len(df)}
    if not daily:
        return None
    last = max(df.index[-1] for df in daily.values())
    cap = cfg.get("account_size", 10000) * p["capital_frac"]
    st = state.data.setdefault("ensemble", {"cash": cap, "start_equity": cap, "qty": {}, "weights": {}, "equity": [],
                                            "last_day": None, "demo_qty": {}})
    day = last.date().isoformat()
    if st.get("last_day") == day:
        return None
    prices = {c: float(df["Close"].iloc[-1]) for c, df in daily.items()}
    equity = st["cash"] + sum(q * prices.get(c, 0) for c, q in st["qty"].items())
    tw = target_weights(daily, p)
    cost = cost_pct / 100
    trades = []
    for c, w in tw.items():
        cur = st["qty"].get(c, 0.0) * prices[c]
        tgt = w * equity
        if abs(tgt - cur) < p["min_rebalance"] * equity and not (tgt == 0 and cur > 0):
            continue
        dq = (tgt - cur) / prices[c]
        st["qty"][c] = st["qty"].get(c, 0.0) + dq
        st["cash"] -= dq * prices[c] + abs(dq) * prices[c] * cost
        trades.append((c, dq))
    for c in [c for c, q in st["qty"].items() if abs(q) < 1e-12]:
        del st["qty"][c]
    equity = st["cash"] + sum(q * prices.get(c, 0) for c, q in st["qty"].items())
    old_w = st.get("weights", {})
    st["weights"] = {c: round(w, 4) for c, w in tw.items()}
    st["equity"] = (st.get("equity", []) + [[day, round(equity, 2)]])[-400:]
    st["last_day"] = day
    if p["demo"] and demo is not None and trades and not dry_run:
        demo_rebalance(demo, st, trades, prices)
    entered = [c for c, w in tw.items() if w > 0 and old_w.get(c, 0) == 0]
    exited = [c for c, w in old_w.items() if w > 0 and tw.get(c, 0) == 0]
    if not (entered or exited):
        return None
    start = st.get("start_equity", cap)
    parts = [f"{c} {old_w.get(c, 0) * 100:.0f} → {tw.get(c, 0) * 100:.0f} %" for c in entered + exited]
    expo = sum(tw.values()) * 100
    msg = (f"🧭 Ensemble (papírově): {' · '.join(parts)}; v trhu {expo:.0f} % kapitálu, hodnota "
           f"{notify.fmt(equity)} USD ({f'{(equity / start - 1) * 100:+.1f}'.replace('.', ',')} %).")
    print(msg)
    tg = send or (None if dry_run or not cfg.get("notify", {}).get("telegram", True) else notify.telegram)
    if tg:
        tg(msg)
    return msg


def demo_rebalance(broker, st, trades, prices):
    """Zrcadlení na spotovém demu: nákup/prodej rozdílu množství (prodává jen to, co ensemble na demu koupil)."""
    from scanner.demo import LOG, spot_symbol
    held = st.setdefault("demo_qty", {})
    for coin, dq in trades:
        sym = spot_symbol(f"{coin}/USDT", getattr(broker, "quote", None))
        try:
            broker.ex.load_markets()
            if sym not in broker.ex.markets:
                continue
            if dq < 0:
                dq = -min(-dq, held.get(coin, 0.0))
            amt = float(broker.ex.amount_to_precision(sym, abs(dq)))
            mn = ((broker.ex.market(sym).get("limits") or {}).get("amount") or {}).get("min") or 0
            if amt <= 0 or amt < mn:
                continue
            side = "buy" if dq > 0 else "sell"
            o = broker.settled(broker.ex.create_order(sym, "market", side, amt, None,
                                                      {"tgtCcy": "base_ccy"} if side == "buy" else {}), sym)
            filled = float(o.get("filled") or amt)
            held[coin] = max(0.0, held.get(coin, 0.0) + (filled if side == "buy" else -filled))
            rec = {"event": "ensemble", "symbol": sym, "side": side, "amount": filled, "price": o.get("average"),
                   "paper_price": prices.get(coin), "time": datetime.now(timezone.utc).isoformat()}
        except Exception as exc:
            rec = {"event": "ensemble_error", "symbol": sym, "error": f"{exc.__class__.__name__}: {str(exc)[:160]}",
                   "time": datetime.now(timezone.utc).isoformat()}
            print(f"[demo ensemble {sym}] {exc}", file=sys.stderr)
        try:
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass


def week_change(state, since_day):
    """Změna hodnoty knihy od `since_day` a celkem (v %), aktuální expozice (v % kapitálu)."""
    st = state.data.get("ensemble") or {}
    eq = st.get("equity") or []
    if not eq:
        return None
    prev = [e for d, e in eq if d < since_day]
    ref = prev[-1] if prev else (st.get("start_equity") or eq[0][1])
    first = st.get("start_equity") or eq[0][1]
    return {"week": (eq[-1][1] / ref - 1) * 100, "total": (eq[-1][1] / first - 1) * 100,
            "expo": sum((st.get("weights") or {}).values()) * 100, "equity": eq[-1][1]}
