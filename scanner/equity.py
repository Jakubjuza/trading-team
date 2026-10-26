"""Denní snímek hodnoty účtu desku → research/equity_log.jsonl (živá křivka pro Agentárium).

Jednou denně (první průchod po `hour` UTC) zapíše:
  • paper: papírový účet desku = account_size + uzavřené R (jádro + pyramida) × riziko na obchod
           + otevřené pozice přeceněné poslední cenou + změna hodnoty 🧭 ensemblu (jeho kniha od startu),
  • demo:  hodnota spotového DEMO účtu OKX (volná měna + mince × poslední cena) – jen čtení zůstatků.
Je to záznam desku, ne ověření od brokera: papír počítá skener sám, demo je simulovaný účet OKX.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "research" / "equity_log.jsonl"


def paper_equity(cfg, state, prices):
    """Hodnota papírového účtu v USD a rozpad na části."""
    risk_usd = cfg.get("account_size", 10000) * cfg.get("risk_pct", 1.0) / 100

    def px(sym):
        return (prices.get(sym) or (None,))[0]
    core_closed = sum(r.get("r", 0) for r in state.data.get("closed", []))
    core_open = 0.0
    for p in state.data.get("open", []):
        s, now = p["setup"], px(p["symbol"])
        risk = abs(s["entry"] - s["stop"])
        if now and risk:
            core_open += (1 if s["direction"] == "long" else -1) * (now - s["entry"]) / risk
    pyr = state.data.get("pyramid") or {}
    pyr_closed = sum(r.get("r", 0) for r in pyr.get("closed", []))
    pyr_open = sum(p.get("r_now", 0) for p in pyr.get("open", []))
    ens = state.data.get("ensemble") or {}
    ens_pnl = 0.0
    if ens.get("start_equity"):
        value = ens.get("cash", 0) + sum(q * (px(f"{c}/USDT") or 0) for c, q in ens.get("qty", {}).items())
        ens_pnl = value - ens["start_equity"]
    parts = {"core": (core_closed + core_open) * risk_usd, "pyramid": (pyr_closed + pyr_open) * risk_usd,
             "ensemble": ens_pnl}
    return cfg.get("account_size", 10000) + sum(parts.values()), {k: round(v, 2) for k, v in parts.items()}


def demo_equity(broker, prices):
    bal = broker.ex.fetch_balance()
    quote = getattr(broker, "quote", None) or "USDT"
    total = float((bal.get(quote) or {}).get("total") or 0)
    for c, b in bal.items():
        if c == quote or not isinstance(b, dict):
            continue
        q = float(b.get("total") or 0)
        p = (prices.get(f"{c}/USDT") or (None,))[0]
        if q and p:
            total += q * p
    return round(total, 2), quote


def snapshot(cfg, state, prices, now, demo=None, dry_run=False, log=None):
    """Zapíše jeden řádek za den (UTC). Vrací záznam nebo None."""
    ec = cfg.get("equity_log") or {}
    if not ec.get("enabled", True):
        return None
    day = now.astimezone(timezone.utc).date().isoformat()
    st = state.data.setdefault("equity_log", {})
    if st.get("day") == day or now.astimezone(timezone.utc).hour < ec.get("hour", 0) or not prices:
        return None
    eq, parts = paper_equity(cfg, state, prices)
    rec = {"t": day, "paper": round(eq, 2), "parts": parts, "time": now.isoformat(timespec="seconds")}
    if demo is not None:
        try:
            rec["demo"], rec["demo_ccy"] = demo_equity(demo, prices)
        except Exception as exc:
            rec["demo_error"] = exc.__class__.__name__
    st["day"] = day
    state.save()
    if not dry_run:
        try:
            with open(log or LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as exc:
            print(f"equity log: {exc}", file=sys.stderr)
    return rec


def read(log=None):
    path = Path(log or LOG)
    out = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


if __name__ == "__main__":
    print(json.dumps(read()[-5:], ensure_ascii=False, indent=1))
    print(datetime.now(timezone.utc).isoformat())
