# File: scraper/scraper/pipelines.py
# REPLACE the entire file with this version

from datetime import datetime
from typing import Any, Dict, List
import logging
from twisted.internet.threads import deferToThread
from django.utils import timezone

logger = logging.getLogger(__name__)


class DjangoWriterPipeline:
    """
    Persist scraped movie data into the Django database.
    LESS RESTRICTIVE VERSION - Accepts more video URLs
    """

    def process_item(self, item: Dict[str, Any], spider):
        return deferToThread(self._save_item, item)

    def _save_item(self, item: Dict[str, Any]):
        from streaming.models import Movie, StreamingLink

        imdb_id = item.get("imdb_id")
        if not imdb_id:
            raise ValueError("imdb_id is required")

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
        
        # CRITICAL: Very permissive video host list
        VALID_VIDEO_HOSTS = [
            # Common video hosts
            "vidoza", "streamtape", "mixdrop", "dood", "filemoon",
            "upstream", "streamlare", "streamhub", "streamwish", "videostr",
            "voe", "streamvid", "mp4upload", "streamplay", "supervideo",
            "gounlimited", "jetload", "vidcloud", "mystream", "vidstream",
            # Additional hosts that might be used
            "fembed", "streamango", "openload", "rapidvideo", "vidlox",
            "clipwatching", "verystream", "streammango", "netu", "vidoza",
            "fastplay", "vidlox", "powvideo", "aparat", "vup", "vshare",
            # Even more hosts
            "tune", "woof", "waaw", "hqq", "netu", "thevideo", "vidup",
            "streamz", "vidfast", "vidoo", "vidbam", "vidbull", "vidto",
        ]
        
        # CRITICAL: Minimal bad patterns - only block obvious non-video URLs
        BAD_PATTERNS = [
            "recaptcha", "google.com/recaptcha",
            "javascript:", 
            "1flix.to/movie/", "1flix.to/tv/",  # Don't save the listing page URLs
            "facebook.com", "twitter.com", "instagram.com",
        ]
        
        valid_links = []
        rejected_count = 0
        
        for link in links:
            source_url = link.get("source_url")
            if not source_url or not isinstance(source_url, str):
                continue
            
            url_lower = source_url.lower().strip()
            
            # Skip invalid URLs
            if not url_lower.startswith(("http://", "https://")):
                rejected_count += 1
                logger.debug(f"❌ Rejected (no http): {source_url[:60]}")
                continue
            
            # Skip bad patterns (very minimal list)
            is_bad = False
            for bad in BAD_PATTERNS:
                if bad in url_lower:
                    is_bad = True
                    rejected_count += 1
                    logger.debug(f"❌ Rejected (bad pattern '{bad}'): {source_url[:60]}")
                    break
            
            if is_bad:
                continue
            
            # Check if it's from a known video host OR looks like a video URL
            is_video_host = any(host in url_lower for host in VALID_VIDEO_HOSTS)
            is_direct_video = any(ext in url_lower for ext in [".mp4", ".m3u8", ".webm", ".mkv", ".avi"])
            looks_like_embed = any(word in url_lower for word in ["embed", "player", "watch", "video", "stream"])
            
            # ACCEPT if ANY of these conditions are true:
            if is_video_host or is_direct_video or looks_like_embed:
                valid_links.append(link)
                logger.info(f"✅ ACCEPTED: {source_url[:80]}")
            else:
                rejected_count += 1
                logger.debug(f"❌ Rejected (not video-like): {source_url[:60]}")
        
        # Log results
        if not valid_links:
            logger.warning(
                f"⚠️ No valid links for {movie.title} - "
                f"Found {len(links)} total, rejected {rejected_count}"
            )
            # Print first few URLs for debugging
            if links:
                logger.info(f"📋 Sample URLs found:")
                for i, link in enumerate(links[:3]):
                    url = link.get("source_url", "")
                    logger.info(f"   {i+1}. {url[:100]}")
        else:
            logger.info(f"✅ Accepted {len(valid_links)}/{len(links)} links for {movie.title}")
        
        # Save links
        saved_count = 0
        for link in valid_links:
            source_url = link.get("source_url")
            
            # Check if link already exists
            existing = StreamingLink.objects.filter(
                movie=movie,
                source_url=source_url
            ).first()
            
            if existing:
                existing.quality = link.get("quality") or "HD"
                existing.language = link.get("language") or "EN"
                existing.is_active = True
                existing.last_checked = now
                existing.save()
            else:
                StreamingLink.objects.create(
                    movie=movie,
                    source_url=source_url,
                    quality=link.get("quality") or "HD",
                    language=link.get("language") or "EN",
                    is_active=True,
                    last_checked=now,
                )
                saved_count += 1

        logger.info(
            f"💾 Saved {movie.title}: "
            f"created={created}, new_links={saved_count}, total_links={len(valid_links)}"
        )
        return item