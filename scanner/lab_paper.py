"""⚡ Papírový běh strategií z registru laboratoře (research/registry.json).

Při každém průchodu skeneru: pro každý timeframe aktivních strategií, kde se právě zavřela svíčka,
  1. doplní svíčky z OKX (cache scanner/cache/lab_<COIN>_<TF>.csv, poprvé ~1000 svíček),
  2. určí režim trhu každé mince z předchozího uzavřeného dne (research/regime.py),
  3. strategie, jejíž režim právě platí, vyhodnotí signál na poslední uzavřené svíčce – stejným kódem jako atlas
     (research/experiments/strategy_atlas.family_signals) → ⚡ zpráva na Telegram + papírový obchod,
  4. otevřené obchody spravuje STEJNOU simulací jako backtest (vstup na open další svíčky, stop / cíl / trailing /
     výstup signálem), poplatky MEXC 0,05 % na stranu → 📕 zpráva při uzavření, záznam do research/lab_trades.jsonl.
  5. 🧠 KONTEXT (research/context.py, model research/context_model.json z testu research/experiments/context_gate.py):
     u každého signálu spočítá kontext trhu (trend mince a BTC, trendovost, pokračování průrazů, nálada, kvalita
     svíčky…). Trendové strategie: když brána v testu PROŠLA, vezme se jen signál se skóre nad prahem, jinak se skóre
     jen zapíše. Strategie s context = "range" (návrat do rozpětí) obchoduje jen v bočním trhu.
  6. LIMIT KORELACE: nejvýš `lab.max_same_dir` souběžných pozic stejného směru a jedna pozice na minci a směr
     (stejný pohyb BTC jinak vybere několik stopů naráz).
Signál, který brána nebo limit nepustí, se sleduje jako STÍNOVÝ obchod (research/lab_shadow.jsonl, bez zpráv),
aby se dalo živě změřit, jestli brána pomáhá. Na burzu se nic neposílá. Selhání nesmí shodit skener – volá se v try/except.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import context, regime, registry  # noqa: E402
from research.experiments import strategy_atlas as atlas  # noqa: E402
from scanner import notify  # noqa: E402

LOG = ROOT / "research" / "lab_trades.jsonl"
SHADOW = ROOT / "research" / "lab_shadow.jsonl"
MODEL = ROOT / "research" / "context_model.json"
CACHE = ROOT / "scanner" / "cache"
TF_TD = {"15m": "15min", "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h", "1d": "1D"}
COST = atlas.COSTS[atlas.MAIN]


def _n(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


def _log(rec, path=None):
    with (path or LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_model(path=None):
    p = Path(path or MODEL)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"lab: model kontextu nečitelný: {exc.__class__.__name__}", file=sys.stderr)
        return None


def decide(model, s, feats, open_pos, max_same_dir, coin):
    """Vezme se signál? Vrací (ano/ne, důvod, skóre, pro, proti)."""
    sc, pos, neg = None, [], []
    if model:
        sc = float(context.score(model, feats)[0])
        pos, neg = context.reasons(model, feats)
    if s.get("context") == "range":
        if not model:
            return False, "chybí model kontextu", sc, pos, neg
        if not bool(context.is_range(model, feats)[0]):
            return False, "trh není boční (průrazy pokračují / denní trend)", sc, pos, neg
    elif model and (model.get("gate") or {}).get("pass") and sc < model["threshold"]:
        return False, f"slabý kontext (skóre {sc:+.2f} < práh {model['threshold']:+.2f})", sc, pos, neg
    if any(o["coin"] == coin and o["dir"] == s["dir"] for o in open_pos):
        return False, "na minci už je pozice stejného směru", sc, pos, neg
    if sum(1 for o in open_pos if o["dir"] == s["dir"]) >= max_same_dir:
        return False, f"limit {max_same_dir} souběžných pozic {s['dir']}", sc, pos, neg
    return True, "", sc, pos, neg


def _exchange():
    import ccxt
    return ccxt.okx({"enableRateLimit": True})


def candles(ex, coin, tf, now, bars=1000):
    """Uzavřené svíčky z OKX s lokální cache; poprvé stáhne ~`bars` svíček, potom jen doplňuje."""
    path = CACHE / f"lab_{coin}_{tf}.csv"
    step = pd.Timedelta(TF_TD[tf])
    df = None
    if path.exists():
        df = pd.read_csv(path, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
    since = (df.index[-1] - 3 * step) if df is not None and len(df) else (now - bars * step)
    rows, cur = [], int(since.timestamp() * 1000)
    for _ in range(40):
        batch = ex.fetch_ohlcv(f"{coin}/USDT", tf, since=cur, limit=100)
        if not batch:
            break
        rows += batch
        nxt = batch[-1][0] + int(step.total_seconds() * 1000)
        if nxt <= cur or nxt > int(now.timestamp() * 1000):
            break
        cur = nxt
    new = pd.DataFrame(rows, columns=["t", "Open", "High", "Low", "Close", "Volume"]).drop_duplicates("t")
    new.index = pd.to_datetime(new.pop("t"), unit="ms", utc=True)
    df = new if df is None else pd.concat([df[~df.index.isin(new.index)], new]).sort_index()
    df = df[df.index + step <= now].iloc[-3000:]                        # jen uzavřené svíčky
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def _daily_context(daily):
    """Režim a filtry d200 / d50 pro každý den (z předchozího uzavřeného dne)."""
    reg = regime.regime_series(daily)
    e200 = daily["Close"].ewm(span=200, adjust=False, min_periods=200).mean()
    e50 = daily["Close"].ewm(span=50, adjust=False, min_periods=50).mean()
    bull = (daily["Close"] > e200).where(e200.notna())
    up = (e50 > e50.shift(1)).where(e50.shift(1).notna())
    bull.index = bull.index + pd.Timedelta("1D")
    up.index = up.index + pd.Timedelta("1D")
    return reg, bull, up


def _prep(df, daily_ctx):
    z = atlas.Ind(df)
    reg, bull, up = daily_ctx
    day = df.index.floor("1D")
    z.flt = {"d200": bull.reindex(day).to_numpy(float), "d50": up.reindex(day).to_numpy(float)}
    z.reg = reg.reindex(day).to_numpy(dtype=object)
    return z


def _params(s):
    """Parametry z textu registru zpět na typy, které čeká family_signals."""
    out = []
    for x in s["params"].split("/"):
        try:
            out.append(int(x))
        except ValueError:
            try:
                out.append(float(x))
            except ValueError:
                out.append(x)
    return tuple(out)


def _simulate(z, s, sig_idx):
    d = 1 if s["dir"] == "long" else -1
    ent, opp = atlas.family_signals(z, s["family"], _params(s), d)
    sa, ta, ga, uo, mh = atlas.EXITS[s["exit"]]
    ii, xx, gg, rf = atlas.simulate(z.o, z.h, z.l, z.c, z.atr, np.array([sig_idx], np.int64), np.asarray(opp, bool),
                                    d, sa, ta, ga, uo, mh)
    if not len(ii):
        return None
    n = len(z.c)
    closed = xx[0] < n - 1 or ii[0] + mh <= n
    return {"entry_i": int(ii[0]), "exit_i": int(xx[0]), "g": float(gg[0]), "rf": float(rf[0]), "closed": bool(closed)}


def _plan(z, s, i):
    d = 1 if s["dir"] == "long" else -1
    sa, ta, ga, uo, mh = atlas.EXITS[s["exit"]]
    px, a = z.c[i], z.atr[i]
    parts = []
    if sa:
        parts.append(f"stop {notify.fmt(px - d * sa * a)} ({sa:g} ATR)")
    if ga:
        parts.append(f"cíl {notify.fmt(px + d * ga * a)}")
    if ta:
        parts.append(f"trailing {ta:g} ATR")
    if uo:
        parts.append("výstup opačným signálem")
    return ", ".join(parts)


def _manage(positions, tf, frames, reg, now, msgs, shadow=False):
    """Posune otevřené obchody timeframu `tf`; uzavřené zapíše (stínové do SHADOW, bez zprávy). Vrací ještě otevřené."""
    still = []
    for o in positions:
        z = frames.get(o["coin"]) if o["tf"] == tf else None
        if z is None:
            still.append(o)
            continue
        s = registry.find(reg, o["sid"]) or o["strategy"]
        d = 1 if o["dir"] == "long" else -1
        pos = np.flatnonzero(z.df.index == pd.Timestamp(o["signal_bar"]))
        if not len(pos):                                              # signál vypadl z okna dat – zavřít na posledním close
            px = z.c[-1]
            g = d * (px / o["entry"] - 1) if o.get("entry") else 0.0
            res = {"entry_i": None, "g": g, "rf": o.get("rf") or 1.0, "exit_i": len(z.c) - 1, "closed": True}
        else:
            res = _simulate(z, s, int(pos[0]))
            if res is None:
                still.append(o)
                continue
            o["entry"] = float(z.o[res["entry_i"]])
            o["rf"] = res["rf"]
        if not res["closed"]:
            still.append(o)
            continue
        r = (res["g"] - 2 * COST) / res["rf"]
        fill = o["entry"] * (1 + d * res["g"]) if o.get("entry") else None     # skutečná výstupní cena (stop/cíl), ne close
        rec = {"event": "close", "sid": o["sid"], "coin": o["coin"], "tf": tf, "dir": o["dir"],
               "signal_bar": o["signal_bar"], "entry": o.get("entry"), "exit_bar": z.df.index[res["exit_i"]].isoformat(),
               "exit": round(fill, 8) if fill is not None else None,
               "g": round(res["g"], 6), "r": round(r, 3), "regime": o.get("regime"), "time": now.isoformat()}
        for k in ("ctx_score", "ctx", "ctx_range", "skip"):
            if k in o:
                rec[k] = o[k]
        _log(rec, SHADOW if shadow else None)
        if not shadow:
            msgs.append(f"🧪📕 {o['label']} · {o['coin']} {o['dir'].upper()} {tf.upper()}: {_n(r)} R "
                        f"({_n(res['g'] * 100 - 2 * COST * 100)} % po poplatcích), papírově.")
    return still


def update(cfg, state, now=None, dry_run=False, send=None, ex=None, reg=None):
    lc = cfg.get("lab") or {}
    if not lc.get("enabled"):
        return []
    now = now or datetime.now(timezone.utc)
    now = pd.Timestamp(now)
    reg = reg if reg is not None else registry.load()
    strats = registry.active(reg)
    st = state.data.setdefault("lab", {"last_eval": {}, "open": []})
    tg = send or (None if dry_run or not cfg.get("notify", {}).get("telegram", True) else notify.telegram)
    coins = [t["symbol"].split("/")[0] for t in cfg.get("tickers", []) if t.get("source") == "crypto"]
    tfs = sorted({s["tf"] for s in strats} | {o["tf"] for o in st["open"] + st.get("shadow", [])},
                 key=lambda x: pd.Timedelta(TF_TD[x]))
    due = []
    for tf in tfs:
        step = pd.Timedelta(TF_TD[tf])
        last_closed = (now.floor(step) - step).isoformat()            # začátek poslední uzavřené svíčky
        if st["last_eval"].get(tf) != last_closed:
            due.append((tf, last_closed))
    if not due:
        return []
    ex = ex or _exchange()
    msgs = []
    daily, ddf = {}, {}
    for coin in coins:
        try:
            ddf[coin] = candles(ex, coin, "1d", now, bars=900)
            daily[coin] = _daily_context(ddf[coin])
        except Exception as exc:
            print(f"lab: denní data {coin} selhala: {exc.__class__.__name__}", file=sys.stderr)
    model = load_model()
    max_same_dir = int(lc.get("max_same_dir", 3))
    dctx = {}
    if model:
        fng_c = None
        try:
            from research.lab import fng_series
            fng_c = fng_series()
        except Exception as exc:
            print(f"lab: nálada pro kontext nedostupná: {exc.__class__.__name__}", file=sys.stderr)
        for coin in ddf:
            try:
                dctx[coin] = context.daily_frame(ddf[coin], ddf.get("BTC"), fng_c)
            except Exception as exc:
                print(f"lab: kontext {coin} selhal: {exc.__class__.__name__}", file=sys.stderr)
    st.setdefault("shadow", [])
    fng = None
    if any(s["family"] == "fng" for s in strats):
        try:
            from research.lab import fng_series
            fng = fng_series()
        except Exception as exc:
            print(f"lab: Strach a chamtivost nedostupné: {exc.__class__.__name__}", file=sys.stderr)
    for tf, last_closed in due:
        frames = {}
        for coin in coins:
            if coin not in daily:
                continue
            try:
                frames[coin] = _prep(candles(ex, coin, tf, now), daily[coin])
                if fng is not None:
                    frames[coin].fng = fng.reindex(frames[coin].df.index.floor("1D")).ffill().to_numpy(float)
            except Exception as exc:
                print(f"lab: {coin} {tf} selhalo: {exc.__class__.__name__}", file=sys.stderr)
        # 1) správa otevřených (a stínových) obchodů
        for key in ("open", "shadow"):
            st[key] = _manage(st.get(key, []), tf, frames, reg, now, msgs, shadow=key == "shadow")
        # 2) nové signály na poslední uzavřené svíčce
        for s in strats:
            if s["tf"] != tf:
                continue
            d = 1 if s["dir"] == "long" else -1
            for coin, z in frames.items():
                if s["family"] == "fng" and not hasattr(z, "fng"):
                    continue
                i = len(z.c) - 1
                if z.df.index[i].isoformat() != last_closed:
                    continue                                          # data ještě nemají poslední svíčku
                rg = z.reg[i]
                if s.get("regimes") and rg not in s["regimes"]:
                    continue
                if any(o["sid"] == s["id"] and o["coin"] == coin for o in st["open"] + st["shadow"]):
                    continue
                if s["filter"] != "none" and z.flt[s["filter"]][i] != (1.0 if d > 0 else 0.0):
                    continue
                ent, _ = atlas.family_signals(z, s["family"], _params(s), d)
                if not len(ent) or ent[-1] != i:
                    continue
                sa0 = atlas.EXITS[s["exit"]][0]
                risk = (sa0 if sa0 > 0 else 2.0) * float(z.atr[i])
                o = {"sid": s["id"], "label": s["label"], "coin": coin, "tf": tf, "dir": s["dir"],
                     "signal_bar": last_closed, "signal_close": float(z.c[i]), "regime": rg,
                     "rf": risk / float(z.c[i]), "stop": float(z.c[i]) - d * risk if sa0 > 0 else None,
                     "strategy": {k: s[k] for k in ("id", "family", "params", "tf", "filter", "exit", "dir", "label")}}
                feats = None
                if model and coin in dctx:
                    try:
                        feats = context.TfContext(z.df, dctx[coin]).at([i], d)
                    except Exception as exc:
                        print(f"lab: kontext signálu selhal: {exc.__class__.__name__}", file=sys.stderr)
                take, why, sc, pro, proti = decide(model if feats else None, s, feats, st["open"], max_same_dir, coin)
                if sc is not None:
                    o["ctx_score"] = round(sc, 3)
                if feats is not None:                                 # metriky kontextu pro měření dopředu
                    o["ctx"] = {k: round(float(v[0]), 3) for k, v in feats.items() if np.isfinite(v[0])}
                    o["ctx_range"] = bool(context.is_range(model, feats)[0])
                if s.get("context"):
                    o["strategy"]["context"] = s["context"]
                if not take:
                    o["skip"] = why
                    st["shadow"].append(o)
                    _log({"event": "signal", **{k: v for k, v in o.items() if k != "strategy"}, "time": now.isoformat()},
                         SHADOW)
                    continue
                st["open"].append(o)
                _log({"event": "signal", **{k: v for k, v in o.items() if k != "strategy"}, "time": now.isoformat()})
                ctx_line = context.describe(model, feats) + "\n" if feats is not None else ""
                if sc is not None and (model.get("gate") or {}).get("pass"):
                    ctx_line += (f"🧠 Skóre {_n(sc)} (práh {_n(model['threshold'])})"
                                 + (f" · pro: {', '.join(pro)}" if pro else "")
                                 + (f" · proti: {', '.join(proti)}" if proti else "") + "\n")
                msgs.append(f"⚡ {s['label']} · {coin} {s['dir'].upper()} {tf.upper()} · režim {rg}\n"
                            f"Vstup ~{notify.fmt(z.c[i])} (open další svíčky), {_plan(z, s, i)}.\n" + ctx_line +
                            f"Laboratoř: {s['status']}, backtest OOS {_n(s['backtest'].get('oos_r', 0))} R. "
                            f"Papírově, ne rada.")
        st["last_eval"][tf] = last_closed
    state.save()
    if tg:
        for m in msgs:
            tg(m)
    for m in msgs:
        print(m)
    return msgs
