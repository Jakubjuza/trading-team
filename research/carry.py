#!/usr/bin/env python3
"""Carry z fundingu (delta-neutrální): long spot + short perpetual stejné velikosti → cena se vyruší, inkasuje se
funding, který platí longy na perpetualu (Hyperliquid, každou hodinu). Bez AI.

Pravidlo (stanovené předem, neladěné): rozhoduje se denně v 00:00 UTC podle průměru fundingu za 7 dní.
Vstup, když je průměr > ENTER_APR (10 % p.a.), výstup, když klesne < EXIT_APR (0 %). Náklady: spot 0,10 % + skluz
0,05 %, perp 0,045 % + skluz 0,05 % – na vstupu i výstupu (4 obchody). Kapitál = spot + marže perpu při páce 2×
(1,5 × velikost pozice). Rozdíl ceny spotu a perpu (basis) se zanedbává – v praxi kolísá, dlouhodobě ~0.

Rizika, která backtest nezachytí: likvidace short perpu při prudkém růstu, když se nedoplní marže; riziko burzy /
smart contractu; dočasný rozdíl cen spot × perp. Proto jen papírově, dokud to uživatel výslovně nepovolí.

Použití (běží v GitHub Actions – Hyperliquid je ze sandboxu blokovaný):
    python3 research/carry.py --report [--days 730] [--out reports/carry.md]
    python3 research/carry.py --now          # aktuální 7denní funding a stav pravidla
"""
import argparse
import json
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
HL_URL = "https://api.hyperliquid.xyz/info"
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "AVAX", "LINK", "ADA"]
ENTER_APR, EXIT_APR = 10.0, 0.0
COST_ROUND_TRIP = 2 * (0.10 + 0.05 + 0.045 + 0.05) / 100          # vstup + výstup, obě nohy, podíl velikosti pozice
CAPITAL_PER_NOTIONAL = 1.5


def _post(payload, timeout=15):
    import requests
    r = requests.post(HL_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def funding_history(coin, start, end=None, post=_post, pause=0.6):
    """Hodinový funding (podíl za hodinu) od `start`; stránkuje po 500 záznamech."""
    end = end or datetime.now(timezone.utc)
    t, rows = int(start.timestamp() * 1000), []
    while t < int(end.timestamp() * 1000):
        batch = post({"type": "fundingHistory", "coin": coin, "startTime": t})
        if not batch:
            break
        rows += batch
        last = int(batch[-1]["time"])
        if last <= t:
            break
        t = last + 1
        if len(batch) < 500:
            break
        _time.sleep(pause)
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series({pd.Timestamp(int(r["time"]), unit="ms", tz="UTC"): float(r["fundingRate"]) for r in rows}).sort_index()
    return s[~s.index.duplicated()]


def backtest(f, enter=ENTER_APR, exit_=EXIT_APR, cost=COST_ROUND_TRIP):
    """f = hodinový funding. Denní rozhodnutí podle 7denního průměru (jen minulost). Výnos v % kapitálu."""
    f = f.sort_index()
    apr7 = f.rolling("7D").mean() * 24 * 365 * 100
    days = pd.date_range(f.index[0].normalize() + pd.Timedelta(days=8), f.index[-1].normalize(), freq="1D", tz="UTC")
    pos, pnl, trades, in_hours = False, [], 0, 0
    for d0, d1 in zip(days[:-1], days[1:]):
        a = apr7[apr7.index < d0]
        if not len(a):
            continue
        a = a.iloc[-1]
        day_cost = 0.0
        if not pos and a > enter:
            pos, trades, day_cost = True, trades + 1, cost / 2
        elif pos and a < exit_:
            pos, day_cost = False, cost / 2
        earned = float(f[(f.index >= d0) & (f.index < d1)].sum()) if pos else 0.0
        in_hours += int(((f.index >= d0) & (f.index < d1)).sum()) if pos else 0
        pnl.append((d1, (earned - day_cost) / CAPITAL_PER_NOTIONAL))
    s = pd.Series(dict(pnl))
    if not len(s):
        return {}
    eq = s.cumsum()
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    yr = s.groupby(s.index.year).sum() * 100
    return {"apr_on_capital_pct": round(float(s.sum()) / yrs * 100, 2), "max_dd_pct": round(float((eq.cummax() - eq).max()) * 100, 2),
            "time_in_pct": round(in_hours / max(1, len(f)) * 100, 1), "round_trips": trades,
            "worst_month_pct": round(float(s.resample("ME").sum().min()) * 100, 2),
            "years": {int(k): round(float(v), 2) for k, v in yr.items()}, "from": s.index[0].date().isoformat(),
            "funding_mean_apr_pct": round(float(f.mean()) * 24 * 365 * 100, 2),
            "funding_negative_hours_pct": round(float((f < 0).mean()) * 100, 1)}


def current(coins=COINS, post=_post):
    """7denní průměr fundingu (p.a.) a co by teď pravidlo dělalo."""
    start = datetime.now(timezone.utc) - timedelta(days=8)
    out = {}
    for c in coins:
        try:
            f = funding_history(c, start, post=post, pause=0.2)
            a = float(f[f.index >= f.index[-1] - pd.Timedelta(days=7)].mean()) * 24 * 365 * 100
            out[c] = {"apr_7d_pct": round(a, 1), "last_apr_pct": round(float(f.iloc[-1]) * 24 * 365 * 100, 1),
                      "rule": "vstup (carry)" if a > ENTER_APR else "mimo" if a < EXIT_APR else "jen držet, pokud už je otevřeno"}
        except Exception as exc:
            out[c] = {"error": f"{exc.__class__.__name__}: {str(exc)[:80]}"}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.now:
        print(json.dumps(current(), ensure_ascii=False, indent=1))
        return
    start = datetime.now(timezone.utc) - timedelta(days=a.days)
    res, md = {}, [f"# Carry z fundingu – backtest ({datetime.now(timezone.utc):%Y-%m-%d})", "",
                   f"Hyperliquid, posledních {a.days} dní, pravidlo vstup > {ENTER_APR:g} % p.a. / výstup < {EXIT_APR:g} % "
                   f"(7denní průměr), náklady {COST_ROUND_TRIP * 100:.2f} % velikosti pozice za celý obchod, kapitál 1,5× pozice.", "",
                   "| Mince | Výnos p.a. na kapitál | Max. propad | V pozici | Obchodů | Nejhorší měsíc | Ø funding p.a. | Hodin se záporným fundingem | Po letech |",
                   "|---|---|---|---|---|---|---|---|---|"]
    for c in COINS:
        try:
            f = funding_history(c, start)
            r = backtest(f)
            always = backtest(f, enter=-1e9, exit_=-1e9)                 # srovnání: pořád v pozici
            r["always_in_apr_pct"] = always.get("apr_on_capital_pct")
            res[c] = r
            md.append(f"| {c} | {r['apr_on_capital_pct']:+.2f} % (pořád v pozici {r['always_in_apr_pct']:+.2f} %) | "
                      f"{r['max_dd_pct']:.2f} % | {r['time_in_pct']:.0f} % | {r['round_trips']} | {r['worst_month_pct']:+.2f} % | "
                      f"{r['funding_mean_apr_pct']:+.1f} % | {r['funding_negative_hours_pct']:.0f} % | {r['years']} |")
        except Exception as exc:
            res[c] = {"error": f"{exc.__class__.__name__}: {exc}"}
            md.append(f"| {c} | chyba: {exc.__class__.__name__} | | | | | | | |")
        print(c, json.dumps(res[c], ensure_ascii=False))
    md += ["", "Rizika mimo backtest: likvidace short perpu při prudkém růstu (marže), riziko burzy, kolísání basis. "
           "Jen papírově. Nejde o finanční poradenství."]
    text = "\n".join(md) + "\n"
    print(text)
    if a.out:
        a.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
