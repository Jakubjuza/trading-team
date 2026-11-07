#!/usr/bin/env python3
"""Downtown výzkum režimů – stažení dat (jen pro větev claude/downtown-regimes, ne pro main).

Sandbox nedosáhne na burzy, proto Actions stáhne hodinové a 15m svíčky OKX (stejná funkce jako research/downtown.py)
a historii Fear & Greed (alternative.me) a uloží je jako .csv.gz do data_dt/ na výzkumné větvi.

    python3 research/experiments/downtown_data.py /tmp/dt_cache data_dt
"""
import json
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research import downtown as D  # noqa: E402

# 8 mincí Downtownu + likvidní alty pro rotace a koše (listované později mají prostě kratší historii)
COINS_1H = D.COINS + ["BNB", "LTC", "BCH", "DOT", "TRX", "NEAR", "APT", "ARB", "OP", "SUI", "INJ", "PEPE", "WIF", "TON", "UNI", "AAVE"]
COINS_15M = ["BTC", "ETH", "SOL"]


def main(cache, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for c in COINS_1H:
        print("1h", c, flush=True)
        try:
            df = D.fetch(c, "1h", cache)
            df.to_csv(out / f"{c}_1h.csv.gz", compression="gzip")
            print("  ", len(df), df.index[0], df.index[-1], flush=True)
        except Exception as exc:  # noqa: BLE001
            print("  chyba", exc, flush=True)
    for c in COINS_15M:
        print("15m", c, flush=True)
        df = D.fetch(c, "15m", cache)
        df.to_csv(out / f"{c}_15m.csv.gz", compression="gzip")
    with urllib.request.urlopen("https://api.alternative.me/fng/?limit=0&format=json", timeout=30) as r:
        fg = json.load(r)["data"]
    (out / "fng.json").write_text(json.dumps(fg), encoding="utf-8")
    shutil.copy(ROOT / "research" / "downtown_kronos.csv.gz", out / "kronos.csv.gz")


if __name__ == "__main__":
    main(*sys.argv[1:3])
