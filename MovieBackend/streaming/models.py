from django.db import models


class Movie(models.Model):
    imdb_id = models.CharField(max_length=20, unique=True, help_text="e.g., 'tt0111161'")
    title = models.CharField(max_length=255)
    year = models.IntegerField(null=True, blank=True)
    TYPE_CHOICES = [
        ("movie", "Movie"),
        ("show", "Show"),
        ("episode", "Episode"),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="movie")
    poster_url = models.URLField(max_length=500, null=True, blank=True)
    synopsis = models.TextField(null=True, blank=True)
    original_detail_url = models.URLField(max_length=1000, null=True, blank=True, help_text="Original source URL from 1flix.to (e.g., https://1flix.to/watch-movie/...)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.year})"


class StreamingLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="links")
    QUALITY_CHOICES = [
        ("CAM", "CAM"),
        ("HD", "HD"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("4K", "4K"),
    ]
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default="HD")
    language = models.CharField(max_length=10, default="EN")
    source_url = models.URLField(max_length=1000)
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.movie.title} - {self.quality}"

