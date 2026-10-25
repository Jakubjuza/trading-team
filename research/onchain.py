#!/usr/bin/env python3
"""On-chain a sentiment data zdarma, bez API klíče – sekce `onchain` datového listu.

  • Fear & Greed Index (alternative.me): dnes, před týdnem, 30denní průměr,
  • stablecoiny celkem (DefiLlama): oběh v USD, změna 7 a 30 dní = přítok/odtok „suchého prachu“ do krypta,
  • TVL blockchainu mince (DefiLlama): změna 7 a 30 dní – kapitál v DeFi na dané síti (ETH, SOL, AVAX …),
  • síť bitcoinu (blockchain.com, mempool.space): hashrate (změna 30 dní), počet transakcí, poplatky.

Ze sandboxu jsou zdroje blokované; běží v GitHub Actions (datový list ke každému signálu).
Interpretaci dělá sentiment-analyst (toky, nálada) – čísla jsou pomalý kontext, ne vstupní signál.
"""
from datetime import datetime, timezone

FNG = "https://api.alternative.me/fng/?limit=31&format=json"
STABLES = "https://stablecoins.llama.fi/stablecoincharts/all"
CHAIN_TVL = "https://api.llama.fi/v2/historicalChainTvl/{chain}"
BTC_CHART = "https://api.blockchain.info/charts/{name}?timespan=60days&format=json&sampled=false"
MEMPOOL_FEES = "https://mempool.space/api/v1/fees/recommended"
CHAINS = {"ETH": "Ethereum", "SOL": "Solana", "AVAX": "Avalanche", "ADA": "Cardano", "BNB": "BSC",
          "XRP": "XRPL", "LINK": None, "DOGE": None, "BTC": None}


def _get_json(url, timeout=10):
    import requests
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (trading-team research)"}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _pct(new, old):
    return None if not old else round((new / old - 1) * 100, 2)


def _err(exc):
    return {"error": f"{exc.__class__.__name__}: {str(exc)[:120]}"}


def fear_greed(get=_get_json):
    rows = get(FNG)["data"]                                              # nejnovější první
    vals = [int(r["value"]) for r in rows]
    return {"value": vals[0], "label": rows[0].get("value_classification"),
            "week_ago": vals[7] if len(vals) > 7 else None,
            "avg_30d": round(sum(vals[:30]) / min(30, len(vals)), 1), "source": "alternative.me"}


def stablecoins(get=_get_json):
    rows = get(STABLES)
    tot = [float(r["totalCirculatingUSD"]["peggedUSD"]) for r in rows if r.get("totalCirculatingUSD", {}).get("peggedUSD")]
    now = tot[-1]
    return {"total_usd_bn": round(now / 1e9, 1), "chg_7d_pct": _pct(now, tot[-8]) if len(tot) > 8 else None,
            "chg_30d_pct": _pct(now, tot[-31]) if len(tot) > 31 else None,
            "chg_7d_usd_bn": round((now - tot[-8]) / 1e9, 2) if len(tot) > 8 else None, "source": "DefiLlama"}


def chain_tvl(chain, get=_get_json):
    rows = get(CHAIN_TVL.format(chain=chain))
    tvl = [float(r["tvl"]) for r in rows]
    now = tvl[-1]
    return {"chain": chain, "tvl_usd_bn": round(now / 1e9, 2), "chg_7d_pct": _pct(now, tvl[-8]) if len(tvl) > 8 else None,
            "chg_30d_pct": _pct(now, tvl[-31]) if len(tvl) > 31 else None, "source": "DefiLlama"}


def btc_network(get=_get_json):
    out = {"source": "blockchain.com, mempool.space"}
    hr = [v["y"] for v in get(BTC_CHART.format(name="hash-rate"))["values"]]
    out["hashrate_ehs"] = round(hr[-1] / 1e6, 1)                         # TH/s → EH/s
    out["hashrate_chg_30d_pct"] = _pct(sum(hr[-7:]) / 7, sum(hr[-37:-30]) / 7) if len(hr) >= 37 else None
    tx = [v["y"] for v in get(BTC_CHART.format(name="n-transactions"))["values"]]
    out["tx_per_day_7d_avg"] = int(sum(tx[-7:]) / 7)
    out["tx_chg_30d_pct"] = _pct(sum(tx[-7:]) / 7, sum(tx[-37:-30]) / 7) if len(tx) >= 37 else None
    try:
        out["fees_sat_vb"] = get(MEMPOOL_FEES)
    except Exception as exc:
        out["fees_sat_vb"] = _err(exc)
    return out


def section_onchain(coin, get=_get_json):
    """Každá podsekce zvlášť – výpadek jednoho zdroje neshodí ostatní."""
    out = {"source": "alternative.me, DefiLlama, blockchain.com, mempool.space",
           "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    parts = {"fear_greed": lambda: fear_greed(get), "stablecoins": lambda: stablecoins(get)}
    if CHAINS.get(coin):
        parts["chain_tvl"] = lambda: chain_tvl(CHAINS[coin], get)
    if coin == "BTC":
        parts["btc_network"] = lambda: btc_network(get)
    for k, fn in parts.items():
        try:
            out[k] = fn()
        except Exception as exc:
            out[k] = _err(exc)
    out["note"] = ("Pomalý kontext (dny až týdny): růst stablecoinů = přítok kapitálu, extrémní strach/chamtivost = "
                   "kontrariánský kontext, ne signál ke vstupu.")
    return out


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(section_onchain(sys.argv[1] if len(sys.argv) > 1 else "BTC"), ensure_ascii=False, indent=1))
