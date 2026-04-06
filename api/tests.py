"""
TEST AUTOMATICI — Teoria e funzionamento

Prima di tutto
    # 1. Crea la migrazione mancante
    python manage.py makemigrations

    # 2. Verifica che sia stata creata (dovresti vedere un nuovo file in api/migrations/)
    # 3. Applica al tuo DB locale (opzionale, ma buona pratica)
    python manage.py migrate

    # 4. Riesegui i test
    python manage.py test

Prima di eseguire i test
    Il test test_upload_immagine_admin usa Pillow per creare un'immagine fake in memoria. Se non ce l'hai installato (il requirements.txt ha giá tutto).

Cosa sono i test automatici?
    I test automatici sono script che verificano che il codice funzioni correttamente,
    simulando le stesse operazioni che faresti a mano (es. in Postman), ma in modo
    automatico, rapido e ripetibile. Ogni volta che modifichi qualcosa nel progetto,
    puoi rieseguire tutti i test in pochi secondi per accertarti di non aver rotto niente.

Come funzionano in Django/DRF?
    Django mette a disposizione TestCase, una classe base che:
      - Crea un database temporaneo e isolato prima di ogni test (non tocca mai il tuo DB reale)
      - Esegue ogni metodo che inizia con "test_" come un test indipendente
      - Fa il rollback del DB dopo ogni test, quindi i dati non si "inquinano" tra un test e l'altro
    DRF aggiunge APIClient: un client HTTP finto che simula richieste GET/POST/PATCH/DELETE
    senza avviare un vero server. Puoi usarlo per mandare richieste e leggere la risposta.

Problema managed=False:
    I nostri modelli (Categoria, Prodotto, Ordine, OrdineProdotto) hanno managed=False
    perche' il DB e' fornito e non vogliamo che Django lo modifichi in produzione.
    Pero' durante i test Django crea un DB temporaneo da zero, e con managed=False
    non crea le tabelle -> i test fallirebbero con errore "no such table".
    SOLUZIONE: la classe ManagedModelTestMixin sovrascrive temporaneamente managed=True
    solo per la durata dei test, usando setUpClass/tearDownClass. Cosi' Django crea
    le tabelle nel DB di test, ma il DB reale non viene mai toccato.

Struttura di un test:
    Ogni metodo test_* segue il pattern AAA (Arrange, Act, Assert):
      - Arrange: prepara i dati necessari (crea utenti, prodotti, ecc.)
      - Act: esegui l'azione (manda la richiesta HTTP con APIClient)
      - Assert: verifica che la risposta sia quella attesa (status code, dati, ecc.)

Come eseguire i test:
    python manage.py test api # Tutti i test
    python manage.py test api.tests.AuthTestCase # Solo una classe
    python manage.py test api.tests.AuthTestCase.test_login_ok # Solo un test

Cosa significa un test che "passa"?
    Verde (OK) = il comportamento e' quello atteso.
    Rosso (FAIL/ERROR) = qualcosa non funziona come dovrebbe.
    Un test che fallisce non significa necessariamente un bug nel test:
    puo' significare che hai cambiato la logica della view senza aggiornare il test.

    Creating test database for alias 'default'...
    ....................
    ----------------------------------------------------------------------
    Ran 20 tests in 3.2s

    OK
    Destroying test database for alias 'default'...
    Ogni . è un test passato. Se vedi una F è un failure (assertion sbagliata), se vedi una E è un errore (eccezione non gestita).
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient  # Client HTTP finto di DRF
from rest_framework import status
from .models import Categoria, Prodotto, Ordine, OrdineProdotto
import io
from PIL import Image  # Per creare un'immagine fake in memoria per il test upload


# ---------------------------------------------------------------------------
# MIXIN — risolve il problema managed=False
# ---------------------------------------------------------------------------
class ManagedModelTestMixin:
    """
    Con managed=False Django non crea le tabelle nel DB di test.
    Questo mixin le abilita temporaneamente solo durante i test:
      - setUpClass: imposta managed=True su tutti i modelli interessati
      - tearDownClass: ripristina managed=False al termine
    In questo modo il DB di produzione non viene mai toccato.
    """
    managed_models = [Categoria, Prodotto, Ordine, OrdineProdotto]

    @classmethod
    def setUpClass(cls):
        # Abilita managed=True su ogni modello prima che Django crei il DB di test
        for model in cls.managed_models:
            model._meta.managed = True
        super().setUpClass()  # Django crea le tabelle qui

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Ripristina managed=False dopo i test
        for model in cls.managed_models:
            model._meta.managed = False


# ---------------------------------------------------------------------------
# HELPER — crea un'immagine PNG valida in memoria (senza file su disco)
# ---------------------------------------------------------------------------
def crea_immagine_fake(nome='test.png', formato='PNG'):
    """
    Crea un file immagine in memoria usando Pillow.
    io.BytesIO e' un buffer in RAM che si comporta come un file aperto.
    Serve per testare l'upload senza creare file reali sul disco.
    """
    img = Image.new('RGB', (10, 10), color=(255, 0, 0))  # Immagine 10x10 rossa
    buffer = io.BytesIO()
    img.save(buffer, format=formato)
    buffer.seek(0)  # Torna all'inizio del buffer (come un rewind)
    buffer.name = nome
    return buffer


# ===========================================================================
# TEST: AUTENTICAZIONE
# ===========================================================================
class AuthTestCase(ManagedModelTestMixin, TestCase):
    """
    Testa register, login, refresh token, logout e /me.
    Ogni metodo test_* e' indipendente: il DB viene resettato tra un test e l'altro.
    """

    def setUp(self):
        # setUp viene eseguito prima di ogni singolo test_*
        # Creiamo un utente normale e uno admin da usare nei test
        self.client = APIClient()
        self.utente = User.objects.create_user(username='mario', password='pass1234!')
        self.admin = User.objects.create_superuser(username='admin', password='admin1234!')

    def test_login_ok(self):
        """ Login con credenziali corrette -> 200 + access token """
        response = self.client.post('/api/auth/login/', {
            'username': 'mario',
            'password': 'pass1234!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)   # Deve esserci il token JWT
        self.assertIn('refresh', response.data)

    def test_login_password_sbagliata(self):
        """ Login con password errata -> 401 Unauthorized """
        response = self.client.post('/api/auth/login/', {
            'username': 'mario',
            'password': 'sbagliata'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_ok(self):
        """ Registrazione nuovo utente -> 201 Created """
        response = self.client.post('/api/auth/register/', {
            'username': 'luigi',
            'email': 'luigi@test.it',
            'password': 'luigi1234!',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='luigi').exists())

    def test_me_autenticato(self):
        """ GET /me con token valido -> 200 + dati utente """
        # Prima facciamo il login per ottenere il token
        login = self.client.post('/api/auth/login/', {'username': 'mario', 'password': 'pass1234!'})
        token = login.data['access']

        # Impostiamo il token nell'header Authorization: Bearer <token>
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'mario')

    def test_me_senza_token(self):
        """ GET /me senza token -> 401 Unauthorized """
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ===========================================================================
# TEST: PRODOTTI
# ===========================================================================
class ProdottoTestCase(ManagedModelTestMixin, TestCase):
    """
    Testa la lista pubblica, il dettaglio, la creazione (solo admin),
    i filtri e l'upload immagine.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username='admin', password='admin1234!')
        self.utente = User.objects.create_user(username='mario', password='pass1234!')

        # Dati di test: una categoria e due prodotti
        self.cat = Categoria.objects.create(nome='Bevande')
        self.p1 = Prodotto.objects.create(nome='Cappuccino', prezzo=2.5, disponibile=1, categoria=self.cat)
        self.p2 = Prodotto.objects.create(nome='Cornetto', prezzo=1.2, disponibile=0, categoria=self.cat)

    def _token_admin(self):
        """ Helper privato: fa login come admin e restituisce il token. """
        r = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'admin1234!'})
        return r.data['access']

    def _token_utente(self):
        """ Helper privato: fa login come utente normale e restituisce il token. """
        r = self.client.post('/api/auth/login/', {'username': 'mario', 'password': 'pass1234!'})
        return r.data['access']

    def test_lista_prodotti_pubblica(self):
        """ GET /prodotti/ senza token -> 200 (endpoint pubblico) """
        response = self.client.get('/api/prodotti/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Con paginazione la risposta e' un dizionario con 'results'
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_filtro_disponibile(self):
        """ GET /prodotti/?disponibile=1 -> solo prodotti disponibili """
        response = self.client.get('/api/prodotti/?disponibile=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tutti i risultati devono avere disponibile=1
        for p in response.data['results']:
            self.assertEqual(p['disponibile'], 1)

    def test_crea_prodotto_admin(self):
        """ POST /prodotti/ come admin -> 201 Created """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token_admin()}')
        response = self.client.post('/api/prodotti/', {
            'nome': 'Latte',
            'prezzo': 1.8,
            'disponibile': 1,
            'categoria': self.cat.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Prodotto.objects.filter(nome='Latte').exists())

    def test_crea_prodotto_utente_normale(self):
        """ POST /prodotti/ come utente normale -> 403 Forbidden """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token_utente()}')
        response = self.client.post('/api/prodotti/', {
            'nome': 'Latte',
            'prezzo': 1.8,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_immagine_admin(self):
        """ POST /prodotti/{id}/upload_immagine/ come admin con PNG valido -> 200 """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token_admin()}')
        immagine = crea_immagine_fake('foto.png')
        # format='multipart' dice ad APIClient di inviare come multipart/form-data
        response = self.client.post(
            f'/api/prodotti/{self.p1.id}/upload_immagine/',
            {'immagine': immagine},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('immagine_url', response.data)

    def test_upload_immagine_file_non_valido(self):
        """ POST upload con file di testo invece di immagine -> 400 Bad Request """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token_admin()}')
        # Creiamo un file finto con content_type testuale
        file_testo = io.BytesIO(b'questo non e una immagine')
        file_testo.name = 'testo.txt'
        response = self.client.post(
            f'/api/prodotti/{self.p1.id}/upload_immagine/',
            {'immagine': file_testo},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ===========================================================================
# TEST: ORDINI
# ===========================================================================
class OrdineTestCase(ManagedModelTestMixin, TestCase):
    """
    Testa creazione ordine, visibilita' (utente vede solo i propri,
    admin vede tutti) e aggiornamento stato.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username='admin', password='admin1234!')
        self.utente1 = User.objects.create_user(username='mario', password='pass1234!')
        self.utente2 = User.objects.create_user(username='luigi', password='pass1234!')

        self.cat = Categoria.objects.create(nome='Bevande')
        self.prodotto = Prodotto.objects.create(nome='Cappuccino', prezzo=2.5, disponibile=1, categoria=self.cat)

        # Creiamo un ordine per utente1 e uno per utente2 direttamente nel DB
        self.ordine_mario = Ordine.objects.create(utente_id=self.utente1.id, stato='in_attesa', totale=2.5)
        self.ordine_luigi = Ordine.objects.create(utente_id=self.utente2.id, stato='completato', totale=5.0)

    def _login(self, username, password='pass1234!'):
        """ Helper: restituisce il token Bearer per un utente. """
        r = self.client.post('/api/auth/login/', {'username': username, 'password': password})
        return r.data['access']

    def test_crea_ordine(self):
        """ POST /ordini/ con prodotto valido -> 201 Created + totale calcolato """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("mario")}')
        response = self.client.post('/api/ordini/', {
            'prodotti': [
                {'prodotto_id': self.prodotto.id, 'quantita': 2}
            ]
        }, format='json')  # format='json' invia come application/json
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Il totale deve essere prezzo * quantita = 2.5 * 2 = 5.0
        self.assertEqual(response.data['totale'], 5.0)

    def test_utente_vede_solo_propri_ordini(self):
        """ GET /ordini/ come mario -> vede solo i suoi ordini, non quelli di luigi """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("mario")}')
        response = self.client.get('/api/ordini/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tutti gli ordini restituiti devono appartenere a mario
        for ordine in response.data['results']:
            self.assertEqual(ordine['utente_id'], self.utente1.id)

    def test_admin_vede_tutti_gli_ordini(self):
        """ GET /ordini/ come admin -> vede ordini di tutti gli utenti """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("admin", "admin1234!")}')
        response = self.client.get('/api/ordini/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # mario + luigi

    def test_aggiorna_stato_admin(self):
        """ PATCH /ordini/{id}/stato/ come admin -> 200 + stato aggiornato """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("admin", "admin1234!")}')
        response = self.client.patch(
            f'/api/ordini/{self.ordine_mario.id}/stato/',
            {'stato': 'completato'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stato'], 'completato')

    def test_aggiorna_stato_utente_normale(self):
        """ PATCH /ordini/{id}/stato/ come utente normale -> 403 Forbidden """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("mario")}')
        response = self.client.patch(
            f'/api/ordini/{self.ordine_mario.id}/stato/',
            {'stato': 'completato'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stato_non_valido(self):
        """ PATCH /ordini/{id}/stato/ con stato inesistente -> 400 Bad Request """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("admin", "admin1234!")}')
        response = self.client.patch(
            f'/api/ordini/{self.ordine_mario.id}/stato/',
            {'stato': 'inventato'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ===========================================================================
# TEST: STATISTICHE ADMIN
# ===========================================================================
class StatsTestCase(ManagedModelTestMixin, TestCase):
    """
    Testa che /api/admin/stats/ restituisca i campi corretti
    e che sia accessibile solo agli admin.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username='admin', password='admin1234!')
        self.utente = User.objects.create_user(username='mario', password='pass1234!')

    def _login(self, username, password):
        r = self.client.post('/api/auth/login/', {'username': username, 'password': password})
        return r.data['access']

    def test_stats_admin(self):
        """ GET /admin/stats/ come admin -> 200 + campi attesi """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("admin", "admin1234!")}')
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica che ci siano tutti e tre i campi nella risposta
        self.assertIn('ordini_per_stato', response.data)
        self.assertIn('prodotto_piu_venduto', response.data)
        self.assertIn('incasso_oggi', response.data)

    def test_stats_utente_normale(self):
        """ GET /admin/stats/ come utente normale -> 403 Forbidden """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._login("mario", "pass1234!")}')
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stats_senza_token(self):
        """ GET /admin/stats/ senza token -> 401 Unauthorized """
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
