"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


def hello_view(request):
    # View base semplice per capire il flusso. NO DRF (APIView)
    return JsonResponse({"message": "Ciao da Django!", "metodo": request.method})


class HomeView(APIView): # Metto APIView e non request per avere la parte grafica di DRF.
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
        "benvenuto": "Gattini Cafe API 🐱",
        "versione": "1.0",
        "endpoints": {
            "autenticazione": {
                "POST /api/auth/register/": "Registrazione nuovo utente",
                "POST /api/auth/login/": "Login — restituisce access + refresh token",
                "POST /api/auth/token/refresh/": "Rinnova access token",
                "POST /api/auth/logout/": "[JWT] Logout — invalida refresh token",
                "GET  /api/auth/me/": "[JWT] Dati utente autenticato"
            },
            "menu_pubblico": {
                "GET /api/categorie/": "Lista categorie",
                "GET /api/categorie/{id}/": "Dettaglio categoria",
                "GET /api/prodotti/": "Lista prodotti (?categoria=id &disponibile=1 &search=testo)",
                "GET /api/prodotti/{id}/": "Dettaglio prodotto"
            },
            "ordini_utente": {
                "GET  /api/ordini/": "[JWT] Lista ordini — admin vede tutti, utente solo i propri",
                "POST /api/ordini/": "[JWT] Crea ordine (totale calcolato automaticamente)",
                "GET  /api/ordini/{id}/": "[JWT] Dettaglio ordine"
            },
            "solo_admin": {
                "PATCH  /api/ordini/{id}/stato/": "[JWT Admin] Aggiorna stato ordine",
                "POST   /api/categorie/": "[JWT Admin] Crea categoria",
                "PUT    /api/categorie/{id}/": "[JWT Admin] Modifica categoria",
                "DELETE /api/categorie/{id}/": "[JWT Admin] Elimina categoria",
                "POST   /api/prodotti/": "[JWT Admin] Crea prodotto",
                "PUT    /api/prodotti/{id}/": "[JWT Admin] Modifica prodotto",
                "PATCH  /api/prodotti/{id}/": "[JWT Admin] Aggiornamento parziale prodotto",
                "DELETE /api/prodotti/{id}/": "[JWT Admin] Elimina prodotto"
            }
        }
    })


urlpatterns = [
    path('', HomeView.as_view()),           # 127.0.0.1:8000/ — home con lista endpoint
    path('admin/', admin.site.urls),
    path('api/hello/', hello_view),         # test base Django (no DRF)
    path('api/', include('api.urls')),      # tutti gli endpoint API
]
