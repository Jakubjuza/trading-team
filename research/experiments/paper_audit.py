"""🔍 Audit papíru laboratoře – je ztráta naživo chyba, nebo jen špatné období? (5. 11. 2026)

Živě 27. 10.–5. 11. 2026: 37 uzavřených obchodů, 4 v zisku, −29 R. Backtest stejných strategií dává v OOS i HOLDOUTU
Ø +0,2 až +0,4 R/obchod (reports/long_gate.md). Tenhle audit přepočítá STEJNÉ dny backtestovým kódem na čerstvých
svíčkách OKX:
  1. Shoda obchod po obchodu: každý živý obchod znovu (stejný signální bar) → vstup, výstup, R. Rozdíl = chyba v papíru.
  2. Úplnost: všechny signály aktivních strategií v okně (stejný režim a filtr) vs. co papír zachytil (živě + stínově).
  3. Co by za stejné dny dal backtest bez limitů (všechny signály, uzavřené) – je období samo o sobě špatné?

    python3 research/experiments/paper_audit.py       → reports/paper_audit.md
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import registry  # noqa: E402
from scanner import lab_paper as lp  # noqa: E402

OUT = ROOT / "reports" / "paper_audit.md"


def rd(path):
    p = Path(path)
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def fmt(x, d=2):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{d}f}".replace(".", ",")


def main():
    now = pd.Timestamp(datetime.now(timezone.utc))
    live = rd(lp.LOG)
    shadow = rd(lp.SHADOW)
    closes = [r for r in live if r["event"] == "close"]
    sigs = [r for r in live + shadow if r["event"] == "signal"]
    reg = registry.load()
    strats = {s["id"]: s for s in reg["strategies"]}
    t0 = min(pd.Timestamp(r["signal_bar"]) for r in live if "signal_bar" in r)
    ex = lp._exchange()
    coins = sorted({r["coin"] for r in live})
    tfs = sorted({strats[r["sid"]]["tf"] for r in live if r.get("sid") in strats} |
                 {s["tf"] for s in registry.active(reg)})
    daily, frames = {}, {}
    for coin in coins:
        daily[coin] = lp._daily_context(lp.candles(ex, coin, "1d", now, bars=900))
        for tf in tfs:
            step = pd.Timedelta(lp.TF_TD[tf])
            bars = int((now - t0) / step) + 600
            frames[(coin, tf)] = lp._prep(lp.candles(ex, coin, tf, now, bars=bars), daily[coin])

    # 1) obchod po obchodu
    rows = []
    for c in closes:
        s = strats.get(c["sid"])
        if not s:
            rows.append({**c, "bt_r": np.nan, "note": "strategie už není v registru"})
            continue
        z = frames[(c["coin"], s["tf"])]
        pos = np.flatnonzero(z.df.index == pd.Timestamp(c["signal_bar"]))
        if not len(pos):
            rows.append({**c, "bt_r": np.nan, "note": "signální bar v datech chybí"})
            continue
        i = int(pos[0])
        d = 1 if s["dir"] == "long" else -1
        ent, _ = lp._signals(z, s, d)
        is_sig = i in set(np.asarray(ent).tolist())
        res = lp._simulate(z, s, i)
        bt_r = (res["g"] - 2 * lp.COST) / res["rf"] if res and res["closed"] else np.nan
        rows.append({**c, "bt_r": bt_r, "bt_entry": float(z.o[res["entry_i"]]) if res else np.nan,
                     "bt_exit": z.df.index[res["exit_i"]].isoformat() if res else None,
                     "note": "" if is_sig else "backtest na tomhle baru signál NEDÁVÁ"})
    df = pd.DataFrame(rows)
    df["diff"] = df["bt_r"] - df["r"]

    # 2) + 3) všechny signály v okně
    allsig = []
    for sid, s in strats.items():
        if s.get("status") not in ("papír", "ověřeno"):
            continue
        d = 1 if s["dir"] == "long" else -1
        for coin in coins:
            z = frames.get((coin, s["tf"]))
            if z is None:
                continue
            ent, _ = lp._signals(z, s, d)
            for i in np.asarray(ent, int):
                t = z.df.index[i]
                if t < t0 or i + 1 >= len(z.c):
                    continue
                if s.get("regimes") and z.reg[i] not in s["regimes"]:
                    continue
                if s["filter"] != "none" and z.flt[s["filter"]][i] != (1.0 if d > 0 else 0.0):
                    continue
                res = lp._simulate(z, s, int(i))
                r = (res["g"] - 2 * lp.COST) / res["rf"] if res and res["closed"] else np.nan
                allsig.append({"sid": sid, "coin": coin, "t": t, "dir": s["dir"], "r": r})
    a = pd.DataFrame(allsig)
    seen = {(r["sid"], r["coin"], pd.Timestamp(r["signal_bar"])) for r in sigs}
    if len(a):
        a["seen"] = [(x.sid, x.coin, x.t) in seen for x in a.itertuples()]

    L = ["# 🔍 Audit papíru laboratoře", "",
         f"Spuštěno {now:%Y-%m-%d %H:%M} UTC · okno od {t0:%Y-%m-%d %H:%M} UTC · čerstvé svíčky OKX, stejný kód jako papír.", "",
         "## 1. Živé obchody znovu backtestem", "",
         f"Živě {len(df)} obchodů: Σ {fmt(df.r.sum(), 1)} R, Ø {fmt(df.r.mean())} R. "
         f"Backtest týchž: Σ {fmt(df.bt_r.sum(), 1)} R, Ø {fmt(df.bt_r.mean())} R. "
         f"Shoda R (±0,05): {int((df['diff'].abs() <= 0.05).sum())}/{int(df.bt_r.notna().sum())}.", "",
         "| mince | strategie | směr | signál | živě R | backtest R | rozdíl | pozn. |", "|---|---|---|---|---|---|---|---|"]
    for x in df.itertuples():
        L.append(f"| {x.coin} | {x.sid.split('|')[0]} {x.sid.split('|')[1]} {x.tf} | {x.dir} | {x.signal_bar[:16]} | "
                 f"{fmt(x.r)} | {fmt(x.bt_r)} | {fmt(x.diff)} | {x.note} |")
    L += ["", "## 2.–3. Všechny signály aktivních strategií v okně", ""]
    if len(a):
        cl = a[a.r.notna()]
        L += [f"Signálů {len(a)} (uzavřených {len(cl)}), papír zachytil (živě nebo stínově) {int(a.seen.sum())}.",
              f"Backtest všech uzavřených signálů za tyto dny: Σ {fmt(cl.r.sum(), 1)} R, Ø {fmt(cl.r.mean())} R, "
              f"výhry {(cl.r > 0).mean() * 100:.0f} %.",
              f"Long {fmt(cl[cl.dir == 'long'].r.mean())} R ({(cl.dir == 'long').sum()}), "
              f"short {fmt(cl[cl.dir == 'short'].r.mean())} R ({(cl.dir == 'short').sum()}).", "",
              "Nezachycené signály (prvních 20):", "", "| strategie | mince | čas | R |", "|---|---|---|---|"]
        for x in a[~a.seen].head(20).itertuples():
            L.append(f"| {strats[x.sid]['label']} | {x.coin} | {x.t:%Y-%m-%d %H:%M} | {fmt(x.r)} |")
    L += ["", "Závěr čti takto: když backtest týchž obchodů dá stejné R jako papír, chyba v papíru není a ztráta je "
          "z období/strategií. Když se liší, chyba je v papíru.", "", "Nejde o finanční poradenství."]
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
