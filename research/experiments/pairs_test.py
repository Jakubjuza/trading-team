#!/usr/bin/env python3
"""Test párového obchodování („Don't trade stocks, trade their relationship“).

Ověřuje tvrzení z videa: KO/PEP „kup toho, kdo zaostal, shortuj lídra“ = +46 000 %.
Testuje dvě pravidla na akciových i krypto párech, hrubě i po nákladech,
a rozdělení IS 60 % / OOS 20 % / odložený vzorek 20 %.

  A) laggard  – denně: long akcie s horším výnosem za posledních N dní, short lepší
                 (varianty N = 5, 20, 60, 120, 250 → ukáže citlivost na parametr)
  B) zscore   – log poměr cen, z-skóre za 60 dní; vstup |z| > 2, výstup z přes 0,
                 stop |z| > 4 (klasický „mezera se otevře, pak se zavře“)

Obě nohy mají po 1,0 nominálu (long $1 + short $1), signál se obchoduje
až na další svíčce (bez pohledu do budoucnosti).
Náklady: --cost-bps za každou otočenou jednotku nominálu (poplatek + skluz),
--borrow % ročně za short akcií (u krypta funding zjednodušeně stejné číslo).

Spuštění:  python3 pairs_test.py               (všechny páry)
           python3 pairs_test.py --pairs KO/PEP BTC-USD/ETH-USD
Výstup:    pairs_report.md, pairs_results.csv, pairs_KO_PEP.png (vedle skriptu nebo --out)
Data: Yahoo Finance (yfinance, jinak přímé volání chart API). Nejde o finanční poradenství.
"""
import argparse
import json
import math
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

STOCK_PAIRS = [
    "KO/PEP", "WMT/TGT", "HD/LOW", "V/MA", "XOM/CVX", "UPS/FDX", "F/GM", "JPM/BAC",
    "MCD/YUM", "DAL/UAL", "LMT/NOC", "NKE/UAA", "PFE/MRK", "GS/MS", "INTC/AMD",
    "COST/BJ", "UBER/LYFT", "VZ/T", "MAR/HLT", "PG/CL", "CAT/DE", "NFLX/DIS",
    "AAL/LUV", "KR/ACI",
]
CRYPTO_PAIRS = ["BTC-USD/ETH-USD", "ETH-USD/SOL-USD", "BTC-USD/SOL-USD", "BTC-USD/XRP-USD"]
LOOKBACKS = [5, 20, 60, 120, 250]


# ---------------------------------------------------------------- data
def _yahoo_direct(ticker):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           "?period1=0&period2=9999999999&interval=1d&events=div,split")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    ts = pd.to_datetime(j["timestamp"], unit="s").normalize()
    adj = j["indicators"].get("adjclose", [{}])[0].get("adjclose") \
        or j["indicators"]["quote"][0]["close"]
    return pd.Series(adj, index=ts, name=ticker, dtype=float).dropna()


def load(ticker, cache_dir):
    path = os.path.join(cache_dir, f"{ticker}.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0].rename(ticker)
    s = None
    try:
        import yfinance as yf
        df = yf.download(ticker, period="max", auto_adjust=True, progress=False)
        if len(df):
            c = df["Close"]
            s = (c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c).rename(ticker).dropna()
    except Exception as e:  # noqa: BLE001
        print(f"  yfinance {ticker}: {e}", file=sys.stderr)
    if s is None or not len(s):
        s = _yahoo_direct(ticker)
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    s = s[~s.index.duplicated()]
    s.to_csv(path)
    return s


# ---------------------------------------------------------------- strategie
def pos_laggard(a, b, n):
    """+1 = long a / short b (a zaostal), −1 = opačně."""
    ra, rb = np.log(a).diff(n), np.log(b).diff(n)
    return np.sign(rb - ra).replace(0, np.nan).ffill().fillna(0)


def pos_zscore(a, b, win=60, z_in=2.0, z_out=0.0, z_stop=4.0):
    spread = np.log(a) - np.log(b)
    z = (spread - spread.rolling(win).mean()) / spread.rolling(win).std()
    pos, out = 0.0, []
    for v in z.values:
        if np.isnan(v):
            out.append(0.0); continue
        if pos == 0:
            if v > z_in and v < z_stop:
                pos = -1.0          # a je drahé vůči b → short a, long b
            elif v < -z_in and v > -z_stop:
                pos = 1.0
        else:
            if abs(v) >= z_stop or (pos == -1 and v <= z_out) or (pos == 1 and v >= -z_out):
                pos = 0.0
        out.append(pos)
    return pd.Series(out, index=z.index)


def run(a, b, pos, cost_bps, borrow_pct, periods):
    ra, rb = a.pct_change().fillna(0), b.pct_change().fillna(0)
    p = pos.shift(1).fillna(0)                       # obchod až další svíčku
    gross = p * (ra - rb)                            # long $1 / short $1
    turnover = 2 * (p - p.shift(1).fillna(0)).abs()  # obě nohy
    cost = turnover * cost_bps / 1e4 + (p != 0) * borrow_pct / 100 / periods
    return gross, gross - cost, int((turnover > 0).sum())


def stats(r, periods):
    r = r.dropna()
    if len(r) < 20:
        return dict(total=np.nan, cagr=np.nan, sharpe=np.nan, maxdd=np.nan)
    eq = (1 + r).cumprod()
    yrs = len(r) / periods
    total = eq.iloc[-1] - 1
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1.0
    sd = r.std()
    sharpe = r.mean() / sd * math.sqrt(periods) if sd > 0 else np.nan
    maxdd = (eq / eq.cummax() - 1).min()
    return dict(total=total, cagr=cagr, sharpe=sharpe, maxdd=maxdd)


def splits(idx):
    n = len(idx)
    i1, i2 = int(n * 0.6), int(n * 0.8)
    return {"IS": idx[:i1], "OOS": idx[i1:i2], "HOLD": idx[i2:]}


# ---------------------------------------------------------------- hlavní běh
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", default=None)
    ap.add_argument("--cost-bps", type=float, default=5.0, help="bps za otočenou jednotku nominálu")
    ap.add_argument("--crypto-cost-bps", type=float, default=10.0)
    ap.add_argument("--borrow", type=float, default=0.5, help="%% ročně za short (akcie)")
    ap.add_argument("--crypto-borrow", type=float, default=8.0, help="%% ročně (funding/půjčka)")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--synthetic", action="store_true", help="test skriptu bez sítě")
    args = ap.parse_args()

    pairs = args.pairs or STOCK_PAIRS + CRYPTO_PAIRS
    cache = os.path.join(args.out, "pairs_cache")
    os.makedirs(cache, exist_ok=True)
    rows, failed, ko_curves = [], [], None

    for pair in pairs:
        ta, tb = pair.split("/")
        crypto = "-USD" in pair
        periods = 365 if crypto else 252
        cbps = args.crypto_cost_bps if crypto else args.cost_bps
        borrow = args.crypto_borrow if crypto else args.borrow
        try:
            if args.synthetic:
                rng = np.random.default_rng(abs(hash(pair)) % 2**32)
                idx = pd.bdate_range("1990-01-01", periods=6000)
                common = rng.normal(3e-4, 0.01, len(idx))
                a = pd.Series(100 * np.exp(np.cumsum(common + rng.normal(0, .008, len(idx)))), idx)
                b = pd.Series(100 * np.exp(np.cumsum(common + rng.normal(0, .008, len(idx)))), idx)
            else:
                a, b = load(ta, cache), load(tb, cache)
        except Exception as e:  # noqa: BLE001
            failed.append(f"{pair}: {e}"); print(f"✗ {pair}: {e}", file=sys.stderr); continue
        df = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        if len(df) < 300:
            failed.append(f"{pair}: málo dat ({len(df)})"); continue
        a, b = df["a"], df["b"]
        print(f"✓ {pair}: {df.index[0].date()} – {df.index[-1].date()} ({len(df)} svíček)")

        variants = {f"laggard_{n}": pos_laggard(a, b, n) for n in LOOKBACKS}
        variants["zscore_60"] = pos_zscore(a, b)
        for name, pos in variants.items():
            gross, net, trades = run(a, b, pos, cbps, borrow, periods)
            row = dict(pair=pair, kind="krypto" if crypto else "akcie", rule=name,
                       start=str(df.index[0].date()), end=str(df.index[-1].date()),
                       changes=trades)
            for tag, r in (("gross", gross), ("net", net)):
                for k, v in stats(r, periods).items():
                    row[f"{tag}_{k}"] = v
            for part, ix in splits(df.index).items():
                s = stats(net.loc[ix], periods)
                row[f"{part}_net_cagr"], row[f"{part}_net_sharpe"] = s["cagr"], s["sharpe"]
            rows.append(row)
            if pair == "KO/PEP":
                ko_curves = ko_curves or {}
                ko_curves[name] = ((1 + gross).cumprod(), (1 + net).cumprod())

    if not rows:
        print("Žádná data – zkontroluj přístup na *.yahoo.com.\n" + "\n".join(failed))
        sys.exit(1)

    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(args.out, "pairs_results.csv"), index=False)
    write_report(res, failed, args, os.path.join(args.out, "pairs_report.md"))
    if ko_curves:
        plot_ko(ko_curves, os.path.join(args.out, "pairs_KO_PEP.png"))
    print(f"\nHotovo → {args.out}/pairs_report.md")


def pct(x):
    return "–" if pd.isna(x) else f"{x*100:+,.0f} %".replace(",", " ")


def num(x):
    return "–" if pd.isna(x) else f"{x:+.2f}"


def write_report(res, failed, args, path):
    L = ["# Test párového obchodování", "",
         f"Náklady: akcie {args.cost_bps} bps/otočka + short {args.borrow} %/rok, "
         f"krypto {args.crypto_cost_bps} bps + {args.crypto_borrow} %/rok. "
         "Long $1 + short $1, signál obchodován další svíčku. Split IS 60 / OOS 20 / HOLD 20 %.", ""]

    ko = res[res.pair == "KO/PEP"]
    if len(ko):
        L += ["## 1. KO/PEP – tvrzení z videa (+46 000 %)", "",
              "| pravidlo | období | celkem hrubě | celkem po nákladech | CAGR po nákl. | Sharpe po nákl. | max DD | HOLD CAGR |",
              "|---|---|---|---|---|---|---|---|"]
        for _, r in ko.iterrows():
            L.append(f"| {r.rule} | {r.start[:4]}–{r.end[:4]} | {pct(r.gross_total)} | {pct(r.net_total)} | "
                     f"{pct(r.net_cagr)} | {num(r.net_sharpe)} | {pct(r.net_maxdd)} | {pct(r.HOLD_net_cagr)} |")
        L.append("")

    for kind in ("akcie", "krypto"):
        sub = res[res.kind == kind]
        if not len(sub):
            continue
        L += [f"## 2. Souhrn podle pravidla – {kind} ({sub.pair.nunique()} párů)", "",
              "| pravidlo | páry se ziskem po nákl. | medián CAGR hrubě | medián CAGR po nákl. | medián Sharpe po nákl. | medián OOS CAGR | medián HOLD CAGR |",
              "|---|---|---|---|---|---|---|"]
        for rule, g in sub.groupby("rule"):
            L.append(f"| {rule} | {(g.net_total > 0).sum()}/{len(g)} | {pct(g.gross_cagr.median())} | "
                     f"{pct(g.net_cagr.median())} | {num(g.net_sharpe.median())} | "
                     f"{pct(g.OOS_net_cagr.median())} | {pct(g.HOLD_net_cagr.median())} |")
        L.append("")

    best = res.sort_values("net_sharpe", ascending=False).head(10)
    L += ["## 3. Top 10 kombinací (pár × pravidlo) podle Sharpe po nákladech", "",
          "Pozor: vybrané zpětně z mnoha pokusů – rozhoduje HOLD sloupec.", "",
          "| pár | pravidlo | CAGR po nákl. | Sharpe | OOS CAGR | HOLD CAGR |", "|---|---|---|---|---|---|"]
    for _, r in best.iterrows():
        L.append(f"| {r.pair} | {r.rule} | {pct(r.net_cagr)} | {num(r.net_sharpe)} | "
                 f"{pct(r.OOS_net_cagr)} | {pct(r.HOLD_net_cagr)} |")
    L.append("")
    if failed:
        L += ["## Nenačteno", ""] + [f"- {f}" for f in failed] + [""]
    L += ["Zdroj dat: Yahoo Finance (upravené ceny). Nejde o finanční poradenství."]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def plot_ko(curves, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for name in ("laggard_20", "laggard_60", "laggard_250", "zscore_60"):
        if name in curves:
            g, n = curves[name]
            line, = ax.plot(g.index, g.values, lw=1, alpha=.45, label=f"{name} hrubě")
            ax.plot(n.index, n.values, lw=1.6, color=line.get_color(), label=f"{name} po nákladech")
    ax.set_yscale("log")
    ax.axhline(1, color="grey", lw=.6)
    ax.set_title("KO/PEP – long zaostávající / short lídr (log)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


if __name__ == "__main__":
    main()
