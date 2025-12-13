from django.db import migrations


def seed_movies(apps, schema_editor):
    Movie = apps.get_model("core", "Movie")
    sample_movies = [
        {
            "title": "City Inferno",
            "description": "A city under siege faces its darkest hour as explosions rock the skyline.",
            "year": 2024,
            "duration_minutes": 135,
            "rating": "TV-MA",
            "genre": ["Action", "Thriller"],
            "image_url": "https://images.unsplash.com/photo-1524985069026-dd778a71c7b4?w=800",
            "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "match_score": 97,
            "is_trending": True,
        },
        {
            "title": "Sunset Hearts",
            "description": "Two souls find love against the backdrop of a beautiful sunset.",
            "year": 2024,
            "duration_minutes": 112,
            "rating": "PG-13",
            "genre": ["Romance", "Drama"],
            "image_url": "https://images.unsplash.com/photo-1464375117522-1311d6a5b81f?w=800",
            "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "match_score": 94,
            "is_new": True,
        },
        {
            "title": "Cosmic Drift",
            "description": "An astronaut lost in the cosmos discovers the true meaning of humanity.",
            "year": 2024,
            "duration_minutes": 150,
            "rating": "PG-13",
            "genre": ["Sci-Fi", "Adventure"],
            "image_url": "https://images.unsplash.com/photo-1444044205806-38f3ed106c10?w=800",
            "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "match_score": 91,
            "is_trending": True,
        },
        {
            "title": "Shadow Manor",
            "description": "A haunted mansion holds secrets that refuse to stay buried.",
            "year": 2024,
            "duration_minutes": 108,
            "rating": "R",
            "genre": ["Horror", "Mystery"],
            "image_url": "https://images.unsplash.com/photo-1417436026363-aa0e5e3ba9d9?w=800",
            "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "match_score": 88,
            "is_new": True,
        },
        {
            "title": "Family Fun",
            "description": "A quirky family embarks on a hilarious adventure.",
            "year": 2024,
            "duration_minutes": 95,
            "rating": "G",
            "genre": ["Animation", "Comedy"],
            "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=800",
            "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "match_score": 95,
            "is_trending": True,
        },
        {
            "title": "Dark Files",
            "description": "Uncover the truth behind unsolved mysteries.",
            "year": 2024,
            "duration_minutes": 105,
            "rating": "TV-MA",
            "genre": ["Documentary", "Crime"],
            "image_url": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800",
            "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
            "match_score": 89,
        },
    ]
    for payload in sample_movies:
        Movie.objects.get_or_create(title=payload["title"], defaults=payload)


def remove_movies(apps, schema_editor):
    Movie = apps.get_model("core", "Movie")
    titles = [
        "City Inferno",
        "Sunset Hearts",
        "Cosmic Drift",
        "Shadow Manor",
        "Family Fun",
        "Dark Files",
    ]
    Movie.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_movies, remove_movies),
    ]

