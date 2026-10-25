"""Zrcadlení papírových obchodů na DEMO účet OKX (virtuální peníze) – test skutečného plnění, skluzu a poplatků.

Bezpečnost:
  • ccxt.okx se vždy přepne do demo režimu (set_sandbox_mode → hlavička x-simulated-trading: 1); bez ní se nic
    nepošle. Ostrý účet tento modul nikdy nepoužije a `live_trading` v configu se ho netýká.
  • klíče jen z prostředí (GitHub Secrets): OKX_DEMO_API_KEY, OKX_DEMO_API_SECRET, OKX_DEMO_PASSPHRASE.
Trh podle `demo.market`:
  • swap (výchozí): perpetual BTC/USDT:USDT… (s `demo.quote: USDC` → BTC/USDC:USDC, OKX EEA nemá USDT), longy i shorty; izolovaná marže, páka `leverage` (výchozí 2×).
    Vstup market + ochranný stop na burze (celá pozice) + reduce-only limit na T1 (polovina pozice).
  • spot: BTC/USDT… bez páky a bez futures oprávnění – JEN LONGY (shorty se na spotu nedají, vynechají se).
    Vstup market + ochranný stop na burze (celé koupené množství); T1 prodá skener marketem (limit na spotu by
    zamkl mince, které potřebuje stop).
Po T1 se stop zbytku posune na vstup; když skener papírovou pozici uzavře (trailing / čas / stop), demo pozice
se zavře marketem a ochranné příkazy se zruší. Plnění a poplatky jdou do research/demo_trades.jsonl.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "research" / "demo_trades.jsonl"
HOSTS = ["eea.okx.com", "www.okx.com"]                  # EEA (účty registrované v EU), globální OKX


def env_keys():
    k = {n: os.environ.get(f"OKX_DEMO_{n}") for n in ("API_KEY", "API_SECRET", "PASSPHRASE")}
    return k if all(k.values()) else None


def swap_symbol(symbol, quote=None):
    """BTC/USDT → BTC/USDT:USDT; s `quote` (např. USDC na OKX EEA) → BTC/USDC:USDC."""
    base, q = symbol.split("/")
    q = quote or q
    return f"{base}/{q}:{q}"


def spot_symbol(symbol, quote=None):
    base, q = symbol.split("/")
    return f"{base}/{quote or q}"


def make_broker(cfg, ex=None):
    """Broker podle `demo.market` (swap / spot)."""
    return (SpotDemoBroker if (cfg.get("demo") or {}).get("market", "swap") == "spot" else DemoBroker)(cfg, ex)


class DemoBroker:
    market_type = "swap"

    def __init__(self, cfg, ex=None):
        self.cfg = cfg.get("demo") or {}
        self.leverage = self.cfg.get("leverage", 2)
        self.quote = self.cfg.get("quote")                       # None = jako signál (USDT); OKX EEA: USDC
        if ex is None:
            keys = env_keys()
            if not keys:
                raise RuntimeError("chybí OKX_DEMO_API_KEY / OKX_DEMO_API_SECRET / OKX_DEMO_PASSPHRASE")
            ex = self.connect(keys)
        if (getattr(ex, "headers", None) or {}).get("x-simulated-trading") != "1":
            raise RuntimeError("OKX není v demo režimu – nic se neposílá")
        self.ex = ex
        self._hedged = None

    def connect(self, keys):
        """Najde server, kde klíč existuje: `demo.hostname`, jinak EEA (my.okx.com – účty z EU) a globální OKX."""
        import ccxt
        hosts = [self.cfg["hostname"]] if self.cfg.get("hostname") else HOSTS
        errors = []
        for host in hosts:
            ex = ccxt.okx({"apiKey": keys["API_KEY"], "secret": keys["API_SECRET"], "password": keys["PASSPHRASE"],
                           "enableRateLimit": True, "hostname": host, "options": {"defaultType": self.market_type}})
            ex.set_sandbox_mode(True)
            try:
                ex.private_get_account_config()
                return ex
            except Exception as exc:
                errors.append(f"{host}: {str(exc)[:120]}")
        raise RuntimeError("klíč nepřijat na žádném serveru OKX – " + " | ".join(errors))

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

    def settled(self, order, sym):
        """Market příkaz: OKX v odpovědi často nevrací cenu plnění – dotáhne se z detailu příkazu."""
        o = order or {}
        if o.get("id") and not (o.get("average") and o.get("filled")):
            try:
                o = {**o, **{k: v for k, v in self.ex.fetch_order(o["id"], sym).items() if v is not None}}
            except Exception as exc:
                print(f"[demo {sym}] detail příkazu: {exc}", file=sys.stderr)
        return o

    def log(self, rec):
        try:
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except Exception as exc:
            print(f"demo deník: {exc}", file=sys.stderr)

    # --- životní cyklus pozice ------------------------------------------------------------
    def resolve(self, symbol):
        """Kontrakt pro signál: OKX EEA X-Perp (lineární, vypořádání v USD, např. BTC-USD_UM_XPERP-310328), jinak
        perpetual v `quote` (USDC) / v kotaci signálu (USDT). None = mince na účtu nemá futures."""
        self.ex.load_markets()
        base = symbol.split("/")[0]
        if self.cfg.get("xperp", True):
            xp = sorted((m for m in self.ex.markets.values() if m.get("base") == base and "_UM_XPERP" in str(m.get("id"))
                         and m.get("linear") is not False and m.get("active") is not False), key=lambda m: m["id"])
            if xp:
                return xp[0]["symbol"]
        cand = swap_symbol(symbol, self.quote)                   # s `quote` jen v té měně (na USDT účet nemá peníze)
        return cand if cand in self.ex.markets else None

    def open(self, pos, size):
        s = pos["setup"]
        sym = self.resolve(pos["symbol"])
        if sym is None:
            return {"status": "no_market", "symbol": pos["symbol"]}
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
        f = self.fill(self.settled(self.ex.create_order(sym, "market", side, n, None, self.params()), sym))
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
            exit_fill = self.fill(self.settled(self.ex.create_order(sym, "market", "sell" if long else "buy", rest, None,
                                                                    self.params(reduceOnly=True)), sym))
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


class SpotDemoBroker(DemoBroker):
    """Spot demo (bez futures oprávnění): jen longy, bez páky, stop jako podmíněný příkaz (algo) v režimu cash."""
    market_type = "spot"

    def hedged(self):
        return False

    def amount(self, sym, qty):
        self.ex.load_markets()
        m = self.ex.market(sym)
        n = float(self.ex.amount_to_precision(sym, qty))
        mn = ((m.get("limits") or {}).get("amount") or {}).get("min") or 0
        return n if n >= mn else 0.0

    @staticmethod
    def fee_usdt(order, base, price):
        """Poplatek v USDT – u nákupu na spotu se strhává v kupované minci."""
        fee = (order or {}).get("fee") or {}
        cost = abs(float(fee.get("cost") or 0))
        return cost * float(price or 0) if fee.get("currency") == base else cost

    def place_stop(self, sym, qty, stop):
        m = self.ex.market(sym)
        res = self.ex.private_post_trade_order_algo({
            "instId": m["id"], "tdMode": "cash", "side": "sell", "ordType": "conditional",
            "sz": self.ex.amount_to_precision(sym, qty), "slTriggerPx": self.ex.price_to_precision(sym, stop),
            "slOrdPx": "-1"})
        d = (res.get("data") or [{}])[0]
        if str(d.get("sCode", "0")) != "0" or not d.get("algoId"):
            raise RuntimeError(f"stop nepřijat: {d.get('sCode')} {d.get('sMsg')}")
        return d["algoId"]

    def cancel_stop(self, sym, algo_id):
        """True = zrušeno; False = stop už neexistuje (vykonal se na burze)."""
        res = self.ex.private_post_trade_cancel_algos([{"algoId": algo_id, "instId": self.ex.market(sym)["id"]}])
        d = (res.get("data") or [{}])[0]
        return str(d.get("sCode", "0")) == "0"

    def open(self, pos, size):
        s = pos["setup"]
        sym = spot_symbol(pos["symbol"], self.quote)
        if s["direction"] != "long":
            return {"status": "skipped_short", "symbol": sym}
        self.ex.load_markets()
        if sym not in (self.ex.markets or {}):
            return {"status": "no_market", "symbol": sym}
        base = sym.split("/")[0]
        n = self.amount(sym, size["qty"])
        if n <= 0:
            return {"status": "too_small", "symbol": sym}
        free = float((self.ex.fetch_balance().get(sym.split("/")[1]) or {}).get("free") or 0)
        if n * s["entry"] > free * 0.98:
            return {"status": "no_funds", "symbol": sym, "free_usdt": free}
        entry = self.settled(self.ex.create_order(sym, "market", "buy", n, None, {"tgtCcy": "base_ccy"}), sym)
        px, filled = entry.get("average") or entry.get("price"), float(entry.get("filled") or n)
        fee = entry.get("fee") or {}
        held = filled - (abs(float(fee.get("cost") or 0)) if fee.get("currency") == base else 0)
        held = float(self.ex.amount_to_precision(sym, held))
        rec = {"status": "open", "mode": "spot", "symbol": sym, "contracts": held, "contract_size": 1, "side": "long",
               "planned_entry": s["entry"], "entry": px, "entry_fee": round(self.fee_usdt(entry, base, px), 4),
               "sl_id": None, "tp_id": None, "opened": datetime.now(timezone.utc).isoformat()}
        try:
            rec["sl_id"] = self.place_stop(sym, held, s["stop"])
        except Exception as exc:
            rec["sl_error"] = str(exc)[:200]
            print(f"[demo {sym}] stop: {exc}", file=sys.stderr)
        if px:
            rec["slippage_pct"] = round((float(px) / s["entry"] - 1) * 100, 3)
        self.log({"event": "open", "id": pos["id"], "strategy": pos.get("strategy"), **rec})
        return rec

    def remaining(self, rec):
        return float(self.ex.amount_to_precision(rec["symbol"], max(0.0, rec["contracts"] - (rec.get("t1_qty") or 0))))

    def move_stop(self, pos, rec, new_stop):
        """T1 na spotu: zrušit stop → prodat polovinu marketem → nový stop zbytku na vstup."""
        sym, base = rec["symbol"], rec["symbol"].split("/")[0]
        if rec.get("sl_id") and not self.cancel_stop(sym, rec["sl_id"]):
            return {**rec, "stopped_on_exchange": True}
        half = float(self.ex.amount_to_precision(sym, rec["contracts"] / 2))
        rec = dict(rec)
        if half > 0 and not rec.get("t1_qty"):
            o = self.settled(self.ex.create_order(sym, "market", "sell", half, None, {}), sym)
            rec.update(t1_qty=half, t1_price=o.get("average") or o.get("price"), t1_fee=round(self.fee_usdt(o, base, 0), 4))
        rest = self.remaining(rec)
        rec["sl_id"] = self.place_stop(sym, rest, new_stop) if rest > 0 else None
        rec["stop_moved"] = new_stop
        self.log({"event": "move_stop", "id": pos["id"], "symbol": sym, "stop": new_stop, "t1_qty": rec.get("t1_qty"),
                  "t1_price": rec.get("t1_price")})
        return rec

    def close(self, pos, rec, reason, paper_r=None):
        sym, base = rec["symbol"], rec["symbol"].split("/")[0]
        stopped = rec.get("stopped_on_exchange", False)
        if rec.get("sl_id") and not stopped:
            stopped = not self.cancel_stop(sym, rec["sl_id"])
        rest = 0.0 if stopped else self.remaining(rec)
        exit_fill, exit_fee = {}, 0.0
        if rest > 0:
            o = self.settled(self.ex.create_order(sym, "market", "sell", rest, None, {}), sym)
            exit_fill, exit_fee = self.fill(o), self.fee_usdt(o, base, 0)
        pnl = None
        if rec.get("entry") and (exit_fill.get("price") or rec.get("t1_price")):
            legs = [(rec["t1_qty"], float(rec["t1_price"]))] if rec.get("t1_price") else []
            if rest > 0 and exit_fill.get("price"):
                legs.append((rest, float(exit_fill["price"])))
            pnl = sum((px - float(rec["entry"])) * q for q, px in legs)
            pnl -= (rec.get("entry_fee") or 0) + (rec.get("t1_fee") or 0) + exit_fee
        out = {"event": "close", "id": pos["id"], "strategy": pos.get("strategy"), "symbol": sym, "reason": reason,
               "tp_filled": rec.get("t1_qty") or 0, "exit": exit_fill.get("price"), "stopped_on_exchange": stopped,
               "pnl_usdt": round(pnl, 2) if pnl is not None and not stopped else None, "paper_r": paper_r,
               "closed": datetime.now(timezone.utc).isoformat()}
        self.log(out)
        return out


def main():
    """Kontrola demo účtu: python3 scanner/demo.py [--market spot|swap] [--test-order]"""
    import argparse
    import yaml
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", choices=["spot", "swap"], help="výchozí podle scanner/config.yaml (demo.market)")
    ap.add_argument("--test-order", action="store_true",
                    help="malý testovací obchod na demo účtu: swap 2 kontrakty BTC, spot 0,001 BTC (vč. stopu a T1)")
    a = ap.parse_args()
    cfg = yaml.safe_load((Path(__file__).resolve().parent / "config.yaml").read_text())
    dc = {**(cfg.get("demo") or {}), **({"market": a.market} if a.market else {})}
    b = make_broker({"demo": dc})
    spot = b.market_type == "spot"
    print("demo režim:", b.ex.headers.get("x-simulated-trading") == "1", "· trh:", b.market_type, "· server:", b.ex.hostname)
    if not spot:
        print("režim pozic:", "long/short" if b.hedged() else "net")
    bal = b.ex.fetch_balance()
    q = b.quote or "USDT"
    print(f"{q}:", (bal.get(q) or {}).get("free"), "volné /", (bal.get(q) or {}).get("total"), "celkem")
    if not spot:
        try:
            pos = b.ex.fetch_positions()
            print("otevřené futures pozice:", len(pos), "(čtení swap pozic OK)")
        except Exception as exc:
            print("futures pozice:", f"{exc.__class__.__name__}: {str(exc)[:160]}")
    print("zůstatky (obchodní účet):", {k: v for k, v in (bal.get("total") or {}).items() if v})
    try:
        fund = b.ex.fetch_balance({"type": "funding"})
        print("zůstatky (Funding účet):", {k: v for k, v in (fund.get("total") or {}).items() if v})
    except Exception as exc:
        print("Funding účet:", f"{exc.__class__.__name__}: {str(exc)[:120]}")
    try:
        cfg_acc = b.ex.private_get_account_config()["data"][0]
        print("účet:", {k: cfg_acc.get(k) for k in ("acctLv", "posMode", "perm", "level", "type")})
    except Exception as exc:
        print("nastavení účtu:", f"{exc.__class__.__name__}: {str(exc)[:120]}")
    b.ex.load_markets()
    for c in ["BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"]:
        sym = spot_symbol(f"{c}/USDT", b.quote) if spot else b.resolve(f"{c}/USDT")
        if spot and sym not in b.ex.markets:
            sym = None
        if sym is None:
            print(f"  {c}: na demu není trh – vynechá se")
            continue
        try:
            m = b.ex.market(sym)
        except Exception as exc:
            print(f"  {sym}: není dostupné ({exc.__class__.__name__})")
            continue
        print(f"  {sym} ({m.get('id')}, vypořádání {m.get('settle')}): kontrakt {m.get('contractSize') or 1} {c}, min. {((m.get('limits') or {}).get('amount') or {}).get('min')}")
    coins = {"BTC", "ETH", "SOL", "XRP", "ADA", "LINK", "AVAX", "DOGE"}
    avail = sorted(f"{m['symbol']} ({m['id']})" for m in b.ex.markets.values()
                   if m.get("base") in coins and (m.get("swap") or m.get("future") or m.get("spot")))
    print("dostupné trhy pro naše mince:", ", ".join(avail) or "žádné")
    if a.test_order:
        t = b.ex.fetch_ticker(spot_symbol("BTC/USDT", b.quote) if spot else b.resolve("BTC/USDT"))["last"]
        pos = {"id": "TEST", "symbol": "BTC/USDT", "strategy": "test",
               "setup": {"direction": "long", "entry": t, "stop": t * 0.95, "targets": [t * 1.05, t * 1.1]}}
        rec = b.open(pos, {"qty": 0.001 if spot else 0.02})
        print("otevřeno:", rec)
        if spot and rec.get("status") == "open":
            rec = b.move_stop(pos, rec, t * 0.97)
            print("T1 (polovina prodána, stop zbytku posunut):", rec)
        print("uzavřeno:", b.close(pos, rec, "test") if rec.get("status") == "open" else "–")


if __name__ == "__main__":
    main()
