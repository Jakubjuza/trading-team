#!/usr/bin/env python3
"""Předpovědi modelu Kronos pro strategii Downtownu „Kronos ×10“ (jen papír, oddělené od desku).

Doplňuje research/downtown_kronos.csv.gz o předpověď close další 2H svíčky pro každou uzavřenou 2H svíčku
od 1. 9. 2025, která v souboru ještě chybí. Nastavení stejné jako test v research/experiments/kronos_test.py
(Kronos-small, kontext 512 svíček, T = 1,0, top_p = 0,9, 5 vzorků, seed 0) – jen data do close svíčky t,
nic z budoucnosti. Starší předpovědi z testu (6. 11. 2026) se nepřepočítávají.

    python3 research/downtown_kronos.py <cache_dir> <kronos_repo_dir> [max_novych]
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from research import downtown as D  # noqa: E402

PRED = ROOT / "research" / "downtown_kronos.csv.gz"
COINS = ["BTC", "ETH", "SOL"]
START = "2025-09-01"
CTX, BATCH, SAMPLES = 512, 16, 5


def load():
    if not PRED.exists():
        return pd.DataFrame(columns=["coin", "t", "close", "pred_close"])
    return pd.read_csv(PRED)


def main(cache, kronos_dir, max_new=600):
    import torch
    sys.path.insert(0, kronos_dir)
    from model import Kronos, KronosPredictor, KronosTokenizer
    torch.manual_seed(0)
    old = load()
    have = set(zip(old["coin"], pd.to_datetime(old["t"], utc=True)))
    todo = []
    frames = {}
    for c in COINS:
        d = D.resample(D.fetch(c, "1h", cache), "2h").rename(columns=str.lower)
        d["amount"] = d["volume"] * d[["open", "high", "low", "close"]].mean(axis=1)
        frames[c] = d
        for i in range(CTX, len(d)):
            t = d.index[i]
            if t >= pd.Timestamp(START, tz="UTC") and (c, t) not in have:
                todo.append((c, i))
    todo = todo[-int(max_new):]
    print(f"Kronos: chybí {len(todo)} předpovědí", flush=True)
    if not todo:
        return
    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    mdl = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    tok.eval(); mdl.eval()
    pr = KronosPredictor(mdl, tok, device="cpu", max_context=CTX)
    rows = []
    for k in range(0, len(todo), BATCH):
        chunk = todo[k:k + BATCH]
        dfs = [frames[c].iloc[i - CTX + 1:i + 1][["open", "high", "low", "close", "volume", "amount"]].reset_index(drop=True) for c, i in chunk]
        xs = [pd.Series(frames[c].index[i - CTX + 1:i + 1]).dt.tz_localize(None) for c, i in chunk]
        ys = [pd.Series([frames[c].index[i] + pd.Timedelta("2h")]).dt.tz_localize(None) for c, i in chunk]
        out = pr.predict_batch(dfs, xs, ys, pred_len=1, T=1.0, top_p=0.9, sample_count=SAMPLES, verbose=False)
        for (c, i), p in zip(chunk, out):
            rows.append({"coin": c, "t": frames[c].index[i].isoformat(), "close": float(frames[c]["close"].iloc[i]),
                         "pred_close": float(p["close"].iloc[0])})
    new = pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(["coin", "t"], keep="first")
    new.sort_values(["coin", "t"]).to_csv(PRED, index=False)
    print(f"Kronos: přidáno {len(rows)} předpovědí", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or []))
