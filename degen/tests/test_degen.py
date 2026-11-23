import json

import pytest

from degen import city, onchain, paper, postmortem, safety, score, sources

MINT = "MiNT1111111111111111111111111111111111111pump"


def tx(slot, signer, deltas, err=None):
    pre, post = [], []
    for i, (owner, (a, b)) in enumerate(deltas.items()):
        pre.append({"accountIndex": i, "mint": MINT, "owner": owner, "uiTokenAmount": {"uiAmount": a}})
        post.append({"accountIndex": i, "mint": MINT, "owner": owner, "uiTokenAmount": {"uiAmount": b}})
    return {"slot": slot, "blockTime": 1700000000 + slot,
            "transaction": {"message": {"accountKeys": [{"pubkey": signer, "signer": True}]}},
            "meta": {"err": err, "preTokenBalances": pre, "postTokenBalances": post}}


def test_early_flow_bundle_and_buyers():
    txs = [
        tx(100, "DEV", {"CURVE": (0, 9.3e8), "DEV": (0, 5e7)}),           # vytvoření + nákup tvůrce
        tx(100, "B1", {"CURVE": (9.3e8, 8.3e8), "B1": (0, 1e8)}),         # bundl ve stejném bloku
        tx(105, "B2", {"CURVE": (8.3e8, 8.1e8), "B2": (0, 2e7)}),
        tx(106, "B1", {"CURVE": (8.1e8, 8.6e8), "B1": (1e8, 5e7)}),       # prodej – není kupec
    ]
    flow = onchain.early_flow([onchain.parse_tx(t, MINT) for t in txs], "DEV")
    assert flow["curve_owner"] == "CURVE"
    assert flow["bundle_share"] == pytest.approx(0.15)
    assert flow["dev_share"] == pytest.approx(0.05)
    assert [b["w"] for b in flow["buyers"]] == ["B1", "B2"]
    assert flow["bundled_wallets"] == 1


def test_failed_tx_ignored():
    assert onchain.parse_tx(tx(1, "X", {"X": (0, 1)}, err={"x": 1}), MINT) is None


def test_holder_share_drops_vault():
    largest = [{"address": "VAULT", "amount": 7e8}] + [{"address": f"H{i}", "amount": 1e7} for i in range(12)]
    share, dropped = onchain.holder_share(largest, 1e9)
    assert dropped == ["VAULT"] and share == pytest.approx(0.10)
    share2, _ = onchain.holder_share(largest, 1e9, exclude={"VAULT"})
    assert share2 == pytest.approx(0.10)


def test_funder_detection_and_stats():
    t = {"transaction": {"message": {"instructions": [
        {"parsed": {"type": "transfer", "info": {"source": "FUNDER", "destination": "W1", "lamports": 5_000_000}}}]}},
        "meta": {"innerInstructions": []}}
    assert onchain.funder_of(t, "W1") == "FUNDER"
    st = onchain.funder_stats({"a": "F", "b": "F", "c": "F", "d": None, "e": "DEV"}, "DEV")
    assert st["shared_max"] == 3 and st["creator_funded"]
    assert len(score.vetoes({"funders": st}, 0)) == 2


def test_score_complete_and_veto():
    tok = {"mcap0": 5000, "twitter": True, "telegram": True, "website": True, "replies": 50}
    mkt = {"buys5": 160, "sells5": 40, "mcap": 15000}
    chain = {"top10": 0.12, "bundle": 0.0, "dev": 0.02}
    s, complete = score.total(score.channels(tok, mkt, chain, 0))
    assert complete and s >= 95
    s2, complete2 = score.total(score.channels(tok, mkt, None, 0))
    assert not complete2 and s2 < s
    assert score.vetoes({"bundle": 0.3, "top10": 0.5}, 6) and len(score.vetoes({"bundle": 0.3, "top10": 0.5}, 6)) == 3


def test_paper_fill_tp_trailing():
    acc = paper.new_account("filtr")
    assert paper.order(acc, MINT, "FROG", "filtr", {"mcap": 10000}, now=0)
    assert not paper.order(acc, MINT, "FROG", "filtr", {"mcap": 10000}, now=1)       # duplicita
    paper.fill_pending(acc, {MINT: {"mcap": 10000, "liq": None}}, now=30)
    p = acc["open"][MINT]
    assert p["entry_mcap"] > 10000                                                     # poplatek + skluz
    paper.manage(acc, {MINT: {"mcap": 25000}}, "filtr", now=60)                         # +150 % → ½ prodáno
    assert p["tp1"] and p["remaining"] == pytest.approx(0.5)
    closed = paper.manage(acc, {MINT: {"mcap": 15000}}, "filtr", now=90)                # −40 % od vrcholu → trailing
    assert closed and closed[0]["why"] == "trailing" and closed[0]["pnl"] > 0
    assert acc["n"] == 1 and acc["wins"] == 1 and not acc["open"]
    assert not paper.order(acc, MINT, "FROG", "filtr", {"mcap": 10000}, now=100)     # už obchodováno


def test_paper_stop_and_stale():
    acc = paper.new_account("opice")
    paper.order(acc, "A", "A", "opice", {"mcap": 10000}, now=0)
    paper.order(acc, "B", "B", "opice", {"mcap": 10000}, now=0)
    paper.fill_pending(acc, {"A": {"mcap": 10000}, "B": {"mcap": 10000}}, now=10)
    c1 = paper.manage(acc, {"A": {"mcap": 5000}}, "opice", now=20)
    assert c1[0]["why"] == "stop" and c1[0]["ret"] < -50
    c2 = paper.manage(acc, {}, "opice", now=10 + paper.STALE_EXIT + 1)
    assert c2[0]["why"] == "bez dat" and c2[0]["ret"] < -70
    assert acc["cash"] < paper.START


def test_run_once_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(city, "STATE", tmp_path / "state.json")
    monkeypatch.setattr(city, "PERSIST", tmp_path / "persist.json")
    monkeypatch.setattr(city, "CITY", tmp_path / "city.json")
    monkeypatch.setattr(city, "TRADES", tmp_path / "trades.jsonl")
    now = 1_800_000_000
    coin = {"mint": MINT, "name": "Frog", "symbol": "FROG", "creator": "DEV", "created": now - 200, "twitter": True,
            "telegram": True, "website": True, "replies": 40, "complete": False, "mcap_usd": 6000, "curve_ata": None,
            "image": None, "src": "pump"}
    mkt = {"mcap": 14000, "price": 1.4e-5, "liq": None, "buys5": 150, "sells5": 30, "vol5": 9000, "vol1h": 20000,
           "dex": "pumpfun", "dexes": ["pumpfun"], "graduated": False, "grad_at": None, "created": now - 200,
           "symbol": "FROG", "name": "Frog", "twitter": True, "telegram": True, "website": True}
    monkeypatch.setattr(sources, "pump_latest", lambda: [dict(coin)])
    monkeypatch.setattr(sources, "gecko_new", lambda pages=1: [])
    seq = iter([7000, 21000, 22000])
    monkeypatch.setattr(sources, "dex_tokens", lambda mints: {MINT: dict(mkt, mcap=next(seq))} if MINT in mints else {})
    monkeypatch.setattr(onchain, "analyze", lambda rpc, t, with_funders=True, deadline=None: {
        "top10": 0.12, "bundle": 0.01, "dev": 0.02, "buyers": [{"w": "W1", "slot": 1, "amt": 1}], "creator": "DEV",
        "funders": {"shared_max": 1, "creator_funded": False}})
    monkeypatch.setattr(city.tg, "send", lambda *a, **k: True)
    monkeypatch.setattr(safety, "check", lambda rpc, t, with_rugcheck=True: {"checked": True, "vetoes": [], "danger": []})
    monkeypatch.setattr(postmortem, "run", lambda rpc, t, n_tx=30, deadline=None: {
        "cause": "dev", "text": "x", "sellers": 1, "dev_share": 1, "insider_share": 0, "top_share": 1, "liq_drop": None, "tx": 3})
    c1 = city.run_once(dry=True, now=now)
    assert c1["stack"][0]["verdict"] == "SKIP"            # tempo zatím 0 → pod 85
    c2 = city.run_once(dry=True, now=now + 30)             # MC 3× → skóre ≥ 85 → příkaz
    acc = {a["key"]: a for a in c2["accounts"]}
    assert acc["filtr"]["pending"] == 1
    c3 = city.run_once(dry=True, now=now + 60)
    acc = {a["key"]: a for a in c3["accounts"]}
    assert len(acc["filtr"]["open"]) == 1 and acc["filtr"]["cash"] < paper.START
    json.dumps(c3)
    assert (tmp_path / "persist.json").exists()


def test_safety_mint_vetoes():
    info = {"value": {"owner": safety.TOKEN_2022, "data": {"parsed": {"info": {
        "mintAuthority": None, "freezeAuthority": "DEV",
        "extensions": [{"extension": "permanentDelegate"}, {"extension": "transferFeeConfig",
                        "state": {"newerTransferFee": {"transferFeeBasisPoints": 900}}}, {"extension": "metadataPointer"}]}}}}}
    m = safety.parse_mint(info)
    v = safety.mint_vetoes(m)
    assert any("freeze" in x for x in v) and any("delegát" in x for x in v) and any("poplatek" in x for x in v)
    clean = safety.parse_mint({"value": {"data": {"parsed": {"info": {"mintAuthority": None, "freezeAuthority": None}}}}})
    assert safety.mint_vetoes(clean) == []


def test_safety_lp_only_outside_pump():
    rc = {"lp_locked": 0.0, "risks": []}
    graduated = {"graduated": True, "dexes": ["raydium"]}
    assert safety.lp_vetoes("AbcRaydiumToken111", graduated, rc)
    assert safety.lp_vetoes("Abc111pump", graduated, rc) == []                       # pump.fun: LP spálené
    assert safety.lp_vetoes("AbcRaydiumToken111", graduated, {"lp_locked": 100.0}) == []


def test_postmortem_classify_dev_and_pool():
    mk = lambda d: {"slot": 1, "time": 1, "signer": "x", "deltas": d}  # noqa: E731
    txs = [mk({"POOL": (1e7), "DEV": -1e7}), mk({"POOL": 5e6, "DEV": -5e6}), mk({"POOL": 1e6, "A": -1e6}),
           mk({"POOL": -2e6, "B": 2e6})]
    r = postmortem.classify(txs, "DEV", set())
    assert r["cause"] == "dev" and r["sellers"] == 2
    r2 = postmortem.classify(txs, "ZZZ", {"DEV"})
    assert r2["cause"] == "insider"
    r3 = postmortem.classify(txs, "DEV", set(), liq_hist=[50000, 48000, 3000], pump_origin=False)
    assert r3["cause"] == "lp"


def test_postmortem_learns_veto():
    xs = [{"crash": True, "f": {"dev5": True}} for _ in range(45)] + [{"crash": False, "f": {"dev5": True}} for _ in range(5)]
    xs += [{"crash": i % 2 == 0, "f": {"dev5": False}} for i in range(150)]
    p0, n0, table = postmortem.learn(xs)
    row = next(r for r in table if r["key"] == "dev5")
    assert row["state"] == "veto" and n0 == 200
    assert postmortem.learned_vetoes(table, {"dev5": True})
    assert postmortem.learned_vetoes(table, {"dev5": False}) == []
    tok = {"score_mcap": 10000, "analyzed": 100, "hist": [[120, 9000, None], [200, 2500, None]]}
    assert postmortem.crash_label(tok, 300) is True
