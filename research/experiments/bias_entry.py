"""Směr z denního grafu + průběžné vstupy na 1H (bez čekání na denní signál) – stanoveno PŘEDEM, 26. 10. 2026.

Data: 1H svíčky (yfinance, ~2 roky) a denní svíčky, 8 mincí. Náklady 0,15 % na stranu.
  A  „směr + vstup“: směr dne z poslední UZAVŘENÉ denní svíčky – long, když Close > EMA200 a EMA50 > EMA50 před
     5 dny; short zrcadlově; jinak se neobchoduje. Vstup kdykoli na 1H ve směru: v posledních 6 svíčkách se Low (long)
     dotklo EMA20 1H a svíčka zavře nad EMA20 i nad High předchozí svíčky (short zrcadlově).
  B  „oba směry“: stejné 1H vstupy long i short bez denního směru.
Stop: swing 6 svíček 1H − 0,1 denního ATR, min. 1,5 % od vstupu. Max. 1 otevřená pozice na minci (na variantu).
Výstupy: X1 cíle 2R/4R (polovina na 2R, stop zbytku na vstup), max. 5 dní; X2 jako dnes – polovina na 2R, zbytek
trailing 3 denní ATR, max. 20 dní. Srovnání: denní strategie (donchian_1d + pullback_1d) ve stejném období, náhodné
vstupy (stejná mince a směr, stejný stop v %, stejný výstup, 10 opakování). Portfolio = všechny obchody (1 na minci).

    python3 research/experiments/bias_entry.py scanner/cache
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scanner import evaluate as ev, setups as st  # noqa: E402
from scanner.calibrate import strategy_params  # noqa: E402

SP = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "scanner" / "cache")
COST = 0.15
COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]
EXITS = {"X1 cíle 2R/4R, 5 dní": (0.5, 0.0, 120), "X2 jako dnes (trailing), 20 dní": (0.5, 3.0, 480)}
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
LIVE = [s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")]


def load(c, tf, days):
    df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_{tf}_{days}d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna().iloc[:-1]


def daily_bias(d1):
    e200, e50 = st.ema(d1["Close"], 200), st.ema(d1["Close"], 50)
    up = (d1["Close"] > e200) & (e50 > e50.shift(5))
    dn = (d1["Close"] < e200) & (e50 < e50.shift(5))
    b = pd.Series(np.where(up, 1, np.where(dn, -1, 0)), index=d1.index)
    b.index = b.index + pd.Timedelta(days=1)                       # platí až po uzavření denní svíčky
    return b, st.Ctx(d1).atr


def signals(h1, d1, use_bias):
    bias, datr = daily_bias(d1)
    datr = pd.Series(datr, index=d1.index + pd.Timedelta(days=1))
    e20 = st.ema(h1["Close"], 20).values
    hi, lo, cl = h1["High"].values, h1["Low"].values, h1["Close"].values
    b_at = bias.reindex(h1.index, method="ffill").fillna(0).values
    a_at = datr.reindex(h1.index, method="ffill").values
    out = []
    for i in range(30, len(h1) - 1):
        for sg in ((int(b_at[i]),) if use_bias else (1, -1)):
            if sg == 0 or np.isnan(a_at[i]):
                continue
            long = sg == 1
            touched = (lo[i - 5:i + 1] <= e20[i - 5:i + 1]).any() if long else (hi[i - 5:i + 1] >= e20[i - 5:i + 1]).any()
            trig = (cl[i] > e20[i] and cl[i] > hi[i - 1]) if long else (cl[i] < e20[i] and cl[i] < lo[i - 1])
            if not (touched and trig):
                continue
            e = cl[i]
            sw = lo[i - 5:i + 1].min() - 0.1 * a_at[i] if long else hi[i - 5:i + 1].max() + 0.1 * a_at[i]
            sw = min(sw, e * (1 - 0.015)) if long else max(sw, e * (1 + 0.015))
            out.append({"i": i, "time": h1.index[i], "dir": "long" if long else "short", "entry": e, "stop": sw,
                        "atr": a_at[i]})
    return out


def sim(h1, s, ex):
    split, trail, hold = ex
    risk = abs(s["entry"] - s["stop"])
    sg = 1 if s["dir"] == "long" else -1
    setup = {"direction": s["dir"], "entry": s["entry"], "stop": s["stop"],
             "targets": [s["entry"] + sg * 2 * risk, s["entry"] + sg * 4 * risk], "meta": {"atr": s["atr"]}}
    return ev.simulate(setup, h1.iloc[s["i"] + 1:], hold, split, COST, trail)


def run_variant(data, use_bias, ex):
    trades = []
    for c, (h1, d1) in data.items():
        busy = None
        for s in signals(h1, d1, use_bias):
            if busy is not None and s["time"] < busy:
                continue
            res = sim(h1, s, ex)
            if res["result"] == "open":
                continue
            busy = h1.index[min(s["i"] + res["bars"], len(h1) - 1)]
            trades.append({**s, "coin": c, "r": res["r"], "exit": busy, "stop_pct": abs(s["entry"] - s["stop"]) / s["entry"]})
    return pd.DataFrame(trades)


def random_r(data, t, ex, k=10, seed=7):
    rng = np.random.default_rng(seed)
    rs = []
    for x in t.itertuples():
        h1 = data[x.coin][0]
        for _ in range(k):
            i = int(rng.integers(30, len(h1) - 2))
            e = float(h1["Close"].iat[i])
            sg = 1 if x.dir == "long" else -1
            s = {"i": i, "dir": x.dir, "entry": e, "stop": e * (1 - sg * x.stop_pct), "atr": x.atr * e / x.entry}
            res = sim(h1, s, ex)
            if res["result"] != "open":
                rs.append(res["r"])
    return float(np.mean(rs))


def summarize(name, t, start, end, rnd=None):
    t = t[(t["time"] >= start) & (t["time"] < end)]
    r = t["r"]
    eq = t.sort_values("exit")["r"].cumsum()
    yrs = (end - start).days / 365.25
    half = t["time"] < start + (end - start) / 2
    return {"varianta": name, "obchodů": len(t), "za měsíc": round(len(t) / (yrs * 12), 1),
            "úspěšnost": f"{(r > 0).mean() * 100:.0f} %", "Ø R ± CI": f"{r.mean():+.3f} ± {1.96 * r.std(ddof=1) / np.sqrt(len(r)):.2f}",
            "1./2. polovina": f"{t[half]['r'].mean():+.2f} / {t[~half]['r'].mean():+.2f}",
            "R/rok": round(r.sum() / yrs, 1), "max propad R": round(float((eq.cummax().clip(lower=0) - eq).max()), 1),
            "náhoda Ø R": None if rnd is None else round(rnd, 3)}


def main():
    data = {c: (load(c, "1h", 730), load(c, "1d", 3650)) for c in COINS}
    start = max(h1.index[0] for h1, _ in data.values()) + pd.Timedelta(days=5)
    end = min(h1.index[-1] for h1, _ in data.values()) - pd.Timedelta(days=21)
    print(f"období {start:%Y-%m-%d} – {end:%Y-%m-%d}\n")
    rows = []
    for ex_name, ex in EXITS.items():
        for name, use_bias in (("A směr + vstup 1H", True), ("B oba směry 1H", False)):
            t = run_variant(data, use_bias, ex)
            rows.append(summarize(f"{name} · {ex_name}", t, start, end, random_r(data, t[(t['time'] >= start) & (t['time'] < end)], ex)))
            if use_bias:
                tt = t[(t["time"] >= start) & (t["time"] < end)]
                print(f"{name} · {ex_name}: long {int((tt['dir'] == 'long').sum())} Ø {tt[tt['dir'] == 'long']['r'].mean():+.2f}, "
                      f"short {int((tt['dir'] == 'short').sum())} Ø {tt[tt['dir'] == 'short']['r'].mean():+.2f}; "
                      f"stop medián {tt['stop_pct'].median() * 100:.1f} %")
    # dnešní denní strategie ve stejném období (bez limitů portfolia, živé výstupy)
    d = []
    for c, (_, d1) in data.items():
        for s in LIVE:
            rp, ex, mr = ev.split_params(strategy_params(s), s["setup"])
            for g in st.find(s["setup"], d1, "both", rp):
                h = g.meta["hold_index"]
                if g.rr[0] < mr or g.hold_time < start or g.hold_time >= end:
                    continue
                res = ev.simulate(g, d1.iloc[h + 1:], ex["max_hold_bars"], ex["split"], COST, ex["trail_atr"])
                if res["result"] != "open":
                    d.append({"time": g.hold_time, "r": res["r"], "exit": d1.index[min(h + res["bars"], len(d1) - 1)]})
    rows.append(summarize("Dnes: denní Donchian + pullback", pd.DataFrame(d), start, end))
    print()
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
