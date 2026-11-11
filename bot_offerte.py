"""
Bot del canale Telegram "Offerte Impazienti".

Come funziona
-------------
Tu scrivi al bot in chat privata un messaggio per ogni offerta:

    https://www.amazon.it/dp/B0XXXXXXXX
    Titolo del prodotto
    39,99
    24,99
    #Elettronica          (facoltativo)

GitHub Actions lancia questo script ogni 10 minuti: legge i messaggi nuovi,
pubblica ogni offerta UNA volta sola nel canale e ti risponde in privato
con "pubblicata" oppure con l'errore.

Non legge niente dalle pagine di Amazon: titolo e prezzi li scrivi tu.
Usa solo la libreria standard di Python (niente da installare).

Prova senza inviare nulla:   python3 bot_offerte.py --prova
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

RE_URL = re.compile(r"https?://\S+")
RE_ASIN = re.compile(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})(?:[/?]|$)")
RE_PREZZO = re.compile(
    r"^(?:€\s*)?(\d{1,3}(?:\.\d{3})+|\d+)(?:[.,](\d{1,2}))?\s*(?:€|euro)?$", re.I
)
DOMINI_CORTI = {"amzn.to", "amzn.eu", "a.co"}

AIUTO = (
    "Mandami un messaggio per ogni offerta, così:\n\n"
    "https://www.amazon.it/dp/B0XXXXXXXX\n"
    "Titolo del prodotto\n"
    "39,99\n"
    "24,99\n"
    "#Categoria (facoltativo)\n\n"
    "Il primo prezzo è quello pieno, il secondo quello scontato. "
    "Con un prezzo solo pubblico l'offerta senza la percentuale."
)


class ErroreOfferta(Exception):
    """Errore da spiegare al proprietario del canale."""


# ---------------------------------------------------------------- prezzi

def leggi_prezzo(testo):
    """'39,99' / '€ 1.299,00' / '39.99' -> numero. None se non è un prezzo."""
    m = RE_PREZZO.match(testo.strip())
    if not m:
        return None
    intero = m.group(1).replace(".", "")
    decimali = (m.group(2) or "0").ljust(2, "0")
    return float(f"{intero}.{decimali}")


def euro(valore):
    """1299.5 -> '1.299,50'"""
    return f"{valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ link

class _SenzaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _dominio(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _apri_link_corto(url):
    """Segue i reindirizzamenti di un link corto e restituisce l'indirizzo finale.
    Legge solo l'intestazione 'Location', non il contenuto della pagina."""
    apri = urllib.request.build_opener(_SenzaRedirect)
    for _ in range(5):
        if RE_ASIN.search(urllib.parse.urlparse(url).path):
            return url
        richiesta = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            apri.open(richiesta, timeout=15).close()
            return url
        except urllib.error.HTTPError as errore:
            prossimo = errore.headers.get("Location")
            if errore.code not in (301, 302, 303, 307, 308) or not prossimo:
                raise
            url = urllib.parse.urljoin(url, prossimo)
    return url


def link_affiliato(url, tag):
    """Restituisce (link pulito con il tuo tag, eventuale avviso)."""
    url = url.rstrip(").,;")
    dominio = _dominio(url)
    if dominio in DOMINI_CORTI:
        try:
            url = _apri_link_corto(url)
            dominio = _dominio(url)
        except Exception:
            if dominio == "amzn.to":
                return url, (
                    "Non sono riuscito ad aprire il link corto: l'ho pubblicato "
                    "così com'è. Controlla che contenga il tuo tag."
                )
            raise ErroreOfferta(
                "Non riesco ad aprire questo link corto. Mandami il link completo "
                "di amazon.it (quello con /dp/ dentro)."
            )
    if dominio != "amazon.it" and not dominio.endswith(".amazon.it"):
        raise ErroreOfferta("Il link non è di amazon.it.")
    m = RE_ASIN.search(urllib.parse.urlparse(url).path)
    if not m:
        raise ErroreOfferta(
            "Nel link non trovo il codice del prodotto. Usa il link della pagina "
            "prodotto (quello con /dp/ dentro)."
        )
    return f"https://www.amazon.it/dp/{m.group(1)}/?tag={tag}", None


# ------------------------------------------------------------- messaggio

def leggi_offerta(testo):
    """Trasforma il tuo messaggio in un dizionario con link, titolo e prezzi."""
    trovato = RE_URL.search(testo)
    if not trovato:
        raise ErroreOfferta("Manca il link del prodotto.\n\n" + AIUTO)
    link = trovato.group(0)
    righe = [r.strip() for r in testo.replace(link, "\n").splitlines() if r.strip()]

    prezzi, titolo, categoria = [], None, None
    for riga in righe:
        prezzo = leggi_prezzo(riga)
        if prezzo is not None:
            prezzi.append(prezzo)
        elif riga.startswith("#") and " " not in riga:
            categoria = riga
        elif titolo is None:
            titolo = riga

    if not titolo:
        raise ErroreOfferta("Manca il titolo del prodotto.\n\n" + AIUTO)
    if not prezzi:
        raise ErroreOfferta("Manca il prezzo.\n\n" + AIUTO)
    if len(prezzi) > 2:
        raise ErroreOfferta("Ho trovato più di due prezzi: mettine al massimo due.")
    if len(prezzi) == 2 and prezzi[1] >= prezzi[0]:
        raise ErroreOfferta(
            "Il secondo prezzo (scontato) deve essere più basso del primo (pieno)."
        )
    return {
        "link": link,
        "titolo": titolo,
        "pieno": prezzi[0] if len(prezzi) == 2 else None,
        "scontato": prezzi[-1],
        "categoria": categoria,
    }


def formatta(offerta, adesso):
    righe = [f"🔥 <b>{html.escape(offerta['titolo'])}</b>", ""]
    if offerta["pieno"]:
        risparmio = offerta["pieno"] - offerta["scontato"]
        sconto = round(risparmio / offerta["pieno"] * 100)
        righe.append(
            f"💰 Passa da <s>{euro(offerta['pieno'])}€</s> "
            f"a <b>{euro(offerta['scontato'])}€</b>"
        )
        righe.append(f"ℹ️ <i>Risparmi: {euro(risparmio)}€ (-{sconto}%)</i>")
    else:
        righe.append(f"💰 <b>{euro(offerta['scontato'])}€</b>")
    righe.append("")
    righe.append(f"🕒 Prezzo delle {adesso:%H:%M} del {adesso:%d/%m}, può cambiare")
    coda = "#adv · link di affiliazione"
    if offerta["categoria"]:
        coda = f"{html.escape(offerta['categoria'])} · {coda}"
    righe.append(coda)
    return "\n".join(righe)


# -------------------------------------------------------------- Telegram

def telegram(token, metodo, **dati):
    richiesta = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{metodo}",
        data=json.dumps(dati).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=30) as risposta:
            return json.load(risposta)["result"]
    except urllib.error.HTTPError as errore:
        corpo = errore.read().decode("utf-8", "replace")
        raise RuntimeError(f"Telegram {metodo}: {corpo}") from None


def pubblica(token, canale, offerta, link, adesso):
    telegram(
        token,
        "sendMessage",
        chat_id=canale,
        text=formatta(offerta, adesso),
        parse_mode="HTML",
        link_preview_options={
            "url": link,
            "prefer_large_media": True,
            "show_above_text": True,
        },
        reply_markup={"inline_keyboard": [[{"text": "🛒 Vai all'offerta", "url": link}]]},
    )


def valuta(messaggio, cfg):
    """Capisce un messaggio privato senza pubblicare niente.
    Restituisce ("risposta", testo o None) oppure ("offerta", (offerta, link, avviso))."""
    chat = messaggio["chat"]
    if chat.get("type") != "private":
        return "risposta", None
    mittente = str(messaggio.get("from", {}).get("id", ""))
    testo = (messaggio.get("text") or messaggio.get("caption") or "").strip()

    if testo.startswith(("/id", "/start")):
        return "risposta", f"Il tuo ID Telegram è {mittente}.\n\n{AIUTO}"
    if not cfg["proprietario"] or mittente != cfg["proprietario"]:
        return "risposta", None
    if testo.startswith("/"):
        return "risposta", AIUTO
    if not cfg["tag"]:
        return "risposta", "Manca il tag di affiliazione (AMAZON_TAG) nei Secrets di GitHub."

    try:
        offerta = leggi_offerta(testo)
        link, avviso = link_affiliato(offerta["link"], cfg["tag"])
    except ErroreOfferta as errore:
        return "risposta", f"❌ Non pubblicata. {errore}"
    return "offerta", (offerta, link, avviso)


def finestra_di_pubblicazione():
    """Vero solo nei primi 10 minuti di ogni mezz'ora (ora italiana).
    Il bot gira ogni 10 minuti, quindi pubblica una sola offerta ogni 30."""
    return datetime.now(ZoneInfo("Europe/Rome")).minute % 30 < 10


def main():
    cfg = {
        "token": os.environ["BOT_TOKEN"],
        "canale": os.environ["CHAT_ID"],
        "proprietario": os.environ.get("OWNER_ID", "").strip(),
        "tag": os.environ.get("AMAZON_TAG", "").strip(),
    }
    # FORZA=true (bottone "Run workflow"): pubblica subito tutte le offerte in coda.
    forza = os.environ.get("FORZA", "").strip().lower() == "true"
    puo_pubblicare = forza or finestra_di_pubblicazione()
    pubblicate, prossimo, errori = 0, None, 0
    while True:
        # Un messaggio alla volta: chiedere il successivo conferma il precedente,
        # così la stessa offerta non viene mai pubblicata due volte.
        parametri = {"limit": 1, "timeout": 0, "allowed_updates": ["message"]}
        if prossimo is not None:
            parametri["offset"] = prossimo
        aggiornamenti = telegram(cfg["token"], "getUpdates", **parametri)
        if not aggiornamenti:
            break
        aggiornamento = aggiornamenti[0]
        prossimo = aggiornamento["update_id"] + 1
        messaggio = aggiornamento.get("message")
        if not messaggio:
            continue
        try:
            tipo, dati = valuta(messaggio, cfg)
            if tipo == "offerta":
                if not forza and (not puo_pubblicare or pubblicate >= 1):
                    break  # non confermata: resta in coda per il prossimo turno
                offerta, link, avviso = dati
                pubblica(cfg["token"], cfg["canale"], offerta, link,
                         datetime.now(ZoneInfo("Europe/Rome")))
                pubblicate += 1
                print(f"Pubblicata: {offerta['titolo']}")
                risposta = f"Pubblicato ✅ / {offerta['titolo']}" + (f"\n⚠️ {avviso}" if avviso else "")
            else:
                risposta = dati
        except Exception as errore:
            errori += 1
            print(f"Errore: {errore}")
            risposta = "❌ Non pubblicata: errore tecnico. Guarda il registro su GitHub Actions."
        if risposta:
            try:
                telegram(cfg["token"], "sendMessage", chat_id=messaggio["chat"]["id"], text=risposta)
            except Exception as errore:
                errori += 1
                print(f"Errore nella risposta: {errore}")
    sys.exit(1 if errori else 0)


def prova():
    esempio = (
        "https://www.amazon.it/Anker-Caricatore/dp/B0CZ7D9G8D/ref=sr_1_1?keywords=anker\n"
        "Anker Prime 250W Caricatore USB C GaN a 6 Porte\n"
        "159,99\n"
        "109,99\n"
        "#Informatica"
    )
    offerta = leggi_offerta(esempio)
    link, _ = link_affiliato(offerta["link"], "iltuotag-21")
    print(formatta(offerta, datetime.now(ZoneInfo("Europe/Rome"))))
    print("\n[bottone] 🛒 Vai all'offerta ->", link)


if __name__ == "__main__":
    prova() if "--prova" in sys.argv else main()
