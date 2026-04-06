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
from .models import Categoria, Prodotto, Ordine
from .serializers import CategoriaSerializer, OrdineCreateSerializer, ProdottoSerializer, UserSerializer, OrdineSerializer
from .permissions import IsOwnerOrAdmin, IsAdminUser
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime


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


class OrdineViewSet(viewsets.ModelViewSet):
    queryset = Ordine.objects.all()
    serializer_class = OrdineSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrdineCreateSerializer
        return OrdineSerializer

    def get_queryset(self):
        # Base: admin vede tutti gli ordini, utente normale solo i propri
        if self.request.user.is_staff:
            qs = Ordine.objects.all()
        else:
            qs = Ordine.objects.filter(utente_id=self.request.user.id)

        # Filtro per data: legge ?data_da= e ?data_a= dai query param
        # Il formato atteso è YYYY-MM-DD (es. ?data_da=2024-11-01&data_a=2024-11-30)
        data_da = self.request.query_params.get('data_da')
        data_a = self.request.query_params.get('data_a')

        try:
            # __date estrae solo la parte data dal DateTimeField, ignorando l'orario
            if data_da:
                # Valida il formato prima di passarlo a Django
                datetime.strptime(data_da, '%Y-%m-%d')
                qs = qs.filter(data_ordine__date__gte=data_da)
            if data_a:
                datetime.strptime(data_a, '%Y-%m-%d')
                qs = qs.filter(data_ordine__date__lte=data_a)
        except ValueError:
            # Se il formato è sbagliato (es. 01-11-2024), restituiamo
            # un queryset vuoto — l'errore viene gestito nella risposta
            # dall'override di list() qui sotto
            self._data_filter_error = True
            return qs.none()

        return qs

    def list(self, request, *args, **kwargs):
        # Se get_queryset ha rilevato un formato data errato, risponde 400
        if getattr(self, '_data_filter_error', False):
            return Response(
                {"error": "Formato data non valido. Usa YYYY-MM-DD (es. 2024-11-01)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().list(request, *args, **kwargs)

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
