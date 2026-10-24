# Rychlý skener (bez AI)

O vstupu rozhoduje jen kód (`rules.py`). Každou minutu stáhne nové svíčky (krypto přes ccxt, akcie přes yfinance),
uloží je do cache, vyhodnotí pravidlo **breakout → retest → hold** (long i short) a nalezený setup:

1. zkontroluje proti `state.json` (stejný setup se nepošle dvakrát) a denní limit,
2. spočítá vstup, stop, cíle, R:R a velikost pozice podle `config.yaml`,
3. vykreslí PNG (`.claude/skills/chart-report/render_chart.py`) a pošle ho na Telegram s 5 řádky shrnutí,
4. zapíše papírový obchod (`broker.py`, ostré obchody vypnuté),
5. volitelně (`ai_explain.enabled`) zavolá AI jen na vysvětlení – až po nalezení setupu.

## Pravidlo breakout → retest → hold

| Krok | LONG | SHORT |
|---|---|---|
| Range | RH = max high, RL = min low posledních `range_lookback` svíček; výška mezi `min_range_pct` a `max_range_pct` | stejné |
| Breakout | první close nad RH | první close pod RL |
| Retest | do `retest_window` svíček low ≤ RH·(1+0,3 %); mezitím všechny close nad RH; retest nezavře pod RH·(1−0,3 %) | high ≥ RL·(1−0,3 %); close pod RL; retest nezavře nad RL·(1+0,3 %) |
| Hold | další svíčka: close > RH a low ≥ RH·(1−0,3 %) | close < RL a high ≤ RL·(1+0,3 %) |
| Vstup | close hold svíčky | stejné |
| Stop | min(low retestu, low holdu) − 0,1·ATR, aspoň 0,5·ATR od vstupu | zrcadlově nad high |
| Cíle | RH + 1× a 2× výška range (nebo násobky R) | RL − 1× a 2× výška range |
| Filtr | R:R na T1 ≥ `min_rr` | stejné |

## Spuštění

```bash
pip install -r scanner/requirements.txt
export TELEGRAM_BOT_TOKEN=...   # nikdy necommitovat
export TELEGRAM_CHAT_ID=...
python3 scanner/scan.py --once --dry-run   # jeden průchod, nic neposílá
python3 scanner/scan.py                    # nepřetržitě, každých poll_seconds (60 s)
python3 -m pytest tests -q                 # testy pravidel
```

## Nepřetržitý běh

Skript potřebuje stroj, který běží pořád a má přístup na burzu (ccxt) a Yahoo:

- **Levný VPS** (např. Hetzner / Contabo, ~4–5 €/měsíc) nebo **Raspberry Pi** doma – doporučeno.
  Použij `scanner/trading-scanner.service` (systemd):
  ```bash
  git clone https://github.com/Jakubjuza/trading-team && cd trading-team
  python3 -m venv .venv && .venv/bin/pip install -r scanner/requirements.txt
  printf 'TELEGRAM_BOT_TOKEN=...\nTELEGRAM_CHAT_ID=...\n' > .env && chmod 600 .env
  sudo cp scanner/trading-scanner.service /etc/systemd/system/   # uprav User a cesty
  sudo systemctl enable --now trading-scanner
  journalctl -u trading-scanner -f    # log
  ```
- **Vlastní počítač**: `python3 scanner/scan.py` v terminálu – běží jen když je počítač zapnutý.
- **GitHub Actions** neumí každou minutu (minimum 5 min, často se zpožděním) a nemá trvalou cache – jen jako nouzovka s `--once`.

Burzu pro krypto zvol podle země serveru (`exchange` v configu): Binance blokuje US IP adresy, Kraken/OKX/Bybit bývají v EU v pořádku.
