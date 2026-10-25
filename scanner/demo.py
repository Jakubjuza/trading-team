"""Zrcadlení papírových obchodů na DEMO účet OKX (virtuální peníze) – test skutečného plnění, skluzu a poplatků.

Bezpečnost:
  • ccxt.okx se vždy přepne do demo režimu (set_sandbox_mode → hlavička x-simulated-trading: 1); bez ní se nic
    nepošle. Ostrý účet tento modul nikdy nepoužije a `live_trading` v configu se ho netýká.
  • klíče jen z prostředí (GitHub Secrets): OKX_DEMO_API_KEY, OKX_DEMO_API_SECRET, OKX_DEMO_PASSPHRASE.
Obchoduje se perpetual swap (BTC/USDT:USDT…), aby šly i shorty; izolovaná marže, páka `leverage` (výchozí 2×).
Správa: vstup market + ochranný stop na burze (celá pozice) + reduce-only limit na T1 (polovina pozice).
Po T1 se stop zbytku posune na vstup; když skener papírovou pozici uzavře (trailing / čas / stop), demo pozice
se zavře marketem a ochranné příkazy se zruší. Plnění a poplatky jdou do research/demo_trades.jsonl.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "research" / "demo_trades.jsonl"


def env_keys():
    k = {n: os.environ.get(f"OKX_DEMO_{n}") for n in ("API_KEY", "API_SECRET", "PASSPHRASE")}
    return k if all(k.values()) else None


def swap_symbol(symbol):
    base, quote = symbol.split("/")
    return f"{base}/{quote}:{quote}"


class DemoBroker:
    def __init__(self, cfg, ex=None):
        self.cfg = cfg.get("demo") or {}
        self.leverage = self.cfg.get("leverage", 2)
        if ex is None:
            keys = env_keys()
            if not keys:
                raise RuntimeError("chybí OKX_DEMO_API_KEY / OKX_DEMO_API_SECRET / OKX_DEMO_PASSPHRASE")
            import ccxt
            ex = ccxt.okx({"apiKey": keys["API_KEY"], "secret": keys["API_SECRET"], "password": keys["PASSPHRASE"],
                           "enableRateLimit": True, "options": {"defaultType": "swap"}})
            ex.set_sandbox_mode(True)
        if (getattr(ex, "headers", None) or {}).get("x-simulated-trading") != "1":
            raise RuntimeError("OKX není v demo režimu – nic se neposílá")
        self.ex = ex
        self._hedged = None

    # --- pomocné ------------------------------------------------------------------------
    def hedged(self):
        if self._hedged is None:
            try:
                mode = self.ex.private_get_account_config()["data"][0].get("posMode")
            except Exception:
                mode = "net_mode"
            self._hedged = mode == "long_short_mode"
        return self._hedged

    def params(self, **kw):
        p = {"tdMode": "isolated", **kw}
        if self.hedged():
            p["hedged"] = True
        return p

    def contracts(self, sym, qty):
        self.ex.load_markets()
        m = self.ex.market(sym)
        cs = m.get("contractSize") or 1
        n = float(self.ex.amount_to_precision(sym, qty / cs))
        mn = ((m.get("limits") or {}).get("amount") or {}).get("min") or 0
        return n if n >= mn else 0.0, cs

    @staticmethod
    def fill(order):
        """Průměrná cena, množství a poplatek (USDT) z odpovědi burzy."""
        o = order or {}
        fee = o.get("fee") or {}
        return {"id": o.get("id"), "price": o.get("average") or o.get("price"), "filled": o.get("filled"),
                "fee": abs(float(fee.get("cost") or 0)) if fee else 0.0}

    def log(self, rec):
        try:
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except Exception as exc:
            print(f"demo deník: {exc}", file=sys.stderr)

    # --- životní cyklus pozice ------------------------------------------------------------
    def open(self, pos, size):
        s = pos["setup"]
        sym = swap_symbol(pos["symbol"])
        long = s["direction"] == "long"
        n, cs = self.contracts(sym, size["qty"])
        if n <= 0:
            return {"status": "too_small", "symbol": sym}
        try:
            self.ex.set_leverage(self.leverage, sym, {"mgnMode": "isolated", **({"posSide": "long" if long else "short"}
                                                                             if self.hedged() else {})})
        except Exception as exc:
            print(f"[demo {sym}] páka: {exc}", file=sys.stderr)
        side, close_side = ("buy", "sell") if long else ("sell", "buy")
        entry = self.ex.create_order(sym, "market", side, n, None, self.params())
        f = self.fill(entry)
        if not f["price"]:
            try:
                f = self.fill(self.ex.fetch_order(entry["id"], sym))
            except Exception:
                pass
        sl = self.ex.create_order(sym, "market", close_side, n, None, self.params(stopLossPrice=s["stop"], reduceOnly=True))
        half = float(self.ex.amount_to_precision(sym, n / 2))
        tp = None
        if half > 0:
            tp = self.ex.create_order(sym, "limit", close_side, half, s["targets"][0], self.params(reduceOnly=True))
        rec = {"status": "open", "symbol": sym, "contracts": n, "contract_size": cs, "side": s["direction"],
               "planned_entry": s["entry"], "entry": f["price"], "entry_fee": f["fee"], "sl_id": sl.get("id"),
               "tp_id": (tp or {}).get("id"), "tp_contracts": half, "opened": datetime.now(timezone.utc).isoformat()}
        if rec["entry"]:
            slip = (rec["entry"] / s["entry"] - 1) * 100 * (1 if long else -1)
            rec["slippage_pct"] = round(slip, 3)
        self.log({"event": "open", "id": pos["id"], "strategy": pos.get("strategy"), **rec})
        return rec

    def move_stop(self, pos, rec, new_stop):
        """Po T1: stop zbytku na vstup (break-even)."""
        sym, long = rec["symbol"], rec["side"] == "long"
        try:
            self.ex.cancel_order(rec["sl_id"], sym, {"trigger": True})
        except Exception as exc:
            print(f"[demo {sym}] zrušení stopu: {exc}", file=sys.stderr)
        remaining = self.remaining(rec)
        if remaining <= 0:
            return rec
        sl = self.ex.create_order(sym, "market", "sell" if long else "buy", remaining, None,
                                  self.params(stopLossPrice=new_stop, reduceOnly=True))
        rec = {**rec, "sl_id": sl.get("id"), "stop_moved": new_stop}
        self.log({"event": "move_stop", "id": pos["id"], "symbol": sym, "stop": new_stop})
        return rec

    def remaining(self, rec):
        done = 0.0
        if rec.get("tp_id"):
            try:
                done = float(self.ex.fetch_order(rec["tp_id"], rec["symbol"]).get("filled") or 0)
            except Exception:
                pass
        return float(self.ex.amount_to_precision(rec["symbol"], max(0.0, rec["contracts"] - done)))

    def close(self, pos, rec, reason, paper_r=None):
        """Zavře zbytek marketem, zruší ochranné příkazy, zapíše výsledek z plnění."""
        sym, long = rec["symbol"], rec["side"] == "long"
        tp = {}
        if rec.get("tp_id"):
            try:
                tp = self.ex.fetch_order(rec["tp_id"], sym)
                if (tp.get("status") or "") == "open":
                    self.ex.cancel_order(rec["tp_id"], sym)
            except Exception as exc:
                print(f"[demo {sym}] T1 příkaz: {exc}", file=sys.stderr)
        try:
            self.ex.cancel_order(rec["sl_id"], sym, {"trigger": True})
            stopped = False
        except Exception:
            stopped = True                                               # stop už se na burze vykonal
        tp_filled = float(tp.get("filled") or 0)
        rest = 0.0 if stopped else float(self.ex.amount_to_precision(sym, max(0.0, rec["contracts"] - tp_filled)))
        exit_fill = {}
        if rest > 0:
            exit_fill = self.fill(self.ex.create_order(sym, "market", "sell" if long else "buy", rest, None,
                                                       self.params(reduceOnly=True)))
        sign = 1 if long else -1
        cs = rec.get("contract_size") or 1
        pnl = None
        if rec.get("entry") and (exit_fill.get("price") or tp_filled):
            legs = []
            if tp_filled:
                legs.append((tp_filled, float(tp.get("average") or tp.get("price"))))
            if rest > 0 and exit_fill.get("price"):
                legs.append((rest, float(exit_fill["price"])))
            pnl = sum(sign * (px - rec["entry"]) * q * cs for q, px in legs)
            pnl -= (rec.get("entry_fee") or 0) + float((tp.get("fee") or {}).get("cost") or 0) + (exit_fill.get("fee") or 0)
        out = {"event": "close", "id": pos["id"], "strategy": pos.get("strategy"), "symbol": sym, "reason": reason,
               "tp_filled": tp_filled, "exit": exit_fill.get("price"), "stopped_on_exchange": stopped,
               "pnl_usdt": round(pnl, 2) if pnl is not None else None, "paper_r": paper_r,
               "closed": datetime.now(timezone.utc).isoformat()}
        self.log(out)
        return out


def main():
    """Kontrola demo účtu: python3 scanner/demo.py [--test-order]"""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-order", action="store_true", help="otevřít a hned zavřít 1 kontrakt BTC (demo)")
    a = ap.parse_args()
    b = DemoBroker({"demo": {"leverage": 2}})
    print("demo režim:", b.ex.headers.get("x-simulated-trading") == "1")
    print("režim pozic:", "long/short" if b.hedged() else "net")
    bal = b.ex.fetch_balance()
    print("USDT:", (bal.get("USDT") or {}).get("free"), "volné /", (bal.get("USDT") or {}).get("total"), "celkem")
    b.ex.load_markets()
    for c in ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]:
        sym = f"{c}/USDT:USDT"
        m = b.ex.market(sym)
        print(f"  {sym}: kontrakt {m.get('contractSize')} {c}, min. {((m.get('limits') or {}).get('amount') or {}).get('min')}")
    if a.test_order:
        t = b.ex.fetch_ticker("BTC/USDT:USDT")["last"]
        pos = {"id": "TEST", "symbol": "BTC/USDT", "strategy": "test",
               "setup": {"direction": "long", "entry": t, "stop": t * 0.95, "targets": [t * 1.05, t * 1.1]}}
        rec = b.open(pos, {"qty": 0.02})
        print("otevřeno:", rec)
        print("uzavřeno:", b.close(pos, rec, "test"))


if __name__ == "__main__":
    main()
