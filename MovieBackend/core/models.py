from django.conf import settings
from django.db import models


class Movie(models.Model):
    """Basic movie metadata."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    year = models.PositiveIntegerField()
    duration_minutes = models.PositiveIntegerField(default=0)
    rating = models.CharField(max_length=20, blank=True)
    genre = models.JSONField(default=list, blank=True)
    image_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    match_score = models.PositiveIntegerField(default=0)
    is_new = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    rank = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_trending", "title"]

    def __str__(self) -> str:
        return self.title


class UserMovieState(models.Model):
    """User interaction and progress for a movie."""

    STATUS_CHOICES = [
        ("watching", "Watching"),
        ("watched", "Watched"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="states")
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=None,
        null=True,
        blank=True,
    )
    progress_percent = models.PositiveSmallIntegerField(default=0)
    position_seconds = models.PositiveIntegerField(default=0)
    in_my_list = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_downloaded = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "movie")
        ordering = ["-last_watched_at"]

    def __str__(self) -> str:
        return f"{self.user or 'anonymous'} - {self.movie.title}"


class OTP(models.Model):
    PURPOSE_CHOICES = [
        ("verify", "Verify Email"),
        ("reset", "Reset Password"),
    ]

    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=16, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["email", "purpose"]),
        ]

    def __str__(self):
        return f"{self.email} - {self.purpose} - {self.code}"
