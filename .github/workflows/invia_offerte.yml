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
        "nome": "Cuffie Bluetooth Wireless",
        "prezzo_originale": 49.90,
        "prezzo_scontato": 29.90,
        "link": "https://www.amazon.it/dp/ESEMPIO1?tag=iltuotag-21",
    },
    {
        "nome": "Smartwatch Fitness Tracker",
        "prezzo_originale": 79.99,
        "prezzo_scontato": 39.99,
        "link": "https://www.amazon.it/dp/ESEMPIO2?tag=iltuotag-21",
    },
    {
        "nome": "Power Bank 20000mAh",
        "prezzo_originale": 34.90,
        "prezzo_scontato": 19.90,
        "link": "https://www.amazon.it/dp/ESEMPIO3?tag=iltuotag-21",
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
