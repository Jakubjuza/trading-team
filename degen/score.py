"""Skóre 0–100 a vety. Váhy jsou PEVNÉ – mění se jen po testu (kalibrace v city.json), nikdy podle rady."""
import math

CHANNELS = [
    # klíč, název, váha
    ("flow", "Tlak nákupů", 20),
    ("momentum", "Tempo růstu", 15),
    ("activity", "Aktivita", 10),
    ("holders", "Rozptyl držitelů", 20),
    ("bundle", "Bez bundlů", 15),
    ("creator", "Čistý tvůrce", 10),
    ("social", "Sítě a komunita", 10),
]
ONCHAIN = {"holders", "bundle"}

VETO_BUNDLE = 0.25       # ≥ 25 % zásoby koupeno v bloku spuštění
VETO_TOP10 = 0.40        # ≥ 40 % zásoby u 10 největších držitelů
VETO_SHARED_FUNDER = 3   # ≥ 3 z 5 prvních kupců financovala stejná peněženka
VETO_SERIAL = 5          # tvůrce spustil ≥ 5 coinů za 24 h


def _lin(x, lo, hi):
    if x is None:
        return None
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


def channels(tok, mkt, chain, creator_launches):
    """Každý kanál 0..1 nebo None (chybí data)."""
    b, s = (mkt or {}).get("buys5"), (mkt or {}).get("sells5")
    flow = _lin(b / (b + s), 0.5, 0.78) if b is not None and s is not None and b + s >= 5 else None
    first = tok.get("mcap0")
    now = (mkt or {}).get("mcap")
    mom = _lin(math.log(now / first), 0, math.log(3)) if first and now else None
    act = _lin(math.log10(b + s), math.log10(20), math.log10(250)) if b is not None and s is not None and b + s > 0 else None
    chain = chain or {}
    holders = None if chain.get("top10") is None else 1 - _lin(chain["top10"], 0.15, 0.35)
    bundle = None if chain.get("bundle") is None else 1 - _lin(chain["bundle"], 0.0, 0.20)
    creator = 1 - _lin(creator_launches, 0, 3) if creator_launches is not None else None
    if creator is not None and chain.get("dev") is not None and chain["dev"] > 0.10:
        creator *= 0.5
    soc = sum(bool(tok.get(k) or (mkt or {}).get(k)) for k in ("twitter", "telegram", "website")) / 3
    soc = min(1.0, soc + min(0.3, (tok.get("replies") or 0) / 100))
    return {"flow": flow, "momentum": mom, "activity": act, "holders": holders, "bundle": bundle,
            "creator": creator, "social": soc}


def vetoes(chain, creator_launches):
    v = []
    chain = chain or {}
    if chain.get("bundle") is not None and chain["bundle"] >= VETO_BUNDLE:
        v.append(f"bundly {chain['bundle'] * 100:.0f} % zásoby v bloku spuštění")
    if chain.get("top10") is not None and chain["top10"] >= VETO_TOP10:
        v.append(f"top 10 drží {chain['top10'] * 100:.0f} %")
    f = chain.get("funders") or {}
    if f.get("shared_max", 0) >= VETO_SHARED_FUNDER:
        v.append(f"{f['shared_max']} první kupci mají stejného financovatele")
    if f.get("creator_funded"):
        v.append("tvůrce financoval první kupce")
    if creator_launches is not None and creator_launches >= VETO_SERIAL:
        v.append(f"sériový tvůrce ({creator_launches} coinů/24 h)")
    return v


def total(ch):
    """→ (skóre 0–100, úplné?) Chybějící kanál = 0,5 (neutrální); úplné jen s on-chain kanály."""
    sc = 0.0
    complete = True
    for k, _, w in CHANNELS:
        x = ch.get(k)
        if x is None:
            x = 0.5
            if k in ONCHAIN or k in ("flow", "momentum"):
                complete = False
        sc += w * x
    return round(sc), complete
