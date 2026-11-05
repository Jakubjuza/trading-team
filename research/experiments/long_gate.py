"""🚧 Brána směru podle stavu trhu – stanoveno PŘEDEM, 5. 11. 2026 (před prvním spuštěním), po spuštění se nic neladí.

Proč: živě (27. 10.–5. 11. 2026) laboratoř uzavřela 28 longů za −26,9 R, 14 z nich v medvědím režimu; shorty 9 za −2,5 R.
Otázka: zhoršuje medvědí režim BTC nebo křehký trh (research/fragility.py) longy všech aktivních strategií i v historii?

Obchody: každý signál aktivní strategie registru na 8 mincích (1H OKX od 2019, stejný kód jako papír a context_gate:
vstup na open další svíčky, výstupy strategie, poplatky MEXC 0,05 %/stranu, filtr a režimy strategie).
Stav v den signálu (známý na začátku dne): režim BTC z předchozího dne (research/regime.py) a K křehkosti BTC
(šoky, jejichž 24 h už uplynulo).

Brány pro LONG:  G1 blokovat při režimu BTC „medvědí“ · G2 blokovat při K ≥ +0,25 (křehký) · G3 = G1 nebo G2.
Brány pro SHORT (zrcadlo, doplněk): S1 blokovat při režimu BTC „býčí“ · S2 blokovat při K ≤ −0,25 · S3 = S1 nebo S2.

PROJDE brána, když: (a) Ø R blokovaných < Ø R ponechaných v OOS (2024-01 … 2025-06) I v HOLDOUTU (od 2025-07),
(b) Ø R blokovaných v OOS+HOLDOUT ≤ 0 (blokací se neztratí zisk), (c) rozdíl ponechané − blokované v OOS+HOLDOUT
má t ≥ 2 (klastry po týdnech), (d) blokovaných v OOS+HOLDOUT ≥ 200.
Výsledek: reports/long_gate.md a research/long_gate.json – papír (scanner/lab_paper.py) použije jen brány, které PROŠLY;
zablokovaný signál jde stínově (měří se dál).

    python3 research/experiments/long_gate.py /tmp/cache
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import fragility, registry  # noqa: E402
from research.experiments import context_gate as cg  # noqa: E402

REPORT = ROOT / "reports" / "long_gate.md"
OUT = ROOT / "research" / "long_gate.json"
GATES = {
    "G1": ("long", "režim BTC medvědí"), "G2": ("long", "křehký trh (K ≥ +0,25)"), "G3": ("long", "G1 nebo G2"),
    "S1": ("short", "režim BTC býčí"), "S2": ("short", "optimistický trh (K ≤ −0,25)"), "S3": ("short", "S1 nebo S2"),
}


def blocked(df, g):
    bear, bull = df.btc_reg == "medvědí", df.btc_reg == "býčí"
    fr_, op = df.k >= fragility.THR, df.k <= -fragility.THR
    return {"G1": bear, "G2": fr_, "G3": bear | fr_, "S1": bull, "S2": op, "S3": bull | op}[g]


def fmt(x, d=3):
    return "–" if x is None or not np.isfinite(x) else f"{x:+.{d}f}".replace(".", ",")


def evaluate(df):
    res = {}
    for g, (dir_, _) in GATES.items():
        x = df[df.dir == dir_]
        b = blocked(x, g).to_numpy()
        row = {}
        for per in ("is", "oos", "hold"):
            m = (x.per == per).to_numpy()
            row[per] = {"keep_n": int((m & ~b).sum()), "keep_r": float(x.r[m & ~b].mean()) if (m & ~b).any() else np.nan,
                        "blk_n": int((m & b).sum()), "blk_r": float(x.r[m & b].mean()) if (m & b).any() else np.nan}
        oh = x.per.isin(["oos", "hold"]).to_numpy()
        dif, t = cg.diff_t(x.r[oh & ~b], x.wk[oh & ~b], x.r[oh & b], x.wk[oh & b])
        blk_oh = float(x.r[oh & b].mean()) if (oh & b).any() else np.nan
        rec = x.t >= x.t.max() - pd.Timedelta(days=180)
        row.update({"diff": float(dif), "t": float(t), "blk_oh_r": blk_oh, "blk_oh_n": int((oh & b).sum()),
                    "recent": {"keep_r": float(x.r[rec & ~b].mean()) if (rec & ~b).any() else np.nan,
                               "blk_r": float(x.r[rec & b].mean()) if (rec & b).any() else np.nan,
                               "blk_n": int((rec & b).sum())}})
        row["pass"] = bool(all(np.isfinite(row[p]["blk_r"]) and row[p]["blk_r"] < row[p]["keep_r"] for p in ("oos", "hold"))
                           and np.isfinite(blk_oh) and blk_oh <= 0 and np.isfinite(t) and t >= 2 and row["blk_oh_n"] >= 200)
        res[g] = row
    return res


def main(cache):
    t0 = time.time()
    h1, daily, dctx, regs, fng = cg.load(cache)
    print(f"data: {time.time() - t0:.0f} s", flush=True)
    df, strats, _ = cg.part_a(h1, dctx, regs)
    df["dir"] = df.sid.map({s["id"]: s["dir"] for s in strats})
    day = pd.DatetimeIndex(df.t).floor("1D")
    df["btc_reg"] = regs["BTC"].reindex(day).to_numpy(dtype=object)
    btc = h1["BTC"][["Open", "High", "Low", "Close"]].astype(float)
    days = pd.date_range(day.min(), day.max(), freq="1D", tz="UTC")
    ks = fragility.series(btc, days)
    df["k"] = ks.reindex(day).to_numpy(float)
    print(f"stav trhu: {time.time() - t0:.0f} s", flush=True)
    res = evaluate(df)

    L = ["# 🚧 Brána směru podle stavu trhu – výsledky testu", "",
         f"Spuštěno {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · {len(strats)} aktivních strategií × 8 mincí · "
         f"{len(df)} obchodů ({(df.dir == 'long').sum()} long, {(df.dir == 'short').sum()} short) · {time.time() - t0:.0f} s.",
         "Pravidla předem (hlavička `research/experiments/long_gate.py`). IS < 2024-01 ≤ OOS < 2025-07 ≤ HOLDOUT.", "",
         "| brána | blokuje | OOS: ponech. / blok. Ø R (n blok.) | HOLDOUT: ponech. / blok. Ø R (n blok.) | "
         "blok. OOS+H Ø R | rozdíl (t) | posl. 180 dní ponech. / blok. (n) | verdikt |",
         "|---|---|---|---|---|---|---|---|"]
    for g, (dir_, lab) in GATES.items():
        r = res[g]
        L.append(f"| {g} {dir_} | {lab} | {fmt(r['oos']['keep_r'])} / {fmt(r['oos']['blk_r'])} ({r['oos']['blk_n']}) | "
                 f"{fmt(r['hold']['keep_r'])} / {fmt(r['hold']['blk_r'])} ({r['hold']['blk_n']}) | {fmt(r['blk_oh_r'])} | "
                 f"{fmt(r['diff'])} ({fmt(r['t'], 1)}) | {fmt(r['recent']['keep_r'])} / {fmt(r['recent']['blk_r'])} "
                 f"({r['recent']['blk_n']}) | {'PROŠLO ✅' if r['pass'] else 'NEPROŠLO ❌'} |")
    L += ["", "Po strategiích – longy, Ø R v OOS+HOLDOUT podle režimu BTC:", "",
          "| strategie | býčí | boční | medvědí | panika |", "|---|---|---|---|---|"]
    oh = df[df.per.isin(["oos", "hold"]) & (df.dir == "long")]
    lab_ = {s["id"]: s["label"] for s in strats}
    for sid, x in oh.groupby("sid"):
        L.append(f"| {lab_[sid]} | " + " | ".join(f"{fmt(x[x.btc_reg == rg].r.mean())} ({(x.btc_reg == rg).sum()})"
                                                 for rg in ("býčí", "boční", "medvědí", "panika")) + " |")
    L += ["", "Prošlé brány použije papír laboratoře (zablokovaný signál jde stínově a měří se dál). Neprošlé se nepoužijí.",
          "", "Nejde o finanční poradenství."]
    REPORT.write_text("\n".join(L) + "\n")
    clean = json.loads(json.dumps(res, default=float).replace("NaN", "null"))
    OUT.write_text(json.dumps({"created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                               "thr_k": fragility.THR, "gates": clean,
                               "active": [g for g, r in res.items() if r["pass"]]}, ensure_ascii=False, indent=1) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cache"))
