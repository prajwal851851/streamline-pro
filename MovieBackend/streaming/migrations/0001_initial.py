from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Movie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("imdb_id", models.CharField(help_text="e.g., 'tt0111161'", max_length=20, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("year", models.IntegerField(blank=True, null=True)),
                (
                    "type",
                    models.CharField(
                        choices=[("movie", "Movie"), ("show", "Show"), ("episode", "Episode")],
                        default="movie",
                        max_length=10,
                    ),
                ),
                ("poster_url", models.URLField(blank=True, max_length=500, null=True)),
                ("synopsis", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="StreamingLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "quality",
                    models.CharField(
                        choices=[("CAM", "CAM"), ("HD", "HD"), ("720p", "720p"), ("1080p", "1080p"), ("4K", "4K")],
                        default="HD",
                        max_length=10,
                    ),
                ),
                ("language", models.CharField(default="EN", max_length=10)),
                ("source_url", models.URLField(max_length=1000)),
                ("is_active", models.BooleanField(default=True)),
                ("last_checked", models.DateTimeField(blank=True, null=True)),
                (
                    "movie",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="links", to="streaming.movie"),
                ),
            ],
        ),
    ]

