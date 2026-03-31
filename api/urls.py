from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from . import views

router = DefaultRouter()
router.register(r'categorie', views.CategoriaViewSet) # r = regex per catturare l’ID
router.register(r'prodotti', views.ProdottoViewSet)
router.register(r'ordini', views.OrdineViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('helloREST/', views.HelloView.as_view()),  # Test base DRF

    # Autenticazione JWT
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', TokenObtainPairView.as_view()),  # DRF JWT pronto
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/me/', views.MeView.as_view()),
]