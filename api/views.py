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
        dati = serializer.data  # Salva i dati prima di eliminare
        prodotto.delete()
        return Response(
            {"messaggio": "Prodotto eliminato con successo.", "prodotto": dati},
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
        # Risultato: [{'stato': 'in_attesa', 'totale': 3}, ...]
        ordini_per_stato = (
            Ordine.objects
            .values('stato')
            .annotate(totale=Count('id'))
            .order_by('stato')
        )
        # Trasformiamo in un dizionario {stato: count} per una risposta più leggibile
        stati = {entry['stato']: entry['totale'] for entry in ordini_per_stato}

        # --- 2. Prodotto più venduto ---
        # Dalla tabella ponte ordine_prodotto, sommiamo le quantità per ogni prodotto
        # values('prodotto') raggruppa per prodotto_id
        # annotate(Sum('quantita')) somma le quantità di ogni gruppo
        # order_by('-totale_venduto') mette il più venduto in cima (- = decrescente)
        prodotto_top = (
            OrdineProdotto.objects
            .values('prodotto__id', 'prodotto__nome')
            .annotate(totale_venduto=Sum('quantita'))
            .order_by('-totale_venduto')
            .first()  # Prende solo il primo (il più venduto)
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
        # data_ordine è un TextField nel formato 'YYYY-MM-DD HH:MM:SS'
        # Usiamo __startswith con la data odierna per filtrare gli ordini di oggi
        oggi = datetime.now().strftime('%Y-%m-%d')  # Es: '2026-04-06'
        incasso_oggi = (
            Ordine.objects
            .filter(data_ordine__startswith=oggi)
            .aggregate(totale=Sum('totale'))  # SUM(totale) su tutti gli ordini di oggi
        )['totale'] or 0  # Se non ci sono ordini oggi, aggregate ritorna None → usiamo 0

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
        Questo è il modo corretto per gestire errori di input in un ViewSet:
        non serve overridare list(), il meccanismo DRF fa tutto da solo.
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
        # Formato atteso: YYYY-MM-DD (es. ?data_da=2024-11-01&data_a=2024-11-30)
        #
        # NOTA: data_ordine è un TextField nel modello (il DB fornito salva date come testo).
        # Usiamo __gte / __lte su stringa: funziona perché il formato YYYY-MM-DD HH:MM:SS
        # è ordinabile lessicograficamente (anno > mese > giorno, sempre stessa lunghezza).
        data_da = self.request.query_params.get('data_da')
        data_a = self.request.query_params.get('data_a')

        if data_da:
            self._valida_data(data_da, 'data_da')
            # Aggiunge l'orario di inizio giornata per includere tutti gli ordini del giorno
            qs = qs.filter(data_ordine__gte=data_da + ' 00:00:00')

        if data_a:
            self._valida_data(data_a, 'data_a')
            # Aggiunge l'orario di fine giornata per includere tutti gli ordini del giorno
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
