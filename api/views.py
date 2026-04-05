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
from rest_framework.permissions import AllowAny, IsAuthenticated # Per test senza permessi
from .models import Categoria, Prodotto, Ordine
from .serializers import CategoriaSerializer, OrdineCreateSerializer, ProdottoSerializer, UserSerializer, OrdineSerializer
from .permissions import IsOwnerOrAdmin, IsAdminUser
from rest_framework import viewsets, filters
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import action

class HelloView(APIView):
    def get(self, request):
        categorie = Categoria.objects.all()[:3]
        serializer = CategoriaSerializer(categorie, many=True)
        return Response({
            "message": "Dato reale dal DB!",
            "categorie": serializer.data
        })

    def post(self, request): # request di DRF ha parser automatici (JSON, form, ecc.).
        return Response({"message": "POST ricevuto!", "metodo": request.method})


class CategoriaViewSet(viewsets.ModelViewSet): # Automaticamente GET lista e GET dettaglio (Boilerplate: codice ripetitivo (es. gestire GET/POST manualmente). ViewSet lo elimina.).
    queryset = Categoria.objects.all() # Cosa mostrare.
    serializer_class = CategoriaSerializer # Come serializzare.
    # permission_classes = [IsAdminUser] # Chi può accedere.

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

class ProdottoViewSet(viewsets.ModelViewSet): # Non ReadOnly: permette anche POST/PUT/DELETE (per admin).
    queryset = Prodotto.objects.all()
    serializer_class = ProdottoSerializer
    # permission_classes = [IsAdminUser] # Solo admin può modificare i prodotti.
    filterset_fields = ['categoria', 'disponibile'] # ?categoria=1&disponibile=1
    search_fields = ['nome', 'descrizione'] # ?search=caffe

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

class RegisterView(APIView): # Valida e crea utente (password hashed automaticamente).
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED) # Utente registrato.
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MeView(APIView): # Solo autenticati; mostra dati utente.
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
class OrdineViewSet(viewsets.ModelViewSet):
    queryset = Ordine.objects.all()  # E' statico per router
    serializer_class = OrdineSerializer # Lista/dettaglio
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
            if self.action == 'create':
                return OrdineCreateSerializer  # Diverso per POST
            return OrdineSerializer

    def perform_create(self, serializer):
        serializer.save(utente_id=self.request.user.id)

    def get_queryset(self):
        if self.request.user.is_staff:  # Admin vede tutti gli ordini.
            return Ordine.objects.all()
        return Ordine.objects.filter(utente_id=self.request.user.id)  # Utente vede solo i propri ordini.
    
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