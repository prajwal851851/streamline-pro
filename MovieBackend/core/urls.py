from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    LogoutView,
    MeView,
    MovieViewSet,
    OTPRequestView,
    OTPVerifyView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    SignupView,
    UserMovieStateViewSet,
)

app_name = "core"

router = DefaultRouter()
router.register(r"movies", MovieViewSet, basename="movie")
router.register(r"user-states", UserMovieStateViewSet, basename="user-state")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/signup", SignupView.as_view(), name="signup-noslash"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/login", LoginView.as_view(), name="login-noslash"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/logout", LogoutView.as_view(), name="logout-noslash"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/me", MeView.as_view(), name="me-noslash"),
    path("auth/otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("auth/otp/request", OTPRequestView.as_view(), name="otp-request-noslash"),
    path("auth/otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("auth/otp/verify", OTPVerifyView.as_view(), name="otp-verify-noslash"),
    path("auth/password/forgot/", PasswordResetRequestView.as_view(), name="password-forgot"),
    path("auth/password/forgot", PasswordResetRequestView.as_view(), name="password-forgot-noslash"),
    path("auth/password/reset/", PasswordResetConfirmView.as_view(), name="password-reset"),
    path("auth/password/reset", PasswordResetConfirmView.as_view(), name="password-reset-noslash"),
]
