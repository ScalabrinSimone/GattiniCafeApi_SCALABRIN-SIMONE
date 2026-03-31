"""
I serializers sono come i "traduttori": prendono un modello (o lista) e lo convertono in dizionario/JSON, e viceversa per input.
"""

import django
from rest_framework import serializers
from .models import Categoria, Prodotto, Ordine, OrdineProdotto
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

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

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user