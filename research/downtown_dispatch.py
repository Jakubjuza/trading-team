#!/usr/bin/env python3
"""Downtown – Dispečer: agent, který divoké strategie zapíná jen ve fázích trhu, kde dřív vydělávaly. Jen papír.

Proč: uživatel (7. 11. 2026) chce, aby strategie nejely slepě, ale jen ve struktuře trhu, která jim sedí.
Výzkum a závěry: reports/downtown_regimes.md (research/experiments/downtown_regimes.py).
Jako ostatní Downtown NIKDY nesahá na skener, registr, riziko, demo ani peníze.

Pravidla stanovená PŘEDEM (7. 11. 2026), po spuštění se neladí:

  Fáze trhu (denně, vždy z uzavřeného PŘEDCHOZÍHO dne, denní close BTC z OKX):
    trend   BTC nad / pod 200denním průměrem                                  → býk / medvěd
    pohyb   efektivita 30 dní = |změna za 30 dní| / součet denních pohybů ≥ 0,25 → trend / pila
    vola    30denní volatilita nad / pod klouzavým mediánem za 365 dní         → divoko / klid
    → 8 fází, např. „býk · trend · klid“.
  Učení (walk-forward, 1. den každého měsíce): z obchodů každé strategie BEZ PÁKY, které skončily před tímto dnem,
    spočítá pro každou fázi průměr a t-statistiku. Fáze je pro strategii zapnutá, když má ≥ 12 obchodů, průměr > 0
    a t ≥ 1. Když je ve fázi zapnutých víc strategií, nasadí tu s nejvyšším t (nejspolehlivější). Jinak hotovost.
  Účet: 1 000 USDT, vždy nasazený celý do jedné strategie (s její pákou a pravidly beze změny). Když jde strategie
    mimo svou fázi, nové vstupy končí (rotace jdou do hotovosti, otevřený obchod doběhne podle svých pravidel).
  Trezor: když se účet zdvojnásobí od posledního základu, 50 % zisku nad základ jde do trezoru (už se neriskuje).
  Bankrot: pod 100 USDT → nový vklad 1 000 USDT (jako ostatní Downtown účty).
  Zpětný test od 1. 7. 2023 (první půlrok 2023 se jen učí), živý papír od LIVE_START.

    python3 research/downtown_dispatch.py [cache_dir]   → samostatně (jinak ho volá research/downtown.py)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from research import downtown as D  # noqa: E402

OUT_MD = ROOT / "reports" / "downtown_dispatch.md"
LEARN_FROM = "2023-01-01"
BT_START = "2023-07-01"
LIVE_START = "2026-11-08"
MIN_N, T_MIN, SWEEP = 12, 1.0, 0.5
ER_TREND = 0.25


# ---------------------------------------------------------------- fáze trhu
def phases(btc_1h):
    b = btc_1h["Close"].resample("1D").last().dropna()
    b = b[b.index + pd.Timedelta("1D") <= datetime.now(timezone.utc)]          # jen uzavřené dny
    sma200 = b.rolling(200).mean()
    er = (b - b.shift(30)).abs() / b.diff().abs().rolling(30).sum()
    vol = np.log(b).diff().rolling(30).std() * np.sqrt(365)
    volmed = vol.rolling(365, min_periods=120).median()
    ok = sma200.notna() & er.notna() & volmed.notna()
    f = pd.DataFrame({"trend": np.where(b > sma200, "býk", "medvěd"), "pohyb": np.where(er >= ER_TREND, "trend", "pila"),
                      "vola": np.where(vol > volmed, "divoko", "klid")}, index=b.index)[ok]
    f["faze"] = f["trend"] + " · " + f["pohyb"] + " · " + f["vola"]
    feat = pd.DataFrame({"btc": b, "sma200": sma200, "er": er, "vol": vol, "volmed": volmed})[ok]
    # fáze platná během dne D = spočtená z close dne D−1; poslední uzavřený den určuje fázi „dnes“
    nxt = f.index[-1] + pd.Timedelta("1D")
    f = pd.concat([f, f.iloc[-1:].set_axis([nxt])]).shift(1).dropna()
    return f, feat


def phase_at(ph, times):
    return ph["faze"].reindex(pd.DatetimeIndex(times).floor("1D")).to_numpy()


def month_of(times):
    t = pd.DatetimeIndex(times).tz_convert("UTC")
    return pd.DatetimeIndex(t.strftime("%Y-%m-01")).tz_localize("UTC")


# ---------------------------------------------------------------- učení
def unlevered_trades(sid, frames, raw):
    """Obchody strategie bez páky (r = čistý výnos obchodu vč. poplatků, skluzu a fundingu)."""
    if sid == "hodl3":   # drží pořád → „obchod“ = den držení BTC (close→close, funding 3× denně)
        bc = raw[("BTC", "1h")]["Close"].resample("1D").last().dropna()
        r = bc.pct_change().dropna() - 3 * D.FUND_8H
        r = r[r.index >= pd.Timestamp(LEARN_FROM, tz="UTC")]
        return pd.DataFrame({"opened": r.index, "t": r.index + pd.Timedelta("1D"), "r": r.to_numpy()})
    acc, _, _, _ = D.run(sid, frames, D.STRATS[sid].get("bt_start", LEARN_FROM), lev=1)
    tr = [x for x in acc.trades if x.get("kind") != "vklad" and "r" in x]
    if not tr:
        return pd.DataFrame(columns=["opened", "t", "r"])
    df = pd.DataFrame(tr)[["opened", "t", "r"]]
    df["opened"] = pd.to_datetime(df["opened"], utc=True)
    df["t"] = pd.to_datetime(df["t"], utc=True)
    return df


def stats(tr):
    out = {}
    for f, g in tr.groupby("faze"):
        r = g["r"].to_numpy(float)
        n, m = len(r), float(r.mean())
        sd = float(r.std(ddof=1)) if n > 2 else 0.0
        out[f] = (n, m, m / (sd / np.sqrt(n)) if sd > 0 else 0.0)
    return out


def make_plan(trades, months):
    """{měsíc: {fáze: [strategie seřazené podle t]}} – jen z obchodů ukončených před začátkem měsíce."""
    plan = {}
    for m in months:
        per = {}
        for sid, tr in trades.items():
            for f, (n, mean, t) in stats(tr[tr["t"] < m]).items():
                if n >= MIN_N and mean > 0 and t >= T_MIN:
                    per.setdefault(f, []).append((t, sid))
        plan[m] = {f: [s for _, s in sorted(v, reverse=True)] for f, v in per.items()}
    return plan


def gate_for(sid, plan, ph):
    def g(idx):
        f, mm = phase_at(ph, idx), month_of(idx)
        return np.array([bool(plan.get(m, {}).get(ff)) and plan[m][ff][0] == sid for ff, m in zip(f, mm)], bool)
    return g


# ---------------------------------------------------------------- účet Dispečera
def dispatch_run(frames_all, trades, plan, ph, start, now):
    """Každá strategie běží ve vlastním podúčtu jen ve „svých“ hodinách (brány se nepřekrývají); účet Dispečera
    skládá jejich hodinové výnosy, k tomu trezor a bankroty."""
    hours = pd.date_range(pd.Timestamp(start, tz="UTC"), pd.Timestamp(now).floor("1h"), freq="1h")
    rets = pd.Series(0.0, index=hours)
    sub_trades, opens = [], []
    sub_val = {}
    for sid in trades:
        acc, cv, pos, idx = D.run(sid, frames_all[sid], start, gate=gate_for(sid, plan, ph))
        if not cv:
            continue
        c = pd.DataFrame(cv, columns=["t", "val", "dep"]).set_index("t")
        c.index = pd.DatetimeIndex(c.index)
        c = c.reindex(hours, method="ffill").dropna()
        prev = c["val"].shift(1)
        r = ((c["val"] - prev - c["dep"].diff()) / prev).fillna(0.0).clip(lower=-1.0)
        rets = rets.add(r.reindex(hours).fillna(0.0), fill_value=0.0)
        sub_val[sid] = c["val"]
        for x in acc.trades:
            if x.get("kind") != "vklad":
                sub_trades.append({**x, "strat": sid})
        if pos:
            opens.append((sid, pos))
    E, dep, vault, base, wipes, vals = D.START_CASH, D.START_CASH, 0.0, D.START_CASH, 0, []
    for t, r in rets.items():
        E *= 1 + max(r, -1.0)
        if E < D.BROKE:
            wipes += 1
            dep += D.START_CASH
            E += D.START_CASH
            base = D.START_CASH
        if E >= 2 * base:
            w = (E - base) * SWEEP
            E -= w
            vault += w
            base = E
        elif E < base / 2:
            base = max(D.START_CASH, E)
        vals.append((t, E + vault, dep))
    cv = pd.DataFrame(vals, columns=["t", "val", "dep"]).set_index("t")
    # obchody přepočtené na účet Dispečera (podíl výnosu podúčtu × hodnota Dispečera při vstupu)
    out_tr = []
    for x in sorted(sub_trades, key=lambda z: z["t"]):
        t0 = pd.Timestamp(x.get("opened") or x["t"])
        sv = sub_val.get(x["strat"])
        if sv is None or t0 < hours[0]:
            continue
        k = max(0, hours.searchsorted(t0.floor("1h")) - 1)
        base_sub, base_disp = float(sv.iloc[min(k, len(sv) - 1)]), float(cv["val"].iloc[k] - 0)
        pnl = x["pnl"] / base_sub * (base_disp - 0) if base_sub > 0 else 0.0
        out_tr.append({**x, "pnl": round(pnl, 2), "name": D.STRATS[x["strat"]]["name"]})
    return cv, out_tr, opens, wipes, vault


def summary(cv, trades, opens, wipes):
    """Stejný tvar jako D.summarize (Agentown čte stejná pole)."""
    class _A:  # noqa: N801
        pass
    a = _A()
    a.trades, a.liqs, a.wipes = trades, sum(1 for x in trades if x.get("kind") == "likvidace"), wipes
    curve = [(t, float(r.val), float(r.dep)) for t, r in cv.iterrows()]
    out = D.summarize(a, curve, None, cv.index)
    if opens:
        sid, p = opens[0]
        out["open"] = {"coin": p["coin"], "dir": p["dir"], "entry": round(p["entry"], 6), "since": p["t0"], "strat": sid,
                       "margin": round(p["margin"], 2), "liq": round(p["liq"], 6),
                       "stop": round(p["stop"], 6) if p["stop"] else None, "tgt": round(p["tgt"], 6) if p["tgt"] else None}
    return out


def build(raw, now=None):
    """Spočítá Dispečera; vrátí záznam do research/downtown.json (stejný tvar jako ostatní strategie + „dispatch“)."""
    now = now or datetime.now(timezone.utc)
    ph, feat = phases(raw[("BTC", "1h")])
    frames_all, trades = {}, {}
    for sid, cfg in D.STRATS.items():
        if sid == "kronos10" and not D.KRONOS:
            continue
        base = "15m" if cfg["tf"] == "15m" else "1h"
        if not all((c, base) in raw for c in cfg["coins"]):
            continue
        fr = {c: D.resample(raw[(c, base)], cfg["tf"]) for c in cfg["coins"]}
        tr = unlevered_trades(sid, fr, raw)
        if tr.empty:
            continue
        tr["faze"] = phase_at(ph, tr["opened"])
        frames_all[sid], trades[sid] = fr, tr.dropna(subset=["faze"])
    months = pd.date_range(pd.Timestamp(BT_START, tz="UTC"), pd.Timestamp(now).floor("1D"), freq="MS")
    plan = make_plan(trades, months)
    cv, tr_bt, opens_bt, wipes_bt, vault_bt = dispatch_run(frames_all, trades, plan, ph, BT_START, now)
    bt = summary(cv, tr_bt, opens_bt, wipes_bt)
    bt["vault"] = round(vault_bt, 2)
    live = {"start": LIVE_START, "n_trades": 0, "equity": D.START_CASH, "deposited": D.START_CASH, "net": 0.0,
            "liquidations": 0, "wipes": 0, "curve": [], "last_trades": [], "open": None, "vault": 0.0}
    if now >= pd.Timestamp(LIVE_START, tz="UTC") + pd.Timedelta("1h"):
        cv2, tr2, op2, w2, v2 = dispatch_run(frames_all, trades, plan, ph, LIVE_START, now)
        if len(cv2):
            live = summary(cv2, tr2, op2, w2)
            live["start"], live["vault"] = LIVE_START, round(v2, 2)
    cur_m = months[-1]
    f_now = ph["faze"].iloc[-1]
    chosen = (plan[cur_m].get(f_now) or [None])[0]
    st_all = {sid: stats(tr) for sid, tr in trades.items()}
    table = {sid: {f: {"n": n, "mean_pct": round(100 * m, 3), "t": round(t, 2)} for f, (n, m, t) in st.items()} for sid, st in st_all.items()}
    hist = []
    for m in months[-12:]:
        hist.append({"month": m.strftime("%Y-%m"), "plan": plan[m]})
    fx = feat.iloc[-1]
    names = {sid: D.STRATS[sid]["name"] for sid in trades}
    return {
        "id": "dispecer", "name": "Dispečer fází", "bt_start": BT_START, "lev": int(D.STRATS[chosen]["lev"]) if chosen else 0,
        "tag": "agent: nasazuje strategii jen v její fázi trhu",
        "rules": ("Každý den určí fázi trhu (BTC nad/pod 200denním průměrem · trend/pila podle efektivity 30 dní · "
                  "volatilita nad/pod mediánem roku). Měsíčně se z minulých obchodů naučí, ve kterých fázích která "
                  "strategie vydělávala (≥ 12 obchodů, průměr > 0, t ≥ 1), a celý účet nasadí jen tam; jinak drží hotovost. "
                  "Při zdvojnásobení účtu odloží 50 % zisku do trezoru"),
        "tf": "1d", "coins": D.COINS, "backtest": bt, "live": live, "updated": now.isoformat(timespec="minutes"),
        "dispatch": {
            "phase_now": f_now, "phase_parts": {k: ph[k].iloc[-1] for k in ("trend", "pohyb", "vola")},
            "features": {"btc": round(float(fx["btc"]), 2), "sma200": round(float(fx["sma200"]), 2), "er30": round(float(fx["er"]), 3),
                         "vol30": round(float(fx["vol"]), 3), "vol_median": round(float(fx["volmed"]), 3), "as_of": fx.name.date().isoformat()},
            "active_now": chosen, "active_name": names.get(chosen), "plan_now": plan[cur_m], "names": names,
            "phase_table": table, "plan_history": hist,
            "phase_share": {k: round(float(v), 3) for k, v in ph["faze"][ph.index >= pd.Timestamp(LEARN_FROM, tz="UTC")].value_counts(normalize=True).items()},
            "rule": {"min_n": MIN_N, "t_min": T_MIN, "er_trend": ER_TREND, "sweep": SWEEP, "learn_from": LEARN_FROM},
        },
    }


def n0(x):
    return f"{x:,.0f}".replace(",", " ")


def write_md(e):
    d, b, lv = e["dispatch"], e["backtest"], e["live"]
    fx = d["features"]
    L = ["# Downtown – Dispečer fází (jen papír)", "",
         f"Aktualizováno {e['updated']} UTC skriptem `research/downtown_dispatch.py` (pravidla stanovená předem v hlavičce).",
         "Agent nasazuje divoké strategie Downtownu jen ve fázích trhu, kde dřív vydělávaly; výzkum v `reports/downtown_regimes.md`.",
         "Oddělené od desku, nejde o finanční poradenství.", "",
         "## Teď", "",
         f"- **Fáze trhu:** {d['phase_now']} (data k {fx['as_of']}: BTC {n0(fx['btc'])} vs. 200denní průměr {n0(fx['sma200'])}, "
         f"efektivita 30 dní {fx['er30']:.2f} (trend od {d['rule']['er_trend']}), volatilita {100 * fx['vol30']:.0f} % vs. medián {100 * fx['vol_median']:.0f} %)",
         f"- **Nasazeno:** {d['active_name'] or 'nic – hotovost (v této fázi žádná strategie neprošla)'}",
         "- **Plán tohoto měsíce:** " + ("; ".join(f"{f} → {', '.join(d['names'][s] for s in v)}" for f, v in d["plan_now"].items()) or "žádná fáze nezapnutá"), "",
         f"## Zpětný test od {e['bt_start']} (walk-forward, učení jen z minulých obchodů)", "",
         f"Vloženo celkem {n0(b['deposited'])} → hodnota {n0(b['equity'])} USDT (z toho trezor {n0(b.get('vault', 0))}), čistě {n0(b['net'])} USDT; "
         f"max. hodnota {n0(b['peak_equity'])}; max. propad {b['max_dd_pct']} %; bankroty {b['wipes']}; obchodů {b['n_trades']}.", "",
         "Roky: " + ", ".join(f"{y}: {v} %" for y, v in b["years"].items()), "",
         f"## Živý papír od {LIVE_START}", "",
         f"Účet {n0(lv.get('equity', 0))} USDT, čistě {n0(lv.get('net', 0))}, obchodů {lv.get('n_trades', 0)}.", "",
         "## Kde která strategie vydělávala (bez páky, průměr na obchod, všechny dosavadní obchody)", "",
         "| Strategie | " + " | ".join(sorted(d["phase_share"])) + " |", "|---|" + "---:|" * len(d["phase_share"])]
    for sid, tab in d["phase_table"].items():
        cells = []
        for f in sorted(d["phase_share"]):
            x = tab.get(f)
            cells.append("–" if not x else f"{'**' if x['n'] >= MIN_N and x['mean_pct'] > 0 and x['t'] >= T_MIN else ''}{x['mean_pct']:+.2f} % (n {x['n']}, t {x['t']:+.1f}){'**' if x['n'] >= MIN_N and x['mean_pct'] > 0 and x['t'] >= T_MIN else ''}")
        L.append(f"| {d['names'][sid]} | " + " | ".join(cells) + " |")
    L += ["", "Tučně = fáze splňuje pravidlo (≥ 12 obchodů, průměr > 0, t ≥ 1). Podíl dní ve fázích: "
          + ", ".join(f"{f} {100 * v:.0f} %" for f, v in sorted(d["phase_share"].items(), key=lambda x: -x[1])) + "."]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(cache="/tmp/dt_cache"):
    D.load_kronos()
    raw = {}
    need = {(c, "15m" if s["tf"] == "15m" else "1h") for s in D.STRATS.values() for c in s["coins"]}
    for c, base in sorted(need):
        raw[(c, base)] = D.fetch(c, base, cache)
    e = build(raw)
    write_md(e)
    print(json.dumps({k: e["dispatch"][k] for k in ("phase_now", "active_now", "plan_now")}, ensure_ascii=False))


if __name__ == "__main__":
    main(*(sys.argv[1:2] or []))
