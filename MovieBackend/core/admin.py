from django.contrib import admin

from .models import Movie, OTP, UserMovieState


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "year",
        "rating",
        "is_trending",
        "is_new",
        "rank",
        "match_score",
    )
    list_filter = ("is_trending", "is_new", "rating", "year", "genre")
    search_fields = ("title", "description")
    ordering = ("title",)


@admin.register(UserMovieState)
class UserMovieStateAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "movie",
        "status",
        "progress_percent",
        "in_my_list",
        "is_favorite",
        "is_downloaded",
        "last_watched_at",
    )
    list_filter = ("status", "in_my_list", "is_favorite", "is_downloaded")
    search_fields = ("user__username", "movie__title")
    autocomplete_fields = ("user", "movie")


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "code", "is_used", "created_at", "expires_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("email", "code")
