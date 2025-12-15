from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import Movie, StreamingLink
from .serializers import MovieSerializer
from .scraper_utils import scrape_movie_on_demand


class StreamingMovieViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only endpoints for scraped streaming movies with on-demand scraping."""

    queryset = Movie.objects.prefetch_related("links").order_by("-created_at")
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type"]  # Allow filtering by type (movie, show, episode)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to check for active links and trigger on-demand scraping if needed.
        """
        instance = self.get_object()
        
        # Check if movie has active links
        active_links = StreamingLink.objects.filter(movie=instance, is_active=True)
        
        # Check if links are stale (older than 24 hours)
        stale_threshold = timezone.now() - timedelta(hours=24)
        stale_links = active_links.filter(last_checked__lt=stale_threshold) | active_links.filter(last_checked__isnull=True)
        
        # If no active links or all links are stale, trigger on-demand scraping
        if active_links.count() == 0 or stale_links.count() == active_links.count():
            # Use the stored original_detail_url if available
            if instance.original_detail_url:
                scrape_movie_on_demand(instance.original_detail_url, movie_id=instance.id)
            else:
                # Fallback: Try to construct the URL from imdb_id
                movie_slug = instance.imdb_id
                if movie_slug:
                    # Try different URL patterns
                    possible_urls = [
                        f"https://1flix.to/movie/{movie_slug}",
                        f"https://1flix.to/tv/{movie_slug}",
                        f"https://1flix.to/{movie_slug}",
                    ]
                    
                    # Trigger scraping for the first URL
                    scrape_movie_on_demand(possible_urls[0], movie_id=instance.id)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def refresh_links(self, request, pk=None):
        """
        Manually trigger a refresh of streaming links for a specific movie.
        POST /api/movies/{id}/refresh_links/
        """
        movie = self.get_object()
        
        # Use the stored original_detail_url if available
        if movie.original_detail_url:
            scrape_movie_on_demand(movie.original_detail_url, movie_id=movie.id)
        else:
            # Fallback: Construct URL from imdb_id
            movie_slug = movie.imdb_id
            if not movie_slug:
                return Response(
                    {"error": "Movie does not have an original_detail_url or imdb_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            possible_urls = [
                f"https://1flix.to/movie/{movie_slug}",
                f"https://1flix.to/tv/{movie_slug}",
                f"https://1flix.to/{movie_slug}",
            ]
            
            # Trigger scraping
            scrape_movie_on_demand(possible_urls[0], movie_id=movie.id)
        
        return Response({
            "message": f"Refresh triggered for {movie.title}. Links will be updated shortly.",
            "status": "scraping"
        })

