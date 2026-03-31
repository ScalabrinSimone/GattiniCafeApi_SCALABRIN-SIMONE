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
from .models import Categoria, Prodotto
from .serializers import CategoriaSerializer, ProdottoSerializer, UserSerializer
from rest_framework import viewsets, filters
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet): # Automaticamente GET lista e GET dettaglio (Boilerplate: codice ripetitivo (es. gestire GET/POST manualmente). ViewSet lo elimina.).
    queryset = Categoria.objects.all() # Cosa mostrare.
    serializer_class = CategoriaSerializer # Come serializzare.
    permission_classes = [AllowAny] # Chi può accedere.

class ProdottoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prodotto.objects.all()
    serializer_class = ProdottoSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['categoria', 'disponibile'] # ?categoria=1&disponibile=1
    search_fields = ['nome', 'descrizione'] # ?search=caffe

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