import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Movie, OTP, UserMovieState
from .serializers import (
    LoginSerializer,
    MovieSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordResetSerializer,
    SignupSerializer,
    UserMovieStateSerializer,
    UserSerializer,
)

User = get_user_model()


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def check_rate_limit(email, purpose, limit=5, minutes=60):
    window_start = timezone.now() - timedelta(minutes=minutes)
    count = OTP.objects.filter(email=email, purpose=purpose, created_at__gte=window_start).count()
    return count < limit


def send_otp(email, purpose):
    if not check_rate_limit(email, purpose):
        return None, "Too many OTP requests. Please try later."
    code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    OTP.objects.create(email=email, code=code, purpose=purpose, expires_at=expires_at)
    send_mail(
        subject="Your verification code",
        message=f"Your {purpose} code is {code}. It expires in 10 minutes.",
        from_email=None,
        recipient_list=[email],
        fail_silently=False,
    )
    return code, None


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        first_name = serializer.validated_data.get("first_name", "")
        last_name = serializer.validated_data.get("last_name", "")

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_active=False,
        )
        _, error = send_otp(email, "verify")
        if error:
            return Response({"detail": error}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "Signup successful. Verify OTP sent."}, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        update_last_login(None, user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Logged out"})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class OTPRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]
        _, error = send_otp(email, purpose)
        if error:
            return Response({"detail": error}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "OTP sent"})


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        purpose = serializer.validated_data["purpose"]

        otp = (
            OTP.objects.filter(
                email=email,
                code=code,
                purpose=purpose,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )
        if not otp:
            return Response({"detail": "Invalid or expired code."}, status=400)

        otp.is_used = True
        otp.save()

        user = User.objects.filter(email=email).first()
        if purpose == "verify":
            if not user:
                return Response({"detail": "User not found."}, status=404)
            user.is_active = True
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user": UserSerializer(user).data})

        return Response({"detail": "OTP verified"})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data={**request.data, "purpose": "reset"})
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        if not User.objects.filter(email=email).exists():
            return Response({"detail": "If the email exists, a reset code was sent."})
        _, error = send_otp(email, "reset")
        if error:
            return Response({"detail": error}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "Reset code sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        otp = (
            OTP.objects.filter(
                email=email,
                code=code,
                purpose="reset",
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )
        if not otp:
            return Response({"detail": "Invalid or expired code."}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)

        user.set_password(new_password)
        user.is_active = True
        user.save()
        otp.is_used = True
        otp.save()
        return Response({"detail": "Password reset successful."})


class MovieViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        movie = self.get_object()
        related = Movie.objects.filter(genre__overlap=movie.genre).exclude(pk=movie.pk)[:10]
        serializer = self.get_serializer(related, many=True)
        return Response(serializer.data)


class UserMovieStateViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserMovieStateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserMovieState.objects.filter(user=self.request.user).select_related("movie")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def set_state(self, request):
        user = request.user
        movie_id = request.data.get("movie_id")
        if not movie_id:
            return Response({"detail": "movie_id is required"}, status=400)
        state, _ = UserMovieState.objects.get_or_create(user=user, movie_id=movie_id)
        serializer = self.get_serializer(state, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(status=request.data.get("status") or state.status or "watching")
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def clear_history(self, request):
        user = request.user
        qs = UserMovieState.objects.filter(user=user)
        qs.update(status=None, progress_percent=0, position_seconds=0)
        return Response({"detail": "History cleared", "count": qs.count()})
