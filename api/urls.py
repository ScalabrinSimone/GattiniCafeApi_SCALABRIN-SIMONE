from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categorie', views.CategoriaViewSet) # r = regex per catturare l’ID
router.register(r'prodotti', views.ProdottoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('helloREST/', views.HelloView.as_view()),  # Test base DRF
]