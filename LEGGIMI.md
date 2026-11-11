# Bot Offerte Impazienti (versione 2)

Tu mandi un'offerta al bot in chat privata, lui la pubblica nel canale una volta sola.
Gira gratis su GitHub Actions ogni 10 minuti. Non serve l'API di Amazon.

## Installazione (una volta sola)

1. Nel repository `Bot-Offerte` su GitHub:
   - carica `bot_offerte.py` (sostituisce quello vecchio);
   - carica `.github/workflows/pubblica-offerte.yml`;
   - **cancella** `.github/workflows/Invia_Offerte.yml`, altrimenti il vecchio bot continua a girare.
2. In Settings → Secrets and variables → Actions controlla i Secrets:
   - `BOT_TOKEN`: c'è già (il token di BotFather);
   - `CHAT_ID`: c'è già (il canale, es. `@OfferteImpazienti`);
   - `OWNER_ID`: nuovo, il tuo ID Telegram (vedi punto 3);
   - `AMAZON_TAG`: nuovo, il tag che ricevi con la nuova domanda di affiliazione (es. `nome-21`).
3. Per sapere il tuo ID: scrivi `/id` al bot in privato, poi su GitHub apri Actions →
   "Pubblica offerte Telegram" → Run workflow. Il bot ti risponde con il numero.
4. Il bot deve essere amministratore del canale con il permesso di pubblicare.

## Uso di tutti i giorni

Scrivi al bot in privato un messaggio per ogni offerta:

```
https://www.amazon.it/dp/B0CZ7D9G8D
Anker Prime 250W Caricatore USB C GaN a 6 Porte
159,99
109,99
#Informatica
```

- Prima riga: il link del prodotto (va bene anche quello lungo copiato dal browser, o `amzn.to`).
  Il bot lo pulisce e ci mette il tuo tag.
- Poi il titolo, il prezzo pieno e il prezzo scontato. La categoria con `#` è facoltativa.
- Con un prezzo solo, pubblica l'offerta senza percentuale.

Il bot controlla la chat ogni 10 minuti e pubblica **una sola offerta ogni 30 minuti**
(nei primi 10 minuti di ogni mezz'ora, ora italiana). Le altre aspettano in coda e, quando
escono, ti risponde `Pubblicato ✅ / nome del prodotto`. Se l'offerta è scritta male ti risponde subito con
`❌` e cosa correggere.

- Telegram conserva i messaggi in coda per 24 ore: non mandarne più di una quarantina alla volta.
- Per pubblicare subito tutta la coda: GitHub → Actions → Pubblica offerte Telegram →
  Run workflow (con "subito" spuntato).

## Limiti da sapere

- I prezzi li scrivi tu: controllali sulla pagina Amazon al momento dell'invio.
  Il post riporta l'ora, perché su Amazon i prezzi cambiano.
- GitHub ferma i workflow programmati dopo 60 giorni senza modifiche al repository:
  ti arriva una mail e basta un clic per riattivarli.
- Prova sul computer senza inviare niente: `python3 bot_offerte.py --prova`
