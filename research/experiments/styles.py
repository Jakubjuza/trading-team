"""Portfolio stylů (varianta A) – přenesení ověřených denních setupů na jiné timeframy, bez ladění.

Stanoveno PŘEDEM (25. 10. 2026), parametry se na těchto datech neladí:
  Poziční (1W, týdenní svíčky z denních, 2016–2026):
    W-don  donchian_breakout: kanál 20 týdnů, stop 2 ATR, trend EMA 40 týdnů (≈ 200 dní), cíle 2R/4R
    W-pb   pullback: EMA 10/20/40 týdnů (≈ 50/100/200 dní), trend EMA 40 týdnů, cíle 2R/4R
    výstup jako denní: polovina na T1, zbytek trailing 3 ATR, max. 20 svíček; bez filtru paniky (málo týdnů)
  Intradenní swing (4H z hodinových svíček, ~2 roky):
    H-don  donchian_breakout se stejnými parametry jako donchian_1d (v počtu svíček), vč. filtru paniky
    H-pb   pullback se stejnými parametry jako pullback_1d (v počtu svíček), vč. filtru paniky
  Referenční: D-don, D-pb = živé denní strategie (stejné období pro srovnání a korelaci).
Měří se: Ø R po nákladech 0,15 %/stranu ± 95% CI, IS/OOS 70/30 podle času, náhodné vstupy (stejná mince, směr,
vzdálenost stopu v ATR a cíle v R; 20 opakování), roky, korelace měsíčních výsledků s denními strategiemi.
Kritérium přijetí (stejné jako u rutiny ladění): OOS Ø R > 0 a nad náhodou, IS není záporné; ≥ 100 obchodů OOS
pro jistotu, jinak jen „papírově k ověření“.

    python3 research/experiments/styles.py scanner/cache
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
OHLCV = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
cfg = yaml.safe_load((ROOT / "scanner/config.yaml").read_text())
LIVE = {s["name"]: s for s in cfg["strategies"] if s["name"] in ("donchian_1d", "pullback_1d")}


def load(c, tf, days):
    df = pd.read_csv(SP / f"eval_crypto_{c}-USDT_{tf}_{days}d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df[list(OHLCV)].dropna()


daily = {c: load(c, "1d", 3650).iloc[:-1] for c in COINS}                     # bez dnešní neuzavřené svíčky
weekly = {c: d.resample("W-SUN", label="left", closed="left").agg(OHLCV).dropna() for c, d in daily.items()}
weekly = {c: w.iloc[:-1] if w.index[-1] + pd.Timedelta(days=7) > daily[c].index[-1] + pd.Timedelta(days=1) else w
          for c, w in weekly.items()}                                        # bez rozjetého týdne
h1 = {c: load(c, "1h", 730) for c in COINS}
h4 = {c: h.resample("4h").agg(OHLCV).dropna().iloc[:-1] for c, h in h1.items()}

EXIT = {"split": 0.5, "trail_atr": 3.0, "max_hold_bars": 20}
W_COMMON = {"trend_ema": 40, "min_stop_pct": 1.5, "target_multiples": [2.0, 4.0]}
STYLES = {
    "W-don": ("donchian_breakout", weekly, {**W_COMMON, "channel": 20, "stop_atr": 2.0}),
    "W-pb": ("pullback", weekly, {**W_COMMON, "lookback": 3, "ema_fast": 10, "ema_mid": 20, "ema_slow": 40}),
    "H-don": ("donchian_breakout", h4, LIVE["donchian_1d"]["params"]),
    "H-pb": ("pullback", h4, LIVE["pullback_1d"]["params"]),
    "D-don": ("donchian_breakout", daily, LIVE["donchian_1d"]["params"]),
    "D-pb": ("pullback", daily, LIVE["pullback_1d"]["params"]),
}


def run(setup, frames, params):
    p = {**params, **EXIT, "min_rr": 1.0}
    rule_p, exit_p, min_rr = ev.split_params(p, setup)
    out = []
    for c, df in frames.items():
        atr = st.Ctx(df).atr
        for s in st.find(setup, df, "both", rule_p):
            h = s.meta["hold_index"]
            if s.rr[0] < min_rr:
                continue
            res = ev.simulate(s, df.iloc[h + 1:], exit_p["max_hold_bars"], exit_p["split"], COST, exit_p["trail_atr"])
            if res["result"] == "open":
                continue
            risk = abs(s.entry - s.stop)
            out.append({"coin": c, "time": s.hold_time, "dir": s.direction, "r": res["r"], "h": h,
                        "exit": df.index[min(h + res["bars"], len(df) - 1)],
                        "stop_atr": risk / atr[h] if atr[h] else np.nan,
                        "t_r": [abs(t - s.entry) / risk for t in s.targets]})
    return pd.DataFrame(out).sort_values("time").reset_index(drop=True) if out else pd.DataFrame()


def random_baseline(trades, frames, k=20, seed=7):
    rng = np.random.default_rng(seed)
    rs = []
    atrs = {c: st.Ctx(df).atr for c, df in frames.items()}
    for _, t in trades.iterrows():
        df, atr = frames[t["coin"]], atrs[t["coin"]]
        for _ in range(k):
            i = int(rng.integers(220, len(df) - 2))
            e, a = float(df["Close"].iloc[i]), atr[i]
            if not a or np.isnan(t["stop_atr"]):
                continue
            sign = 1 if t["dir"] == "long" else -1
            risk = t["stop_atr"] * a
            s = {"direction": t["dir"], "entry": e, "stop": e - sign * risk,
                 "targets": [e + sign * m * risk for m in t["t_r"]], "meta": {"atr": a}}
            res = ev.simulate(s, df.iloc[i + 1:], EXIT["max_hold_bars"], EXIT["split"], COST, EXIT["trail_atr"])
            if res["result"] != "open":
                rs.append(res["r"])
    return float(np.mean(rs)) if rs else np.nan


def ci(x):
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan


def summary(name, t, frames, start=None):
    if start is not None:
        t = t[t["time"] >= start].reset_index(drop=True)
    if t.empty:
        return {"styl": name, "n": 0}, t
    cut = t["time"].iloc[int(len(t) * 0.7)]
    is_, oos = t[t["time"] < cut]["r"], t[t["time"] >= cut]["r"]
    eq = t.sort_values("exit").set_index("exit")["r"].cumsum()
    yrs = t.groupby(t["exit"].dt.year)["r"].sum().round(1).to_dict()
    span_m = max(1.0, (t["time"].iloc[-1] - t["time"].iloc[0]).days / 30.4)
    return {"styl": name, "n": len(t), "obchodů/měs": round(len(t) / span_m, 1),
            "Ø R": round(t["r"].mean(), 3), "± CI": round(ci(t["r"]), 3),
            "IS Ø R": round(is_.mean(), 3), "OOS n": len(oos), "OOS Ø R": round(oos.mean(), 3),
            "OOS ± CI": round(ci(oos), 3), "náhoda Ø R": round(random_baseline(t, frames), 3),
            "P(zisk)": round((t["r"] > 0).mean(), 2), "max DD R": round(float((eq.cummax() - eq).max()), 1),
            "Σ R": round(t["r"].sum(), 1), "roky": yrs}, t


def monthly(t):
    return t.set_index("exit")["r"].resample("ME").sum() if not t.empty else pd.Series(dtype=float)


if __name__ == "__main__":
    res, trades = [], {}
    h4_start = min(df.index[0] for df in h4.values()) + pd.Timedelta(days=40)  # zahřátí EMA 200 na 4H
    for name, (setup, frames, params) in STYLES.items():
        t = run(setup, frames, params)
        trades[name] = t
        res.append(summary(name, t, frames)[0])
        if name.startswith("D-"):                                            # denní jen za stejné období jako 4H
            row, td = summary(name + " (od 4H)", t, frames, start=h4_start)
            trades[name + " (od 4H)"] = td
            res.append(row)
    cols = ["styl", "n", "obchodů/měs", "Ø R", "± CI", "IS Ø R", "OOS n", "OOS Ø R", "OOS ± CI", "náhoda Ø R",
            "P(zisk)", "max DD R", "Σ R"]
    table = pd.DataFrame(res)
    print(table[cols].to_string(index=False))
    print("\nPo letech (Σ R):")
    for r in res:
        print(f"  {r['styl']:16} {r.get('roky')}")
    d = monthly(pd.concat([trades["D-don"], trades["D-pb"]]))
    print("\nKorelace měsíčních výsledků s denními strategiemi (D-don + D-pb):")
    for name in ("W-don", "W-pb", "H-don", "H-pb"):
        m = monthly(trades[name])
        j = pd.concat([m, d], axis=1, join="inner").dropna()
        print(f"  {name}: {j.corr().iloc[0, 1]:+.2f} ({len(j)} měsíců)" if len(j) > 6 else f"  {name}: málo dat")
    out = SP / "styles_trades.csv"
    pd.concat([t.assign(styl=k) for k, t in trades.items() if not t.empty]).drop(columns=["t_r"]).to_csv(out)
    print(f"\nObchody: {out}")
