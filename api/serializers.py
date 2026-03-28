"""
I serializers sono come i "traduttori": prendono un modello (o lista) e lo convertono in dizionario/JSON, e viceversa per input.
"""

from rest_framework import serializers
from .models import Categoria, Prodotto, Ordine, OrdineProdotto
from django.contrib.auth.models import User

class CategoriaSerializer(serializers.ModelSerializer): # ModelSerializer fa 90% del lavoro automaticamente.
    class Meta:
        model = Categoria
        fields = '__all__'  # Tutti i campi (include tutto).

class ProdottoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prodotto
        fields = '__all__'

class OrdineProdottoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdineProdotto
        fields = '__all__'

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class OrdineSerializer(serializers.ModelSerializer):
    utente = SimpleUserSerializer(read_only=True)  # mostra dati utente
    prodotti = OrdineProdottoSerializer(source='ordineprodotto_set', many=True, read_only=True)  # Prodotti dell'ordine (è il reverse FK (da Ordine → lista OrdineProdotto)).

    class Meta:
        model = Ordine
        fields = '__all__'