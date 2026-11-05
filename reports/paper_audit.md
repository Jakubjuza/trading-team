# 🔍 Audit papíru laboratoře

Spuštěno 2026-11-05 19:48 UTC · okno od 2026-10-27 20:00 UTC · čerstvé svíčky OKX, stejný kód jako papír.

## 1. Živé obchody znovu backtestem

Živě 37 obchodů: Σ -29,4 R, Ø -0,79 R. Backtest týchž: Σ -29,4 R, Ø -0,79 R. Shoda R (±0,05): 37/37.

| mince | strategie | směr | signál | živě R | backtest R | rozdíl | pozn. |
|---|---|---|---|---|---|---|---|
| XRP | donchian 100 1h | long | 2026-10-27T23:00 | -0,96 | -0,96 | +0,00 |  |
| BTC | donchian 100 1h | long | 2026-10-28T08:00 | -1,12 | -1,12 | -0,00 |  |
| BTC | vol_break 55/1.5 1h | long | 2026-10-28T08:00 | -1,12 | -1,12 | -0,00 |  |
| ETH | vol_break 55/1.5 1h | long | 2026-10-28T08:00 | -1,09 | -1,09 | +0,00 |  |
| DOGE | donchian 100 1h | long | 2026-10-28T03:00 | -0,79 | -0,79 | -0,00 |  |
| ADA | ma_cross sma/20/50/cross 2h | short | 2026-10-28T12:00 | -1,04 | -1,04 | -0,00 |  |
| XRP | macd 19/39/9/signal 2h | long | 2026-10-28T18:00 | -1,07 | -1,07 | +0,00 |  |
| ADA | macd 19/39/9/signal 2h | long | 2026-10-28T18:00 | -1,05 | -1,05 | -0,00 |  |
| LINK | boll_break 20/2.5 4h | long | 2026-10-28T00:00 | -1,04 | -1,04 | +0,00 |  |
| DOGE | boll_break 20/2.5 4h | long | 2026-10-27T20:00 | -0,79 | -0,79 | -0,00 |  |
| ADA | ma_cross sma/20/50/cross 2h | short | 2026-10-29T02:00 | -1,03 | -1,03 | -0,00 |  |
| BTC | macd 19/39/9/signal 2h | long | 2026-10-29T14:00 | -1,09 | -1,09 | +0,00 |  |
| ETH | macd 19/39/9/signal 2h | long | 2026-10-29T14:00 | -1,06 | -1,06 | +0,00 |  |
| LINK | macd 19/39/9/signal 2h | long | 2026-10-29T14:00 | -1,04 | -1,04 | +0,00 |  |
| BTC | rsi_mom 60 2h | long | 2026-10-29T14:00 | -1,09 | -1,09 | +0,00 |  |
| LINK | rsi_mom 60 2h | long | 2026-10-29T14:00 | -1,04 | -1,04 | +0,00 |  |
| ADA | macd 19/39/9/signal 2h | long | 2026-10-29T14:00 | -1,04 | -1,04 | -0,00 |  |
| DOGE | rsi_mom 60 2h | long | 2026-10-29T14:00 | -1,05 | -1,05 | +0,00 |  |
| SOL | macd 19/39/9/signal 2h | long | 2026-10-29T16:00 | -0,73 | -0,73 | +0,00 |  |
| AVAX | macd 19/39/9/signal 2h | long | 2026-10-29T16:00 | -1,04 | -1,04 | +0,00 |  |
| DOGE | macd 19/39/9/signal 2h | long | 2026-10-29T16:00 | -1,05 | -1,05 | +0,00 |  |
| AVAX | ma_cross sma/20/50/cross 2h | short | 2026-10-29T16:00 | +1,47 | +1,47 | +0,00 |  |
| DOGE | rsi_mom 60 4h | long | 2026-10-29T12:00 | -1,04 | -1,04 | +0,00 |  |
| BTC | price_ma ema/200 4h | long | 2026-10-29T12:00 | -0,78 | -0,78 | +0,00 |  |
| SOL | macd 19/39/9/signal 12h | long | 2026-10-28T00:00 | -1,33 | -1,33 | -0,00 |  |
| ETH | macd 19/39/9/signal 12h | long | 2026-10-28T12:00 | -0,93 | -0,93 | +0,00 |  |
| LINK | macd 19/39/9/signal 12h | long | 2026-10-28T12:00 | -1,56 | -1,56 | -0,00 |  |
| AVAX | macd 19/39/9/signal 2h | long | 2026-10-31T00:00 | -0,21 | -0,21 | -0,00 |  |
| ETH | macd 19/39/9/signal 2h | long | 2026-10-31T06:00 | +0,35 | +0,35 | -0,00 |  |
| SOL | ma_cross sma/20/50/cross 2h | short | 2026-10-29T22:00 | +1,06 | +1,06 | -0,00 |  |
| XRP | ma_cross sma/20/50/cross 2h | short | 2026-10-29T22:00 | -0,40 | -0,40 | -0,00 |  |
| BTC | keltner 2.5 2h | short | 2026-10-29T22:00 | +0,60 | +0,60 | -0,00 |  |
| AVAX | ma_cross sma/20/50/cross 2h | short | 2026-11-03T04:00 | -1,04 | -1,04 | +0,00 |  |
| SOL | macd 19/39/9/signal 2h | long | 2026-11-03T12:00 | -1,06 | -1,06 | +0,00 |  |
| BTC | ma_cross sma/20/50/cross 2h | short | 2026-11-03T10:00 | -1,08 | -1,08 | +0,00 |  |
| LINK | supertrend 10/3.0 4h | short | 2026-11-04T00:00 | -1,02 | -1,02 | -0,00 |  |
| ADA | macd 19/39/9/signal 2h | long | 2026-11-04T04:00 | -1,05 | -1,05 | +0,00 |  |

## 2.–3. Všechny signály aktivních strategií v okně

Signálů 229 (uzavřených 189), papír zachytil (živě nebo stínově) 42.
Backtest všech uzavřených signálů za tyto dny: Σ -145,8 R, Ø -0,77 R, výhry 16 %.
Long -0,84 R (151), short -0,50 R (38).

Nezachycené signály (prvních 20):

| strategie | mince | čas | R |
|---|---|---|---|
| MACD 19 39 9 signal · 12H long | ADA | 2026-11-04 00:00 | – |
| MACD 19 39 9 signal · 12H long | AVAX | 2026-11-01 12:00 | – |
| MACD 19 39 9 signal · 12H long | BTC | 2026-11-04 12:00 | – |
| MACD 19 39 9 signal · 12H long | DOGE | 2026-11-03 12:00 | – |
| MACD 19 39 9 signal · 12H long | LINK | 2026-10-31 00:00 | – |
| MACD 19 39 9 signal · 12H long | XRP | 2026-11-03 12:00 | – |
| Bollinger průraz 20 2.5 · 6H long | BTC | 2026-11-04 12:00 | – |
| Bollinger průraz 20 2.5 · 6H long | ETH | 2026-11-04 06:00 | – |
| Bollinger průraz 20 2.5 · 6H long | XRP | 2026-11-03 12:00 | – |
| Bollinger průraz 20 2.5 · 6H long | XRP | 2026-11-04 12:00 | – |
| Bollinger průraz 50 2.5 · 4H short | ADA | 2026-10-29 20:00 | -1,02 |
| Bollinger průraz 50 2.5 · 4H short | AVAX | 2026-10-29 20:00 | -1,02 |
| Bollinger průraz 50 2.5 · 4H short | AVAX | 2026-10-30 12:00 | -1,02 |
| Bollinger průraz 50 2.5 · 4H short | BTC | 2026-10-29 20:00 | -1,04 |
| Bollinger průraz 50 2.5 · 4H short | ETH | 2026-10-30 00:00 | -1,03 |
| Bollinger průraz 50 2.5 · 4H short | ETH | 2026-10-30 12:00 | -1,03 |
| Bollinger průraz 50 2.5 · 4H short | LINK | 2026-10-29 20:00 | -1,02 |
| Bollinger průraz 50 2.5 · 4H short | SOL | 2026-10-29 20:00 | – |
| Bollinger průraz 50 2.5 · 4H short | SOL | 2026-10-30 12:00 | – |
| Bollinger průraz 50 2.5 · 4H short | XRP | 2026-10-29 20:00 | -1,03 |

Závěr čti takto: když backtest týchž obchodů dá stejné R jako papír, chyba v papíru není a ztráta je z období/strategií. Když se liší, chyba je v papíru.

Nejde o finanční poradenství.
