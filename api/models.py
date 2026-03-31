# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

"""
I modelli Django sono classi Python che rappresentano tabelle del database. Django usa la reflection (ORM) per tradurre query Python in SQL.

Dato che il DB è fornito, uso inspectdb per generare i modelli automaticamente dalle tabelle reali.

managed=False -> Django non proverà a creare/modificare tabelle. Usa solo il DB com’è, perfetto per DB forniti.

Pulire api/models.py: Cancella tutto e tieni solo questi 4 modelli (gli altri sono di Django, gestiti automaticamente). 
Cambi importanti (da messaggio autogenerato):
    Aggiunto id = models.AutoField(primary_key=True) dove mancava (standard Django).

    db_column='categoria_id' per FK corrette.

    on_delete=models.DO_NOTHING per non crashare su delete.


Test:
(bash)
python manage.py shell

(python)
from api.models import Categoria, Prodotto, Ordine
print("Categorie:", Categoria.objects.count())
print("Prodotti:", Prodotto.objects.count())
print("Ordini:", Ordine.objects.count())
Categoria.objects.all()[:2]  # primi 2
"""


class Categoria(models.Model):
    id = models.AutoField(primary_key=True)  # aggiungi id PK
    nome = models.TextField()
    descrizione = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categoria'

class Prodotto(models.Model):
    id = models.AutoField(primary_key=True)  # aggiungi id PK
    nome = models.TextField()
    descrizione = models.TextField(blank=True, null=True)
    prezzo = models.FloatField()
    disponibile = models.IntegerField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, models.DO_NOTHING, db_column='categoria_id', blank=True, null=True)
    immagine_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prodotto'

class Ordine(models.Model):
    id = models.AutoField(primary_key=True)  # aggiungi id PK
    utente_id = models.IntegerField()
    data_ordine = models.TextField(blank=True, null=True)  # probabilmente DateTime, ma ok per ora
    stato = models.CharField(max_length=20, default='in_attesa')  # Automaticamente messo a "in_attesa" se non specificato.
    totale = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ordine'

class OrdineProdotto(models.Model):
    id = models.AutoField(primary_key=True)  # aggiungi se non c'è
    ordine = models.ForeignKey(Ordine, models.DO_NOTHING, db_column='ordine_id')
    prodotto = models.ForeignKey(Prodotto, models.DO_NOTHING, db_column='prodotto_id')
    quantita = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ordine_prodotto'