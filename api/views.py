from django.shortcuts import render

"""
Perché DRF è meglio

    Metodi separati: get(), post(), put(), delete() — logico e scalabile.

    Response automatica: sempre JSON, gestisce content-type.

    Status code: return Response(data, status=status.HTTP_201_CREATED).

    Request parser: request.data per JSON body.

    Permissions: ereditabile (anonimo, autenticato, admin).

    Throttling, paginazione già pronti.

Questa è la base di tutti gli endpoint del tuo progetto
"""

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Categoria, Prodotto, Ordine, OrdineProdotto
from .serializers import CategoriaSerializer, OrdineCreateSerializer, ProdottoSerializer, UserSerializer, OrdineSerializer
from .permissions import IsOwnerOrAdmin, IsAdminUser
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from django.db.models import Count, Sum  # Per le aggregazioni ORM (COUNT e SUM in SQL)
from django.conf import settings         # Per leggere MEDIA_ROOT e MEDIA_URL
import os                                # Per creare cartelle e costruire percorsi file


class ApiRootView(APIView):
    # Mostra tutti gli endpoint disponibili nell'interfaccia DRF del browser
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "categorie": request.build_absolute_uri('categorie/'),
            "prodotti": request.build_absolute_uri('prodotti/'),
            "ordini": request.build_absolute_uri('ordini/'),
            "auth": {
                "register": request.build_absolute_uri('auth/register/'),
                "login": request.build_absolute_uri('auth/login/'),
                "refresh": request.build_absolute_uri('auth/token/refresh/'),
                "logout": request.build_absolute_uri('auth/logout/'),
                "me": request.build_absolute_uri('auth/me/'),
            },
            "admin": {
                "stats": request.build_absolute_uri('admin/stats/'),
            }
        })


class HelloView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categorie = Categoria.objects.all()[:3]
        serializer = CategoriaSerializer(categorie, many=True)
        return Response({
            "message": "Dato reale dal DB!",
            "categorie": serializer.data
        })

    def post(self, request):
        return Response({"message": "POST ricevuto!", "metodo": request.method})


class ProdottoFilter(django_filters.FilterSet):
    """
    Filtro custom per Prodotto.
    Il campo disponibile nel modello e' IntegerField (0/1), non BooleanField.
    Questo filtro accetta sia la forma numerica (?disponibile=1)
    che quella booleana (?disponibile=true / ?disponibile=false),
    mappando entrambe al valore intero corretto prima della query SQL.
    """
    disponibile = django_filters.CharFilter(method='filter_disponibile')

    def filter_disponibile(self, queryset, name, value):
        if value.lower() in ['true', '1']:
            return queryset.filter(disponibile=1)
        if value.lower() in ['false', '0']:
            return queryset.filter(disponibile=0)
        return queryset

    class Meta:
        model = Prodotto
        fields = ['categoria', 'disponibile']


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class ProdottoViewSet(viewsets.ModelViewSet):
    queryset = Prodotto.objects.all()
    serializer_class = ProdottoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProdottoFilter
    search_fields = ['nome', 'descrizione']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def destroy(self, request, *args, **kwargs):
        # Sovrascrive il destroy standard (che ritorna 204 senza corpo)
        # per restituire un JSON di conferma con i dati del prodotto eliminato.
        prodotto = self.get_object()
        serializer = self.get_serializer(prodotto)
        dati = serializer.data
        prodotto.delete()
        return Response(
            {"messaggio": "Prodotto eliminato con successo.", "prodotto": dati},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='upload_immagine', permission_classes=[IsAdminUser])
    def upload_immagine(self, request, pk=None):
        """
        POST /api/prodotti/{id}/upload_immagine/
        Permette all'admin di caricare un'immagine per un prodotto.

        PROBLEMA: immagine_url nel modello e' un TextField (managed=False, DB fornito).
        Non possiamo usare ImageField di Django perche' richiederebbe una migration
        su una tabella che non gestiamo (managed=False).

        SOLUZIONE: gestiamo l'upload manualmente in 3 passi:
          1. Leggiamo il file da request.FILES (multipart/form-data)
          2. Lo salviamo fisicamente in MEDIA_ROOT/prodotti/<nome_file>
          3. Aggiorniamo immagine_url del prodotto con il percorso URL pubblico

        Il file e' salvato sul disco locale. Non va in git (media/ e' nel .gitignore).
        In produzione si userebbe un storage esterno (S3, Cloudinary, ecc.).
        """
        prodotto = self.get_object()

        # request.FILES contiene i file inviati con Content-Type: multipart/form-data
        # Il campo del form deve chiamarsi 'immagine'
        immagine = request.FILES.get('immagine')

        if not immagine:
            return Response(
                {"error": "Nessun file ricevuto. Invia il file nel campo 'immagine'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Valida il tipo di file: accetta solo immagini comuni
        tipi_consentiti = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if immagine.content_type not in tipi_consentiti:
            return Response(
                {"error": f"Tipo file non supportato: {immagine.content_type}. Usa JPEG, PNG, GIF o WEBP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Costruisce il percorso fisico dove salvare il file
        # MEDIA_ROOT e' definito in settings.py (es. <progetto>/media/)
        cartella = os.path.join(settings.MEDIA_ROOT, 'prodotti')
        os.makedirs(cartella, exist_ok=True)  # Crea la cartella se non esiste

        # Usa il nome originale del file (es. cappuccino.jpg)
        # In un progetto reale si userebbe un UUID per evitare collisioni di nomi
        percorso_file = os.path.join(cartella, immagine.name)

        # Scrive il file sul disco chunk per chunk (efficiente anche per file grandi)
        with open(percorso_file, 'wb') as f:
            for chunk in immagine.chunks():
                f.write(chunk)

        # Costruisce l'URL pubblico: MEDIA_URL + sottocartella + nome file
        # Es: /media/prodotti/cappuccino.jpg -> http://127.0.0.1:8000/media/prodotti/cappuccino.jpg
        url_immagine = request.build_absolute_uri(
            settings.MEDIA_URL + 'prodotti/' + immagine.name
        )

        # Aggiorna il campo immagine_url nel DB con l'URL pubblico
        prodotto.immagine_url = url_immagine
        prodotto.save()

        return Response(
            {"messaggio": "Immagine caricata con successo.", "immagine_url": url_immagine},
            status=status.HTTP_200_OK
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    # Invalida il refresh token mettendolo in blacklist.
    # L'access token rimane valido fino a scadenza naturale,
    # ma senza refresh il client non può rinnovarlo → sessione terminata.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout effettuato."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Token non valido."}, status=status.HTTP_400_BAD_REQUEST)


class AdminStatsView(APIView):
    """
    Endpoint statistiche per admin: GET /api/admin/stats/
    Richiede autenticazione JWT e is_staff=True.

    Restituisce:
    - ordini_per_stato: quanti ordini ci sono per ogni stato
    - prodotto_piu_venduto: il prodotto con la somma di quantità ordinata più alta
    - incasso_oggi: somma dei totali degli ordini creati oggi
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        # --- 1. Ordini per stato ---
        # values('stato') raggruppa per stato (GROUP BY stato in SQL)
        # annotate(Count('id')) aggiunge il conteggio per ogni gruppo
        ordini_per_stato = (
            Ordine.objects
            .values('stato')
            .annotate(totale=Count('id'))
            .order_by('stato')
        )
        stati = {entry['stato']: entry['totale'] for entry in ordini_per_stato}

        # --- 2. Prodotto più venduto ---
        # Dalla tabella ponte ordine_prodotto, sommiamo le quantità per ogni prodotto
        # La doppia underscore (prodotto__nome) è la sintassi Django per fare JOIN
        prodotto_top = (
            OrdineProdotto.objects
            .values('prodotto__id', 'prodotto__nome')
            .annotate(totale_venduto=Sum('quantita'))
            .order_by('-totale_venduto')
            .first()
        )

        if prodotto_top:
            prodotto_info = {
                "id": prodotto_top['prodotto__id'],
                "nome": prodotto_top['prodotto__nome'],
                "quantita_totale_venduta": prodotto_top['totale_venduto'],
            }
        else:
            prodotto_info = None

        # --- 3. Incasso totale del giorno ---
        # data_ordine è TextField nel formato 'YYYY-MM-DD HH:MM:SS'
        # startswith filtra tutti gli orari dello stesso giorno in modo semplice
        oggi = datetime.now().strftime('%Y-%m-%d')
        incasso_oggi = (
            Ordine.objects
            .filter(data_ordine__startswith=oggi)
            .aggregate(totale=Sum('totale'))
        )['totale'] or 0

        return Response({
            "ordini_per_stato": stati,
            "prodotto_piu_venduto": prodotto_info,
            "incasso_oggi": round(incasso_oggi, 2),
        })


class OrdineViewSet(viewsets.ModelViewSet):
    queryset = Ordine.objects.all()
    serializer_class = OrdineSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrdineCreateSerializer
        return OrdineSerializer

    def _valida_data(self, valore, nome_param):
        """
        Valida che il valore sia nel formato YYYY-MM-DD.
        Se non lo è, lancia ValidationError che DRF intercetta
        e restituisce automaticamente come risposta 400 BAD REQUEST.
        """
        try:
            datetime.strptime(valore, '%Y-%m-%d')
        except ValueError:
            raise ValidationError({
                nome_param: f"Formato non valido: '{valore}'. Usa YYYY-MM-DD (es. 2026-04-06)."
            })

    def get_queryset(self):
        # Base: admin vede tutti gli ordini, utente normale solo i propri
        if self.request.user.is_staff:
            qs = Ordine.objects.all()
        else:
            qs = Ordine.objects.filter(utente_id=self.request.user.id)

        # Filtro per data: legge ?data_da= e ?data_a= dai query param
        # NOTA: data_ordine è TextField, quindi usiamo __gte/__lte su stringa.
        # Funziona perché YYYY-MM-DD HH:MM:SS è ordinabile lessicograficamente.
        data_da = self.request.query_params.get('data_da')
        data_a = self.request.query_params.get('data_a')

        if data_da:
            self._valida_data(data_da, 'data_da')
            qs = qs.filter(data_ordine__gte=data_da + ' 00:00:00')

        if data_a:
            self._valida_data(data_a, 'data_a')
            qs = qs.filter(data_ordine__lte=data_a + ' 23:59:59')

        return qs

    """
    @action crea un endpoint extra su un ViewSet esistente, al di fuori dei 7 standard
    (list, create, retrieve, update, partial_update, destroy).
    detail=True  → agisce su un oggetto specifico: /api/ordini/{id}/stato/
    detail=False → agisce sulla lista: /api/ordini/stato/ (non il nostro caso)
    url_path     → il pezzo di URL aggiunto dopo l'id: "stato" → /api/ordini/1/stato/
    methods      → solo PATCH accettato
    permission_classes → sovrascrive i permessi del ViewSet solo per questa action
    """

    @action(detail=True, methods=['patch'], url_path='stato', permission_classes=[IsAdminUser])
    def aggiorna_stato(self, request, pk=None):
        ordine = self.get_object()
        stato = request.data.get('stato')
        stati_validi = ['in_attesa', 'in_preparazione', 'completato', 'annullato']
        if stato not in stati_validi:
            return Response(
                {'error': f'Stato non valido. Valori: {stati_validi}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ordine.stato = stato
        ordine.save()
        return Response(OrdineSerializer(ordine).data)
