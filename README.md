# Product Monitor Bot

Bot Telegram per monitorare la disponibilità e i prezzi dei prodotti su vari siti web.

## Caratteristiche

- ✅ Monitoraggio automatico di prodotti su siti web
- 🔔 Notifiche in tempo reale per cambiamenti di stock e prezzo
- 🤖 Interfaccia Telegram con pulsanti interattivi
- 🔄 Esecuzione manuale tramite GitHub Actions
- 💾 Salvataggio persistente dei dati
- 🆓 Completamente gratuito

## Setup

### 1. Creare il Bot Telegram

1. Apri Telegram e cerca `@BotFather`
2. Invia `/newbot`
3. Scegli il nome: `All Matcha Restock Bot 3`
4. Scegli l'username: `all_matcha_restock_bot3` (o simile se occupato)
5. Salva il token che ricevi

### 2. Ottenere il Chat ID

1. Cerca il tuo bot su Telegram e avvia una conversazione con `/start`
2. Vai su: `https://api.telegram.org/bot[TOKEN]/getUpdates`
   (sostituisci [TOKEN] con il token del tuo bot)
3. Cerca il numero dopo `"chat":{"id":` - quello è il tuo chat ID

### 3. Configurare GitHub

1. Fai fork di questo repository o caricalo sul tuo GitHub
2. Vai su Settings → Secrets and variables → Actions
3. Aggiungi questi secrets:
   - `TELEGRAM_BOT_TOKEN`: il token del bot
   - `TELEGRAM_CHAT_ID`: il tuo chat ID

### 4. Avviare il Bot

Il bot ha due modalità:

#### Modalità Interattiva (Locale)
```bash
python main.py
```

#### Modalità Monitoraggio (GitHub Actions)
- Vai su Actions tab nel tuo repository
- Seleziona "Product Monitor Bot"
- Clicca "Run workflow"

## Utilizzo

### Comandi del Bot

- `/start` - Mostra il menu principale

### Funzioni Disponibili

1. **➕ Aggiungi Link** - Aggiungi un singolo prodotto
2. **🗑️ Rimuovi Link** - Rimuovi un prodotto specifico
3. **📋 Lista Link** - Visualizza tutti i prodotti monitorati
4. **🔍 Controlla Ora** - Esegui controllo immediato
5. **📎 Aggiungi Multi Link** - Aggiungi più prodotti insieme
6. **🗑️ Rimuovi Tutti** - Cancella tutti i prodotti

### Formato Link

**Singolo link:**
```
https://esempio.com/prodotto
```

**Link con nome personalizzato:**
```
https://esempio.com/prodotto|Nome Prodotto
```

**Link multipli:**
```
https://sito1.com/prodotto1|Prodotto 1
https://sito2.com/prodotto2|Prodotto 2
https://sito3.com/prodotto3
```

## File Struttura

```
all_matcha_restock_bot3/
├── main.py                 # Bot Telegram principale
├── monitor_runner.py       # Runner per GitHub Actions
├── requirements.txt        # Dipendenze Python
├── monitored_links.json    # Database dei link (auto-generato)
├── .github/
│   └── workflows/
│       └── monitor.yml     # Configurazione GitHub Actions
└── README.md              # Questa documentazione
```

## Sicurezza

- I token sono archiviati come GitHub Secrets
- Nessun dato sensibile nel codice
- Controlli di accesso via Chat ID

## Limitazioni

- Non supporta siti con protezione anti-bot avanzata
- Alcuni siti potrebbero richiedere configurazioni specifiche
- Rate limiting per evitare il blocco IP

## Supporto

Per problemi o domande, apri una issue su GitHub.
