"""
I serializers sono come i "traduttori": prendono un modello (o lista) e lo convertono in dizionario/JSON, e viceversa per input.
"""

from django.utils import timezone # Per aggiungere data_ordine automaticamente (in int)
import django
from rest_framework import serializers
from .models import Categoria, Prodotto, Ordine, OrdineProdotto
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.serializers import CurrentUserDefault

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
    utente_id = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Ordine
        fields = '__all__'
        read_only_fields = ['totale', 'data_ordine']  # calcolati auto
    
    def create(self, validated_data):
        validated_data['utente_id'] = self.context['request'].user.id
        validated_data['data_ordine'] = timezone.now()
        return super().create(validated_data)

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
    
class OrdineProdottoCreateSerializer(serializers.ModelSerializer):
    prodotto_id = serializers.PrimaryKeyRelatedField(queryset=Prodotto.objects.all())

    class Meta:
        model = OrdineProdotto
        fields = ['prodotto_id', 'quantita']

class OrdineCreateSerializer(serializers.ModelSerializer):
    prodotti = OrdineProdottoCreateSerializer(many=True)
    utente_id = serializers.HiddenField(default=CurrentUserDefault())
    
    class Meta:
        model = Ordine
        fields = '__all__'
        read_only_fields = ['totale', 'data_ordine']

    def create(self, validated_data):
        prodotti_data = validated_data.pop('prodotti')
        ordine = Ordine.objects.create(**validated_data)
        
        totale = 0
        for prod_data in prodotti_data:
            prodotto = prod_data.pop('prodotto_id')
            quantita = prod_data['quantita']
            ordine_prodotto = OrdineProdotto.objects.create(ordine=ordine, **prod_data)
            totale += prodotto.prezzo * quantita
        
        ordine.totale = totale
        ordine.save()
        return ordine