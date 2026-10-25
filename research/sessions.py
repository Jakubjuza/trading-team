#!/usr/bin/env python3
"""Světové burzy a jejich vliv na krypto – kalendář otevírání + měření z historie.

Krypto se obchoduje non-stop, ale likvidita a volatilita se mění podle toho, které tradiční trhy
jsou otevřené. Modul:
  • zná časy otevření/zavření hlavních burz (místní čas → UTC, letní/zimní čas přes zoneinfo),
  • řekne, které trhy jsou teď otevřené a co se otevírá v příštích 24 h (v čase Prahy),
  • z hodinových svíček změří, jak se krypto chovalo v hodinách po každém otevření
    (volatilita vůči průměrné hodině, průměrný směr, podíl růstů) a jak dopadl víkendový pohyb
    po nedělním otevření (CME futures + Asie): pokračování nebo odraz.

Bez AI a bez internetu – stačí svíčky. Výsledek čte datový list (sekce `sessions`) a agenti desku.

Použití:
    python3 research/sessions.py             # co je otevřené teď + co se otevírá (JSON)
    python3 research/sessions.py --stats     # přepočítat research/sessions_stats.json + reports/market_sessions.md
"""
import argparse
import math
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

PRAGUE = ZoneInfo("Europe/Prague")
DAYS_CS = ["po", "út", "st", "čt", "pá", "so", "ne"]
ROOT = Path(__file__).resolve().parent.parent
STATS = ROOT / "research" / "sessions_stats.json"


def prague(ts, fmt="%H:%M"):
    loc = ts.astimezone(PRAGUE)
    return f"{DAYS_CS[loc.weekday()]} {loc.strftime(fmt)}"

# název: (zóna, otevření, zavření, dny v týdnu 0=po … 6=ne)
SESSIONS = {
    "Sydney (ASX)": ("Australia/Sydney", time(10, 0), time(16, 0), range(0, 5)),
    "Tokio (TSE)": ("Asia/Tokyo", time(9, 0), time(15, 30), range(0, 5)),
    "Hongkong (HKEX)": ("Asia/Hong_Kong", time(9, 30), time(16, 0), range(0, 5)),
    "Londýn (LSE)": ("Europe/London", time(8, 0), time(16, 30), range(0, 5)),
    "New York (NYSE)": ("America/New_York", time(9, 30), time(16, 0), range(0, 5)),
}
# CME bitcoin futures: týdenní otevření neděle 17:00 Chicago, zavření pátek 16:00 Chicago
CME = ("America/Chicago", time(17, 0), time(16, 0))


def _local_events(zone, t, days, start, end):
    tz = ZoneInfo(zone)
    d = start.astimezone(tz).date() - timedelta(days=1)
    stop = end.astimezone(tz).date() + timedelta(days=1)
    out = []
    while d <= stop:
        if d.weekday() in days:
            ts = datetime.combine(d, t, tzinfo=tz).astimezone(timezone.utc)
            if start <= ts < end:
                out.append(ts)
        d += timedelta(days=1)
    return out


def opens(name, start, end):
    """Časy otevření (UTC) burzy `name` mezi start a end. Svátky se neřeší (vliv je malý)."""
    if name == "CME (neděle)":
        return _local_events(CME[0], CME[1], {6}, start, end)
    zone, o, _, days = SESSIONS[name]
    return _local_events(zone, o, set(days), start, end)


def cme_weekends(start, end):
    """Dvojice (pátek zavření CME, neděle otevření CME) v UTC."""
    out = []
    for sun in opens("CME (neděle)", start, end):
        fri = datetime.combine(sun.astimezone(ZoneInfo(CME[0])).date() - timedelta(days=2), CME[2],
                               tzinfo=ZoneInfo(CME[0])).astimezone(timezone.utc)
        out.append((fri, sun))
    return out


def session_now(now=None):
    """Co je otevřené teď a co se otevře/zavře v příštích 24 h (čas Prahy)."""
    now = now or datetime.now(timezone.utc)
    open_now, upcoming = [], []
    for name, (zone, o, c, days) in SESSIONS.items():
        tz = ZoneInfo(zone)
        loc = now.astimezone(tz)
        if loc.weekday() in days and o <= loc.time() < c:
            open_now.append(name)
        for ts in opens(name, now, now + timedelta(hours=24)):
            upcoming.append((ts, name))
    for ts in opens("CME (neděle)", now, now + timedelta(hours=24)):
        upcoming.append((ts, "CME (neděle)"))
    upcoming.sort()
    return {"now_prague": prague(now, "%d.%m. %H:%M"),
            "open_now": open_now or ["žádná velká burza (jen krypto)"],
            "weekend_cme_closed": _cme_closed(now),
            "next_24h": [{"prague": prague(ts),
                          "in_hours": round((ts - now).total_seconds() / 3600, 1), "open": ev}
                         for ts, ev in upcoming]}


def _cme_closed(now):
    loc = now.astimezone(ZoneInfo(CME[0]))
    wd, t = loc.weekday(), loc.time()
    return (wd == 4 and t >= CME[2]) or wd == 5 or (wd == 6 and t < CME[1])


# --- měření z historie ---------------------------------------------------------------------
def _bar_at(df, ts):
    """Index první hodinové svíčky, která začíná v ts nebo po něm (otevření v :30 → další celá hodina)."""
    i = df.index.searchsorted(pd.Timestamp(ts))
    return i if i < len(df) else None


def open_effect(df, name, hours=4):
    """Pohyb v `hours` hodinách po otevření burzy vs. stejně dlouhé okno kdykoli jindy.

    vol_ratio > 1 = po otevření se hýbe víc než obvykle. avg_ret / p_up = jestli má otevření směr."""
    c = df["Close"].to_numpy()
    o = df["Open"].to_numpy()
    rets, absr = [], []
    for ts in opens(name, df.index[0].to_pydatetime(), df.index[-1].to_pydatetime()):
        i = _bar_at(df, ts)
        if i is None or i + hours > len(df):
            continue
        x = c[i + hours - 1] / o[i] - 1
        rets.append(x)
        absr.append(abs(x))
    if len(rets) < 20:
        return {"n": len(rets)}
    base = np.abs(c[hours - 1:] / o[: len(o) - hours + 1] - 1)
    rets = np.array(rets)
    se = rets.std(ddof=1) / math.sqrt(len(rets))
    return {"n": len(rets), "hours": hours,
            "vol_ratio": round(float(np.mean(absr) / base.mean()), 2),
            "avg_ret_pct": round(float(rets.mean() * 100), 3),
            "t_stat": round(float(rets.mean() / se), 2) if se else 0.0,
            "p_up": round(float((rets > 0).mean()), 3)}


def weekend_effect(df, hours=(4, 24), big_move_pct=2.0):
    """Víkend (pátek zavření CME → neděle otevření CME) a co následovalo po nedělním otevření.

    reversal = znaménko pohybu po otevření je opačné než víkendový pohyb (odraz).
    Počítá se zvlášť pro všechny víkendy a pro velké pohyby (|víkend| ≥ big_move_pct)."""
    c = df["Close"].to_numpy()
    o = df["Open"].to_numpy()
    rows = []
    for fri, sun in cme_weekends(df.index[0].to_pydatetime(), df.index[-1].to_pydatetime()):
        i0, i1 = _bar_at(df, fri), _bar_at(df, sun)
        if i0 is None or i1 is None or i1 + max(hours) > len(df):
            continue
        wk = o[i1] / o[i0] - 1
        rows.append([wk] + [c[i1 + h - 1] / o[i1] - 1 for h in hours])
    if len(rows) < 20:
        return {"n": len(rows)}
    a = np.array(rows)
    out = {"n": len(a), "big_move_pct": big_move_pct}
    for j, h in enumerate(hours, start=1):
        for label, m in (("all", np.ones(len(a), bool)), ("big_down", a[:, 0] <= -big_move_pct / 100),
                         ("big_up", a[:, 0] >= big_move_pct / 100)):
            sub = a[m]
            if len(sub) < 5:
                out[f"{label}_{h}h"] = {"n": int(len(sub))}
                continue
            rev = np.sign(sub[:, j]) == -np.sign(sub[:, 0])
            out[f"{label}_{h}h"] = {"n": int(len(sub)), "p_reversal": round(float(rev.mean()), 3),
                                    "avg_after_pct": round(float(sub[:, j].mean() * 100), 2)}
        out[f"corr_{h}h"] = round(float(np.corrcoef(a[:, 0], a[:, j])[0, 1]), 3)
    return out


def cme_gaps(df, days=5, min_gap_pct=0.5, seed=7):
    """CME gap = rozdíl mezi cenou při pátečním zavření CME a nedělním otevření. „Zavření gapu“ =
    cena se do `days` dnů vrátí na páteční úroveň. Kontrola: stejně vzdálená úroveň od náhodné hodiny
    (ve směru proti pohybu) – jestli gapy přitahují cenu víc než jakákoli jiná úroveň."""
    h, l, o = df["High"].to_numpy(), df["Low"].to_numpy(), df["Open"].to_numpy()
    win = days * 24
    filled, dist = [], []
    for fri, sun in cme_weekends(df.index[0].to_pydatetime(), df.index[-1].to_pydatetime()):
        i0, i1 = _bar_at(df, fri), _bar_at(df, sun)
        if i0 is None or i1 is None or i1 + win > len(df):
            continue
        lvl, px = o[i0], o[i1]
        g = px / lvl - 1
        if abs(g) * 100 < min_gap_pct:
            continue
        seg = slice(i1, i1 + win)
        filled.append(bool(l[seg].min() <= lvl) if g > 0 else bool(h[seg].max() >= lvl))
        dist.append(g)
    if len(filled) < 10:
        return {"n": len(filled)}
    rng = np.random.default_rng(seed)
    ctrl = []
    for g in dist:
        for _ in range(20):
            i = int(rng.integers(0, len(df) - win))
            lvl = o[i] / (1 + g)
            seg = slice(i, i + win)
            ctrl.append(bool(l[seg].min() <= lvl) if g > 0 else bool(h[seg].max() >= lvl))
    return {"n": len(filled), "days": days, "min_gap_pct": min_gap_pct,
            "p_filled": round(float(np.mean(filled)), 3), "p_random_level": round(float(np.mean(ctrl)), 3),
            "avg_gap_pct": round(float(np.mean(np.abs(dist)) * 100), 2)}


def hour_profile(df):
    """Průměrná absolutní změna podle hodiny dne (UTC) vůči průměru – kdy je trh živý."""
    x = (df["Close"] / df["Open"] - 1).abs()
    prof = x.groupby(df.index.hour).mean() / x.mean()
    return {int(h): round(float(v), 2) for h, v in prof.items()}


def history_stats(df):
    names = list(SESSIONS) + ["CME (neděle)"]
    return {"opens_4h": {n: open_effect(df, n, 4) for n in names},
            "weekend": weekend_effect(df),
            "cme_gaps": cme_gaps(df),
            "hour_profile_utc": hour_profile(df),
            "period": f"{df.index[0]:%Y-%m-%d} – {df.index[-1]:%Y-%m-%d}"}


def pooled(per_coin):
    """Průměr přes mince (každá mince má stejnou váhu) + rozpětí min–max."""
    names = list(SESSIONS) + ["CME (neděle)"]
    out = {"opens_4h": {}}
    for n in names:
        rows = [c["opens_4h"][n] for c in per_coin.values() if c["opens_4h"][n].get("n", 0) >= 20]
        if rows:
            out["opens_4h"][n] = {k: round(float(np.mean([r[k] for r in rows])), 3)
                                  for k in ("vol_ratio", "avg_ret_pct", "t_stat", "p_up")}
            out["opens_4h"][n]["vol_ratio_range"] = [min(r["vol_ratio"] for r in rows), max(r["vol_ratio"] for r in rows)]
    g = [c["cme_gaps"] for c in per_coin.values() if c["cme_gaps"].get("n", 0) >= 10]
    if g:
        out["cme_gaps"] = {k: round(float(np.mean([x[k] for x in g])), 3) for k in ("p_filled", "p_random_level", "avg_gap_pct")}
        out["cme_gaps"]["days"] = g[0]["days"]
    w = [c["weekend"] for c in per_coin.values() if c["weekend"].get("n", 0) >= 20]
    for key in ("big_down_24h", "big_up_24h", "big_down_4h", "big_up_4h"):
        rows = [x[key] for x in w if x.get(key, {}).get("n", 0) >= 5]
        if rows:
            out.setdefault("weekend", {})[key] = {"p_reversal": round(float(np.mean([r["p_reversal"] for r in rows])), 3),
                                                  "avg_after_pct": round(float(np.mean([r["avg_after_pct"] for r in rows])), 2)}
    return out


def load_stats(path=STATS):
    import json
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def coin_stats(stats, coin):
    """Statistiky mince, když jsou; jinak průměr přes mince."""
    return (stats.get("coins") or {}).get(coin) or stats.get("pooled") or {}


def current_gap(h1, now=None):
    """Aktuální CME gap: páteční zavření CME vs. nedělní otevření a jestli už ho cena zavřela."""
    now = now or datetime.now(timezone.utc)
    pairs = cme_weekends(now - timedelta(days=7), now)
    if h1 is None or not pairs:
        return None
    fri, sun = pairs[-1]
    i0, i1 = _bar_at(h1, fri), _bar_at(h1, sun)
    if i0 is None or i1 is None:
        return None
    lvl, px = float(h1["Open"].iloc[i0]), float(h1["Open"].iloc[i1])
    after = h1.iloc[i1:]
    gap = px / lvl - 1
    filled = bool(after["Low"].min() <= lvl) if gap > 0 else bool(after["High"].max() >= lvl)
    return {"friday_close": round(lvl, 6), "sunday_open": round(px, 6), "gap_pct": round(gap * 100, 2),
            "filled": filled, "since": prague(sun)}


def section_sessions(h1=None, now=None, coin=None, stats=None):
    """Sekce datového listu: co je otevřené, co se otevírá v 24 h + co o tom říká historie (2 roky, 8+ mincí)."""
    now = now or datetime.now(timezone.utc)
    stats = load_stats() if stats is None else stats
    st = coin_stats(stats, coin)
    out = {"source": "kalendář burz (zoneinfo) + research/sessions_stats.json "
                     f"({stats.get('period', 'bez statistik')})", "as_of": now.isoformat(timespec="seconds"),
           **session_now(now)}
    for ev in out["next_24h"]:
        e = (st.get("opens_4h") or {}).get(ev["open"])
        if e:
            ev["hist_vol_4h_x"] = e["vol_ratio"]
            ev["hist_avg_ret_4h_pct"] = e["avg_ret_pct"]
    gap = current_gap(h1, now)
    if gap:
        out["cme_gap"] = gap
    out["history"] = {k: st[k] for k in ("cme_gaps", "weekend") if k in st}
    out["note"] = ("hist_vol_4h_x = kolikrát větší pohyb za 4 h po otevření než za běžné 4 h. Směr po otevření "
                   "historicky není statisticky významný (|t| < 2) – otevření mění volatilitu a likviditu, ne směr.")
    return out


def context_line(now=None, coin=None, stats=None, horizon_h=6, min_vol=1.2):
    """Krátký řádek do Telegramu: nejbližší otevření, které historicky zvedá volatilitu, nebo víkend."""
    now = now or datetime.now(timezone.utc)
    stats = load_stats() if stats is None else stats
    st = coin_stats(stats, coin).get("opens_4h", {})
    s = session_now(now)
    for ev in s["next_24h"]:
        v = (st.get(ev["open"]) or {}).get("vol_ratio")
        if ev["in_hours"] <= horizon_h and v and v >= min_vol:
            name = "CME futures (konec víkendu)" if ev["open"] == "CME (neděle)" else ev["open"]
            return f"Burzy: {ev['prague']} otevírá {name} – hist. {str(round(v, 1)).replace('.', ',')}× větší pohyb za 4 h"
    if s["weekend_cme_closed"]:
        return "Burzy: víkend – tradiční trhy zavřené, nižší likvidita"
    return ""


def weekend_daily_check(daily, thr_pct=2.0):
    """Kontrola na dlouhé denní historii: po propadu So+Ne ≥ thr % roste pondělí častěji než po jiném
    2denním propadu? Vrací řádky do reportu."""
    rows = []
    for coin, df in daily.items():
        if df is None or len(df) < 400:
            continue
        two = df["Close"] / df["Open"].shift(1) - 1
        nxt = df["Close"].shift(-1) / df["Open"].shift(-1) - 1
        rows.append(pd.DataFrame({"two": two, "nxt": nxt, "sun": df.index.dayofweek == 6}).dropna())
    if not rows:
        return []
    d = pd.concat(rows)
    big = d[d.two <= -thr_pct / 100]
    out = []
    for label, m in ((f"po víkendovém propadu ≥ {thr_pct:g} %", big.sun), (f"po jiném 2denním propadu ≥ {thr_pct:g} %", ~big.sun)):
        x = big[m].nxt
        ci = 1.96 * x.std() / math.sqrt(len(x))
        out.append(f"- {label}: další den růst v {(x > 0).mean():.0%} případů, Ø {x.mean() * 100:+.2f} % ± {ci * 100:.2f} (n={len(x)})")
    yr = big[big.sun].groupby(big[big.sun].index.year).nxt.apply(lambda s: (s > 0).mean())
    out.append("- po letech (víkendový propad → růst v pondělí): " + ", ".join(f"{y}: {v:.0%}" for y, v in yr.items() if y >= 2018))
    return out


def upcoming_line(now=None, hours=4, stats=None):
    """Řádek do heartbeatu: co se otevře do příští zprávy (s historickou volatilitou)."""
    now = now or datetime.now(timezone.utc)
    stats = load_stats() if stats is None else stats
    st = (stats.get("pooled") or {}).get("opens_4h", {})
    evs = [e for e in session_now(now)["next_24h"] if e["in_hours"] <= hours]
    if not evs:
        return ""
    def one(e):
        v = (st.get(e["open"]) or {}).get("vol_ratio")
        name = "CME futures" if e["open"] == "CME (neděle)" else e["open"].split(" (")[0]
        return f"{e['prague'].split(' ')[1]} {name}" + (f" ({str(round(v, 1)).replace('.', ',')}× pohyb)" if v and v >= 1.2 else "")
    return "Burzy do další zprávy: " + ", ".join(one(e) for e in evs)


def build_stats(frames):
    """frames: {coin: hodinové svíčky} → statistiky pro research/sessions_stats.json."""
    coins = {c: history_stats(df) for c, df in frames.items() if df is not None and len(df) > 24 * 120}
    periods = [v["period"] for v in coins.values()]
    return {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "period": periods[0] if periods else "", "coins": coins, "pooled": pooled(coins)}


def report_md(stats, daily_check=None):
    p = stats["pooled"]
    md = [f"# Světové burzy a krypto ({stats['generated'][:10]})", "",
          f"Hodinové svíčky {stats['period']}, {len(stats['coins'])} mincí ({', '.join(stats['coins'])}). "
          "Časy otevření v místním čase burzy (letní/zimní čas se počítá zvlášť pro každou zemi).", "",
          "## Co se děje 4 hodiny po otevření", "",
          "| Otevření | Pohyb vs. běžné 4 h | Rozpětí mezi mincemi | Ø směr | t-stat | P(růst) |", "|---|---|---|---|---|---|"]
    for n, e in p["opens_4h"].items():
        lo, hi = e["vol_ratio_range"]
        md.append(f"| {n} | {e['vol_ratio']:.2f}× | {lo:.2f}–{hi:.2f}× | {e['avg_ret_pct']:+.2f} % | {e['t_stat']:+.1f} | {e['p_up']:.0%} |")
    g = p.get("cme_gaps", {})
    w = p.get("weekend", {})
    md += ["", "Směr po otevření není u žádné burzy statisticky významný (|t| < 2). Otevření mění **volatilitu**, ne směr.", "",
           "## CME gap", "",
           f"Cena se do {g.get('days', 5)} dnů vrátila na úroveň pátečního zavření CME v **{g.get('p_filled', 0):.0%}** případů "
           f"(gap ≥ 0,5 %, Ø velikost {g.get('avg_gap_pct', 0):.1f} %). Stejně vzdálená náhodná úroveň: {g.get('p_random_level', 0):.0%}. "
           "Gap tedy cenu přitahuje mírně víc než jiná úroveň – vhodný jako cíl nebo magnet, ne jako jistota.", "",
           "## Víkendový pohyb a nedělní otevření (CME + Asie)", "",
           "| Víkend | 4 h po otevření: odraz | Ø pohyb | 24 h po otevření: odraz | Ø pohyb |", "|---|---|---|---|---|"]
    for lab, k in (("propad ≥ 2 %", "big_down"), ("růst ≥ 2 %", "big_up")):
        a, b = w.get(f"{k}_4h", {}), w.get(f"{k}_24h", {})
        md.append(f"| {lab} | {a.get('p_reversal', 0):.0%} | {a.get('avg_after_pct', 0):+.2f} % | {b.get('p_reversal', 0):.0%} | {b.get('avg_after_pct', 0):+.2f} % |")
    if daily_check:
        md += ["", "**Kontrola na 10 letech denních dat** (So+Ne → pondělí, 8 mincí):", ""] + daily_check
    md += ["", "Závěr: za poslední 2 roky odraz po víkendovém propadu převažoval, ale na 10 letech je rozdíl proti "
           "jakémukoli jinému 2dennímu propadu malý a silně kolísá podle roku. Je to režimní jev, ne pravidlo – "
           "desk ho bere jako kontext s nízkou jistotou, ne jako signál."]
    md += ["", "## Kdy je trh živý (BTC, hodina UTC → násobek průměrné hodinové změny)", "",
           " · ".join(f"{h}:00 {v:.2f}×" for h, v in stats["coins"].get("BTC", next(iter(stats["coins"].values())))["hour_profile_utc"].items()),
           "", "## Jak to desk používá", "",
           "- Datový list má sekci `sessions`: co je otevřené, co se otevírá v příštích 24 h s historickou volatilitou, aktuální CME gap.",
           "- macro-analyst ji hodnotí, entry-exit-planner a devils-advocate řeší vstup těsně před otevřením New Yorku / CME (širší knoty).",
           "- Telegram signál má v řádku 4 upozornění, když se do 6 h otevírá burza s ≥ 1,2× volatilitou, nebo je víkend.",
           "- Do pravidel skeneru se otevírání burz zatím **nepřidává** – směrový efekt se neprokázal.",
           "", "Nejde o finanční poradenství."]
    return "\n".join(md) + "\n"


def main():
    import json
    import sys
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", action="store_true", help="jen co je otevřené teď")
    ap.add_argument("--stats", action="store_true", help="přepočítat statistiky z 2 let hodinových svíček")
    ap.add_argument("--cache-dir", type=Path, default=ROOT / "scanner" / "cache")
    ap.add_argument("--report", type=Path, default=ROOT / "reports" / "market_sessions.md")
    a = ap.parse_args()
    if not a.stats:
        print(json.dumps(section_sessions(), ensure_ascii=False, indent=1))
        return
    import yaml
    from scanner import evaluate as ev
    cfg = yaml.safe_load((ROOT / "scanner" / "config.yaml").read_text(encoding="utf-8"))
    frames = {}
    for t in cfg["tickers"]:
        if t["source"] == "crypto":
            frames[t["symbol"].split("/")[0]] = ev.load_history(t["symbol"], "crypto", "1h", 730,
                                                                cfg.get("exchange", "kraken"), a.cache_dir)
    daily = {c: ev.load_history(f"{c}/USDT", "crypto", "1d", 3650, cfg.get("exchange", "kraken"), a.cache_dir)
             for c in frames}
    stats = build_stats(frames)
    STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    a.report.write_text(report_md(stats, weekend_daily_check(daily)), encoding="utf-8")
    print(f"OK: {STATS}, {a.report}")


if __name__ == "__main__":
    main()
