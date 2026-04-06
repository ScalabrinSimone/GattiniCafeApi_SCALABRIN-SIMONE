# client/client.py
#
# Client Python per GattiniCafeApi.
# Esegue in sequenza: login, visualizza menu, crea un ordine.
#
# Dipendenze: pip install requests
# Uso: python client.py

import requests

# URL base dell'API. Cambia porta se Django gira su un'altra.
BASE_URL = "http://127.0.0.1:8000/api"


def login(username: str, password: str) -> str:
    """
    Esegue il login tramite JWT.
    POST /api/token/ -> {"access": "...", "refresh": "..."}
    Restituisce l'access token da usare nelle richieste successive.
    """
    risposta = requests.post(
        f"{BASE_URL}/token/",
        json={"username": username, "password": password}
    )
    # raise_for_status lancia un'eccezione se status >= 400
    # (es. 401 Unauthorized se le credenziali sono errate)
    risposta.raise_for_status()
    token = risposta.json()["access"]
    print(f"[OK] Login effettuato come '{username}'")
    return token


def visualizza_menu(token: str) -> list:
    """
    Recupera la lista dei prodotti disponibili.
    GET /api/prodotti/ -> risposta paginata: {"count": N, "results": [...]}
    Stampa id, nome, prezzo e disponibilità di ogni prodotto.
    Restituisce la lista dei prodotti per la selezione successiva.
    """
    headers = {"Authorization": f"Bearer {token}"}
    risposta = requests.get(f"{BASE_URL}/prodotti/", headers=headers)
    risposta.raise_for_status()

    dati = risposta.json()
    # La risposta è paginata grazie a DEFAULT_PAGINATION_CLASS in settings.py:
    # i prodotti sono dentro "results", non direttamente nella lista.
    # Se per qualche motivo la paginazione non fosse attiva, dati sarebbe già una lista.
    prodotti = dati.get("results", dati)

    print("\n=== MENU ===")
    for p in prodotti:
        # disponibile è un IntegerField (1 = disponibile, 0 = non disponibile)
        disponibile = "✓" if p.get("disponibile") else "✗"
        print(f"  [{p['id']}] {p['nome']} - €{p['prezzo']:.2f}  {disponibile}")
    print()

    return prodotti


def crea_ordine(token: str, prodotti_selezionati: list[dict]) -> dict:
    """
    Crea un nuovo ordine con i prodotti scelti.
    POST /api/ordini/ con body:
      {
        "prodotti": [
          {"prodotto_id": 1, "quantita": 2},
          ...
        ]
      }
    Il serializer OrdineCreateSerializer:
    - assegna automaticamente utente_id dall'utente autenticato (HiddenField)
    - calcola il totale sommando prezzo * quantita per ogni prodotto
    - imposta data_ordine e stato='in_attesa' automaticamente
    Restituisce l'ordine creato come dizionario.
    """
    headers = {"Authorization": f"Bearer {token}"}

    # Il campo si chiama "prodotto_id" (non "id") perché OrdineCreateSerializer
    # usa OrdineProdottoCreateSerializer che ha il campo prodotto_id come PrimaryKeyRelatedField
    body = {"prodotti": prodotti_selezionati}

    risposta = requests.post(
        f"{BASE_URL}/ordini/",
        json=body,
        headers=headers
    )
    risposta.raise_for_status()

    ordine = risposta.json()
    print(f"[OK] Ordine #{ordine['id']} creato! Totale: €{ordine['totale']:.2f}")
    return ordine


def main():
    # --- 1. LOGIN ---
    print("=== GattiniCafe Client ===")
    username = input("Username: ")
    password = input("Password: ")

    try:
        token = login(username, password)
    except requests.HTTPError as e:
        print(f"[ERRORE] Login fallito: {e.response.status_code} - {e.response.text}")
        return

    # --- 2. VISUALIZZA MENU ---
    try:
        prodotti = visualizza_menu(token)
    except requests.HTTPError as e:
        print(f"[ERRORE] Impossibile caricare il menu: {e.response.status_code}")
        return

    if not prodotti:
        print("Nessun prodotto disponibile.")
        return

    # --- 3. SELEZIONE PRODOTTI ---
    # Costruisce un set di id validi per validare l'input dell'utente
    ids_validi = {str(p["id"]) for p in prodotti}
    selezionati = []

    print("Inserisci i prodotti da ordinare (premi invio senza ID per confermare):")
    while True:
        id_input = input("  ID prodotto: ").strip()

        # Invio vuoto = fine selezione
        if not id_input:
            break

        if id_input not in ids_validi:
            print(f"  [!] ID '{id_input}' non valido, riprova")
            continue

        quantita_input = input(f"  Quantità per prodotto {id_input}: ").strip()
        if not quantita_input.isdigit() or int(quantita_input) < 1:
            print("  [!] Quantità non valida, riprova")
            continue

        # prodotto_id (non id) perché è il nome del campo in OrdineProdottoCreateSerializer
        selezionati.append({
            "prodotto_id": int(id_input),
            "quantita": int(quantita_input)
        })
        print(f"  [+] Aggiunto prodotto {id_input} x{quantita_input}")

    if not selezionati:
        print("Nessun prodotto selezionato, uscita.")
        return

    # --- 4. CREA ORDINE ---
    try:
        crea_ordine(token, selezionati)
    except requests.HTTPError as e:
        print(f"[ERRORE] Creazione ordine fallita: {e.response.status_code} - {e.response.text}")


if __name__ == "__main__":
    main()
