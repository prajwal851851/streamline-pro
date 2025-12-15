import os
import sys
import django

sys.path.append('MovieBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieBackends.settings')
django.setup()

from streaming.models import Movie, StreamingLink
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

twenty_min_ago = timezone.now() - timedelta(minutes=20)
one_hour_ago = timezone.now() - timedelta(hours=1)

# Last 20 minutes
new_movies = Movie.objects.filter(created_at__gte=twenty_min_ago, type='movie').count()
new_shows = Movie.objects.filter(created_at__gte=twenty_min_ago, type='show').count()
updated_movies = Movie.objects.filter(updated_at__gte=twenty_min_ago, created_at__lt=twenty_min_ago, type='movie').count()
updated_shows = Movie.objects.filter(updated_at__gte=twenty_min_ago, created_at__lt=twenty_min_ago, type='show').count()
new_links = StreamingLink.objects.filter(last_checked__gte=twenty_min_ago).count()

# Last 1 hour
recent_1h = Movie.objects.filter(updated_at__gte=one_hour_ago).count()

# Type distribution
type_dist = list(Movie.objects.values('type').annotate(count=Count('type')))

# Totals
total_movies = Movie.objects.filter(type='movie').count()
total_shows = Movie.objects.filter(type='show').count()
total_all = Movie.objects.count()

print("=" * 50)
print("SCRAPER STATISTICS")
print("=" * 50)
print(f"\nLast 20 Minutes:")
print(f"   New Movies Created: {new_movies}")
print(f"   New TV Shows Created: {new_shows}")
print(f"   Existing Movies Updated: {updated_movies}")
print(f"   Existing TV Shows Updated: {updated_shows}")
print(f"   Links Updated/Added: {new_links}")

print(f"\nLast 1 Hour:")
print(f"   Total Items Updated: {recent_1h}")

print(f"\nType Distribution:")
for t in type_dist:
    print(f"   {t['type']}: {t['count']}")

print(f"\nTotal in Database:")
print(f"   Total Movies: {total_movies}")
print(f"   Total TV Shows: {total_shows}")
print(f"   Total Items: {total_all}")

# Check if spider might be running
if recent_1h > 0 or new_links > 0:
    print(f"\n[ACTIVE] Spider appears to be running")
else:
    print(f"\n[INACTIVE] Spider appears to be stopped (no updates in last hour)")

