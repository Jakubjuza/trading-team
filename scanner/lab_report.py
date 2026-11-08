"""📊 Přehled papírových obchodů pro Telegram: řádky textu a obrázek (dashboard) se stavem laboratoře a účtu.

- `lines(state, prices)` – řádky pro /pozice a zprávu o stavu (otevřené laboratorní obchody s výsledkem v R a %).
- `render(state, prices, out)` – PNG 1080 × 1350 ve stylu Agentownu (8. 11.): neonové karty čtvrtí (Trade City, Laboratoř,
  Downtown, Mozek s vahami kupolí, AI Lab), sloupce otevřených obchodů laboratoře podle výsledku,
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


def _json(name):
    p = ROOT / "research" / name
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except Exception:
        return None


def districts(state, prices=None):
    """Souhrn čtvrtí Agentownu z dat v repozitáři (vše papír)."""
    ops, cl = open_positions(state, prices), closed_trades()
    reg = registry.load()
    out = {"lab": {"active": len(registry.active(reg)), "open": len(ops), "closed": len(cl),
                   "sum_r": sum(c["r"] for c in cl), "win": (sum(1 for c in cl if c["r"] > 0) / len(cl) * 100) if cl else None}}
    core_cl = state.data.get("closed", [])
    ens = _ensemble_value(state, prices)
    out["city"] = {"open": len(state.data.get("open", [])), "closed": len(core_cl), "sum_r": sum(c.get("r", 0) for c in core_cl),
                   "ens_pct": ens[1] if ens else None, "ens_held": ens[2] if ens else []}
    b = _json("brain.json")
    if b:
        out["brain"] = {"phase": (b.get("phase") or {}).get("name"), "domes": [(d["name"], d["weight_pct"], d.get("up", 0), d.get("down", 0)) for d in b.get("domes", [])],
                        "live_net": (b.get("live") or {}).get("net"), "n": b.get("n_strategies")}
    a = _json("ai_lab.json")
    if a:
        ss = a.get("strategies", [])
        best = max(ss, key=lambda x: (x.get("live") or {}).get("net") or 0, default=None)
        out["ai"] = {"n": len(ss), "pass": sum(1 for x in ss if x.get("pass")), "live_net": sum((x.get("live") or {}).get("net") or 0 for x in ss),
                     "live_trades": sum((x.get("live") or {}).get("n_trades") or 0 for x in ss), "best": best.get("name") if best else None}
    d = _json("downtown.json")
    if d:
        ss = d.get("strategies", [])
        out["dt"] = {"n": len(ss), "live_net": sum((x.get("live") or {}).get("net") or 0 for x in ss),
                     "up": sum(1 for x in ss if ((x.get("live") or {}).get("net") or 0) > 0),
                     "wipes": sum((x.get("live") or {}).get("wipes") or 0 for x in ss),
                     "trades": sum((x.get("live") or {}).get("n_trades") or 0 for x in ss)}
    return out


def district_lines(state, prices=None):
    """Krátké řádky „🏙️ čtvrti Agentownu“ pro textové zprávy."""
    D = districts(state, prices)
    L = ["🏙️ Agentown · čtvrti (papír)"]
    c = D["city"]
    L.append(f"🌆 Trade City: jádro otevřené {c['open']} · uzavřené {c['closed']} ({_n(c['sum_r'])} R)"
             + (f" · 🧭 ensemble {_n(c['ens_pct'], 1)} %" if c["ens_pct"] is not None else ""))
    lb = D["lab"]
    L.append(f"🔬 Laboratoř: {lb['active']} strategií · otevřené {lb['open']} · uzavřené {lb['closed']} ({_n(lb['sum_r'])} R"
             + (f", {lb['win']:.0f} % výher)" if lb["win"] is not None else ")"))
    if "brain" in D:
        b = D["brain"]
        L.append(f"🧠 Mozek: fáze {b['phase']} · " + " · ".join(f"{n} {w:.0f} %".replace(".", ",") for n, w, _, _ in b["domes"]))
    if "ai" in D:
        a = D["ai"]
        L.append(f"🤖 AI Lab: {a['pass']}/{a['n']} prošlo testem · živě {a['live_trades']} obch., {_n(a['live_net'], 0)} USDT")
    if "dt" in D:
        t = D["dt"]
        L.append(f"🌃 Downtown: živě {_n(t['live_net'], 0)} USDT · v plusu {t['up']}/{t['n']} · bankroty {t['wipes']}")
    return L


def render(state, prices, out, now=None):
    """Obrázek ve stylu Agentownu: vesmírné pozadí, neonové karty čtvrtí, otevřené obchody a křivka laboratoře."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import FancyBboxPatch

    SPACE, CARD, CY, MG = "#05040f", "#0c0a1e", "#3ff2ff", "#ff3df2"
    DOME = {"Pevnost": "#4fe3c1", "Spořitelna": "#8fe9ff", "Motor": "#ffc457", "Divočina": "#ff8a6b"}
    now = (now or datetime.now(timezone.utc)).astimezone(TZ)
    ops, cl = open_positions(state, prices), closed_trades()
    D = districts(state, prices)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": FG, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig = plt.figure(figsize=(9, 11.25), dpi=120, facecolor=SPACE)
    bg = fig.add_axes([0, 0, 1, 1], zorder=-10); bg.axis("off")
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    from matplotlib.colors import LinearSegmentedColormap
    bg.imshow(grad, aspect="auto", cmap=LinearSegmentedColormap.from_list("s", ["#160c3c", "#090620", SPACE]), extent=[0, 1, 0, 1])
    rng = np.random.default_rng(7)
    bg.scatter(rng.random(160), rng.random(160), s=rng.random(160) * 2.2, color="white", alpha=.35, lw=0)
    for x in np.linspace(0, 1, 19):
        bg.axvline(x, color=CY, alpha=.025, lw=.6)
    bg.set_xlim(0, 1); bg.set_ylim(0, 1)

    glow = [pe.withStroke(linewidth=6, foreground=CY, alpha=.18)]
    fig.text(.06, .952, "AGENTOWN", fontsize=27, color="#eef0ff", fontweight="light", path_effects=glow)
    fig.text(.065, .93, "≡ " + f"{now:%d. %m. %Y %H:%M}" + " · přehled čtvrtí · jen papír, ne rada", fontsize=10.5, color=MUTED)
    ax = fig.add_axes([.745, .925, .2, .05]); ax.axis("off")                       # létající talíř
    ax.add_patch(matplotlib.patches.Ellipse((.5, .45), .9, .32, color="#c9cfee"))
    ax.add_patch(matplotlib.patches.Ellipse((.5, .5), .62, .1, color=MG, alpha=.9))
    ax.add_patch(matplotlib.patches.Wedge((.5, .5), .2, 0, 180, color=CY, alpha=.85))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    def card(x, y, w, h, col, title, value, sub, value_col=FG):
        a = fig.add_axes([x, y, w, h]); a.axis("off")
        for lw, al in ((9, .07), (5, .14), (1.6, 1)):
            a.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=.07", fc=CARD if lw < 2 else "none",
                                       ec=col, lw=lw, alpha=al, transform=a.transAxes, clip_on=False))
        a.text(.07, .8, title, fontsize=10, color=col, fontweight="bold", transform=a.transAxes)
        a.text(.07, .44, value, fontsize=19, color=value_col, fontweight="bold", transform=a.transAxes)
        a.text(.07, .14, sub, fontsize=8.4, color=MUTED, transform=a.transAxes)
        return a

    sgn = lambda v, d=0: ("–" if v is None else _n(v, d))
    c, lb = D["city"], D["lab"]
    card(.06, .80, .27, .105, "#ff4fd8", "● TRADE CITY", f"{c['open']} otevř.", f"jádro Σ {sgn(c['sum_r'], 2)} R · ensemble {sgn(c['ens_pct'], 1)} %")
    card(.365, .80, .27, .105, "#b98cff", "● LABORATOŘ", f"{lb['open']} otevř.",
         f"{lb['active']} strategií · Σ {sgn(lb['sum_r'], 2)} R" + (f" · {lb['win']:.0f} % výher" if lb["win"] is not None else ""),
         )
    t = D.get("dt") or {}
    card(.67, .80, .27, .105, "#ff3b5c", "● DOWNTOWN", f"{sgn(t.get('live_net'))} USDT" if t else "–",
         f"živě · v plusu {t.get('up', 0)}/{t.get('n', 0)} · bankroty {t.get('wipes', 0)}" if t else "data chybí",
         UP if (t.get("live_net") or 0) > 0 else (DOWN if (t.get("live_net") or 0) < 0 else FG))
    b = D.get("brain")
    a = card(.06, .655, .575, .125, "#7dffcf", "● MOZEK · váhy kapitálu podle fáze trhu", "", "")
    if b:
        a.text(.07, .56, f"fáze: {b['phase']}", fontsize=13, color=FG, fontweight="bold", transform=a.transAxes)
        x0 = .07
        for name, w, up_n, dn_n in b["domes"]:
            ww = .86 * w / 100
            a.add_patch(FancyBboxPatch((x0, .27), max(ww - .006, .01), .12, boxstyle="round,pad=0,rounding_size=.02",
                                       fc=DOME.get(name, MUTED), ec="none", transform=a.transAxes))
            a.text(x0 + .005, .1, f"{name} {w:.0f} %".replace(".", ","), fontsize=7.8, color=DOME.get(name, MUTED), transform=a.transAxes)
            x0 += ww
    else:
        a.text(.07, .45, "mozek se ještě nepočítal", fontsize=11, color=MUTED, transform=a.transAxes)
    ai = D.get("ai") or {}
    card(.67, .655, .27, .125, "#b6ff5c", "● AI LAB", f"{ai.get('pass', 0)}/{ai.get('n', 0)} prošlo" if ai else "–",
         f"živě {ai.get('live_trades', 0)} obch. · {sgn(ai.get('live_net'))} USDT" if ai else "data chybí")

    # otevřené obchody laboratoře
    fig.text(.06, .615, "Otevřené obchody laboratoře · výsledek teď (R po poplatcích)", fontsize=12.5, fontweight="bold",
             color=FG, path_effects=[pe.withStroke(linewidth=4, foreground="#b98cff", alpha=.15)])
    ax = fig.add_axes([.36, .345, .42, .25], facecolor="none")
    shown = ops[:10]
    if shown:
        vals = [p["r"] if p["r"] is not None else 0.0 for p in shown][::-1]
        labs = [f"{p['coin']} {p['dir'][0].upper()} · {_short(p)}" for p in shown][::-1]
        cols = [UP if v >= 0 else DOWN for v in vals]
        ax.barh(range(len(vals)), vals, color=cols, height=.6, alpha=.95)
        ax.barh(range(len(vals)), vals, color=cols, height=.9, alpha=.15)
        ax.axvline(0, color=LINE, lw=1.2)
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels([lab if len(lab) <= 32 else lab[:31] + "…" for lab in labs], fontsize=9, color=FG)
        span = max(.5, max(abs(v) for v in vals) * 1.15)
        ax.set_xlim(-span, span)
        from matplotlib.transforms import blended_transform_factory
        tr = blended_transform_factory(ax.transAxes, ax.transData)
        for i, (v, p) in enumerate(zip(vals, shown[::-1])):
            ax.text(1.04, i, _n(v), transform=tr, va="center", ha="left", fontsize=10, fontweight="bold", color=UP if v >= 0 else DOWN)
            ax.text(1.2, i, (_n(p["pct"], 1) + " %") if p["pct"] is not None else "?", transform=tr, va="center", ha="left", fontsize=9, color=MUTED)
        if len(ops) > len(shown):
            fig.text(.36, .33, f"… a dalších {len(ops) - len(shown)}", fontsize=9, color=MUTED)
    else:
        ax.set_xlim(-1, 1); ax.set_yticks([])
        ax.text(0, .5, "Žádný otevřený obchod – strategie čekají na signál ve svém režimu trhu.",
                ha="center", va="center", fontsize=10.5, color=MUTED, transform=ax.transAxes)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8.5); ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=LINE, lw=.6, alpha=.5)

    # křivka uzavřených obchodů
    fig.text(.06, .285, "Uzavřené obchody laboratoře · součet R v čase", fontsize=12.5, fontweight="bold",
             path_effects=[pe.withStroke(linewidth=4, foreground=CY, alpha=.15)])
    ax2 = fig.add_axes([.1, .06, .84, .2], facecolor="none")
    if cl:
        s = pd.Series([c["r"] for c in cl], index=pd.to_datetime([c["time"] for c in cl], utc=True)).sort_index().cumsum()
        first = s.index[0] - (s.index[-1] - s.index[0]) * .04 - pd.Timedelta(minutes=30)
        s = pd.concat([pd.Series([0.0], index=[first]), s])
        x = s.index.tz_convert(TZ)
        col = UP if s.iloc[-1] >= 0 else DOWN
        ax2.fill_between(x, 0, s.values, color=col, alpha=.14, step="post")
        for lw, al in ((7, .1), (4, .2), (2, 1)):
            ax2.step(x, s.values, where="post", color=col, lw=lw, alpha=al)
        ax2.scatter([x[-1]], [s.iloc[-1]], color=FG, s=26, zorder=3)
        ax2.axhline(0, color=LINE, lw=1)
        ax2.set_ylabel("Σ R")
        import matplotlib.dates as mdates
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.", tz=TZ))
    else:
        ax2.set_xticks([]); ax2.set_yticks([])
        ax2.text(.5, .5, "Zatím žádný uzavřený obchod.", ha="center", va="center", fontsize=11, color=MUTED, transform=ax2.transAxes)
    for sp in ax2.spines.values():
        sp.set_visible(False)
    ax2.grid(axis="y", color=LINE, lw=.6, alpha=.5)
    ax2.tick_params(labelsize=8.5)
    fig.text(.06, .018, "Agentown · papírové obchody a výzkum, žádné skutečné peníze. Nejde o finanční poradenství.", fontsize=8, color=MUTED)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SPACE)
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
