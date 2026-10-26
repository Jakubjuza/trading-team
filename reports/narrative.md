# 📡 Radar vyprávění (26. 10. 2026)

Cíl: zachytit chvíli, kdy na trhu **sílí** jedno vyprávění („bear market přichází“, „bottom is in“) u více zdrojů
naráz, a ověřit, jestli ho potvrzuje cena – nejdřív na 1H, pak 4H, pak 1D. Kód `research/narrative.py`, běží ve skeneru
jednou za hodinu, příkaz `/radar` v Telegramu. Bez AI; výklad dělá týdenní report nálady a sentiment-analyst desku.

## Zdroje (veřejné, bez klíče)

| Skupina | Zdroje | Váha |
|---|---|---|
| Analytici | Google News „bitcoin analyst/trader/strategist + bear/bull/bottom/top/rally/crash“ | 1,5 |
| Média | CoinDesk, Cointelegraph, The Block, Decrypt, Bitcoin Magazine, CryptoSlate, Blockworks | 1 |
| Telegram | @WatcherGuru, @wublockchainenglish, @cointelegraph, @glassnode (veřejné kanály, `narrative.telegram_channels`) | 1 |
| Komunita | Reddit r/BitcoinMarkets | 0,5 |

Ověřeno z GitHub Actions 26. 10. 2026. Nefungovalo (HTTP chyba): Glassnode Insights RSS, Bybit API oznámení,
Reddit r/CryptoCurrency. Nečte se: X/Twitter (jen placené API), Threads (bez veřejného rozhraní), zprávy Bybit a MEXC
(bez veřejného feedu dostupného z GitHubu). První kontrola: 201 zpráv za 3 dny, 25 se směrem (17 býčích, 8 medvědích).

## Jak se počítá

1. **Třídění** – fráze vyprávění: medvědí („bear market“, „top is in“, „breaks below“, „more downside“, „liquidations“ …),
   býčí („bottom is in“, „bull run“, „breakout“, „reclaims“, „inflows“ …), „konec bear marketu“ = býčí. Otázka = poloviční váha.
2. **Shoda (72 h)** – net = (býčí − medvědí) / (celkem + 1), vážené zdrojem. „Medvědí / býčí shoda“ = |net| ≥ 0,25
   a aspoň 4 různé zdroje na té straně. „Sílí“ = net o ≥ 0,15 dál od základu posledních 14 dní.
3. **Potvrzení cenou BTC** na 1H, 4H, 1D: ✅ = close na správné straně středu Bollingerova pásma (SMA20) a v posledních
   5 svíčkách prolomené minimum (maximum) 20 předchozích; 〰️ = jen správná strana pásma. Stupeň = kolik TF po sobě od 1H má ✅.
4. **Zpráva** na Telegram jen při nové shodě nebo vyšším stupni potvrzení (max. 2 denně), když vyprávění sílí.

## Měření dopředu

- Každá zpráva se směrem se uloží s cenou BTC (`research/narrative_log.jsonl`). Po 7 a 30 dnech: šla cena jejím směrem?
  → úspěšnost každého zdroje (`research/narrative_sources.json`). Zdroj s n ≥ 10 a úspěšností > 55 % dostane u desku větší váhu.
- Každý signál radaru (`research/narrative_calls.jsonl`) se vyhodnotí za 7 a 30 dní (pohyb BTC ve směru v %).
- Po ≥ 30 signálech se rozhodne, jestli radar přidává hodnotu (např. jako filtr směru pro desk) – předem: Ø pohyb ve
  směru za 7 dní > 0 v obou polovinách a lepší než stejné pravidlo bez potvrzení cenou. Do té doby jen popis.

Nejde o finanční poradenství.
