from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .models import Movie
from .serializers import MovieSerializer


class StreamingMovieViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only endpoints for scraped streaming movies."""

    queryset = Movie.objects.prefetch_related("links").order_by("-created_at")
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]

