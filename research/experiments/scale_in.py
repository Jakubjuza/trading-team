"""Dokupování při poklesu s malou pákou, částečný řez ztráty, znovuotevření a dlouhé držení po obratu (stanoveno PŘEDEM, 26. 10. 2026).

Otázka uživatele: začít malou testovací pozicí při poklesu, postupně dokupovat, při určité ztrátě část prodat
se ztrátou a znovu otevřít níž (nebo na místě řezu), aby se snížila průměrná cena, a po obratu držet co nejdéle.
Navazuje na reports/capitulation.md (dno z denních dat načasovat nešlo) a reports/pyramid.md (přikupování do ZISKU prošlo).

Data: denní svíčky ~10 let, 8 mincí (stejná cache jako scanner/evaluate.py). Každá mince má vlastní podúčet 1 000 USD,
portfolio = součet (8 000 USD). Jen long. Mezi kampaněmi hotovost.
Spouštěč kampaně: close ≤ 80 % maxima close za 30 dní (pokles ≥ 20 %), žádná otevřená kampaň.
Kampaň (E0 = equity podúčtu na začátku, kus = 0,25 × E0 notional):
  test     1 kus na zavření spouštěcí svíčky,
  dokup    další kus pokaždé, když Low ≤ 95 % ceny posledního nákupu (limit na té ceně); max. 5 dokupů
           → nejvýš 6 kusů = 1,5 × E0 (páka max. ~1,5×; hotovost pod nulou = půjčka 10 % p.a.),
  řez      (V1, V2) Low ≤ 85 % průměrné ceny → prodat polovinu pozice; další řez až na 85 % ceny předchozího řezu,
  znovu    V1 „níž“: koupit zpět prodané množství, když Low ≤ 95 % ceny řezu;
           V2 „na místě“: koupit zpět prodané množství, když High ≥ cena řezu (nejdřív den po řezu),
  obrat    jakmile close > průměrná cena, zapne se trailing: výstup celé pozice na close < nejlepší close − 3 × ATR14,
  limit    max. 365 dní, pak výstup na close.
Varianty: B1 jeden nákup 1 × E0 bez dokupů (srovnání) · V0 jen dokupovat bez řezu · V1 · V2;
  každá bez stopu kampaně a se stopem kampaně (ztráta 20 % / 35 % E0 → zavřít vše; při −20 % stop přijde dřív než řez).
Události uvnitř dne v pořadí cen shora dolů (dokup, řez, znovu níž, stop kampaně, likvidace), gap pod úroveň = plnění
  na Open. Likvidace (cross): equity ≤ 5 % notional → prodat vše. Náklady 0,1 % na každé plnění.
Srovnání: stejná pravidla z náhodných dnů (300 startů na minci), buy & hold mince (podúčet 1 000 USD).
Kritérium (předem): varianta projde, když je Ø výsledek kampaně lepší než B1 i než náhodné starty v obou polovinách
  období a v OOS (posledních 30 % kampaní) a max. propad portfolia je menší než u buy & hold.

    python3 research/experiments/scale_in.py [cache_dir]        # stahuje denní data (GitHub Actions)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
FEE, BORROW, MM = 0.001, 0.10, 0.05
DROP, LOOK = 0.80, 30
UNIT, ADD_STEP, MAX_ADDS = 0.25, 0.95, 5
CUT, REBUY_LOW = 0.85, 0.95
TRAIL, MAX_DAYS = 3.0, 365
VARIANTS = ["B1", "V0", "V1", "V2"]
NAMES = {"B1": "B1 jeden nákup 1× účtu", "V0": "V0 jen dokupovat", "V1": "V1 dokup + řez + znovu níž",
         "V2": "V2 dokup + řez + znovu na místě"}


def atr(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


class Book:
    """Hotovost + množství; průměrná cena se prodejem nemění (prodej jen realizuje zisk/ztrátu)."""

    def __init__(self, cash):
        self.cash, self.qty, self.basis = cash, 0.0, 0.0
        self.fills = 0

    def buy(self, q, px):
        self.cash -= q * px * (1 + FEE)
        self.basis += q * px
        self.qty += q
        self.fills += 1

    def sell(self, q, px):
        q = min(q, self.qty)
        if self.qty:
            self.basis *= 1 - q / self.qty
        self.cash += q * px * (1 - FEE)
        self.qty -= q
        self.fills += 1

    def avg(self):
        return self.basis / self.qty if self.qty else 0.0

    def equity(self, px):
        return self.cash + self.qty * px


def campaign(o, h, l, c, a, i0, E0, v, cat):
    """Jedna kampaň od zavření svíčky i0. Vrací (konec_index, equity_po, denní equity, info)."""
    b = Book(E0)
    unit = UNIT * E0
    if v == "B1":
        b.buy(E0 / c[i0], c[i0])
        adds_left = 0
    else:
        b.buy(unit / c[i0], c[i0])
        adds_left = MAX_ADDS
    last_buy, next_cut, rebuy = c[i0], None, None                 # rebuy = (množství, cena, den řezu)
    armed, best, liquidated, cut_n = False, None, False, 0
    curve = []
    end = min(i0 + MAX_DAYS, len(c) - 1)
    for i in range(i0 + 1, end + 1):
        if b.cash < 0:
            b.cash -= -b.cash * BORROW / 365
        done = False
        for _ in range(20):                                        # události uvnitř dne shora dolů
            lv = []
            if adds_left:
                lv.append((last_buy * ADD_STEP, "add"))
            if v in ("V1", "V2") and b.qty:
                lv.append((next_cut if next_cut else b.avg() * CUT, "cut"))
            if v == "V1" and rebuy:
                lv.append((rebuy[1], "rebuy"))
            if cat and b.qty:
                lv.append(((E0 * (1 - cat) - b.cash) / b.qty, "cat"))
            if b.cash < 0 and b.qty:
                lv.append((-b.cash / ((1 - MM) * b.qty), "liq"))
            lv = [(p, k) for p, k in lv if p >= l[i]]
            if not lv:
                break
            p, k = max(lv)
            px = min(o[i], p)
            if k == "add":
                b.buy(unit / px, px)
                last_buy, adds_left = px, adds_left - 1
            elif k == "cut":
                q = b.qty / 2
                b.sell(q, px)
                cut_n += 1
                next_cut = px * CUT
                if v == "V1":
                    rebuy = (q + (rebuy[0] if rebuy else 0), px * REBUY_LOW, i)
                else:
                    rebuy = (q + (rebuy[0] if rebuy else 0), px, i)
            elif k == "rebuy":
                b.buy(rebuy[0], px)
                last_buy, rebuy = px, None
            else:                                                  # stop kampaně / likvidace
                liquidated = k == "liq"
                b.sell(b.qty, px)
                done = True
                break
        if not done and v == "V2" and rebuy and i > rebuy[2] and h[i] >= rebuy[1]:
            px = max(o[i], rebuy[1])
            b.buy(rebuy[0], px)
            last_buy, rebuy = px, None
        if not done and b.qty:
            if not armed and c[i] > b.avg():
                armed, best = True, c[i]
            if armed:
                best = max(best, c[i])
                if c[i] < best - TRAIL * a[i]:
                    b.sell(b.qty, c[i])
                    done = True
        if not done and i == end and b.qty:
            b.sell(b.qty, c[i])
            done = True
        curve.append(b.equity(c[i]))
        if done:
            return i, b.equity(c[i]), curve, {"liq": liquidated, "cuts": cut_n, "days": i - i0}
    return end, b.equity(c[end]), curve, {"liq": liquidated, "cuts": cut_n, "days": end - i0}


def run_coin(df, v, cat, start=1000.0):
    o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
    a = atr(df).values
    peak30 = df["Close"].rolling(LOOK).max().values
    eq, camps, i = start, [], LOOK + 1
    daily = np.full(len(c), np.nan)
    daily[:i + 1] = start
    while i < len(c) - 1:
        if c[i] <= DROP * peak30[i]:
            j, after, curve, info = campaign(o, h, l, c, a, i, eq, v, cat)
            camps.append({"time": df.index[i], "ret": after / eq - 1, **info})
            daily[i + 1:i + 1 + len(curve)] = curve                  # dny i+1 … j
            eq = max(after, 0.0)
            i = j
        i += 1
        if i < len(c) and np.isnan(daily[i]):
            daily[i] = eq
    return camps, pd.Series(daily, index=df.index).ffill()


def random_ret(df, v, cat, rng, n=300):
    o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
    a = atr(df).values
    out = []
    for _ in range(n):
        i = int(rng.integers(LOOK + 1, len(c) - 30))
        out.append(campaign(o, h, l, c, a, i, 1000.0, v, cat)[1] / 1000 - 1)
    return np.array(out)


def max_dd(s):
    return float((1 - s / s.cummax()).max())


def cagr(s):
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    return (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1 if s.iloc[-1] > 0 and yrs > 0 else -1.0


def main():
    data = {}
    for c in COINS:
        df = ev.load_history(f"{c}/USDT", "crypto", "1d", 3650, cache_dir=SP)
        if df is None or df.empty:
            print(f"{c}: bez dat")
            continue
        data[c] = df[["Open", "High", "Low", "Close"]].dropna().iloc[:-1]
        print(f"{c}: {len(data[c])} dní {data[c].index[0]:%Y-%m-%d} – {data[c].index[-1]:%Y-%m-%d}", flush=True)
    rng = np.random.default_rng(5)
    bh = {c: 1000 * df["Close"] / df["Close"].iloc[0] for c, df in data.items()}
    bh_port = pd.concat(bh, axis=1).ffill().fillna(1000).sum(axis=1)
    print(f"\nBuy & hold portfolio (8 × 1 000 USD od začátku dat mince): konec {bh_port.iloc[-1]:,.0f} USD, "
          f"CAGR {cagr(bh_port) * 100:+.0f} %, max. propad {max_dd(bh_port) * 100:.0f} %")

    print("\n| Varianta | Stop kampaně | Kampaní | Úspěšnost | Ø kampaň | Medián | Nejhorší | Likvidací | Ø dní | "
          "IS / OOS Ø | 1. / 2. polovina | Náhodné starty Ø | Portfolio konec | CAGR | Max. propad |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    res = {}
    for cat in (None, 0.20, 0.35):
        for v in VARIANTS:
            camps, curves = [], {}
            for c, df in data.items():
                cs, s = run_coin(df, v, cat)
                for x in cs:
                    x["coin"] = c
                camps += cs
                curves[c] = s
            camps.sort(key=lambda x: x["time"])
            r = np.array([x["ret"] for x in camps])
            port = pd.concat(curves, axis=1).ffill().fillna(1000).sum(axis=1)
            rnd = np.concatenate([random_ret(df, v, cat, rng) for df in data.values()])
            cut, half = int(len(r) * 0.7), len(r) // 2
            res[(v, cat)] = (r, rnd, camps, port)
            print(f"| {NAMES[v]} | {f'−{cat * 100:.0f} %' if cat else 'bez'} | {len(r)} | {(r > 0).mean() * 100:.0f} % | "
                  f"{r.mean() * 100:+.1f} % | {np.median(r) * 100:+.1f} % | {r.min() * 100:+.0f} % | "
                  f"{sum(x['liq'] for x in camps)} | {np.mean([x['days'] for x in camps]):.0f} | "
                  f"{r[:cut].mean() * 100:+.1f} / {r[cut:].mean() * 100:+.1f} % | "
                  f"{r[:half].mean() * 100:+.1f} / {r[half:].mean() * 100:+.1f} % | {rnd.mean() * 100:+.1f} % | "
                  f"{port.iloc[-1]:,.0f} | {cagr(port) * 100:+.0f} % | {max_dd(port) * 100:.0f} % |")

    print("\n=== Kritérium: Ø kampaň > B1 a > náhodné starty v obou polovinách i v OOS, max. propad < buy & hold ===")
    for cat in (None, 0.20, 0.35):
        rb = res[("B1", cat)][0]
        for v in ("V0", "V1", "V2"):
            r, rnd, _, port = res[(v, cat)]
            cut, half = int(len(r) * 0.7), len(r) // 2
            cb, hb = int(len(rb) * 0.7), len(rb) // 2
            ok = (r[:half].mean() > max(rb[:hb].mean(), rnd.mean()) and r[half:].mean() > max(rb[hb:].mean(), rnd.mean())
                  and r[cut:].mean() > max(rb[cb:].mean(), rnd.mean()) and max_dd(port) < max_dd(bh_port))
            print(f"  {NAMES[v]} ({f'stop −{cat * 100:.0f} %' if cat else 'bez stopu'}): {'✅ prošlo' if ok else '❌ neprošlo'}")

    print("\nPo letech (Ø kampaň v %, bez stopu kampaně):")
    for v in VARIANTS:
        camps = res[(v, None)][2]
        yrs = pd.Series([x["ret"] for x in camps], index=[x["time"].year for x in camps])
        print(f"  {v}: " + " · ".join(f"{y} {g.mean() * 100:+.0f} % (n={len(g)})" for y, g in yrs.groupby(level=0)))
    print("\nNejhorší kampaně (V1, bez stopu):")
    for x in sorted(res[("V1", None)][2], key=lambda x: x["ret"])[:5]:
        print(f"  {x['coin']} {x['time']:%Y-%m-%d}: {x['ret'] * 100:+.0f} %, řezů {x['cuts']}, {x['days']} dní, "
              f"likvidace {'ano' if x['liq'] else 'ne'}")


if __name__ == "__main__":
    main()
