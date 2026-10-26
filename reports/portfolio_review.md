# Co funguje: přehled výzkumu a kombinace strategií (26. 10. 2026)

## Co říkají studie

- **Denní obchodníci většinou prodělávají.** Brazílie (Chague, De-Losso, Giovannetti, *Day Trading for a Living?*):
  97 % lidí, kteří obchodovali déle než 300 dní, prodělalo ([SSRN / FGV](https://econpapers.repec.org/RePEc:fgv:eesptd:525)).
  Tchaj-wan (Barber, Lee, Liu, Odean, 15 let dat): drtivá většina denních obchodníků je ztrátová
  ([pracovní verze](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/day%20trading%20and%20learning%20110217.pdf)).
- **AI/LLM obchodní agenti** – výhody z krátkých testů se na 20 letech a 100+ akciích výrazně zmenšují
  (FINSABER, [arXiv 2505.07078](https://arxiv.org/abs/2505.07078)).
- **Trend v kryptu funguje** – ensemble Donchian kanálů s řízením volatility, Sharpe > 1,5 podle autorů
  (Zarattini, Pagani, Barbon, [Catching Crypto Trends](https://ideas.repec.org/p/chf/rpseri/rp2580.html)); momentum v kryptu
  ([Liu & Tsyvinski 2021](https://ideas.repec.org/a/oup/rfinst/v34y2021i6p2689-2727..html)).
- **Vnitrodenní vzory** – momentum BTC v rámci dne ([Shen, Urquhart, Wang](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/));
  hodinové efekty nejsou stálé napříč burzami a obdobími ([Baur a kol.](https://research-repository.uwa.edu.au/en/publications/bitcoin-time-of-day-day-of-week-and-month-of-year-effects-in-retu/)).

## Nové testy (stanovené předem)

**Long BTC 21:00–23:00 UTC** ([Quantpedia](https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/)),
1H data 2 roky, 728 dní: před náklady +0,044 % denně, po nákladech 0,07 %/stranu −0,10 %, 0,15 % −0,26 % → ❌ náklady sežerou efekt.

**Donchian ensemble s cílovou volatilitou** (`research/experiments/ensemble.py`): 5 kanálů (10–160 dní), signál = podíl
modelů v longu, váha mince × min(1; 40 % / roční volatilita) / 8, jen long, rebalance denně, náklady 0,15 % z obratu.

| | Výnos/rok | Volatilita | Sharpe | Max. propad | Sharpe IS / OOS | Odložený rok (10/2025–10/2026) |
|---|---|---|---|---|---|---|
| BTC držení | +50 % | 67 % | 0,94 | −83 % | 0,99 / 1,47 | −27 % |
| 8 mincí držení | +96 % | 85 % | 1,21 | −88 % | 1,42 / 1,25 | −47 % |
| Jádro (denní signály, 0,5 % riziko) | +11,6 % | 8 % | 1,35 | −12 % | 1,48 / 1,50 | +0,8 % |
| Ensemble | +19,4 % | 15 % | 1,24 | −26 % | 1,42 / 1,47 | −8,8 % |
| **Jádro + 50 % ensemble** | **+22,3 %** | **11 %** | **1,86** | **−16 %** | **2,08 / 2,12** | −3,6 % |

Korelace denních výnosů jádra a ensemblu −0,03 (nezávislé). Ensemble: Ø expozice 17 % kapitálu, obrat 5× ročně.
Po letech (jádro + ensemble): 2017 +17 · 2018 +22 · 2019 +14 · 2020 +46 · 2021 +81 · 2022 −1 · 2023 +25 · 2024 +29 · 2025 +4 · 2026 −6 %.

## Závěr

✅ **Ensemble prošel** (IS i OOS Sharpe ~1,4, shoda se studií) a hlavně **se nekoreluje s jádrem** – kombinace má lepší
poměr výnosu k riziku než kterákoli část zvlášť (Sharpe 1,86, propad −16 %). V odloženém roce (medvědí trh: BTC −27 %,
mince −47 %) ztratil −8,8 %, kombinace −3,6 %. Jen long → jde zrcadlit na spotovém demu.

Nejde o finanční poradenství.
