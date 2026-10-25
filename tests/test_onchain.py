"""On-chain sekce – odpovědi API napodobené (sandbox je blokuje)."""
from research import onchain as oc


def fake_get(url):
    if "alternative.me" in url:
        return {"data": [{"value": str(20 + i), "value_classification": "Extreme Fear" if i == 0 else "Fear"} for i in range(31)]}
    if "stablecoincharts" in url:
        return [{"date": str(i), "totalCirculatingUSD": {"peggedUSD": 300e9 + i * 1e9}} for i in range(40)]
    if "historicalChainTvl/Solana" in url:
        return [{"date": i, "tvl": 10e9 - i * 0.1e9} for i in range(40)]
    if "hash-rate" in url:
        return {"values": [{"x": i, "y": 600e6 + i * 1e6} for i in range(60)]}
    if "n-transactions" in url:
        return {"values": [{"x": i, "y": 400000} for i in range(60)]}
    if "mempool" in url:
        return {"fastestFee": 5, "halfHourFee": 3, "hourFee": 2}
    raise ConnectionError("blocked")


def test_onchain_btc_and_sol():
    btc = oc.section_onchain("BTC", fake_get)
    assert btc["fear_greed"]["value"] == 20 and btc["fear_greed"]["week_ago"] == 27
    assert btc["stablecoins"]["total_usd_bn"] == 339.0 and btc["stablecoins"]["chg_7d_pct"] > 0
    assert btc["btc_network"]["hashrate_ehs"] == 659.0 and btc["btc_network"]["tx_chg_30d_pct"] == 0.0
    assert "chain_tvl" not in btc
    sol = oc.section_onchain("SOL", fake_get)
    assert sol["chain_tvl"]["chain"] == "Solana" and sol["chain_tvl"]["chg_7d_pct"] < 0 and "btc_network" not in sol


def test_onchain_partial_failure():
    def get(url):
        if "alternative.me" in url:
            raise ConnectionError("down")
        return fake_get(url)
    d = oc.section_onchain("ETH", get)
    assert "error" in d["fear_greed"] and "error" in d["chain_tvl"] and "error" not in d["stablecoins"]
