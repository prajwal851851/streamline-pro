from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import Movie, OTP, UserMovieState

User = get_user_model()


class UserMovieStateSerializer(serializers.ModelSerializer):
    movie_id = serializers.PrimaryKeyRelatedField(
        source="movie", queryset=Movie.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = UserMovieState
        fields = [
            "id",
            "movie_id",
            "status",
            "progress_percent",
            "position_seconds",
            "in_my_list",
            "is_favorite",
            "is_downloaded",
            "last_watched_at",
        ]
        read_only_fields = ["id", "last_watched_at"]

    def validate_status(self, value):
        # Allow clearing history by sending null/empty status.
        if value == "":
            return None
        return value


class MovieSerializer(serializers.ModelSerializer):
    user_state = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "description",
            "year",
            "duration_minutes",
            "rating",
            "genre",
            "image_url",
            "video_url",
            "match_score",
            "is_new",
            "is_trending",
            "rank",
            "user_state",
        ]

    def get_user_state(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            return None
        state = obj.states.filter(user=user).first()
        if not state:
            return None
        return UserMovieStateSerializer(state).data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("Account not verified.")
        attrs["user"] = user
        return attrs


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES)


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=OTP.PURPOSE_CHOICES)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

