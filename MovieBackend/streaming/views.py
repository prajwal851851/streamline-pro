from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Movie, StreamingLink
from .serializers import MovieSerializer
from .scraper_utils import scrape_movie_on_demand
from .link_health import check_link_health

logger = logging.getLogger(__name__)


class StreamingMovieViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Read-only endpoints for scraped streaming movies with on-demand scraping
    and real-time link validation.
    """

    queryset = Movie.objects.prefetch_related("links").order_by("-created_at")
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type"]
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to check for active links and trigger on-demand scraping if needed.
        Returns movie with validated working links.
        """
        instance = self.get_object()
        
        # Get active links
        active_links = StreamingLink.objects.filter(movie=instance, is_active=True)
        
        # Check if links are stale (older than 24 hours) or non-existent
        stale_threshold = timezone.now() - timedelta(hours=24)
        stale_links = active_links.filter(
            last_checked__lt=stale_threshold
        ) | active_links.filter(last_checked__isnull=True)
        
        needs_refresh = (
            active_links.count() == 0 or  # No active links
            stale_links.count() == active_links.count() or  # All links are stale
            active_links.count() < 2  # Too few links (want at least 2 backup options)
        )
        
        if needs_refresh:
            logger.info(f"🔄 Movie '{instance.title}' needs refresh - triggering on-demand scraping")
            
            # Use stored URL or construct it
            target_url = instance.original_detail_url
            if not target_url:
                # Construct URL from imdb_id
                if instance.type == "show":
                    target_url = f"https://1flix.to/tv/{instance.imdb_id}"
                else:
                    target_url = f"https://1flix.to/movie/{instance.imdb_id}"
            
            # Trigger on-demand scraping (runs in background)
            scrape_movie_on_demand(target_url, movie_id=instance.id)
            
            # Return current data with a flag indicating refresh is in progress
            serializer = self.get_serializer(instance)
            data = serializer.data
            data['_refreshing'] = True
            data['_message'] = 'Fetching fresh streaming links...'
            return Response(data)
        
        # Links are fresh, return as normal
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def refresh_links(self, request, pk=None):
        """
        Manually trigger a refresh of streaming links for a specific movie.
        POST /api/streaming/movies/{id}/refresh_links/
        """
        movie = self.get_object()
        
        # Use stored URL or construct it
        target_url = movie.original_detail_url
        if not target_url:
            if movie.type == "show":
                target_url = f"https://1flix.to/tv/{movie.imdb_id}"
            else:
                target_url = f"https://1flix.to/movie/{movie.imdb_id}"
        
        logger.info(f"🔄 Manual refresh triggered for '{movie.title}'")
        
        # Trigger scraping
        scrape_movie_on_demand(target_url, movie_id=movie.id)
        
        return Response({
            "message": f"Refresh triggered for {movie.title}",
            "status": "scraping",
            "estimated_time": "15-30 seconds"
        })
    
    @action(detail=True, methods=['get'])
    def validate_links(self, request, pk=None):
        """
        Validate all links for a movie and return only working ones.
        GET /api/streaming/movies/{id}/validate_links/
        """
        movie = self.get_object()
        links = StreamingLink.objects.filter(movie=movie, is_active=True)
        
        validated_links = []
        for link in links:
            result = check_link_health(link.source_url)
            if result.is_healthy:
                link.is_active = True
                link.last_checked = timezone.now()
                link.save(update_fields=['is_active', 'last_checked'])
                validated_links.append(link)
            else:
                link.is_active = False
                link.last_checked = timezone.now()
                link.save(update_fields=['is_active', 'last_checked'])
        
        serializer = self.get_serializer(movie)
        data = serializer.data
        data['validated_links_count'] = len(validated_links)
        data['total_links_checked'] = links.count()
        
        return Response(data)