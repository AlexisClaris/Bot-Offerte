"""
Bot Telegram per l'invio automatico di offerte prodotto Amazon.
Eseguito da GitHub Actions ogni 10 minuti: invia tutti i prodotti
della lista e poi termina.
"""

import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ⚠️ Sostituisci "link" con il TUO link affiliato Amazon generato
# tramite SiteStripe (deve contenere il tuo tag, es. ?tag=iltuotag-21)
PRODOTTI = [
    {
        "nome": "PATONA Batteria J-S1 1400mAh per BlackBerry Curve 9320 9720",
        "prezzo_originale": 15.50,
        "prezzo_scontato": 11.95,
        "link": "https://amzn.to/4xKnOL4",
    },
    {
        "nome": "NIVEA SUN Protect & Hydrate SPF 30 Formato Viaggio 100 ml",
        "prezzo_originale": 7.99,
        "prezzo_scontato": 5.68,
        "link": "https://amzn.to/4Aw7b8r",
    },
    {
        "nome": "Amazon Basics Filtri per acqua, adatto e compatibile con tutte le caraffe BRITA, incluse le PerfectFit, 6 unità, confezione da 1",
        "prezzo_originale": 34.90,
        "prezzo_scontato": 19.84,
        "link": "https://amzn.to/4hgp1DC",
    },
]


def calcola_sconto(originale, scontato):
    """Calcola automaticamente la percentuale di sconto."""
    if not originale or originale <= 0:
        return 0
    return round((1 - scontato / originale) * 100)


def formatta_messaggio(prodotto):
    nome = prodotto["nome"]
    prezzo_originale = float(prodotto["prezzo_originale"])
    prezzo_scontato = float(prodotto["prezzo_scontato"])
    sconto = calcola_sconto(prezzo_originale, prezzo_scontato)

    return (
        f"🔥 *{nome}*\n\n"
        f"~~💰 {prezzo_originale:.2f}€~~\n"
        f"✅ *{prezzo_scontato:.2f}€*  (-{sconto}%)\n\n"
        f"⏰ Offerta a tempo limitato!"
    )


def invia_prodotto(prodotto):
    messaggio = formatta_messaggio(prodotto)
    tastiera = {
        "inline_keyboard": [[
            {"text": "🛒 Acquista Ora", "url": prodotto["link"]}
        ]]
    }
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": messaggio,
        "parse_mode": "Markdown",
        "reply_markup": tastiera,
    }
    return requests.post(url, json=payload, timeout=15)


def main():
    for prodotto in PRODOTTI:
        risposta = invia_prodotto(prodotto)
        if risposta.status_code == 200:
            print(f"✅ Inviato: {prodotto['nome']}")
        else:
            print(f"❌ Errore invio '{prodotto['nome']}': {risposta.text}")


if __name__ == "__main__":
    main()
