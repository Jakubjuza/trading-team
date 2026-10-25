# Experimenty: přizpůsobení trhu a nové typy strategií

Skripty, ze kterých vychází `reports/adaptive.md`. Všechny varianty byly stanovené předem se standardními hodnotami
(žádné ladění na stejných datech); filtry vidí jen minulost, equity filtry jen obchody uzavřené před signálem.

Data: denní svíčky ~10 let, 8 mincí – stejná cache jako `scanner/evaluate.py` (`eval_crypto_<COIN>-USDT_1d_3650d.csv`).
Nejdřív je stáhni (např. `python3 scanner/calibrate.py`), pak:

```
python3 research/experiments/adaptive_variants.py scanner/cache    # V0–V8: režimy, equity filtry, walk-forward
python3 research/experiments/adaptive_robust.py scanner/cache  # filtr paniky – sousední hodnoty, strategie, mince
python3 research/experiments/htf_filter.py scanner/cache         # filtr podle týdne/měsíce
python3 research/experiments/htf_robust.py scanner/cache       # týdenní filtr – EMA 10–40 týdnů
python3 research/experiments/mean_reversion.py scanner/cache          # mean reversion RSI(2)
python3 research/experiments/rotation.py scanner/cache    # rotace dual momentum
python3 research/experiments/tsmom.py scanner/cache       # držet nad SMA200, jinak hotovost
python3 research/carry.py --report                             # carry z fundingu (potřebuje Hyperliquid → GitHub Actions)
```
