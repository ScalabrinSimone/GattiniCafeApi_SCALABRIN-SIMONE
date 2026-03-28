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
from rest_framework.permissions import AllowAny # Per test senza permessi
from .models import Categoria, Prodotto
from .serializers import CategoriaSerializer, ProdottoSerializer
from rest_framework import viewsets, filters

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