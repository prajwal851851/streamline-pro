"""
Django management command to check the health of all streaming links.
Run this periodically (e.g., every hour via cron) to mark dead links as inactive.

Usage:
    python manage.py check_link_health
    python manage.py check_link_health --limit 100  # Check only first 100 links
    python manage.py check_link_health --older-than 24  # Only check links older than 24 hours
"""
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from streaming.models import StreamingLink


class Command(BaseCommand):
    help = 'Check health of streaming links and mark dead ones as inactive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of links to check (useful for testing)',
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=None,
            help='Only check links that were last checked more than N hours ago',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Request timeout in seconds (default: 5)',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        older_than_hours = options.get('older_than')
        timeout = options.get('timeout', 5)
        
        # Build queryset
        queryset = StreamingLink.objects.all()
        
        # Filter by last_checked if older-than is specified
        if older_than_hours:
            cutoff_time = timezone.now() - timedelta(hours=older_than_hours)
            queryset = queryset.filter(
                last_checked__lt=cutoff_time
            ) | queryset.filter(last_checked__isnull=True)
        
        # Apply limit if specified
        if limit:
            queryset = queryset[:limit]
        
        total_links = queryset.count()
        self.stdout.write(f'Checking {total_links} streaming links...')
        
        active_count = 0
        inactive_count = 0
        error_count = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for link in queryset:
            try:
                # Use HEAD request for efficiency (lightweight check)
                response = requests.head(
                    link.source_url,
                    timeout=timeout,
                    headers=headers,
                    allow_redirects=True
                )
                
                # Check status code
                if response.status_code == 200:
                    link.is_active = True
                    active_count += 1
                elif response.status_code in [404, 403, 410]:
                    # 404 Not Found, 403 Forbidden, 410 Gone
                    link.is_active = False
                    inactive_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  Dead link: {link.movie.title} - Status {response.status_code}')
                    )
                else:
                    # Other status codes - mark as inactive to be safe
                    link.is_active = False
                    inactive_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  Suspicious link: {link.movie.title} - Status {response.status_code}')
                    )
                
            except requests.Timeout:
                # Timeout - mark as inactive
                link.is_active = False
                inactive_count += 1
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  Timeout: {link.movie.title}')
                )
            except requests.RequestException as e:
                # Other request errors - mark as inactive
                link.is_active = False
                inactive_count += 1
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  Error checking {link.movie.title}: {str(e)[:50]}')
                )
            except Exception as e:
                # Unexpected errors
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  Unexpected error for {link.movie.title}: {str(e)[:50]}')
                )
            
            # Update last_checked timestamp
            link.last_checked = timezone.now()
            link.save(update_fields=['is_active', 'last_checked'])
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Health Check Complete ==='))
        self.stdout.write(f'Total checked: {total_links}')
        self.stdout.write(self.style.SUCCESS(f'Active links: {active_count}'))
        self.stdout.write(self.style.WARNING(f'Inactive links: {inactive_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        
        # Clean up movies with no active links
        from streaming.models import Movie
        movies_with_no_active_links = Movie.objects.filter(
            links__is_active=True
        ).distinct()
        all_movies = Movie.objects.all().distinct()
        movies_to_delete = []
        
        for movie in all_movies:
            active_links = StreamingLink.objects.filter(movie=movie, is_active=True)
            if active_links.count() == 0:
                movies_to_delete.append(movie.id)
        
        if movies_to_delete:
            deleted_count = Movie.objects.filter(id__in=movies_to_delete).delete()[0]
            self.stdout.write(
                self.style.WARNING(f'\nDeleted {deleted_count} movies/TV shows with no active links')
            )

