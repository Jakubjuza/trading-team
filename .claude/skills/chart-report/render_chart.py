#!/usr/bin/env python3
"""Vykreslí PNG report obchodu: svíčky, vstup/stop/cíle, range zónu a scénáře.

Použití:
    python3 render_chart.py --spec spec.json [--csv data.csv] [--out reports/AAPL_2026-10-24.png]

Data: --csv (Date, Open, High, Low, Close[, Volume]; podporuje i export z Investing.com
se sloupcem Price), jinak yfinance. Když data nejdou získat, skončí s kódem 2
a vypíše řádek začínající DATA_UNAVAILABLE.
"""
import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mplfinance as mpf  # noqa: E402
import pandas as pd  # noqa: E402

COLORS = {
    "entry": "#1f6feb",
    "stop": "#d1242f",
    "target": "#1a7f37",
    "range": "#bf8700",
    "optimistic": "#1a7f37",
    "neutral": "#6e7781",
    "bad": "#d1242f",
}
SCENARIO_LABELS = {"optimistic": "Optimistický", "neutral": "Neutrální", "bad": "Špatný"}


def fail_no_data(reason):
    print(f"DATA_UNAVAILABLE: {reason}. Pošli CSV se sloupci Date, Open, High, Low, Close[, Volume].")
    sys.exit(2)


def parse_number(val):
    """'1,234.5' / '1 234,5' / '39.54M' / '850K' -> float."""
    if pd.isna(val):
        return float("nan")
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(" ", "").replace(" ", "")
    mult = 1.0
    m = re.match(r"^(.*?)([KMB])$", s, re.I)
    if m:
        s, suf = m.group(1), m.group(2).upper()
        mult = {"K": 1e3, "M": 1e6, "B": 1e9}[suf]
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if s.count(",") == 1 and len(s.split(",")[1]) != 3 else s.replace(",", "")
    try:
        return float(s) * mult
    except ValueError:
        return float("nan")


def load_csv(path):
    df = pd.read_csv(path)
    cols = {c.lower().strip().rstrip("."): c for c in df.columns}
    rename = {}
    for want, aliases in {
        "Date": ["date", "datetime", "time", "datum"],
        "Open": ["open"],
        "High": ["high"],
        "Low": ["low"],
        "Close": ["close", "price", "adj close", "close/last", "last"],
        "Volume": ["volume", "vol"],
    }.items():
        for a in aliases:
            if a in cols:
                rename[cols[a]] = want
                break
    df = df.rename(columns=rename)
    missing = [c for c in ("Date", "Open", "High", "Low", "Close") if c not in df.columns]
    if missing:
        fail_no_data(f"v CSV chybí sloupce {missing}")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).set_index("Date").sort_index()
    for c in ("Open", "High", "Low", "Close", "Volume"):
        if c in df.columns:
            df[c] = df[c].map(parse_number)
    return df[[c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]].dropna(
        subset=["Open", "High", "Low", "Close"]
    )


def load_yfinance(ticker, period, interval):
    try:
        import yfinance as yf

        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    except Exception as exc:  # síť, chybějící balík…
        fail_no_data(f"yfinance selhal ({exc.__class__.__name__})")
    if df is None or df.empty:
        fail_no_data("yfinance nevrátil žádná data (síť je nejspíš blokovaná)")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[[c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]].dropna()


def spread_labels(ax, items, min_gap_px=17):
    """items: [(y, text, color)] -> svislé posuny v bodech, aby se štítky nepřekrývaly."""
    if not items:
        return []
    ys_px = [ax.transData.transform((0, y))[1] for y, _, _ in items]
    order = sorted(range(len(items)), key=lambda i: ys_px[i])
    placed = {}
    prev = None
    for i in order:
        y = ys_px[i] if prev is None else max(ys_px[i], prev + min_gap_px)
        placed[i] = y
        prev = y
    to_pt = 72.0 / ax.figure.dpi
    return [(placed[i] - ys_px[i]) * to_pt for i in range(len(items))]


def draw_price_labels(ax, items, x):
    for (y, text, color), dy in zip(items, spread_labels(ax, items)):
        ax.annotate(text, xy=(x, y), xytext=(6, dy), textcoords="offset points", va="center", ha="left",
                    fontsize=8.5, color="white", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="none"), annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=color, lw=0.8) if abs(dy) > 1 else None)


def fmt(p, decimals):
    return f"{p:,.{decimals}f}".replace(",", " ").replace(".", ",")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="JSON se zadáním obchodu")
    ap.add_argument("--csv", help="CSV se svíčkami (jinak yfinance)")
    ap.add_argument("--out", help="cesta k PNG (výchozí reports/<TICKER>_<datum>.png)")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    ticker = spec["ticker"]
    bars = int(spec.get("bars", 60))
    horizon = int(spec.get("horizon_bars", 8))
    dec = int(spec.get("decimals", 2))

    df = load_csv(args.csv) if args.csv else load_yfinance(
        spec.get("yf_symbol", ticker), spec.get("period", "6mo"), spec.get("interval", "1d")
    )
    df = df.tail(bars)
    if len(df) < 5:
        fail_no_data(f"jen {len(df)} svíček")
    has_vol = bool("Volume" in df.columns and df["Volume"].fillna(0).sum() > 0)

    style = mpf.make_marketcolors(up="#1a7f37", down="#d1242f", edge="inherit", wick="inherit", volume="in")
    mstyle = mpf.make_mpf_style(base_mpf_style="yahoo", marketcolors=style, gridstyle=":", gridcolor="#d0d7de",
                                y_on_right=False, rc={"font.family": "DejaVu Sans"})
    extra = {"panel_ratios": (4, 1)} if has_vol else {}
    fig, axes = mpf.plot(
        df, type="candle", style=mstyle, volume=has_vol, returnfig=True, figsize=(14, 8),
        datetime_format=spec.get("datetime_format", "%d.%m."), xrotation=0, tight_layout=False, ylabel="Cena",
        ylabel_lower="Objem" if has_vol else "", scale_padding={"left": 0.7, "right": 1.9, "top": 0.7, "bottom": 1.15},
        **extra,
    )
    ax = axes[0]
    n = len(df)
    last_x = n - 1
    scenarios = spec.get("scenarios", [])
    path_len = max([p[0] for sc in scenarios for p in sc["path"]] + [horizon])
    # budoucí oblast: šipky + místo pro texty scénářů
    x_end = last_x + max(path_len + int(n * 0.45), horizon)
    for a in axes:
        a.set_xlim(-1, x_end)

    title = spec.get("title") or f"{ticker} – {spec.get('direction', 'long')} setup"
    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=10)

    # Y rozsah tak, aby se vešly všechny úrovně (před výpočtem pozic štítků)
    rng = spec.get("range")
    lines = [("entry", spec["entry"], "Vstup"), ("stop", spec["stop"], "Stop")]
    lines += [("target", t["price"], t.get("label", f"T{i + 1}")) for i, t in enumerate(spec.get("targets", []))]
    levels = [p for _, p, _ in lines] + ([rng["low"], rng["high"]] if rng else [])
    levels += [p[1] for sc in scenarios for p in sc["path"]]
    lo = min(levels + [df["Low"].min()])
    hi = max(levels + [df["High"].max()])
    pad = (hi - lo) * 0.07
    ax.set_ylim(lo - pad, hi + pad)

    labels = []
    # Range zóna a range high
    if rng:
        ax.axhspan(rng["low"], rng["high"], color=COLORS["range"], alpha=0.12, zorder=0)
        ax.axhline(rng["high"], color=COLORS["range"], ls="--", lw=1.2)
        labels.append((rng["high"], f"{rng.get('high_label', 'Range high')} {fmt(rng['high'], dec)}", COLORS["range"]))
        ax.text(0, rng["low"], f" {rng.get('label', 'Range')} {fmt(rng['low'], dec)}–{fmt(rng['high'], dec)}",
                color=COLORS["range"], fontsize=8.5, va="bottom", fontweight="bold")

    # Vstup, stop, cíle
    for kind, price, label in lines:
        ax.axhline(price, color=COLORS[kind], lw=1.4, ls="-" if kind != "target" else "-.")
        labels.append((price, f"{label} {fmt(price, dec)}", COLORS[kind]))
    draw_price_labels(ax, labels, x_end)

    # Scénáře – trajektorie z poslední svíčky, texty vpravo od konců šipek
    start = float(df["Close"].iloc[-1])
    text_items = []
    for sc in scenarios:
        kind = sc.get("kind", "neutral")
        color = COLORS.get(kind, "#6e7781")
        xs = [last_x] + [last_x + p[0] for p in sc["path"]]
        ys = [start] + [p[1] for p in sc["path"]]
        ax.plot(xs[:-1] + [xs[-1]], ys, ls="--", lw=2, color=color, marker="o", ms=3.5, zorder=5)
        ax.annotate("", xy=(xs[-1], ys[-1]), xytext=(xs[-2], ys[-2]),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=2, mutation_scale=16), zorder=6)
        prob = f" (~{sc['prob']})" if sc.get("prob") else ""
        txt = f"{SCENARIO_LABELS.get(kind, kind)}{prob}\n" + "\n".join(textwrap.wrap(sc["text"], 28))
        text_items.append((ys[-1], txt, color))
    tx = last_x + path_len + 0.8
    for (y, txt, color), dy in zip(text_items, spread_labels(ax, text_items, min_gap_px=64)):
        ax.annotate(txt, xy=(tx, y), xytext=(0, dy), textcoords="offset points", ha="left", va="center",
                    fontsize=8.3, color=color, fontweight="bold", linespacing=1.25,
                    bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, alpha=0.95), zorder=7)

    if scenarios:
        ax.axvline(last_x + 0.5, color="#8c959f", lw=0.8, ls=":")
        ax.text(last_x + 0.8, lo - pad * 0.6, "simulace →", va="bottom", fontsize=8, color="#57606a")

    caption = spec.get("caption", "")
    src = spec.get("data_source") or (f"CSV {Path(args.csv).name}" if args.csv else "yfinance")
    note = " Scénáře jsou simulace, ne předpověď." if scenarios else ""
    caption = (caption + ". " if caption else "") + f"Data: {src}.{note} Nejde o finanční poradenství."
    fig.text(0.045, 0.012, "\n".join(textwrap.wrap(caption, 165)), fontsize=10.5, va="bottom", ha="left",
             color="#24292f", linespacing=1.4)

    out = Path(args.out or f"reports/{ticker}_{df.index[-1]:%Y-%m-%d}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print(f"OK: {out}")


if __name__ == "__main__":
    main()
