from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StreamingMovieViewSet

app_name = "streaming"

router = DefaultRouter()
router.register(r"movies", StreamingMovieViewSet, basename="streaming-movie")

urlpatterns = [
    path("", include(router.urls)),
]

