from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from . import views

router = DefaultRouter()
router.register(r'categorie', views.CategoriaViewSet)
router.register(r'prodotti', views.ProdottoViewSet)
router.register(r'ordini', views.OrdineViewSet)

urlpatterns = [
    path('', views.ApiRootView.as_view()),       # api/ — lista endpoint nel browser DRF
    path('', include(router.urls)),              # api/categorie/, api/prodotti/, api/ordini/
    path('helloREST/', views.HelloView.as_view()),

    # Autenticazione JWT
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('auth/me/', views.MeView.as_view()),
]
