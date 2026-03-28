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
from .models import Categoria
from .serializers import CategoriaSerializer

class HelloView(APIView):
    def get(self, request): # Response invece di JsonResponse (più potente: gestisce status code, headers, serializzazione).
        categorie = Categoria.objects.all()[:3]  # Primi 3
        serializer = CategoriaSerializer(categorie, many=True)
        return Response({"message": "Dato reale dal DB (DRF)", 
        "metodo": request.method ,
        "categorie": serializer.data  # <-- JSON pronto (test serializer: modello → serializer → JSON automatico.)
        })

    def post(self, request): # request di DRF ha parser automatici (JSON, form, ecc.).
        return Response({"message": "POST ricevuto!", "metodo": request.method})