from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    RegisterUserView,
    ActivateView,
    LogoutView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("activate/", ActivateView.as_view(), name="activate"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

app_name = "user"
