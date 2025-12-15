# File: scraper/scraper/pipelines.py
# REPLACE the entire file

from datetime import datetime
from typing import Any, Dict, List
import logging
from twisted.internet.threads import deferToThread
from django.utils import timezone

logger = logging.getLogger(__name__)


class DjangoWriterPipeline:
    """
    Persist scraped movie data with STRICT filtering to reject YouTube and social media
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
        
        # CRITICAL: Known video hosting domains
        VALID_VIDEO_HOSTS = [
            "vidoza", "streamtape", "mixdrop", "dood", "filemoon",
            "upstream", "streamlare", "streamhub", "streamwish", "videostr",
            "voe", "streamvid", "mp4upload", "streamplay", "supervideo",
            "gounlimited", "jetload", "vidcloud", "mystream", "vidstream",
            "fembed", "streamango", "openload", "rapidvideo", "vidlox",
            "clipwatching", "verystream", "streammango", "netu",
            "fastplay", "powvideo", "aparat", "vup", "vshare",
            "tune", "woof", "waaw", "hqq", "thevideo", "vidup",
            "streamz", "vidfast", "vidoo", "vidbam", "vidbull", "vidto",
        ]
        
        # CRITICAL: Patterns to REJECT (YouTube, social media, etc.)
        BAD_PATTERNS = [
            # Social media & video platforms (NOT streaming hosts)
            "youtube.com", "youtu.be", "youtube-nocookie.com",
            "facebook.com", "fb.com",
            "twitter.com", "x.com",
            "instagram.com",
            "tiktok.com",
            "dailymotion.com",
            "vimeo.com",
            
            # Movie info sites (not streaming)
            "imdb.com",
            "themoviedb.org",
            "tvdb.com",
            "rottentomatoes.com",
            
            # Other
            "google.com", "recaptcha",
            "1flix.to/movie/", "1flix.to/tv/",  # Don't save the listing page URLs
            "javascript:", 
            "#",
        ]
        
        # CRITICAL: Keywords that indicate streaming
        STREAMING_KEYWORDS = [
            "embed", "player", "watch", "stream", "video",
            ".m3u8", ".mp4", ".webm", ".mkv"
        ]
        
        valid_links = []
        rejected_count = 0
        rejected_youtube = 0
        
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
            
            # CRITICAL: Reject YouTube and social media
            is_bad = False
            for bad in BAD_PATTERNS:
                if bad in url_lower:
                    is_bad = True
                    rejected_count += 1
                    if "youtube" in bad or "youtu.be" in bad:
                        rejected_youtube += 1
                        logger.info(f"❌ Rejected YOUTUBE: {source_url[:80]}")
                    else:
                        logger.debug(f"❌ Rejected (bad pattern '{bad}'): {source_url[:60]}")
                    break
            
            if is_bad:
                continue
            
            # Check if it's from a known video host OR has streaming keywords
            is_video_host = any(host in url_lower for host in VALID_VIDEO_HOSTS)
            has_streaming_keyword = any(keyword in url_lower for keyword in STREAMING_KEYWORDS)
            
            # ACCEPT if either condition is true
            if is_video_host or has_streaming_keyword:
                valid_links.append(link)
                logger.info(f"✅ ACCEPTED: {source_url[:80]}")
            else:
                rejected_count += 1
                logger.debug(f"❌ Rejected (not video-like): {source_url[:60]}")
        
        # Log results
        if not valid_links:
            logger.warning(
                f"⚠️ No valid streaming links for {movie.title} - "
                f"Found {len(links)} total, rejected {rejected_count} (YouTube: {rejected_youtube})"
            )
            # Print first few URLs for debugging
            if links:
                logger.info(f"📋 Sample URLs found:")
                for i, link in enumerate(links[:5]):
                    url = link.get("source_url", "")
                    logger.info(f"   {i+1}. {url[:100]}")
        else:
            logger.info(
                f"✅ Accepted {len(valid_links)}/{len(links)} links for {movie.title} "
                f"(Rejected YouTube: {rejected_youtube})"
            )
        
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