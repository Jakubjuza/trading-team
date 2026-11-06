"""Kronos (open-source „foundation model“ pro svíčky) – umí předpovědět další 2H svíčku krypta?

Podnět: virální příspěvek (getintoai, 6. 11. 2026) o dashboardu, který předpovídá 2hodinové svíčky modelem Kronos.
Model: Kronos, arXiv 2508.02739 (AAAI 2026), https://github.com/shiyu-coder/Kronos (commit 67b630e),
váhy NeoQuasar/Kronos-small (24,7 M parametrů) + NeoQuasar/Kronos-Tokenizer-base z Hugging Face.

Stanoveno PŘEDEM (6. 11. 2026), nic se po spuštění neladí:

  Data: hodinové svíčky OKX spot USDT, přeskupené na 2H; mince BTC, ETH, SOL.
  Testované období: od 1. 9. 2025 do poslední uzavřené svíčky. Model i váhy vyšly v srpnu 2025, takže tyto
        svíčky nemohl vidět při tréninku (předpoklad: tréninková data nejsou novější než zveřejnění).
  Předpověď: na close každé 2H svíčky t vezme model posledních 512 svíček (max. kontext Kronos-small),
        pred_len = 1, T = 1,0, top_p = 0,9, sample_count = 5 (průměr), torch seed 0.
        pred_ret = předpovězený close(t+1) / close(t) − 1.
  Skutečnost: vstup na open(t+1), výstup na close(t+1); ret = close(t+1) / open(t+1) − 1.
  Směr: hit = sign(pred_ret) == sign(close(t+1) − close(t)); srovnání s 50 %, s „momentem“
        (sign posledního výnosu) a s „vždy nahoru“. Binomický test proti 50 %.
  Chyba: MAE předpovězeného výnosu vs. MAE nulové předpovědi (náhodná procházka).
  Obchody: náklady 0,15 % na stranu (poplatek + skluz, jako atlas), tj. 0,30 % za obchod.
        A – každou svíčku long/short podle znaménka pred_ret,
        B – jen když |pred_ret| > 0,30 % (předpověď větší než náklady).
        Náhoda: stejné svíčky, stejný počet longů a shortů, náhodně prohozené směry (2000×).
  Stabilita: první × druhá polovina testovaného období (dělí se datem uprostřed).
  PROJDE jen když (vše dohromady za 3 mince):
        úspěšnost směru ≥ 52 % s p < 0,01, lepší než moment i „vždy nahoru“,
        a B má Ø čistý výnos > 0 s t ≥ 2, kladný v obou polovinách a nad 95. percentilem náhody.
  Jinak NEPROJDE (pro náš desk bez použití). Jde jen o výzkum, na peníze ani skener se nesahá.

Použití:  kronos_test.py predict COIN OUT.csv KRONOS_DIR   |   kronos_test.py report CSV [CSV ...]
"""
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

TEST_START = "2025-09-01"
DATA_START = "2025-03-01"          # rezerva na 512 svíček kontextu (2H ≈ 43 dní) i výpadky
CTX, BATCH, SAMPLES = 512, 16, 5
COST = 0.0015                      # na stranu
BUDGET_S = float(os.environ.get("KRONOS_BUDGET_S", 4.6 * 3600))
OUT_REPORT = Path(__file__).resolve().parents[2] / "reports" / "kronos.md"


def fetch_1h(coin, start):
    import ccxt
    ex = ccxt.okx({"enableRateLimit": True})
    step = 3_600_000
    since = int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    end = int(datetime.now(timezone.utc).timestamp() * 1000)
    rows, errs = [], 0
    while since < end:
        try:
            batch = ex.fetch_ohlcv(f"{coin}/USDT", "1h", since=since, limit=100)
        except Exception as exc:  # noqa: BLE001
            errs += 1
            print(f"  {coin} {pd.Timestamp(since, unit='ms')}: {exc.__class__.__name__}", flush=True)
            if errs > 50:
                raise
            time.sleep(3)
            continue
        if not batch:
            since += 100 * step
            continue
        rows += batch
        nxt = batch[-1][0] + step
        since = nxt if nxt > since else since + 100 * step
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).drop_duplicates("ts")
    df.index = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
    return df.sort_index()


def to_2h(h1):
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    d = h1.resample("2h").agg(agg).dropna()
    return d[d.index + pd.Timedelta("2h") <= datetime.now(timezone.utc)]


def predict(coin, out, kronos_dir):
    import torch
    sys.path.insert(0, kronos_dir)
    from model import Kronos, KronosPredictor, KronosTokenizer
    torch.manual_seed(0)
    torch.set_num_threads(os.cpu_count() or 2)
    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    mdl = Kronos.from_pretrained("NeoQuasar/Kronos-small")
    tok.eval(); mdl.eval()
    pr = KronosPredictor(mdl, tok, device="cpu", max_context=CTX)

    d = to_2h(fetch_1h(coin, DATA_START))
    d["amount"] = d["volume"] * d[["open", "high", "low", "close"]].mean(axis=1)
    idx = [i for i in range(CTX, len(d) - 1) if d.index[i] >= pd.Timestamp(TEST_START, tz="UTC")]
    print(f"{coin}: {len(d)} svíček 2H, {len(idx)} předpovědí", flush=True)
    t0, rows = time.time(), []
    for k in range(0, len(idx), BATCH):
        if time.time() - t0 > BUDGET_S:
            print(f"  časový rozpočet vyčerpán po {len(rows)} předpovědích", flush=True)
            break
        chunk = idx[k:k + BATCH]
        dfs = [d.iloc[i - CTX + 1:i + 1].reset_index(drop=True) for i in chunk]
        xs = [pd.Series(d.index[i - CTX + 1:i + 1]).dt.tz_localize(None) for i in chunk]
        ys = [pd.Series([d.index[i + 1]]).dt.tz_localize(None) for i in chunk]
        preds = pr.predict_batch(dfs, xs, ys, pred_len=1, T=1.0, top_p=0.9, sample_count=SAMPLES, verbose=False)
        for i, p in zip(chunk, preds):
            c0 = d["close"].iloc[i]
            rows.append({"coin": coin, "t": d.index[i].isoformat(), "close": c0, "pred_close": float(p["close"].iloc[0]),
                         "prev_close": d["close"].iloc[i - 1], "next_open": d["open"].iloc[i + 1],
                         "next_close": d["close"].iloc[i + 1]})
        if (k // BATCH) % 20 == 0:
            el = time.time() - t0
            print(f"  {len(rows)}/{len(idx)}  {el/60:.1f} min", flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{coin}: hotovo {len(rows)} předpovědí za {(time.time()-t0)/60:.1f} min", flush=True)


def binom_p(k, n):
    """jednostranné p (k úspěchů z n proti 50 %), normální aproximace"""
    if n == 0:
        return float("nan")
    z = (k - n / 2) / math.sqrt(n / 4)
    return 0.5 * math.erfc(z / math.sqrt(2))


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def stats(df, rng):
    pr = df["pred_close"] / df["close"] - 1
    act = np.sign(df["next_close"] - df["close"])
    mom = np.sign(df["close"] - df["prev_close"])
    ret = df["next_close"] / df["next_open"] - 1
    valid = act != 0
    hit = (np.sign(pr) == act)[valid]
    out = {"n": int(len(df)), "hit": hit.mean(), "p": binom_p(int(hit.sum()), int(valid.sum())),
           "mom": (mom == act)[valid].mean(), "up": (act[valid] > 0).mean(),
           "mae_ratio": (pr - (df["next_close"] / df["close"] - 1)).abs().mean() / (df["next_close"] / df["close"] - 1).abs().mean(),
           "pred_abs": pr.abs().median()}
    for name, mask in (("A", pr != 0), ("B", pr.abs() > 2 * COST)):
        side = np.sign(pr[mask]).to_numpy()
        r = ret[mask].to_numpy()
        net = side * r - 2 * COST
        rnd = []
        for _ in range(2000):
            s = rng.permutation(side)
            rnd.append((s * r - 2 * COST).mean())
        out[name] = {"n": int(mask.sum()), "mean": net.mean() * 100 if len(net) else float("nan"),
                     "t": tstat(net), "sum": net.sum() * 100, "gross": (side * r).mean() * 100 if len(net) else float("nan"),
                     "p95": np.percentile(rnd, 95) * 100 if len(net) else float("nan"),
                     "win": (net > 0).mean() if len(net) else float("nan")}
    return out


def pct(x, d=1):
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x*100:.{d}f} %".replace(".", ",")


def num(x, d=3):
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.{d}f}".replace(".", ",").replace("-", "−")


def report(paths):
    df = pd.concat([pd.read_csv(p) for p in paths if Path(p).exists() and Path(p).stat().st_size > 0], ignore_index=True)
    df["t"] = pd.to_datetime(df["t"], utc=True)
    rng = np.random.default_rng(0)
    mid = df["t"].min() + (df["t"].max() - df["t"].min()) / 2
    groups = [(c, df[df.coin == c]) for c in sorted(df.coin.unique())] + [("Vše", df), ("1. polovina", df[df.t < mid]), ("2. polovina", df[df.t >= mid])]
    S = {g: stats(x, rng) for g, x in groups if len(x) > 10}
    a = S["Vše"]
    b, h1, h2 = a["B"], S.get("1. polovina", {}).get("B", {}), S.get("2. polovina", {}).get("B", {})
    passed = (a["hit"] >= 0.52 and a["p"] < 0.01 and a["hit"] > a["mom"] and a["hit"] > a["up"]
              and b["n"] > 0 and b["mean"] > 0 and b["t"] >= 2 and h1.get("mean", -1) > 0 and h2.get("mean", -1) > 0
              and b["mean"] > b["p95"])
    L = ["# Kronos – předpověď další 2H svíčky (BTC, ETH, SOL)", "",
         f"Vygenerováno {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC skriptem `research/experiments/kronos_test.py` (pravidla stanovená předem jsou v jeho hlavičce).",
         f"Model Kronos-small ([arXiv 2508.02739](https://arxiv.org/abs/2508.02739), [GitHub](https://github.com/shiyu-coder/Kronos)), kontext 512 svíček, 5 vzorků.",
         f"Období {df.t.min():%d. %m. %Y} – {df.t.max():%d. %m. %Y}, {len(df)} předpovědí. Náklady 0,30 % za obchod (0,15 % na stranu).", "",
         f"## Verdikt: **{'PROJDE' if passed else 'NEPROJDE'}**", "",
         "## Směr další svíčky", "", "| Skupina | Předpovědí | Kronos trefa | p (vs. 50 %) | Moment | Vždy nahoru | MAE vs. nulová předpověď | Medián velikosti předpovědi |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g, s in S.items():
        L.append(f"| {g} | {s['n']} | {pct(s['hit'])} | " + f"{s['p']:.3f} | ".replace(".", ",") + f"{pct(s['mom'])} | {pct(s['up'])} | " + f"{s['mae_ratio']:.3f}".replace(".", ",") + f" | {pct(s['pred_abs'], 2)} |")
    L += ["", "MAE poměr < 1 znamená, že Kronos odhadne velikost pohybu přesněji než předpověď „cena se nezmění“.", "",
          "## Obchodování podle předpovědi (1 svíčka, po nákladech)", "",
          "| Skupina | Pravidlo | Obchodů | Ø hrubě | Ø čistě | t | Σ čistě | Výher | 95. perc. náhody |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g, s in S.items():
        for k, lab in (("A", "každá svíčka"), ("B", "předpověď nad 0,30 %")):
            r = s[k]
            L.append(f"| {g} | {lab} | {r['n']} | {num(r['gross'])} % | {num(r['mean'])} % | {num(r['t'], 2)} | {num(r['sum'], 1)} % | {pct(r['win'], 0)} | {num(r['p95'])} % |")
    L += ["", "Hodnoty v % jsou výnos na jeden obchod (ne R). Σ je prostý součet, bez skládání a bez páky.",
          "Jen výzkum na historických datech; nejde o finanční poradenství."]
    OUT_REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    if sys.argv[1] == "predict":
        predict(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        report(sys.argv[2:])
