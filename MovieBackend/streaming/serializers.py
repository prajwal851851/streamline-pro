from rest_framework import serializers

from .models import Movie, StreamingLink


class StreamingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamingLink
        fields = ["id", "quality", "language", "source_url", "is_active", "last_checked"]
        read_only_fields = ["id", "last_checked"]


class MovieSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "imdb_id",
            "title",
            "year",
            "type",
            "poster_url",
            "synopsis",
            "original_detail_url",
            "created_at",
            "updated_at",
            "links",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "links"]
    
    def get_links(self, obj):
        # Only return active links
        active_links = obj.links.filter(is_active=True)
        return StreamingLinkSerializer(active_links, many=True).data

