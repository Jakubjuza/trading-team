"""Rozhraní pro zadání příkazu. Výchozí stav: jen papírový režim, nic se neodesílá.

Ostrý příkaz projde jen když platí VŠE:
  - config `live_trading: true`,
  - volající předá `confirm=True` (výslovné potvrzení uživatele pro tento konkrétní příkaz),
  - existuje implementace pro burzu/brokera (zatím žádná → NotImplementedError).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

PAPER_LOG = Path(__file__).resolve().parent / "paper_trades.json"


class LiveTradingDisabled(RuntimeError):
    pass


def place_order(order, config, confirm=False, paper_log=PAPER_LOG):
    """order: {symbol, side ('buy'|'sell'), qty, entry, stop, targets, setup_id}.

    Vrací záznam o příkazu. V papírovém režimu jen zapíše do paper_trades.json.
    """
    live = bool(config.get("live_trading", False))
    if not live:
        return _paper(order, paper_log)
    if not confirm:
        raise LiveTradingDisabled("live_trading je zapnuté, ale chybí výslovné potvrzení (confirm=True). Nic neodesláno.")
    raise NotImplementedError("Ostré obchodování zatím není implementované. Nic neodesláno.")


def _paper(order, paper_log):
    paper_log = Path(paper_log)
    trades = json.loads(paper_log.read_text()) if paper_log.exists() else []
    rec = {**order, "mode": "paper", "status": "open", "time": datetime.now(timezone.utc).isoformat()}
    trades.append(rec)
    paper_log.write_text(json.dumps(trades, ensure_ascii=False, indent=2) + "\n")
    return rec
