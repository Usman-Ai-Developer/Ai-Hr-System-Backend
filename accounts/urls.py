from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LogoutView,
    MeView,
    MeAvatarView,
    MyTokenObtainPairView,
    hr_dashboard
)

urlpatterns = [
    # =========================
    # 🔐 AUTHENTICATION
    # =========================
    path("login/", MyTokenObtainPairView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),

    # =========================
    # 👤 USER PROFILE
    # =========================
    path("me/", MeView.as_view(), name="me"),
    path("me/avatar/", MeAvatarView.as_view(), name="me-avatar"),   # ✅ avatar upload

    # =========================
    # 🔓 LOGOUT
    # =========================
    path("logout/", LogoutView.as_view(), name="logout"),

    # =========================
    # 🧑‍💼 HR OPERATIONS
    # =========================
    path("hr-dashboard/", hr_dashboard, name="hr-dashboard"),
    # =========================
    # 🔄 TOKEN REFRESH
    # =========================
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]