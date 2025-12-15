# File: scraper/scraper/pipelines.py
# REPLACE the entire file with this

from datetime import datetime
from typing import Any, Dict, List
import requests
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
        from streaming.models import Movie, StreamingLink

        imdb_id = item.get("imdb_id")
        if not imdb_id:
            raise ValueError("imdb_id is required on each item")

        defaults = {
            "title": item.get("title") or "",
            "year": item.get("year"),
            "type": item.get("type") or "movie",
            "poster_url": item.get("poster_url"),
            "synopsis": item.get("synopsis"),
            "original_detail_url": item.get("original_detail_url"),
        }
        movie, created = Movie.objects.update_or_create(imdb_id=imdb_id, defaults=defaults)

        links: List[Dict[str, Any]] = item.get("links") or []
        now = timezone.now()
        
        # Known good video hosting services (expanded list)
        VALID_VIDEO_HOSTS = [
            "vidoza", "streamtape", "mixdrop", "dood", "filemoon",
            "upstream", "streamlare", "streamhub", "streamwish", "videostr",
            "voe", "streamvid", "mp4upload", "streamplay", "supervideo",
            "gounlimited", "jetload", "vidcloud", "mystream", "vidstream"
        ]
        
        # Bad patterns to reject
        BAD_PATTERNS = [
            "recaptcha", "google.com/recaptcha", "gstatic.com",
            "javascript:", "ads", "advertising", "analytics",
            "youtube.com", "youtu.be",  # YouTube is just trailers
            "1flix.to",  # Don't save the source site URLs
            "facebook.com", "twitter.com", "instagram.com"
        ]
        
        valid_links = []
        for link in links:
            source_url = link.get("source_url")
            if not source_url or not isinstance(source_url, str):
                continue
            
            url_lower = source_url.lower().strip()
            
            # Skip invalid URLs
            if not url_lower.startswith(("http://", "https://")):
                continue
            
            # Skip bad patterns
            if any(bad in url_lower for bad in BAD_PATTERNS):
                logger.debug(f"Rejected (bad pattern): {source_url[:80]}")
                continue
            
            # Must be from a valid video host OR be a direct video file
            is_video_host = any(host in url_lower for host in VALID_VIDEO_HOSTS)
            is_direct_video = any(ext in url_lower for ext in [".mp4", ".m3u8", ".webm", ".mkv"])
            
            if not (is_video_host or is_direct_video):
                logger.debug(f"Rejected (not video host): {source_url[:80]}")
                continue
            
            # This link passed all filters!
            valid_links.append(link)
            logger.info(f"✅ Accepted link: {source_url[:80]}")
        
        # Save movie even if no links (will be available for retry)
        if not valid_links:
            logger.warning(f"⚠️  No valid links found for {movie.title} - saved movie without links")
        else:
            logger.info(f"✅ Saving {len(valid_links)} links for {movie.title}")
        
        # Save links
        saved_count = 0
        for link in valid_links:
            source_url = link.get("source_url")
            
            # Check if link already exists (avoid duplicates)
            existing = StreamingLink.objects.filter(
                movie=movie,
                source_url=source_url
            ).first()
            
            if existing:
                # Update existing link
                existing.quality = link.get("quality") or "HD"
                existing.language = link.get("language") or "EN"
                existing.is_active = True
                existing.last_checked = now
                existing.save()
                logger.debug(f"Updated existing link: {source_url[:80]}")
            else:
                # Create new link
                StreamingLink.objects.create(
                    movie=movie,
                    source_url=source_url,
                    quality=link.get("quality") or "HD",
                    language=link.get("language") or "EN",
                    is_active=True,
                    last_checked=now,
                )
                saved_count += 1
                logger.debug(f"Created new link: {source_url[:80]}")

        logger.info(f"💾 Saved movie: {movie.title} (created={created}, new_links={saved_count})")
        return item