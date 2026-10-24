# Telegram hlídač

Běží v GitHub Actions každých 15 min (`.github/workflows/watcher.yml`), bez AI.
Čte `levels.json` (zapisuje ho skill `skener` 2× denně), kontroluje uzavřené svíčky přes yfinance
a posílá na Telegram:

- 📋 nový hlídaný setup (jakmile ho skener přidá),
- 🔔 spuštění spouštěče (s grafem, pokud existuje),
- ❌ zneplatnění (cena prošla stopem před spuštěním).

`state.json` si pamatuje, co už bylo posláno (workflow ho commituje zpět).

## Nastavení Telegramu

1. V Telegramu napiš **@BotFather** → `/newbot` → zvol jméno → dostaneš **token** (`123456:ABC...`).
2. Napiš svému novému botovi libovolnou zprávu (třeba „ahoj“).
3. Zjisti své **chat ID**: napiš botovi **@userinfobot** – odpoví číslem `Id`.
4. GitHub → repozitář → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` = token z kroku 1,
   - `TELEGRAM_CHAT_ID` = číslo z kroku 3.
5. **Actions → Telegram hlídač → Run workflow**, zaškrtni „Jen poslat testovací zprávu“ → na Telegram přijde ✅.

Lokální test bez odesílání: `python3 watcher/watch.py --dry-run`.
