<div align="center">

# 🐱 Gattini Cafe API

**API REST per la gestione di menu e ordini del Gattini Cafe**  
*Project by Scalabrin Simone · TPSIT · 5ªAII*

![Django](https://img.shields.io/badge/Django-6.0.3-092E20?style=flat-square&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.17.1-red?style=flat-square)
![JWT](https://img.shields.io/badge/JWT-SimpleJWT-orange?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-20%20passing-brightgreen?style=flat-square)

</div>

---

## 📖 Panoramica

Pallino, un maestoso Maine Coon con un debole per i cappuccini, ha bisogno di un sistema moderno per gestire il suo caffè felino. Questo progetto è il backend completo: autenticazione JWT, gestione del menu, ordini, statistiche admin e un client Python per consumare le API.

### Stack tecnico

| Componente | Tecnologia |
|---|---|
| Framework backend | Django 6.0.3 + Django REST Framework 3.17.1 |
| Autenticazione | JWT con `djangorestframework-simplejwt` |
| Database | SQLite (`gattini_cafe.db` fornito) |
| Filtri | `django-filter` + `SearchFilter` |
| CORS | `django-cors-headers` |
| Upload immagini | Pillow |
| Test | Django `TestCase` + DRF `APIClient` (20 test) |
| Client | Python + `requests` |

---

## 📁 Struttura del Progetto

```
GattiniCafeApi_SCALABRIN-SIMONE/
├── manage.py
├── gattini_cafe.db              ← DB SQLite con dati di esempio
├── requirements.txt
├── RichiesteREST.http           ← Chiamate per REST Client (VS Code)
├── Gattini Cafe API.postman_collection.json  ← Collection Postman
├── .gitignore
│
├── config/                      ← Configurazione Django
│   ├── settings.py
│   └── urls.py
│
├── api/                         ← App principale
│   ├── models.py                ← Categoria, Prodotto, Ordine, OrdineProdotto
│   ├── serializers.py           ← Serializers DRF
│   ├── views.py                 ← ViewSet + APIView
│   ├── urls.py                  ← Router + endpoint auth/admin
│   ├── permissions.py           ← IsOwnerOrAdmin, IsAdminUser
│   ├── tests.py                 ← 20 test automatici
│   └── migrations/
│
├── client/                      ← Client Python (bonus +10 punti)
│   ├── client.py
│   └── requirements.txt
│
└── media/                       ← Upload immagini prodotti (non versionata)
```

---

## ⚙️ Installazione

### Prerequisiti
- Python 3.10+ installato
- `git` installato

### 1. Clona il repository (creato con ssh)

```bash
git clone https://github.com/ScalabrinSimone/GattiniCafeApi_SCALABRIN-SIMONE.git
cd GattiniCafeApi_SCALABRIN-SIMONE
```

### 2. Crea e attiva il virtualenv

```bash
# Crea
python -m venv .venv

# Attiva su Linux/macOS
source .venv/bin/activate

# Attiva su Windows
.venv\Scripts\activate
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Configura il database

Il file `gattini_cafe.db` è già presente nel repository con dati di esempio.  
Django è già configurato per usarlo in `config/settings.py`.

Poiché la struttura del DB è preesistente, applica le migrazioni senza modificare il database:

```bash
python manage.py migrate --fake
```

Poi crea fisicamente le tabelle per la blacklist JWT (necessarie per il login):

```bash
python manage.py migrate --fake token_blacklist zero
python manage.py migrate token_blacklist
```

> **Nota:** `--fake` dice a Django di registrare le migrazioni come eseguite senza applicarle fisicamente, perché le tabelle esistono già nel DB fornito.
> Il secondo step è necessario perché le tabelle di `token_blacklist` non sono incluse nel DB fornito e devono essere create da zero.


### 5. Crea un superuser

Le password degli utenti di test nel DB sono state resettate, quindi serve creare un admin:

```bash
python manage.py createsuperuser
```

Cosniglio di usare le seguenti credenziali (preinserite su postman):
- Nome utente: `admin`.
- Email: `*nessuna*`.
- Password: `admin1234`.

> **Nota:** La password verrá dichiarata come non sicura da django, premere y per metterla senza fare controllo password.
---

## 🚀 Avvio del server

```bash
python manage.py runserver
```

Il server sarà disponibile su: **http://127.0.0.1:8000**

---

## 🔑 Credenziali per i test (consigliati per test veloci su postman/estensione)

> Crea il superuser con `createsuperuser` come mostrato sopra, oppure usa queste credenziali di esempio se presenti nel DB:

| Ruolo | Username | Password |
|---|---|---|
| Admin | `admin` | definita al createsuperuser |
| Utente normale | `pallino` | `Miagola123!` |

---

## 🛠️ Come testare le API

Hai quattro modi per fare chiamate alle API, scegli quello che preferisci.

---

### Opzione 1 — Postman (consigliato, interfaccia grafica)

Nel repository è inclusa una collection Postman pronta all'uso con tutte le chiamate già configurate, incluso il salvataggio automatico del token JWT.

1. Apri [Postman](https://www.postman.com/downloads/)
2. Clicca **Import** → seleziona il file `Gattini Cafe API.postman_collection.json` dalla root del progetto
3. Inserisci nelle **variabili della collezione** e inserire su `baseUrl: http://127.0.0.1:8000` 
4. Avvia il server Django (`python manage.py runserver`)
5. Esegui prima la chiamata **Login** per salvare il token, poi tutte le altre

> Il token viene salvato automaticamente come variabile della collection e inserito nell'header `Authorization: Bearer` di ogni richiesta protetta.

---

### Opzione 2 — REST Client su VS Code (comodo, zero installazioni extra)

Nel repository è incluso il file `RichiesteREST.http` con tutte le chiamate già scritte, inclusa la gestione automatica dei token JWT tra una chiamata e l'altra.

1. Installa l'estensione **[REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)** di Huachao Mao su VS Code
2. Apri il file `RichiesteREST.http`
3. Avvia il server Django
4. Clicca **"Send Request"** sopra ogni blocco per eseguirlo

Il file gestisce i token in modo intelligente: esegui prima il blocco `# @name login`, poi tutte le richieste successive usano `{{login.response.body.access}}` in automatico senza dover copiare nulla a mano.

---

### Opzione 3 — curl (terminale, nessun tool esterno)

Se non vuoi installare nulla, puoi usare `curl` direttamente dal terminale.

**Login:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "pallino", "password": "Miagola123!"}'
```

**Lista prodotti (pubblico, nessun token necessario):**
```bash
curl http://127.0.0.1:8000/api/prodotti/
```

Copia il valore di `access` dalla risposta del login e usalo così nelle chiamate protette:

**Crea un ordine:**
```bash
curl -X POST http://127.0.0.1:8000/api/ordini/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "note": "Senza lattosio",
    "prodotti": [
      {"prodotto_id": 1, "quantita": 2}
    ]
  }'
```

---

### Opzione 4 — Client Python (incluso nel repo)

Per chi preferisce uno script interattivo da terminale, c'è il client Python nella cartella `client/`. Fa login, mostra il menu e crea un ordine in modo guidato — senza dover scrivere nessuna chiamata a mano. Vedi la sezione [Client Python](#-client-python) più sotto.

---

## 📡 Endpoint disponibili

### Autenticazione

| Metodo | Endpoint | Auth | Descrizione |
|---|---|---|---|
| `POST` | `/api/auth/register/` | ❌ | Registra un nuovo utente |
| `POST` | `/api/auth/login/` | ❌ | Login → restituisce `access` + `refresh` token |
| `POST` | `/api/auth/token/refresh/` | ❌ | Rinnova l'access token |
| `GET` | `/api/auth/me/` | ✅ JWT | Dati dell'utente loggato |
| `POST` | `/api/auth/logout/` | ✅ JWT | Invalida il refresh token |

### Menu (pubblici)

| Metodo | Endpoint | Auth | Descrizione |
|---|---|---|---|
| `GET` | `/api/categorie/` | ❌ | Lista categorie |
| `GET` | `/api/categorie/{id}/` | ❌ | Dettaglio categoria |
| `GET` | `/api/prodotti/` | ❌ | Lista prodotti (con filtri e paginazione) |
| `GET` | `/api/prodotti/{id}/` | ❌ | Dettaglio prodotto |

**Query parameters per `/api/prodotti/`:**
- `?categoria=<id>` — filtra per categoria
- `?disponibile=true` (o `1`) — solo prodotti disponibili
- `?search=<testo>` — ricerca per nome o descrizione
- `?page=<n>` — paginazione (10 per pagina di default)
- `?page_size=<n>` — modifica la dimensione della pagina (max 100)

### Gestione menu (solo admin)

| Metodo | Endpoint | Auth | Descrizione |
|---|---|---|---|
| `POST` | `/api/prodotti/` | ✅ Admin | Crea prodotto |
| `PUT/PATCH` | `/api/prodotti/{id}/` | ✅ Admin | Modifica prodotto |
| `DELETE` | `/api/prodotti/{id}/` | ✅ Admin | Elimina prodotto |
| `POST` | `/api/prodotti/{id}/upload_immagine/` | ✅ Admin | Carica immagine (multipart) |
| `POST` | `/api/categorie/` | ✅ Admin | Crea categoria |
| `PUT/PATCH` | `/api/categorie/{id}/` | ✅ Admin | Modifica categoria |
| `DELETE` | `/api/categorie/{id}/` | ✅ Admin | Elimina categoria |

### Ordini (utente autenticato)

| Metodo | Endpoint | Auth | Descrizione |
|---|---|---|---|
| `GET` | `/api/ordini/` | ✅ JWT | Lista ordini (propri o tutti se admin) |
| `POST` | `/api/ordini/` | ✅ JWT | Crea ordine |
| `GET` | `/api/ordini/{id}/` | ✅ JWT | Dettaglio ordine |
| `PATCH` | `/api/ordini/{id}/stato/` | ✅ Admin | Aggiorna stato ordine |

**Query parameters per `/api/ordini/`:**
- `?data_da=YYYY-MM-DD` — filtra ordini da questa data
- `?data_a=YYYY-MM-DD` — filtra ordini fino a questa data

### Admin

| Metodo | Endpoint | Auth | Descrizione |
|---|---|---|---|
| `GET` | `/api/admin/stats/` | ✅ Admin | Statistiche: ordini per stato, prodotto più venduto, incasso di oggi |

---

## 🧪 Test automatici

Il progetto include **20 test automatici** che coprono autenticazione, prodotti, ordini e statistiche.

```bash
# Esegui tutti i test
python manage.py test

# Solo i test di autenticazione
python manage.py test api.tests.AuthTestCase

# Solo i test sugli ordini
python manage.py test api.tests.OrdineTestCase

# Verbose (mostra il nome di ogni test)
python manage.py test --verbosity=2
```

Output atteso:
```
Found 20 test(s).
Creating test database for alias 'default'...
....................
----------------------------------------------------------------------
Ran 20 tests in ~4s

OK
Destroying test database for alias 'default'...
```

### Copertura dei test

| Suite | Test | Cosa verifica |
|---|---|---|
| `AuthTestCase` | 5 | Login OK/fallito, register, `/me` con e senza token |
| `ProdottoTestCase` | 6 | Lista pubblica, filtro disponibile, crea (admin vs utente), upload immagine |
| `OrdineTestCase` | 6 | Crea ordine + totale, visibilità per ruolo, aggiorna stato, stato invalido |
| `StatsTestCase` | 3 | Stats accessibili solo ad admin, campi risposta corretti |

---

## 🐍 Client Python

Nella cartella `client/` c'è uno script Python che consuma le API simulando un cliente del Gattini Cafe.

### Cosa fa

1. **Login** → ottiene il token JWT e lo salva in memoria per tutte le richieste successive
2. **Visualizza il menu** → lista prodotti con disponibilità e prezzi
3. **Crea un ordine** → seleziona prodotti e quantità in modo interattivo

### Come avviarlo

```bash
cd client
pip install -r requirements.txt
python client.py
```

### Esempio di sessione

```
=== GattiniCafe Client ===
Username: pallino
Password: ········
[OK] Login effettuato come 'pallino'

=== MENU ===
  [1] Cappuccino - €2.50  ✓
  [2] Cornetto - €1.20  ✓
  [3] Matcha Latte - €3.80  ✓

Inserisci i prodotti da ordinare (premi invio senza ID per confermare):
  ID prodotto: 1
  Quantità per prodotto 1: 2
  [+] Aggiunto prodotto 1 x2
  ID prodotto:
[OK] Ordine #42 creato! Totale: €5.00
```

---

## 🔒 Logica dei permessi

| Risorsa | Anonimo | Utente loggato | Admin (`is_staff`) |
|---|---|---|---|
| `GET /prodotti/`, `GET /categorie/` | ✅ | ✅ | ✅ |
| `POST/PUT/DELETE /prodotti/`, `POST/PUT/DELETE /categorie/` | ❌ | ❌ | ✅ |
| `GET /ordini/` | ❌ | ✅ (solo propri) | ✅ (tutti) |
| `POST /ordini/` | ❌ | ✅ | ✅ |
| `PATCH /ordini/{id}/stato/` | ❌ | ❌ | ✅ |
| `GET /admin/stats/` | ❌ | ❌ | ✅ |

---

## 🎁 Funzionalità bonus implementate

- ✅ **Paginazione** — lista prodotti e ordini paginata (10/pagina, max 100 con `?page_size=`)
- ✅ **Statistiche admin** — `GET /api/admin/stats/`
- ✅ **Upload immagine** — `POST /api/prodotti/{id}/upload_immagine/`
- ✅ **Filtro ordini per data** — `?data_da=` e `?data_a=`
- ✅ **Test automatici** — 20 test con Django TestCase
- ✅ **Client Python** — script interattivo in `client/`

---

## 📦 Dipendenze

```
Django==6.0.3
djangorestframework==3.17.1
djangorestframework_simplejwt==5.5.1
django-cors-headers==4.9.0
django-filter==25.2
pillow==12.2.0
PyJWT==2.12.1
```

---

<div align="center">
  <sub>Progetto realizzato da <strong>Simone Scalabrin</strong> · ITIS A. Rossi · 5ªAII</sub><br>
  <sub>🐾 Pallino il Maine Coon approva questo README</sub>
</div>
