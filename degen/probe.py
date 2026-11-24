"""Diagnostika zdrojů (spouští se jen v testovacím běhu na větvi): bezpečnost a pitva na pár coinech z city.json."""
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from degen import postmortem, safety, sources  # noqa: E402


def main():
    city = json.loads((Path(__file__).parent / "city.json").read_text())
    st = {}
    rpc = sources.Rpc(st)
    mints = [f["mint"] for f in city.get("feed", [])[:2]] + [t["mint"] for a in city.get("accounts", []) for t in a.get("trades", [])][:2]
    extra = [m for m in os.environ.get("DEGEN_PROBE_MINTS", "").split(",") if m]
    mints = extra or mints
    for m in mints:
        mk = sources.dex_tokens([m]).get(m)
        print("TRH", m, json.dumps(mk, ensure_ascii=False)[:600])
        tok = {"mint": m, "mkt": mk, "hist": [], "chain": {}}
        s = safety.check(rpc, tok)
        print("BEZPEČNOST", m, json.dumps({k: s[k] for k in ("checked", "vetoes", "dev_hold", "danger")}, ensure_ascii=False),
              "rugcheck", json.dumps(s["rugcheck"], ensure_ascii=False)[:300])
        p = postmortem.run(rpc, tok, n_tx=15)
        print("PITVA", m, json.dumps(p, ensure_ascii=False))
    print("RPC", rpc.b, sources.STATUS)


if __name__ == "__main__":
    main()
