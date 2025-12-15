"""
Script to check scraping progress - shows current movie count and links
"""
import os
import sys
import django

sys.path.append('MovieBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieBackends.settings')
django.setup()

from streaming.models import Movie, StreamingLink
from django.utils import timezone
from datetime import timedelta

# Get current stats
total = Movie.objects.count()
with_url = Movie.objects.exclude(original_detail_url__isnull=True).exclude(original_detail_url='').count()
active_links = StreamingLink.objects.filter(is_active=True).count()
inactive_links = StreamingLink.objects.filter(is_active=False).count()

# Count by type
movies = Movie.objects.filter(type='movie').count()
shows = Movie.objects.filter(type='show').count()

# Recent movies (last hour)
one_hour_ago = timezone.now() - timedelta(hours=1)
recent = Movie.objects.filter(created_at__gte=one_hour_ago).count()
recent_with_url = Movie.objects.filter(created_at__gte=one_hour_ago).exclude(original_detail_url__isnull=True).exclude(original_detail_url='').count()

print("=" * 50)
print("SCRAPING PROGRESS")
print("=" * 50)
print(f"\nTotal Movies/TV Shows: {total}")
print(f"  - Movies: {movies}")
print(f"  - TV Shows: {shows}")
print(f"\nMovies with original_detail_url: {with_url} ({with_url/total*100:.1f}%)")
print(f"Movies without URL: {total - with_url}")
print(f"\nStreaming Links:")
print(f"  - Active: {active_links}")
print(f"  - Inactive: {inactive_links}")
print(f"  - Total: {active_links + inactive_links}")
print(f"\nRecent Activity (last hour):")
print(f"  - New movies: {recent}")
print(f"  - With URLs: {recent_with_url}")
print("=" * 50)

