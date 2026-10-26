"""Dokupování při poklesu s malou pákou, částečný řez ztráty, znovuotevření a dlouhé držení po obratu (stanoveno PŘEDEM, 26. 10. 2026).

Otázka uživatele: začít malou testovací pozicí při poklesu, postupně dokupovat, při určité ztrátě část prodat
se ztrátou a znovu otevřít níž (nebo na místě řezu), aby se snížila průměrná cena, a po obratu držet co nejdéle.
Navazuje na reports/capitulation.md (dno z denních dat načasovat nešlo) a reports/pyramid.md (přikupování do ZISKU prošlo).

Data: denní svíčky ~10 let, 8 mincí (stejná cache jako scanner/evaluate.py). Každá mince má vlastní podúčet 1 000 USD,
portfolio = součet (8 000 USD). Mezi kampaněmi hotovost.
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
Doplněno 26. 10. 2026 (stanoveno PŘED během, otázka „když není trend nahoru, je dolů“):
  SHORT  zrcadlo: spouštěč close ≥ 120 % minima close za 30 dní; dokup shortu každých +5 %, řez při +15 % nad průměrem,
         V1 znovu o 5 % výš, V2 znovu při návratu na cenu řezu; trailing 3 ATR nad nejlepším close; půjčka mince 10 % p.a.,
         likvidace při equity ≤ 5 % notional,
  LS     long kampaň jen při close > SMA200, short kampaň jen při close < SMA200 (jedna kampaň naráz na minci);
         náhodné starty berou směr podle SMA200 toho dne.
Kritérium (předem, pro každý režim zvlášť proti B1 a náhodě téhož režimu): varianta projde, když je Ø výsledek kampaně lepší než B1 i než náhodné starty v obou polovinách
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
MODES = ["long", "short", "LS"]
MODE_NAMES = {"long": "LONG – dokupování při poklesu", "short": "SHORT – zrcadlově, dokupování shortu při růstu",
              "LS": "LS – long při poklesu nad SMA200, short při růstu pod SMA200"}


def atr(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


class Book:
    """Hotovost + množství (short = záporné množství); průměrná cena se zavřením části nemění (jen realizuje výsledek)."""

    def __init__(self, cash, side=1):
        self.cash, self.qty, self.basis, self.side = cash, 0.0, 0.0, side

    def open(self, q, px):                                         # q > 0 kusů mince ve směru kampaně
        self.cash -= self.side * q * px + FEE * q * px
        self.basis += q * px
        self.qty += self.side * q

    def close(self, q, px):
        size = self.size()
        q = min(q, size)
        if size:
            self.basis *= 1 - q / size
        self.cash += self.side * q * px - FEE * q * px
        self.qty -= self.side * q

    def size(self):
        return abs(self.qty)

    def avg(self):
        return self.basis / self.size() if self.size() else 0.0

    def equity(self, px):
        return self.cash + self.qty * px


def campaign(o, h, l, c, a, i0, E0, v, cat, side=1):
    """Jedna kampaň od zavření svíčky i0 (side 1 = long, −1 = short, zrcadlově). Vrací (konec, equity_po, denní equity, info)."""
    m = (lambda f: f) if side == 1 else (lambda f: 2 - f)          # 0,95 → 1,05; 0,85 → 1,15
    b = Book(E0, side)
    unit = UNIT * E0
    b.open((E0 if v == "B1" else unit) / c[i0], c[i0])
    adds_left = 0 if v == "B1" else MAX_ADDS
    last, next_cut, rebuy = c[i0], None, None                      # rebuy = (množství, cena, den řezu)
    armed, best, liquidated, cut_n = False, None, False, 0
    curve = []
    end = min(i0 + MAX_DAYS, len(c) - 1)
    for i in range(i0 + 1, end + 1):
        if side == 1 and b.cash < 0:
            b.cash -= -b.cash * BORROW / 365                       # půjčka hotovosti na long nad 1× účtu
        elif side == -1:
            b.cash -= b.size() * c[i - 1] * BORROW / 365           # půjčka mince na short
        done = False
        for _ in range(20):                                        # nepříznivé události v pořadí ceny
            lv = []
            if adds_left:
                lv.append((last * m(ADD_STEP), "add"))
            if v in ("V1", "V2") and b.size():
                lv.append((next_cut if next_cut else b.avg() * m(CUT), "cut"))
            if v == "V1" and rebuy:
                lv.append((rebuy[1], "rebuy"))
            if cat and b.size():
                lv.append(((E0 * (1 - cat) - b.cash) / b.qty, "cat"))
            if b.size():
                liq = b.cash / (MM * b.size() - b.qty)
                if liq > 0:
                    lv.append((liq, "liq"))
            lv = [(p, k) for p, k in lv if (p >= l[i] if side == 1 else p <= h[i])]
            if not lv:
                break
            p, k = max(lv) if side == 1 else min(lv)
            px = min(o[i], p) if side == 1 else max(o[i], p)
            if k == "add":
                b.open(unit / px, px)
                last, adds_left = px, adds_left - 1
            elif k == "cut":
                q = b.size() / 2
                b.close(q, px)
                cut_n += 1
                next_cut = px * m(CUT)
                rebuy = (q + (rebuy[0] if rebuy else 0), px * m(REBUY_LOW) if v == "V1" else px, i)
            elif k == "rebuy":
                b.open(rebuy[0], px)
                last, rebuy = px, None
            else:                                                  # stop kampaně / likvidace
                liquidated = k == "liq"
                b.close(b.size(), px)
                done = True
                break
        if not done and v == "V2" and rebuy and i > rebuy[2] and (h[i] >= rebuy[1] if side == 1 else l[i] <= rebuy[1]):
            px = max(o[i], rebuy[1]) if side == 1 else min(o[i], rebuy[1])
            b.open(rebuy[0], px)
            last, rebuy = px, None
        if not done and b.size():
            if not armed and side * (c[i] - b.avg()) > 0:
                armed, best = True, c[i]
            if armed:
                best = max(best, c[i]) if side == 1 else min(best, c[i])
                if side * (c[i] - best) < -TRAIL * a[i]:
                    b.close(b.size(), c[i])
                    done = True
        if not done and i == end and b.size():
            b.close(b.size(), c[i])
            done = True
        curve.append(b.equity(c[i]))
        if done:
            return i, b.equity(c[i]), curve, {"liq": liquidated, "cuts": cut_n, "days": i - i0}
    return end, b.equity(c[end]), curve, {"liq": liquidated, "cuts": cut_n, "days": end - i0}


def sides(df, mode):
    """Směr kampaně pro každý den: 1 long, −1 short, 0 nic (spouštěč a filtr trendu jen z uzavřených svíček)."""
    cl = df["Close"]
    down = (cl <= DROP * cl.rolling(LOOK).max()).values
    up = (cl >= (2 - DROP) * cl.rolling(LOOK).min()).values
    trend = (cl > cl.rolling(200).mean()).values
    has = cl.rolling(200).mean().notna().values
    if mode == "long":
        return np.where(down, 1, 0)
    if mode == "short":
        return np.where(up, -1, 0)
    return np.where(has & down & trend, 1, np.where(has & up & ~trend, -1, 0))   # LS: long nad SMA200, short pod


def run_coin(df, v, cat, mode="long", start=1000.0):
    o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
    a = atr(df).values
    sd = sides(df, mode)
    eq, camps, i = start, [], LOOK + 1
    daily = np.full(len(c), np.nan)
    daily[:i + 1] = start
    while i < len(c) - 1:
        if sd[i]:
            j, after, curve, info = campaign(o, h, l, c, a, i, eq, v, cat, int(sd[i]))
            camps.append({"time": df.index[i], "ret": after / eq - 1, "side": int(sd[i]), **info})
            daily[i + 1:i + 1 + len(curve)] = curve                  # dny i+1 … j
            eq = max(after, 0.0)
            i = j
        i += 1
        if i < len(c) and np.isnan(daily[i]):
            daily[i] = eq
    return camps, pd.Series(daily, index=df.index).ffill()


def random_ret(df, v, cat, rng, mode="long", n=300):
    """Stejná pravidla z náhodného dne; u LS směr podle SMA200 toho dne."""
    o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
    a = atr(df).values
    trend = (df["Close"] > df["Close"].rolling(200).mean()).values
    lo = 200 if mode == "LS" else LOOK + 1
    out = []
    for _ in range(n):
        i = int(rng.integers(lo, len(c) - 30))
        side = 1 if mode == "long" else -1 if mode == "short" else (1 if trend[i] else -1)
        out.append(campaign(o, h, l, c, a, i, 1000.0, v, cat, side)[1] / 1000 - 1)
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

    res = {}
    for mode in MODES:
        print(f"\n=== {MODE_NAMES[mode]} ===")
        print("| Varianta | Stop kampaně | Kampaní | Úspěšnost | Ø kampaň | Medián | Nejhorší | Likvidací | Ø dní | "
              "IS / OOS Ø | 1. / 2. polovina | Náhodné starty Ø | Portfolio konec | CAGR | Max. propad |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for cat in (None, 0.20, 0.35):
            for v in VARIANTS:
                camps, curves = [], {}
                for c, df in data.items():
                    cs, s = run_coin(df, v, cat, mode)
                    for x in cs:
                        x["coin"] = c
                    camps += cs
                    curves[c] = s
                camps.sort(key=lambda x: x["time"])
                r = np.array([x["ret"] for x in camps])
                port = pd.concat(curves, axis=1).ffill().fillna(1000).sum(axis=1)
                rnd = np.concatenate([random_ret(df, v, cat, rng, mode) for df in data.values()])
                res[(mode, v, cat)] = (r, rnd, camps, port)
                if len(r) < 2:
                    print(f"| {NAMES[v]} | {f'−{cat * 100:.0f} %' if cat else 'bez'} | {len(r)} | – |")
                    continue
                cut, half = int(len(r) * 0.7), len(r) // 2
                print(f"| {NAMES[v]} | {f'−{cat * 100:.0f} %' if cat else 'bez'} | {len(r)} | {(r > 0).mean() * 100:.0f} % | "
                      f"{r.mean() * 100:+.1f} % | {np.median(r) * 100:+.1f} % | {r.min() * 100:+.0f} % | "
                      f"{sum(x['liq'] for x in camps)} | {np.mean([x['days'] for x in camps]):.0f} | "
                      f"{r[:cut].mean() * 100:+.1f} / {r[cut:].mean() * 100:+.1f} % | "
                      f"{r[:half].mean() * 100:+.1f} / {r[half:].mean() * 100:+.1f} % | {rnd.mean() * 100:+.1f} % | "
                      f"{port.iloc[-1]:,.0f} | {cagr(port) * 100:+.0f} % | {max_dd(port) * 100:.0f} % |")

    print("\n=== Kritérium: Ø kampaň > B1 a > náhodné starty v obou polovinách i v OOS, max. propad < buy & hold ===")
    for mode in MODES:
        for cat in (None, 0.20, 0.35):
            rb = res[(mode, "B1", cat)][0]
            for v in ("V0", "V1", "V2"):
                r, rnd, _, port = res[(mode, v, cat)]
                if len(r) < 4 or len(rb) < 4:
                    continue
                cut, half = int(len(r) * 0.7), len(r) // 2
                cb, hb = int(len(rb) * 0.7), len(rb) // 2
                ok = (r[:half].mean() > max(rb[:hb].mean(), rnd.mean()) and r[half:].mean() > max(rb[hb:].mean(), rnd.mean())
                      and r[cut:].mean() > max(rb[cb:].mean(), rnd.mean()) and max_dd(port) < max_dd(bh_port))
                print(f"  {mode} · {NAMES[v]} ({f'stop −{cat * 100:.0f} %' if cat else 'bez stopu'}): "
                      f"{'✅ prošlo' if ok else '❌ neprošlo'}")

    print("\nLS (long nad SMA200, short pod) rozděleno podle směru – Ø kampaň, n:")
    for cat in (None, 0.20, 0.35):
        for v in VARIANTS:
            camps = res[("LS", v, cat)][2]
            part = []
            for sd, lab in ((1, "long"), (-1, "short")):
                r = [x["ret"] for x in camps if x["side"] == sd]
                part.append(f"{lab} {np.mean(r) * 100 if r else float('nan'):+.1f} % (n={len(r)})")
            print(f"  {v} {f'stop −{cat * 100:.0f} %' if cat else 'bez stopu'}: " + " · ".join(part))

    for mode in MODES:
        print(f"\nPo letech – {mode} (Ø kampaň v %, bez stopu kampaně):")
        for v in VARIANTS:
            camps = res[(mode, v, None)][2]
            if not camps:
                continue
            yrs = pd.Series([x["ret"] for x in camps], index=[x["time"].year for x in camps])
            print(f"  {v}: " + " · ".join(f"{y} {g.mean() * 100:+.0f} % (n={len(g)})" for y, g in yrs.groupby(level=0)))
        print(f"Nejhorší kampaně – {mode} (V1, bez stopu):")
        for x in sorted(res[(mode, "V1", None)][2], key=lambda x: x["ret"])[:5]:
            print(f"  {x['coin']} {x['time']:%Y-%m-%d} {'long' if x['side'] == 1 else 'short'}: {x['ret'] * 100:+.0f} %, "
                  f"řezů {x['cuts']}, {x['days']} dní, likvidace {'ano' if x['liq'] else 'ne'}")


if __name__ == "__main__":
    main()
