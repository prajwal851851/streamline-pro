"""
Script to clean up movies/TV shows with no streaming links or only broken/dead links.
Removes movies from the database that have:
1. No streaming links at all
2. Only links that are dead/broken (contain error messages)
"""
import os
import sys
import django

# Setup Django
sys.path.append('MovieBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieBackends.settings')
django.setup()

from streaming.models import Movie, StreamingLink

def cleanup_dead_links():
    """Remove movies/TV shows with no links or only dead links"""
    
    # Find all movies with no links
    movies_without_links = Movie.objects.filter(links__isnull=True).distinct()
    count_no_links = movies_without_links.count()
    
    print(f"Found {count_no_links} movies/TV shows with no streaming links")
    
    # Find all movies and check their links
    all_movies = Movie.objects.all().distinct()
    movies_to_delete = set()
    dead_link_patterns = [
        "file not found",
        "404",
        "not found",
        "deleted",
        "removed",
        "copyright",
        "violation",
        "sorry",
        "can't find",
        "can not find",
        "does not exist",
        "we're sorry",
        "we are sorry"
    ]
    
    print(f"\nChecking {all_movies.count()} movies/TV shows for dead links...")
    
    for movie in all_movies:
        links = StreamingLink.objects.filter(movie=movie)
        
        if links.count() == 0:
            # No links at all - already handled above
            continue
        
        # Check if all links are dead or inactive
        active_links = []
        for link in links:
            url_lower = link.source_url.lower() if link.source_url else ""
            
            # Check if URL contains dead link indicators
            is_dead = any(pattern in url_lower for pattern in dead_link_patterns)
            
            # Link is considered active if: is_active=True AND doesn't contain dead patterns
            if link.is_active and not is_dead:
                active_links.append(link)
        
        # If no active links, mark for deletion
        if len(active_links) == 0:
            movies_to_delete.add(movie.id)
            print(f"  Marking for deletion: {movie.title} (all {links.count()} links are dead/inactive)")
    
    # Delete movies with no links
    deleted_no_links = movies_without_links.delete()[0]
    print(f"\nDeleted {deleted_no_links} movies/TV shows with no links")
    
    # Delete movies with only dead links
    if movies_to_delete:
        movies_with_dead_links = Movie.objects.filter(id__in=movies_to_delete)
        deleted_dead_links = movies_with_dead_links.delete()[0]
        print(f"Deleted {deleted_dead_links} movies/TV shows with only dead links")
    else:
        print("No movies/TV shows with only dead links found")
    
    # Final count
    remaining = Movie.objects.count()
    remaining_with_links = Movie.objects.filter(links__isnull=False).distinct().count()
    
    print(f"\n=== CLEANUP COMPLETE ===")
    print(f"Remaining movies/TV shows: {remaining}")
    print(f"  - With streaming links: {remaining_with_links}")
    print(f"  - Without streaming links: {remaining - remaining_with_links}")

if __name__ == "__main__":
    cleanup_dead_links()

