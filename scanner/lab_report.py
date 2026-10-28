"""📊 Přehled papírových obchodů pro Telegram: řádky textu a obrázek (dashboard) se stavem laboratoře a účtu.

- `lines(state, prices)` – řádky pro /pozice a zprávu o stavu (otevřené laboratorní obchody s výsledkem v R a %).
- `render(state, prices, out)` – PNG 1080 × 1350: dlaždice účtu, sloupce otevřených obchodů podle výsledku,
  křivka součtu R uzavřených obchodů. Barvy jako Agentown (tmavě modrá, mátová / korálová pro zisk / ztrátu).
Výsledek otevřeného obchodu = aktuální cena proti vstupu, po poplatcích MEXC (0,05 % na stranu), v R podle rizika
obchodu (vzdálenost stopu). Jen papírově, nic se neobchoduje.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import registry  # noqa: E402

LOG = ROOT / "research" / "lab_trades.jsonl"
CACHE = ROOT / "scanner" / "cache"
COST = 0.0005
TZ = ZoneInfo("Europe/Prague")
BG, PANEL, LINE, FG, MUTED = "#0d1438", "#151d4a", "#28336e", "#e8eef7", "#9fb2c9"
UP, DOWN, GOLD, PINK = "#4fe3c1", "#ff7a6b", "#ffc457", "#ff4fd8"


def _n(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


def latest_price(coin, prices=None):
    """Nejčerstvější cena: poslední uzavřená hodinová svíčka laboratoře, jinak cena ze skeneru."""
    best = None
    for tf in ("15m", "1h", "2h", "4h"):
        p = CACHE / f"lab_{coin}_{tf}.csv"
        if p.exists():
            try:
                df = pd.read_csv(p, index_col=0)
                t = pd.to_datetime(df.index[-1], utc=True)
                if best is None or t > best[0]:
                    best = (t, float(df["Close"].iloc[-1]))
            except Exception:
                pass
    if best:
        return best[1]
    q = (prices or {}).get(f"{coin}/USDT")
    return float(q[0]) if q else None


def open_positions(state, prices=None):
    out = []
    for o in (state.data.get("lab") or {}).get("open", []):
        px = latest_price(o["coin"], prices)
        entry = o.get("entry") or o.get("signal_close")
        rf = o.get("rf")
        d = 1 if o["dir"] == "long" else -1
        pct = (d * (px / entry - 1) - 2 * COST) * 100 if px and entry else None
        r = pct / 100 / rf if pct is not None and rf else None
        out.append({**o, "now": px, "entry_px": entry, "pct": pct, "r": r})
    out.sort(key=lambda p: -(p["r"] if p["r"] is not None else (p["pct"] or 0) / 2))
    return out


def closed_trades():
    if not LOG.exists():
        return []
    rows = [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if r.get("event") == "close"]


def _short(o):
    lab = o.get("label") or o.get("sid", "")
    for suf in (" long", " short"):
        lab = lab.replace(suf, "")
    return lab


def lines(state, prices=None, limit=12):
    ops, cl = open_positions(state, prices), closed_trades()
    if not ops and not cl and not (state.data.get("lab") or {}):
        return []
    tot = sum(c["r"] for c in cl)
    head = f"⚡ Laboratoř (papírově): otevřené {len(ops)}, uzavřené {len(cl)}"
    if cl:
        head += f", Σ {_n(tot)} R, úspěšnost {sum(1 for c in cl if c['r'] > 0) / len(cl):.0%}"
    out = [head]
    for p in ops[:limit]:
        res = (f"{_n(p['r'])} R ({_n(p['pct'])} %)" if p["r"] is not None
               else (f"{_n(p['pct'])} %" if p["pct"] is not None else "cena ?"))
        out.append(f"• {p['coin']} {p['dir'].upper()} {p['tf'].upper()} · {_short(p)}: {res}")
    if len(ops) > limit:
        out.append(f"• … a dalších {len(ops) - limit}")
    return out


def _ensemble_value(state, prices):
    ens = state.data.get("ensemble") or {}
    held = {c: q for c, q in (ens.get("qty") or {}).items() if q > 0}
    if not held and not ens.get("equity"):
        return None
    val = (ens.get("cash") or 0) + sum(q * (latest_price(c, prices) or 0) for c, q in held.items())
    start = ens.get("start_equity") or val
    return val, (val / start - 1) * 100 if start else 0.0, sorted(held)


def render(state, prices, out, now=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    now = (now or datetime.now(timezone.utc)).astimezone(TZ)
    ops, cl = open_positions(state, prices), closed_trades()
    reg = registry.load()
    n_active = len(registry.active(reg))
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig = plt.figure(figsize=(9, 11.25), dpi=120, facecolor=BG)

    # hlavička
    fig.text(.06, .955, "Agentown · přehled", fontsize=24, fontweight="bold", color=FG)
    fig.text(.06, .928, f"{now:%d. %m. %Y %H:%M} · papírově, ne rada", fontsize=12, color=MUTED)

    # dlaždice
    tot = sum(c["r"] for c in cl)
    win = (sum(1 for c in cl if c["r"] > 0) / len(cl) * 100) if cl else None
    core = len(state.data.get("open", []))
    ens = _ensemble_value(state, prices)
    tiles = [("Laboratoř", f"{len(ops)} otevř.", f"{n_active} strategií aktivních", PINK),
             ("Uzavřené (lab)", f"{len(cl)}", f"Σ {_n(tot)} R" + (f" · {win:.0f} % výher" if win is not None else ""),
              UP if tot >= 0 else DOWN),
             ("Ensemble", f"{_n(ens[1], 1)} %" if ens else "–", ", ".join(ens[2]) if ens and ens[2] else "v hotovosti", GOLD),
             ("Jádro 1D", f"{core} otevř.", "čeká na průraz" if not core else "v pozici", UP)]
    for i, (t, v, s, c) in enumerate(tiles):
        x0 = .06 + i * .225
        ax = fig.add_axes([x0, .80, .205, .1]); ax.axis("off")
        ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=.08", fc=PANEL, ec=c, lw=1.6,
                                    transform=ax.transAxes))
        ax.text(.08, .76, t, fontsize=10.5, color=MUTED, transform=ax.transAxes)
        ax.text(.08, .4, v, fontsize=18, fontweight="bold", color=FG, transform=ax.transAxes)
        ax.text(.08, .13, s, fontsize=8.6, color=c, transform=ax.transAxes)

    # otevřené obchody – výsledek v R
    ax = fig.add_axes([.36, .37, .4, .38], facecolor=BG)
    fig.text(.06, .765, "Otevřené obchody laboratoře – výsledek teď (R, po poplatcích)", fontsize=13.5, fontweight="bold")
    shown = ops[:14]
    if shown:
        vals = [p["r"] if p["r"] is not None else 0.0 for p in shown][::-1]
        labs = [f"{p['coin']} {p['dir'][0].upper()} · {_short(p)}" for p in shown][::-1]
        cols = [UP if v >= 0 else DOWN for v in vals]
        ax.barh(range(len(vals)), vals, color=cols, height=.62)
        ax.axvline(0, color=LINE, lw=1.2)
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels([lab if len(lab) <= 34 else lab[:33] + "…" for lab in labs], fontsize=9.5, color=FG)
        span = max(.5, max(abs(v) for v in vals) * 1.15)
        ax.set_xlim(-span, span)
        from matplotlib.transforms import blended_transform_factory
        tr = blended_transform_factory(ax.transAxes, ax.transData)
        ax.text(1.04, len(vals) - .35, "R        %", transform=tr, fontsize=9, color=MUTED, va="bottom")
        for i, (v, p) in enumerate(zip(vals, shown[::-1])):
            c = UP if v >= 0 else DOWN
            ax.text(1.04, i, _n(v), transform=tr, va="center", ha="left", fontsize=10.5, fontweight="bold", color=c)
            ax.text(1.2, i, _n(p["pct"], 1) if p["pct"] is not None else "?", transform=tr, va="center", ha="left",
                    fontsize=10, color=FG)
        if len(ops) > len(shown):
            fig.text(.36, .35, f"… a dalších {len(ops) - len(shown)}", fontsize=9.5, color=MUTED)
    else:
        ax.set_xlim(-1, 1); ax.set_yticks([])
        ax.text(0, .5, "Žádný otevřený obchod – strategie čekají na signál ve svém režimu trhu.",
                ha="center", va="center", fontsize=11, color=MUTED, transform=ax.transAxes)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=LINE, lw=.6, alpha=.6)

    # křivka uzavřených obchodů
    fig.text(.06, .3, "Uzavřené obchody laboratoře – součet R v čase", fontsize=13.5, fontweight="bold")
    ax2 = fig.add_axes([.1, .06, .84, .21], facecolor=BG)
    if cl:
        s = pd.Series([c["r"] for c in cl], index=pd.to_datetime([c["time"] for c in cl], utc=True)).sort_index().cumsum()
        first = s.index[0] - (s.index[-1] - s.index[0]) * .04 - pd.Timedelta(minutes=30)
        s = pd.concat([pd.Series([0.0], index=[first]), s])
        x = s.index.tz_convert(TZ)
        ax2.fill_between(x, 0, s.values, color=UP if s.iloc[-1] >= 0 else DOWN, alpha=.15, step="post")
        ax2.step(x, s.values, where="post", color=UP if s.iloc[-1] >= 0 else DOWN, lw=2.2)
        ax2.scatter([x[-1]], [s.iloc[-1]], color=FG, s=26, zorder=3)
        ax2.axhline(0, color=LINE, lw=1)
        ax2.set_ylabel("Σ R")
        import matplotlib.dates as mdates
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m. %H:%M", tz=TZ))
    else:
        ax2.set_xticks([]); ax2.set_yticks([])
        ax2.text(.5, .5, "Zatím žádný uzavřený obchod. Křivka se objeví po prvním výsledku.",
                 ha="center", va="center", fontsize=11, color=MUTED, transform=ax2.transAxes)
    for sp in ax2.spines.values():
        sp.set_visible(False)
    ax2.grid(axis="y", color=LINE, lw=.6, alpha=.6)
    ax2.tick_params(labelsize=9)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)
    return out


def send_board(state, prices, caption, send_photo=None):
    """Vykreslí přehled a pošle ho jako obrázek (selhání nesmí shodit skener)."""
    try:
        from scanner import notify
        out = render(state, prices, ROOT / "reports" / "telegram" / "prehled.png")
        return (send_photo or notify.telegram)(caption, photo=out)
    except Exception as exc:
        print(f"přehled (obrázek) selhal: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return False
