#!/usr/bin/env python3
"""Downtown – výzkum fází trhu a „Dispečer“ (agent, který strategie zapíná jen v jejich fázi). Jen papír.

Otázka (uživatel 7. 11. 2026): každá divoká strategie je v nějaké fázi trhu vysoce zisková – dá se ta fáze poznat
PŘEDEM a strategii pouštět jen tehdy?

Postup bez pohledu do budoucnosti:
  1. Každá strategie (8 stávajících z research/downtown.py + nové z rešerše) se projede bez páky → seznam obchodů
     s časem vstupu a čistým výnosem (poplatky, skluz, funding).
  2. Fáze trhu se počítá z denních dat BTC a košíku mincí, vždy z UZAVŘENÉHO předchozího dne:
       trend   BTC nad / pod 200denním průměrem
       pohyb   efektivita 30 dní (|změna| / součet denních pohybů) ≥ 0,25 = trend, jinak pila
       vola    30denní volatilita BTC nad / pod svým klouzavým mediánem za 365 dní
     → 8 fází (např. „býk · trend · klid“).
  3. Dispečer (walk-forward): na začátku každého měsíce vezme jen obchody, které už skončily, a pro každou strategii
     zapne fáze, kde měla průměr > 0 při aspoň MIN_N obchodech a t-statistice ≥ T_MIN. Celý měsíc pak strategie
     obchoduje jen v zapnutých fázích. Prvních 6 měsíců (2023 H1) se jen učí.
  4. Kontrola štěstí: stejný podíl času zapnutý NÁHODNĚ (200 losování) – pokud fáze nic nevědí, Dispečer nebude lepší.

    python3 research/experiments/downtown_regimes.py DATA_DIR OUT_DIR
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import downtown as D  # noqa: E402

D.TF_H["1d"] = 24.0
D.TF_H["6h"] = 6.0
COINS8 = D.COINS
MIN_N, T_MIN, LEARN_UNTIL = 12, 1.0, "2023-07-01"
# (název, sloupec fází, min. obchodů, min. t) – A je předem stanovená, B a C jsou citlivostní kontrola
VARIANTS = [("A8", "faze", 12, 1.0), ("B4", "faze4", 12, 1.0), ("C4", "faze4", 8, 0.5)]

NEW = {
    "max20": {"name": "Průraz 20 dní ×5", "tf": "1d", "coins": ["BTC", "ETH", "SOL"], "lev": 5,
              "tag": "trend z denního grafu", "src": "Quantpedia MAX(N), Concretum (Zarattini 2025)",
              "rules": "long na close nad 20denním maximem · stop = střed 20denního kanálu (jen nahoru) · max 60 dní"},
    "squeeze10": {"name": "Squeeze průraz ×10", "tf": "1h", "coins": COINS8, "lev": 10,
                  "tag": "výbuch po klidu", "src": "Bollinger squeeze (TTM)",
                  "rules": "šířka Bollinger(20,2) na 120h minimu, pak close mimo pásmo → jeho směrem · stop 1,5 ATR, trailing 3 ATR, max 72 h"},
    "bear_rot5": {"name": "Medvědí rotace ×5", "tf": "4h", "coins": COINS8, "lev": 5,
                  "tag": "short nejslabší mince", "src": "TSMOM/XSMOM (Liu-Tsyvinski-Wu; arXiv 2602.11708)",
                  "rules": "když je BTC pod EMA200 (4h): short mince s nejhorším výnosem za 24 h (je-li záporný) · přepíná po 4 h"},
    "rot_w3": {"name": "Týdenní hybnost ×3", "tf": "1d", "coins": COINS8, "lev": 3,
               "tag": "nejsilnější mince za 3 týdny", "src": "Liu-Tsyvinski-Wu (NBER w25882), 3týdenní hybnost",
               "rules": "drží long mince s nejlepším výnosem za 21 dní (je-li kladný) · přepíná denně"},
    "night10": {"name": "Noční BTC ×10", "tf": "1h", "coins": ["BTC"], "lev": 10,
                "tag": "z newyorského close do rána", "src": "Quantpedia: overnight sessions (MAX10)",
                "rules": "ve 21:00 UTC, je-li BTC na 10denním maximu → long do 14:00 UTC (17 h) · stop na likvidaci"},
    "shock10": {"name": "Odraz po šoku ×10", "tf": "1h", "coins": COINS8, "lev": 10,
                "tag": "přestřelení po panice", "src": "J. Economic Studies 2022 (overreaction 6–24 h)",
                "rules": "hodinová svíčka pod −4 σ (σ = 7denní) → long na 12 h · stop 4 ATR"},
}
EXITS_NEW = {
    "max20": (None, None, None, None, None, 60),
    "squeeze10": (None, None, 1.5, None, 3.0, 72),
    "night10": (None, None, None, None, None, 17),
    "shock10": (None, None, 4.0, None, None, 12),
}
ALL = {**{k: dict(v) for k, v in D.STRATS.items()}, **NEW}


def load(data):
    data = Path(data)
    raw = {}
    for p in data.glob("*_1h.csv.gz"):
        df = pd.read_csv(p, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        raw[(p.name.split("_")[0], "1h")] = df
    for p in data.glob("*_15m.csv.gz"):
        df = pd.read_csv(p, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        raw[(p.name.split("_")[0], "15m")] = df
    if (data / "kronos.csv.gz").exists():
        D.KRONOS_PRED = data / "kronos.csv.gz"
        D.load_kronos()
    return raw


# ---------------------------------------------------------------- signály nových strategií
def new_signals(sid, d, coin):
    c, o, h, l = d["Close"], d["Open"], d["High"], d["Low"]
    if sid == "max20":
        return np.where(c >= c.rolling(20).max(), 1, 0)
    if sid == "squeeze10":
        m, s = c.rolling(20).mean(), c.rolling(20).std()
        bw = (4 * s / m)
        sq = (bw <= bw.rolling(120).min() * 1.05).shift(1).fillna(False).astype(bool)
        sq = sq.rolling(6).max().fillna(0).astype(bool)      # squeeze v posledních 6 h
        return np.where(sq & (c > m + 2 * s), 1, np.where(sq & (c < m - 2 * s), -1, 0))
    if sid == "night10":
        hi10 = c.rolling(240).max()
        return np.where((d.index.hour == 20) & (c >= hi10 * 0.999), 1, 0)   # close 20–21 h → vstup na open 21:00
    if sid == "shock10":
        r = np.log(c).diff()
        sd = r.rolling(168).std().shift(1)
        return np.where(r < -4 * sd, 1, 0)
    raise KeyError(sid)


def signals_any(sid, d, coin):
    return new_signals(sid, d, coin) if sid in NEW else D.signals(sid, d, coin)


# ---------------------------------------------------------------- jeden běh (kopie D.run s bránou a pákou)
def run(sid, frames, trade_from, lev=None, gate=None, trade_to=None, sweep=None):
    """gate: funkce(pd.DatetimeIndex) -> bool pole, rozhoduje se na close svíčky j (známé v čase rozhodnutí)."""
    cfg = ALL[sid]
    lev = lev or cfg["lev"]
    tf, hours = cfg["tf"], D.TF_H[cfg["tf"]]
    coins = [c for c in cfg["coins"] if c in frames]
    idx = frames[coins[0]].index
    for c in coins[1:]:
        idx = idx.union(frames[c].index)
    F = {c: frames[c].reindex(idx) for c in coins}
    O = {c: F[c]["Open"].to_numpy(float) for c in coins}
    H = {c: F[c]["High"].to_numpy(float) for c in coins}
    L = {c: F[c]["Low"].to_numpy(float) for c in coins}
    C = {c: F[c]["Close"].to_numpy(float) for c in coins}
    A = {c: D.atr(F[c]).to_numpy(float) for c in coins}
    G = np.ones(len(idx), bool) if gate is None else np.asarray(gate(idx), bool)
    target = sid in ("rot5", "hodl3", "bear_rot5", "rot_w3")
    if target:
        if sid == "rot5":
            score = pd.DataFrame({c: F[c]["Close"].pct_change(6) for c in coins}).to_numpy(float)
        elif sid == "rot_w3":
            score = pd.DataFrame({c: F[c]["Close"].pct_change(21) for c in coins}).to_numpy(float)
        elif sid == "bear_rot5":
            b = F["BTC"]["Close"]
            bear = (b < b.ewm(span=200, adjust=False, min_periods=200).mean()).to_numpy()
            score = pd.DataFrame({c: -F[c]["Close"].pct_change(6) for c in coins}).to_numpy(float).copy()
            score[~bear] = np.nan
        else:
            score = np.ones((len(idx), 1))
    else:
        S = {c: np.asarray(signals_any(sid, F[c], c), float) for c in coins}
    exits = EXITS_NEW.get(sid) or D.EXITS.get(sid, (None, None, None, None, None, 10 ** 9))
    t_from = pd.Timestamp(trade_from, tz="UTC")
    start_i = max(1, int(np.searchsorted(idx.values, t_from.to_datetime64())))
    end_i = len(idx) if trade_to is None else int(np.searchsorted(idx.values, pd.Timestamp(trade_to, tz="UTC").to_datetime64()))
    acc = D.Account()
    pos = None
    marti_k = 0
    curve = []
    liq_mult = 1 / lev - D.MM
    fund = D.FUND_8H * hours / 8
    tdir = -1 if sid == "bear_rot5" else 1
    vault = [0.0, D.START_CASH]   # trezor (vybrané zisky), základ pro další zdvojnásobení

    def do_sweep():
        # sweep = podíl zisku, který se při zdvojnásobení účtu vybere do trezoru (jen bez otevřené pozice)
        if sweep and pos is None and acc.eq >= 2 * vault[1]:
            w = (acc.eq - vault[1]) * sweep
            acc.eq -= w
            vault[0] += w
            vault[1] = acc.eq
        if acc.eq < vault[1] / 2 and pos is None:
            vault[1] = max(D.START_CASH, acc.eq)

    def close_pos(i, px, why):
        nonlocal pos, marti_k
        d, c = pos["dir"], pos["coin"]
        fill = px * (1 - d * D.SLIP)
        ret = d * (fill / pos["entry"] - 1)
        pnl = pos["notional"] * ret - pos["notional"] * fill / pos["entry"] * D.FEE - pos["fund"]
        pnl = max(pnl, -pos["margin"])
        acc.eq += pnl
        acc.trades.append({"t": idx[i], "kind": why, "coin": c, "dir": d, "opened": pos["t0"], "pnl": pnl,
                           "r": pnl / pos["margin"] / lev - D.FEE})   # výnos bez páky vč. vstupního poplatku
        if sid == "marti10":
            marti_k = 0 if pnl > 0 or marti_k >= 6 else marti_k + 1
        pos = None
        acc.refill(idx[i])

    def liquidate(i):
        nonlocal pos, marti_k
        acc.liqs += 1
        acc.eq -= pos["margin"]
        acc.trades.append({"t": idx[i], "kind": "likvidace", "coin": pos["coin"], "dir": pos["dir"], "opened": pos["t0"],
                           "pnl": -pos["margin"], "r": -1.0 / lev})
        if sid == "marti10":
            marti_k = 0 if marti_k >= 6 else marti_k + 1
        pos = None
        acc.refill(idx[i])

    def open_pos(i, c, d):
        nonlocal pos
        frac = min(1.0, 2 ** marti_k / 64) if sid == "marti10" else 1.0
        px = O[c][i]
        if not np.isfinite(px) or acc.eq < D.BROKE:
            return
        entry = px * (1 + d * D.SLIP)
        margin = acc.eq * frac
        notional = margin * lev
        acc.eq -= notional * D.FEE
        margin = min(margin, acc.eq)
        a = A[c][i - 1]
        sp, tp, sa, ta, tr, mx = exits
        stop = entry * (1 - d * sp) if sp else (entry - d * sa * a if sa and np.isfinite(a) else None)
        tgt = entry * (1 + d * tp) if tp else (entry + d * ta * a if ta and np.isfinite(a) else None)
        trail = (tr * a) if tr and np.isfinite(a) else None
        if sid == "max20":
            hh = pd.Series(C[c][:i]).rolling(20).max().iloc[-1]
            ll = pd.Series(C[c][:i]).rolling(20).min().iloc[-1]
            stop = (hh + ll) / 2
        pos = {"coin": c, "dir": d, "entry": entry, "margin": margin, "notional": notional, "stop": stop, "tgt": tgt,
               "trail": trail, "best": entry, "bars": 0, "max": mx, "fund": 0.0,
               "liq": entry * (1 - d * liq_mult), "t0": idx[i]}

    for i in range(start_i, end_i):
        j = i - 1
        g = G[j]
        if target:
            row = score[j]
            want = None
            if g:
                if sid == "hodl3":
                    want = (coins[0], 1)
                elif np.isfinite(row).any() and np.nanmax(row) > 0:
                    want = (coins[int(np.nanargmax(row))], tdir)
            if pos and (want is None or (pos["coin"], pos["dir"]) != want):
                close_pos(i, O[pos["coin"]][i], "přepnutí")
            if pos is None and want:
                open_pos(i, *want)
        elif pos is None and g:
            for c in coins:
                s = S[c][j]
                if s and np.isfinite(O[c][i]):
                    open_pos(i, c, int(s))
                    break
        if pos:
            c, d = pos["coin"], pos["dir"]
            o, h, l, cl = O[c][i], H[c][i], L[c][i], C[c][i]
            if not np.isfinite(cl):
                continue
            pos["fund"] += pos["notional"] * fund * d
            adverse = l if d > 0 else h
            hit = lambda lvl, x: lvl is not None and ((x <= lvl) if d > 0 else (x >= lvl))  # noqa: E731
            if hit(pos["liq"], o) or (hit(pos["liq"], adverse) and not (pos["stop"] is not None and d * (pos["stop"] - pos["liq"]) > 0)):
                liquidate(i)
            elif pos["stop"] is not None and hit(pos["stop"], o):
                close_pos(i, o, "stop")
            elif pos["stop"] is not None and hit(pos["stop"], adverse):
                close_pos(i, pos["stop"], "stop")
            elif pos["tgt"] is not None and (h >= pos["tgt"] if d > 0 else l <= pos["tgt"]):
                close_pos(i, pos["tgt"], "cíl")
            else:
                pos["bars"] += 1
                if pos["trail"]:
                    pos["best"] = max(pos["best"], cl) if d > 0 else min(pos["best"], cl)
                    ns = pos["best"] - d * pos["trail"]
                    pos["stop"] = ns if pos["stop"] is None else (max(pos["stop"], ns) if d > 0 else min(pos["stop"], ns))
                if sid == "max20":
                    hh = np.nanmax(C[c][max(0, i - 19):i + 1]); ll = np.nanmin(C[c][max(0, i - 19):i + 1])
                    pos["stop"] = max(pos["stop"], (hh + ll) / 2)
                if pos["bars"] >= pos["max"]:
                    close_pos(i, cl, "čas")
        do_sweep()
        val = acc.eq + vault[0]
        if pos and np.isfinite(C[pos["coin"]][i]):
            c, d = pos["coin"], pos["dir"]
            val += max(-pos["margin"], pos["notional"] * d * (C[c][i] / pos["entry"] - 1) - pos["fund"])
        curve.append((idx[i], val, acc.dep))
    acc.vault = vault[0]
    return acc, curve, pos, idx


def frames_for(sid, raw):
    cfg = ALL[sid]
    base = "15m" if cfg["tf"] == "15m" else "1h"
    out = {}
    for c in cfg["coins"]:
        if (c, base) in raw:
            out[c] = D.resample(raw[(c, base)], cfg["tf"])
    if sid == "bear_rot5" and "BTC" not in out:
        out["BTC"] = D.resample(raw[("BTC", "1h")], "4h")
    return out


# ---------------------------------------------------------------- fáze trhu (denně, posunuto o den)
def phases(raw):
    b = raw[("BTC", "1h")]["Close"].resample("1D").last().dropna()
    sma200 = b.rolling(200).mean()
    dr = b.diff().abs()
    er = (b - b.shift(30)).abs() / dr.rolling(30).sum()
    vol = np.log(b).diff().rolling(30).std() * np.sqrt(365)
    volmed = vol.rolling(365, min_periods=120).median()
    ph = pd.DataFrame({
        "trend": np.where(b > sma200, "býk", "medvěd"),
        "pohyb": np.where(er >= 0.25, "trend", "pila"),
        "vola": np.where(vol > volmed, "divoko", "klid"),
    }, index=b.index)
    ok = sma200.notna() & er.notna() & volmed.notna()
    ph = ph[ok]
    ph["faze"] = ph["trend"] + " · " + ph["pohyb"] + " · " + ph["vola"]
    ph["faze4"] = ph["trend"] + " · " + ph["pohyb"]
    # fáze platná během dne D = spočtená z close dne D−1
    ph = ph.shift(1).dropna()
    extra = pd.DataFrame({"btc": b, "sma200": sma200, "er": er, "vol": vol, "volmed": volmed}).reindex(ph.index)
    return ph, extra


def phase_at(ph, times, col="faze"):
    s = ph[col]
    days = pd.DatetimeIndex(times).floor("1D")
    return s.reindex(days).to_numpy()


# ---------------------------------------------------------------- Dispečer (walk-forward)
def decide(trades, ph, month_start, min_n=None, t_min=None):
    """Které fáze jsou pro strategii zapnuté v měsíci od month_start (jen z obchodů ukončených před ním)."""
    past = trades[trades["t"] < month_start]
    on = set()
    stats = {}
    for f, g in past.groupby("faze"):
        r = g["r"].to_numpy()
        n = len(r)
        m = float(r.mean())
        t = m / (r.std(ddof=1) / np.sqrt(n)) if n > 2 and r.std(ddof=1) > 0 else 0.0
        stats[f] = (n, m, t)
        if n >= (min_n or MIN_N) and m > 0 and t >= (T_MIN if t_min is None else t_min):
            on.add(f)
    return on, stats


def gate_from_plan(plan, ph, col="faze"):
    """plan: {month(Timestamp) -> set(fází)} → funkce pro run()."""
    def g(idx):
        idx = pd.DatetimeIndex(idx)
        f = phase_at(ph, idx, col)
        m = idx.tz_convert("UTC").to_period("M").to_timestamp().tz_localize("UTC")
        out = np.zeros(len(idx), bool)
        for k, mm in enumerate(m):
            s = plan.get(mm)
            out[k] = bool(s) and f[k] in s
        return out
    return g


def summ(acc, curve):
    if not curve:
        return {}
    cv = pd.DataFrame(curve, columns=["t", "val", "dep"]).set_index("t")
    life = (cv["dep"].diff().fillna(0) > 0).cumsum()
    peak = cv.groupby(life)["val"].cummax()
    tr = [x for x in acc.trades if x.get("kind") != "vklad"]
    return {"equity": float(cv["val"].iloc[-1]), "deposited": float(cv["dep"].iloc[-1]),
            "net": float(cv["val"].iloc[-1] - cv["dep"].iloc[-1]), "peak": float(cv["val"].max()),
            "max_dd": float((cv["val"] / peak - 1).min()), "liqs": acc.liqs, "wipes": acc.wipes, "n": len(tr),
            "curve": cv}


def main(data, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    raw = load(data)
    ph, extra = phases(raw)
    res = {"phases_share": ph["faze"].value_counts(normalize=True).round(3).to_dict()}
    months = pd.date_range(pd.Timestamp(LEARN_UNTIL, tz="UTC"), pd.Timestamp.now(tz="UTC").normalize(), freq="MS")
    rows = []
    for sid, cfg in ALL.items():
        if sid == "kronos10" and not D.KRONOS:
            continue
        fr = frames_for(sid, raw)
        if not fr:
            continue
        start = cfg.get("bt_start", D.BT_START)
        # 1) bez páky → obchody s fází při vstupu
        acc1, cv1, _, _ = run(sid, fr, start, lev=1)
        tr = pd.DataFrame([x for x in acc1.trades if x.get("kind") != "vklad"])
        if sid == "hodl3":   # drží pořád → „obchod“ = jeden den držení (close→close, funding 3× denně)
            bc = raw[("BTC", "1h")]["Close"].resample("1D").last().dropna()
            dd = bc.pct_change().dropna() - 3 * D.FUND_8H
            tr = pd.DataFrame({"opened": dd.index, "t": dd.index + pd.Timedelta("1D"), "r": dd.to_numpy()})
            tr = tr[tr["opened"] >= pd.Timestamp(start, tz="UTC")]
        if tr.empty:
            continue
        tr["faze"] = phase_at(ph, tr["opened"])
        tr = tr.dropna(subset=["faze"])
        by = tr.groupby("faze")["r"].agg(["count", "mean", "sum"])
        # 2) slepě s pákou
        blind = summ(*run(sid, fr, LEARN_UNTIL)[:2])
        # 3) Dispečer – plán měsíc po měsíci
        plan, log = {}, []
        for m in months:
            on, st = decide(tr, ph, m)
            plan[m] = on
            log.append({"month": m.strftime("%Y-%m"), "on": sorted(on)})
        g = gate_from_plan(plan, ph)
        acc_g, cv_g, pos_g, idx_g = run(sid, fr, LEARN_UNTIL, gate=g)
        gated = summ(acc_g, cv_g)
        on_share = float(np.mean(g(pd.date_range(pd.Timestamp(LEARN_UNTIL, tz="UTC"), idx_g[-1], freq="1h"))))
        # 4) náhodné zapínání se stejným podílem času (po dnech)
        rng = np.random.default_rng(7)
        days = pd.date_range(pd.Timestamp(LEARN_UNTIL, tz="UTC"), idx_g[-1].normalize(), freq="1D")
        rnd_net = []
        for _ in range(60 if on_share > 0 else 0):
            mask = pd.Series(rng.random(len(days)) < on_share, index=days)
            gr = lambda idx, mask=mask: mask.reindex(pd.DatetimeIndex(idx).floor("1D")).fillna(False).to_numpy()  # noqa: E731
            s = summ(*run(sid, fr, LEARN_UNTIL, gate=gr)[:2])
            rnd_net.append(s.get("net", 0.0))
        # bez páky: průměr na obchod slepě vs. v zapnutých fázích (jen obchody po LEARN_UNTIL)
        oos = tr[tr["opened"] >= pd.Timestamp(LEARN_UNTIL, tz="UTC")].copy()
        oos["m"] = oos["opened"].dt.tz_convert("UTC").dt.to_period("M").dt.to_timestamp().dt.tz_localize("UTC")
        oos["on"] = [f in plan.get(m, set()) for f, m in zip(oos["faze"], oos["m"])]
        # varianty Dispečera (všechny se hlásí, žádná se nevybírá potichu)
        variants = {}
        for vname, col, mn, tm in VARIANTS:
            trv = tr.copy(); trv["faze"] = phase_at(ph, trv["opened"], col)
            planv = {m: decide(trv, ph, m, mn, tm)[0] for m in months}
            sv = summ(*run(sid, fr, LEARN_UNTIL, gate=gate_from_plan(planv, ph, col))[:2])
            yr = {}
            if sv:
                e = sv["curve"]["val"] - sv["curve"]["dep"]
                for y, gy in e.groupby(e.index.year):
                    yr[str(y)] = round(float(gy.iloc[-1] - (e[e.index.year < y].iloc[-1] if (e.index.year < y).any() else 0.0)))
                sv["curve"].resample("1D").last().to_csv(out / f"curve_{sid}_{vname}.csv")
            variants[vname] = {"net": round(sv.get("net", 0.0)), "max_dd": round(sv.get("max_dd", 0.0), 3), "wipes": sv.get("wipes", 0),
                               "liqs": sv.get("liqs", 0), "n": sv.get("n", 0), "peak": round(sv.get("peak", 0.0)), "years": yr,
                               "on_now": sorted(planv[months[-1]]) if len(months) else []}
        rows.append({
            "variants": variants,
            "id": sid, "name": cfg["name"], "lev": cfg["lev"], "src": cfg.get("src", "research/downtown.py"),
            "by_phase": {f: {"n": int(r["count"]), "mean_pct": round(100 * r["mean"], 3), "sum_pct": round(100 * r["sum"], 1)} for f, r in by.iterrows()},
            "oos_blind_mean_pct": round(100 * oos["r"].mean(), 3) if len(oos) else None, "oos_blind_n": int(len(oos)),
            "oos_on_mean_pct": round(100 * oos.loc[oos["on"], "r"].mean(), 3) if oos["on"].any() else None, "oos_on_n": int(oos["on"].sum()),
            "oos_off_mean_pct": round(100 * oos.loc[~oos["on"], "r"].mean(), 3) if (~oos["on"]).any() else None,
            "blind": {k: v for k, v in blind.items() if k != "curve"},
            "gated": {k: v for k, v in gated.items() if k != "curve"},
            "on_share": round(on_share, 3),
            "random_net_median": float(np.median(rnd_net)) if rnd_net else None,
            "random_beaten_pct": round(100 * float(np.mean(np.array(rnd_net) < gated.get("net", 0))), 0) if rnd_net else None,
            "plan_last": log[-1]["on"] if log else [], "plan": log,
        })
        print(sid, "slepě", round(blind.get("net", 0)), "dispečer", round(gated.get("net", 0)), "podíl zapnuto", round(on_share, 2),
              "náhoda medián", rows[-1]["random_net_median"], "překonáno %", rows[-1]["random_beaten_pct"], flush=True)
        gated["curve"].resample("1D").last().to_csv(out / f"curve_{sid}_dispecer.csv")
        blind["curve"].resample("1D").last().to_csv(out / f"curve_{sid}_slepe.csv")
    res["strategies"] = rows
    res["now_phase"] = ph["faze"].iloc[-1]
    res["now_extra"] = {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in extra.iloc[-1].items()}
    (out / "regimes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:3])
