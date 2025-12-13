from django.contrib import admin

from .models import Movie, StreamingLink


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "imdb_id", "year", "type", "created_at")
    search_fields = ("title", "imdb_id")
    list_filter = ("type", "year")


@admin.register(StreamingLink)
class StreamingLinkAdmin(admin.ModelAdmin):
    list_display = ("movie", "quality", "language", "is_active", "last_checked")
    list_filter = ("quality", "language", "is_active")
    search_fields = ("movie__title", "source_url")

