from datetime import datetime
from typing import Any, Dict, List

import logging
from twisted.internet.threads import deferToThread
from django.utils import timezone

logger = logging.getLogger(__name__)


class DjangoWriterPipeline:
    """
    Persist scraped movie data into the Django database using the streaming app models.
    Run DB work in a thread to avoid async-ORM issues with Playwright reactor.
    """

    def process_item(self, item: Dict[str, Any], spider):
        return deferToThread(self._save_item, item)

    def _save_item(self, item: Dict[str, Any]):
        from streaming.models import Movie, StreamingLink  # Imported lazily after Django setup

        imdb_id = item.get("imdb_id")
        if not imdb_id:
            raise ValueError("imdb_id is required on each item")

        defaults = {
            "title": item.get("title") or "",
            "year": item.get("year"),
            "type": item.get("type") or "movie",
            "poster_url": item.get("poster_url"),
            "synopsis": item.get("synopsis"),
        }
        movie, created = Movie.objects.update_or_create(imdb_id=imdb_id, defaults=defaults)

        links: List[Dict[str, Any]] = item.get("links") or []
        now = timezone.now()
        
        # Final safety filter - never save bad URLs
        bad_patterns = [
            "recaptcha", "google.com/recaptcha", "gstatic.com", 
            "javascript:", "javascript:;", "ads", "advertising", "analytics",
            "youtube.com", "youtu.be"  # YouTube is just trailers, not actual movies
        ]
        
        # Only accept actual video hosting services
        valid_video_hosts = [
            "vidoza", "streamtape", "mixdrop", "dood", "filemoon", 
            "upstream", "streamlare", "streamhub", "streamwish"
        ]
        
        valid_links = []
        for link in links:
            source_url = link.get("source_url")
            if not source_url or not isinstance(source_url, str):
                continue
            
            url_lower = source_url.lower().strip()
            
            # Reject bad URLs
            if any(bad in url_lower for bad in bad_patterns):
                logger.warning(f"Skipping bad URL for {movie.title}: {source_url[:100]}")
                continue
            
            # Reject ALL 1flix.to URLs - we only want actual video hosting services
            if "1flix.to" in url_lower:
                logger.warning(f"Skipping 1flix.to URL for {movie.title}: {source_url[:100]}")
                continue
            
            # Only accept URLs from actual video hosting services (not YouTube trailers)
            if not any(host in url_lower for host in valid_video_hosts):
                # Allow direct video file URLs (mp4, m3u8, etc.)
                if not any(ext in url_lower for ext in [".mp4", ".m3u8", ".webm", ".mkv", ".avi"]):
                    logger.warning(f"Skipping non-video-host URL for {movie.title}: {source_url[:100]}")
                    continue
            
            valid_links.append(link)
        
        # Only save if we have valid links
        if not valid_links:
            logger.warning(f"No valid links found for {movie.title}, skipping link save")
            return item
        
        for link in valid_links:
            source_url = link.get("source_url")
            StreamingLink.objects.update_or_create(
                movie=movie,
                source_url=source_url,
                defaults={
                    "quality": link.get("quality") or "HD",
                    "language": link.get("language") or "EN",
                    "is_active": link.get("is_active", True),
                    "last_checked": link.get("last_checked") or now,
                },
            )

        logger.info("Saved movie %s (created=%s)", movie.title, created)
        return item

