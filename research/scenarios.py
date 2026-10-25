#!/usr/bin/env python3
"""Scénáře na delších timeframech – týden, měsíc, halvingový cyklus. Bez AI, jen z historie cen.

Stav trhu (z uzavřených svíček, nic z budoucnosti):
  • týden: close vs. EMA 21 týdnů („býčí pásmo“) a její sklon, RSI 14 týdnů,
  • měsíc: close vs. SMA 10 měsíců (klasický dlouhodobý trendový filtr),
  • propad od historického maxima, pozice v 52týdenním rozpětí, fáze BTC halvingového cyklu.

Scénáře (rozpětí, kam se cena může dostat za 4, 13 a 26 týdnů): historické výnosy všech mincí normované
volatilitou v okamžiku startu (z = log výnos / (σ_denní · √dní)), percentily z se přenesou na DNEŠNÍ volatilitu
mince. Medvědí = 10. percentil, základní = medián, býčí = 90. percentil. Volatilita se mění, proto se škáluje –
staré bubliny (+1000 %) tak nenafukují dnešní scénáře. Směr (P(růst)) podle režimu se v testu od roku 2022
nepotvrdil, proto se nepoužívá (reports/scenarios.md).

Použití:
    python3 research/scenarios.py BTC            # sekce pro datový list (JSON)
    python3 research/scenarios.py --report       # kalibrace + report pro všechny mince z config.yaml
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

HORIZONS = {"4 týdny": 28, "13 týdnů": 91, "26 týdnů": 182}
STATS = ROOT / "research" / "scenario_stats.json"     # percentily z (8 mincí, celá historie) – obnovuje --report
CENTER = True        # neutrální střed: v kalibraci po letech od 2022 sedí lépe než empirický (reports/scenarios.md)
HALVINGS = ["2012-11-28", "2016-07-09", "2020-05-11", "2024-04-20"]     # data halvingů bitcoinu (podle bloků)


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def weekly(daily):
    """Týdenní svíčky po–ne z denních; poslední neúplný týden se vynechá."""
    w = daily.resample("W-SUN", label="right", closed="right").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    last_day = daily.index[-1]
    if len(w) and w.index[-1] > last_day.normalize() + pd.Timedelta(hours=0) and last_day.dayofweek != 6:
        w = w.iloc[:-1]
    return w


def monthly(daily):
    m = daily.resample("ME").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    last_day = daily.index[-1]
    if len(m) and (last_day + pd.Timedelta(days=1)).month == last_day.month:     # měsíc ještě neskončil
        m = m.iloc[:-1]
    return m


def regime_series(daily):
    """Pro každý den režim z UZAVŘENÝCH týdnů a měsíců před ním: 'týden↑/↓ měsíc↑/↓' (NaN při krátké historii)."""
    w = daily["Close"].resample("W-SUN", label="right", closed="right").last().dropna()
    m = daily["Close"].resample("ME").last().dropna()
    w_up = (w > ema(w, 21)).where(np.arange(len(w)) >= 21)
    m_up = (m > m.rolling(10).mean()).where(m.rolling(10).mean().notna())
    # týden s koncem v neděli D je známý až od pondělí D+1 → posun o 1 den; měsíc obdobně
    w_up.index = w_up.index + pd.Timedelta(days=1)
    m_up.index = m_up.index + pd.Timedelta(days=1)
    wd = w_up.reindex(daily.index, method="ffill")
    md = m_up.reindex(daily.index, method="ffill")
    lab = pd.Series(np.nan, index=daily.index, dtype=object)
    ok = wd.notna() & md.notna()
    lab[ok] = ("týden " + np.where(wd[ok].astype(bool), "↑", "↓") + " · měsíc " + np.where(md[ok].astype(bool), "↑", "↓"))
    return lab


def vol_series(daily, span=30):
    """EWMA směrodatná odchylka denních log výnosů (jen minulost)."""
    r = np.log(daily["Close"]).diff()
    return r.ewm(span=span, min_periods=span).std()


def z_returns(daily, days):
    """Budoucí log výnos za `days` dní normovaný volatilitou v okamžiku startu."""
    c = np.log(daily["Close"])
    return (c.shift(-days) - c) / (vol_series(daily) * np.sqrt(days))


def z_quantiles(frames, days, until=None, since=None, qs=(0.1, 0.5, 0.9), center=None):
    """Percentily normovaných výnosů přes všechny mince. until: jen okna, jejichž výsledek je známý před `until`.
    center=True: střed posunutý na nulu (bez předpokládaného růstu/poklesu), tvar rozdělení zůstává."""
    center = CENTER if center is None else center
    parts = []
    for d in frames.values():
        z = z_returns(d, days)
        m = z.notna()
        if until is not None:
            m &= (d.index + pd.Timedelta(days=days)) < until
        if since is not None:
            m &= d.index >= since
        parts.append(z[m])
    z = pd.concat(parts)
    out = {q: float(z.quantile(q)) for q in qs}
    if center:
        mid = float(z.quantile(0.5))
        out = {q: v - mid for q, v in out.items()}
    return out, int(len(z))


def scenario_range(daily, zq, days):
    """Scénářové ceny z dnešní volatility: cena · exp(z_q · σ · √dní)."""
    price = float(daily["Close"].iloc[-1])
    sig = float(vol_series(daily).iloc[-1])
    lv = {q: price * float(np.exp(z * sig * np.sqrt(days))) for q, z in zq.items()}
    return {"medvědí (10 %)": round(lv[0.1], 6), "základní (medián)": round(lv[0.5], 6), "býčí (90 %)": round(lv[0.9], 6),
            "pásmo_pct": [round((lv[0.1] / price - 1) * 100, 1), round((lv[0.9] / price - 1) * 100, 1)],
            "vol_annual_pct": round(sig * np.sqrt(365) * 100, 1)}


def state(daily):
    w, m = weekly(daily), monthly(daily)
    c = float(daily["Close"].iloc[-1])
    out = {"close": round(c, 6), "as_of": daily.index[-1].date().isoformat()}
    if len(w) > 25:
        e21 = ema(w["Close"], 21)
        out["week"] = {"close": round(float(w["Close"].iloc[-1]), 6), "ema21": round(float(e21.iloc[-1]), 6),
                       "above_ema21": bool(w["Close"].iloc[-1] > e21.iloc[-1]),
                       "ema21_slope_4w_pct": round(float(e21.iloc[-1] / e21.iloc[-5] - 1) * 100, 2),
                       "rsi14": round(float(rsi(w["Close"]).iloc[-1]), 1),
                       "high_52w": round(float(w["High"].iloc[-52:].max()), 6), "low_52w": round(float(w["Low"].iloc[-52:].min()), 6),
                       "last_week": w.index[-1].date().isoformat()}
        rng = out["week"]["high_52w"] - out["week"]["low_52w"]
        out["week"]["pos_52w_pct"] = round((c - out["week"]["low_52w"]) / rng * 100, 1) if rng else None
    if len(m) > 11:
        s10 = m["Close"].rolling(10).mean()
        out["month"] = {"close": round(float(m["Close"].iloc[-1]), 6), "sma10": round(float(s10.iloc[-1]), 6),
                        "above_sma10": bool(m["Close"].iloc[-1] > s10.iloc[-1]),
                        "prev_month_high": round(float(m["High"].iloc[-1]), 6), "prev_month_low": round(float(m["Low"].iloc[-1]), 6),
                        "rsi14": round(float(rsi(m["Close"]).iloc[-1]), 1) if len(m) > 15 else None,
                        "last_month": m.index[-1].strftime("%Y-%m")}
    ath = float(daily["High"].max())
    out["drawdown_from_high_pct"] = round((c / ath - 1) * 100, 1)
    out["history_high"] = {"price": round(ath, 6), "date": daily["High"].idxmax().date().isoformat(),
                           "note": "maximum v dostupné historii (nemusí být ATH, pokud je historie krátká)"}
    return out


def cycle(daily_btc, now=None):
    """Fáze halvingového cyklu + jak dopadly stejné fáze minulých cyklů (jen BTC, malý vzorek)."""
    now = pd.Timestamp(now or daily_btc.index[-1])
    halv = [pd.Timestamp(h, tz="UTC") for h in HALVINGS]
    last = max(h for h in halv if h <= now)
    days = int((now - last).days)
    analogs = []
    for h in halv[:-1]:
        t = h + pd.Timedelta(days=days)
        if t < daily_btc.index[0] or t + pd.Timedelta(days=182) > daily_btc.index[-1]:
            continue
        i = daily_btc.index.searchsorted(t)
        c0 = float(daily_btc["Close"].iloc[i])
        seg = daily_btc["Close"].iloc[i:i + 183]
        analogs.append({"halving": h.date().isoformat(), "ret_26w_pct": round((float(seg.iloc[-1]) / c0 - 1) * 100, 1),
                        "max_dd_26w_pct": round((float(seg.min()) / c0 - 1) * 100, 1)})
    peaks = []
    for a, b in zip(halv, halv[1:] + [now]):
        b = min(b, a + pd.Timedelta(days=730))                          # vrchol cyklu = maximum do 24 měsíců po halvingu
        seg = daily_btc["Close"][(daily_btc.index >= a) & (daily_btc.index < b)]
        if len(seg) > 300:
            peaks.append({"halving": a.date().isoformat(), "peak_after_months": round((seg.idxmax() - a).days / 30.44, 1),
                          "peak_date": seg.idxmax().date().isoformat()})
    return {"last_halving": last.date().isoformat(), "days_since": days, "months_since": round(days / 30.44, 1),
            "same_phase_prev_cycles": analogs, "cycle_peaks": peaks,
            "note": "jen 2–3 minulé cykly → anekdota, ne statistika"}


def build_stats(frames):
    out = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "center": CENTER,
           "coins": list(frames), "z": {}}
    for name, days in HORIZONS.items():
        zq, n = z_quantiles(frames, days)
        out["z"][name] = {"q10": round(zq[0.1], 4), "q50": round(zq[0.5], 4), "q90": round(zq[0.9], 4), "n_days": n}
    if "BTC" in frames:
        out["btc_cycle_peaks"] = cycle(frames["BTC"])["cycle_peaks"]
    return out


def load_stats(path=STATS):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def zq_from_stats(stats, horizon):
    z = (stats.get("z") or {}).get(horizon)
    return {0.1: z["q10"], 0.5: z["q50"], 0.9: z["q90"]} if z else None


def quick_range(daily, horizon="4 týdny", stats=None):
    """Rozpětí scénářů jen z posledních svíček (cache skeneru) + uložených percentilů. None = málo dat."""
    stats = load_stats() if stats is None else stats
    zq = zq_from_stats(stats, horizon)
    if zq is None or daily is None or len(daily) < 40 or np.isnan(vol_series(daily).iloc[-1]):
        return None
    return scenario_range(daily, zq, HORIZONS[horizon])


def section_scenarios(coin, frames=None, now=None, stats=None):
    """Sekce datového listu `scenarios`. frames = {coin: denní svíčky s dlouhou historií} (None = stáhne)."""
    frames = frames or load_frames([coin, "BTC"])
    stats = load_stats() if stats is None else stats
    d = frames[coin]
    reg = regime_series(d).iloc[-1]
    out = {"source": "denní svíčky (yfinance / burza), percentily research/scenario_stats.json, výpočet research/scenarios.py",
           "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"), "state": state(d),
           "regime": reg if isinstance(reg, str) else None, "scenarios": {}}
    for name, days in HORIZONS.items():
        zq = zq_from_stats(stats, name)
        n = (stats.get("z") or {}).get(name, {}).get("n_days")
        if zq is None:
            zq, n = z_quantiles(frames, days)
        out["scenarios"][name] = {**scenario_range(d, zq, days), "n_days_history": n}
    if "BTC" in frames:
        out["btc_cycle"] = cycle(frames["BTC"], now)
    out["note"] = ("Rozpětí = kam se cena v minulosti dostala při stejné volatilitě (10.–90. percentil), ne předpověď směru. "
                   "Kalibrace na datech od 2022 v reports/scenarios.md. Režim (týden/měsíc) je popis trendu – "
                   "směr podle něj se v testu nepotvrdil.")
    return out


def closed_days(df, now=None):
    """Jen uzavřené denní svíčky (yfinance vrací i dnešní rozpracovanou)."""
    today = pd.Timestamp(now or datetime.now(timezone.utc)).tz_convert("UTC").normalize()
    return df[df.index < today]


def load_frames(coins, cache_dir=None, now=None):
    from scanner import evaluate as ev
    out = {}
    for c in coins:
        df = ev.load_history(f"{c}/USDT", "crypto", "1d", 3650, "kraken", cache_dir or ROOT / "scanner" / "cache")
        if df is not None and len(df):
            out[c] = closed_days(df[["Open", "High", "Low", "Close"]].astype(float), now)
    return out


def fmt_price(x):
    if x >= 1000:
        return f"{x:,.0f}".replace(",", " ")
    return (f"{x:.2f}" if x >= 1 else f"{x:.4f}").replace(".", ",")


def outlook_lines(frames, coins, horizon="13 týdnů", stats=None):
    """Řádky týdenního výhledu na Telegram (frames stačí z cache skeneru – ~600 denních svíček)."""
    days = HORIZONS[horizon]
    stats = load_stats() if stats is None else stats
    zq = zq_from_stats(stats, horizon) or z_quantiles(frames, days)[0]
    lines = []
    for c in coins:
        if c not in frames:
            continue
        d = frames[c]
        st = state(d)
        wk, mo = st.get("week", {}), st.get("month", {})
        trend = (f"týden {'↑' if wk.get('above_ema21') else '↓'} · měsíc {'↑' if mo.get('above_sma10') else '↓'}"
                 if wk and mo else "krátká historie")
        sc = scenario_range(d, zq, days)
        lines.append(f"{c} {fmt_price(st['close'])} · {trend} · {horizon}: {fmt_price(sc['medvědí (10 %)'])} – "
                     f"{fmt_price(sc['býčí (90 %)'])} (medián {fmt_price(sc['základní (medián)'])})")
    return lines


def calibration(frames, split="2022-01-01"):
    """Percentily z dat před `split` → jak často skutečnost od `split` padla pod 10 %, nad medián, nad 90 %
    (cíl 10 % / 50 % / 10 %) a do pásma 10–90 % (cíl 80 %). Pro srovnání i P(růst) podle režimu."""
    split = pd.Timestamp(split, tz="UTC")
    rows = []
    for name, days in HORIZONS.items():
        zq, n_train = z_quantiles(frames, days, until=split, center=False)
        below = above_med = above = n = 0
        regs = {}
        for d in frames.values():
            z = z_returns(d, days)
            test = z[(d.index >= split)].dropna()
            below += int((test < zq[0.1]).sum())
            above_med += int((test > zq[0.5]).sum())
            above += int((test > zq[0.9]).sum())
            n += len(test)
            lab = regime_series(d)
            fr = (np.log(d["Close"]).shift(-days) - np.log(d["Close"]))
            for reg in lab.dropna().unique():
                tr = fr[(lab == reg) & ((d.index + pd.Timedelta(days=days)) < split)].dropna()
                te = fr[(lab == reg) & (d.index >= split)].dropna()
                b = regs.setdefault(reg, [0, 0, 0, 0])
                b[0] += int((tr > 0).sum()); b[1] += len(tr); b[2] += int((te > 0).sum()); b[3] += len(te)
        rows.append({"horizon": name, "n_train": n_train, "n_test": n,
                     "below_q10": round(below / n, 3), "above_median": round(above_med / n, 3), "above_q90": round(above / n, 3),
                     "coverage_10_90": round(1 - below / n - above / n, 3), "z": {str(k): round(v, 3) for k, v in zq.items()},
                     "regimes": {r: {"pred_p_up": round(v[0] / v[1], 3) if v[1] else None,
                                     "actual_p_up": round(v[2] / v[3], 3) if v[3] else None, "n_test": v[3]}
                                 for r, v in sorted(regs.items())}})
    return rows


def walk_forward(frames, years=range(2022, 2027), center=True):
    """Každý rok Y: percentily jen z dat před Y, test na roce Y. Souhrn přes roky (cíl 10 % / 50 % / 10 %)."""
    out = []
    for name, days in HORIZONS.items():
        below = above_med = above = n = 0
        for y in years:
            y0, y1 = pd.Timestamp(f"{y}-01-01", tz="UTC"), pd.Timestamp(f"{y + 1}-01-01", tz="UTC")
            zq, _ = z_quantiles(frames, days, until=y0, center=center)
            for d in frames.values():
                z = z_returns(d, days)
                test = z[(d.index >= y0) & (d.index < y1)].dropna()
                below += int((test < zq[0.1]).sum())
                above_med += int((test > zq[0.5]).sum())
                above += int((test > zq[0.9]).sum())
                n += len(test)
        if n:
            out.append({"horizon": name, "n_test": n, "below_q10": round(below / n, 3), "above_median": round(above_med / n, 3),
                        "above_q90": round(above / n, 3), "coverage_10_90": round(1 - (below + above) / n, 3)})
    return out


def calib_error(rows):
    """Součet odchylek od cílů 10 % / 50 % / 10 % (menší = lepší kalibrace)."""
    return round(sum(abs(r["below_q10"] - 0.1) + abs(r["above_median"] - 0.5) + abs(r["above_q90"] - 0.1) for r in rows), 3)


def report(frames):
    cal = calibration(frames)
    wf = {"empirický střed": walk_forward(frames, center=False), "neutrální střed": walk_forward(frames, center=True)}
    md = [f"# Scénáře na delších timeframech ({datetime.now(timezone.utc):%Y-%m-%d})", "",
          f"Denní svíčky {len(frames)} mincí ({', '.join(frames)}). Scénáře = percentily historických výnosů normovaných "
          "volatilitou, přenesené na dnešní volatilitu mince. Kalibrace: percentily jen z dat do konce roku 2021, "
          "porovnané se skutečností od roku 2022 (data, která model neviděl).", "",
          "Jednorázový test (empirický střed, data do 2021 → od 2022):", "",
          "| Horizont | Pod medvědím (cíl 10 %) | Nad mediánem (cíl 50 %) | Nad býčím (cíl 10 %) | V pásmu (cíl 80 %) | Dní testu |",
          "|---|---|---|---|---|---|"]
    md += [f"| {r['horizon']} | {r['below_q10'] * 100:.0f} % | {r['above_median'] * 100:.0f} % | {r['above_q90'] * 100:.0f} % | "
           f"{r['coverage_10_90'] * 100:.0f} % | {r['n_test']} |" for r in cal]
    md += ["", "**Kalibrace po letech 2022–2026** (každý rok jen z dat před ním) – dvě varianty středu:", "",
           "| Varianta | Horizont | Pod medvědím (10 %) | Nad mediánem (50 %) | Nad býčím (10 %) | V pásmu (80 %) |",
           "|---|---|---|---|---|---|"]
    for lab, rows in wf.items():
        md += [f"| {lab} | {r['horizon']} | {r['below_q10'] * 100:.0f} % | {r['above_median'] * 100:.0f} % | "
               f"{r['above_q90'] * 100:.0f} % | {r['coverage_10_90'] * 100:.0f} % |" for r in rows]
    md += ["", "Chyba kalibrace (součet odchylek od cílů, menší = lepší): "
           + ", ".join(f"{lab} {calib_error(rows)}" for lab, rows in wf.items())
           + f". Skener používá: {'neutrální' if CENTER else 'empirický'} střed."]
    md += ["", "Směr podle režimu (týden nad/pod EMA21 × měsíc nad/pod SMA10) – P(růst) v datech do 2021 vs. od 2022:", "",
           "| Horizont | Režim | Do 2021 | Od 2022 | Dní testu |", "|---|---|---|---|---|"]
    for r in cal:
        for reg, v in r["regimes"].items():
            if v["pred_p_up"] is not None and v["actual_p_up"] is not None:
                md.append(f"| {r['horizon']} | {reg} | {v['pred_p_up'] * 100:.0f} % | {v['actual_p_up'] * 100:.0f} % | {v['n_test']} |")
    md += ["", "Čtení: rozpětí jsou použitelná, když skutečnost padá pod medvědí a nad býčí scénář zhruba v 10 % případů. "
           "Směr podle režimu se mezi obdobími neudržel (do 2021 býčí historie), proto ho desk nepoužívá jako pravděpodobnost. "
           "Okna se překrývají → nezávislých období je mnohem méně než dní.", "", "Nejde o finanční poradenství."]
    return "\n".join(md) + "\n", {"split_2022": cal, "walk_forward": wf}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("coin", nargs="?", default="BTC")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--cache-dir", type=Path)
    a = ap.parse_args()
    import yaml
    cfg = yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text(encoding="utf-8"))
    coins = [t["symbol"].split("/")[0] for t in cfg["tickers"] if t["source"] == "crypto"]
    frames = load_frames(coins if a.report else sorted({a.coin, "BTC"}), a.cache_dir)
    if a.report:
        md, cal = report(frames)
        (ROOT / "reports" / "scenarios.md").write_text(md, encoding="utf-8")
        (ROOT / "research" / "scenarios_calibration.json").write_text(json.dumps(cal, ensure_ascii=False, indent=1) + "\n")
        STATS.write_text(json.dumps(build_stats(frames), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(md)
        print("\n".join(outlook_lines(frames, coins)))
        return
    print(json.dumps(section_scenarios(a.coin, frames), ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
