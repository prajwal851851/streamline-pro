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
    Persist scraped movie data with STRICT filtering - NO YouTube
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
        
        # CRITICAL: Known video hosting domains (expanded list)
        VALID_VIDEO_HOSTS = [
            # Primary hosts
            "vidoza", "streamtape", "mixdrop", "doodstream", "dood", 
            "filemoon", "upstream", "streamlare", "streamhub", "streamwish",
            "videostr", "voe", "streamvid", "mp4upload", "streamplay",
            "supervideo", "gounlimited", "jetload", "vidcloud", "mystream",
            "vidstream", "fembed", "streamango", "rapidvideo", "vidlox",
            "clipwatching", "verystream", "streammango", "netu", "fastplay",
            "powvideo", "aparat", "vup", "vshare", "tune", "woof", "waaw",
            "hqq", "thevideo", "vidup", "streamz", "vidfast", "vidoo",
            "vidbam", "vidbull", "vidto", "vidsrc", "fmovies",
            
            # With TLDs
            "streamtape.com", "streamta.pe", "stape.fun",
            "mixdrop.co", "mixdrop.to", "mixdrop.sx", "mixdrop.is",
            "doodstream.com", "dood.watch", "dood.to", "dood.so", "dood.cx",
            "vidoza.net", "vidoza.co",
            "upstream.to",
            "filemoon.sx", "filemoon.in",
            "streamlare.com",
            "voe.sx",
        ]
        
        # CRITICAL: Patterns to REJECT
        BAD_PATTERNS = [
            # Social media & video platforms
            "youtube.com", "youtu.be", "youtube-nocookie.com",
            "facebook.com", "fb.com",
            "twitter.com", "x.com",
            "instagram.com", "tiktok.com",
            "dailymotion.com", "vimeo.com",
            
            # Movie info sites
            "imdb.com", "themoviedb.org", "tvdb.com", "rottentomatoes.com",
            
            # Other
            "google.com", "recaptcha",
            "1flix.to/movie/", "1flix.to/tv/",
            "javascript:", "#",
        ]
        
        # CRITICAL: Patterns indicating streaming
        STREAMING_PATTERNS = [
            "embed", "player", "watch", "stream", "video",
            "/e/", "/v/", "/f/", "/d/",
            ".m3u8", ".mp4", ".webm", ".mkv"
        ]
        
        valid_links = []
        rejected_count = 0
        rejected_youtube = 0
        rejected_stats = {
            'youtube': 0,
            'social_media': 0,
            'movie_info': 0,
            'site_navigation': 0,
            'not_video_like': 0,
            'other': 0
        }
        
        for link in links:
            source_url = link.get("source_url")
            if not source_url or not isinstance(source_url, str):
                continue
            
            url_lower = source_url.lower().strip()
            
            # Must be HTTP/HTTPS
            if not url_lower.startswith(("http://", "https://")):
                rejected_count += 1
                rejected_stats['other'] += 1
                continue
            
            # CRITICAL: Reject YouTube and bad patterns
            is_bad = False
            for bad in BAD_PATTERNS:
                if bad in url_lower:
                    is_bad = True
                    rejected_count += 1
                    
                    # Categorize rejection
                    if "youtube" in bad or "youtu.be" in bad:
                        rejected_youtube += 1
                        rejected_stats['youtube'] += 1
                        logger.info(f"❌ Rejected YOUTUBE: {source_url[:80]}")
                    elif any(x in bad for x in ['facebook', 'twitter', 'instagram', 'tiktok']):
                        rejected_stats['social_media'] += 1
                        logger.debug(f"❌ Rejected (social media): {source_url[:60]}")
                    elif any(x in bad for x in ['imdb', 'themoviedb', 'tvdb', 'rotten']):
                        rejected_stats['movie_info'] += 1
                    elif '1flix.to' in bad:
                        rejected_stats['site_navigation'] += 1
                    else:
                        rejected_stats['other'] += 1
                    break
            
            if is_bad:
                continue
            
            # Check if it's from a known video host
            is_video_host = any(host in url_lower for host in VALID_VIDEO_HOSTS)
            
            # Check if has streaming keywords
            has_streaming_keyword = any(keyword in url_lower for keyword in STREAMING_PATTERNS)
            
            # ACCEPT if either condition is true
            if is_video_host or has_streaming_keyword:
                valid_links.append(link)
                logger.info(f"✅ ACCEPTED: {source_url[:80]}")
            else:
                rejected_count += 1
                rejected_stats['not_video_like'] += 1
                logger.debug(f"❌ Rejected (not video-like): {source_url[:60]}")
        
        # Log comprehensive results
        if not valid_links:
            logger.warning(
                f"⚠️ No valid streaming links for {movie.title}\n"
                f"   Found: {len(links)} total URLs\n"
                f"   Rejected: YouTube={rejected_youtube}, Social={rejected_stats['social_media']}, "
                f"Movie Info={rejected_stats['movie_info']}, Nav={rejected_stats['site_navigation']}, "
                f"Not Video={rejected_stats['not_video_like']}, Other={rejected_stats['other']}"
            )
            
            # Show sample URLs for debugging
            if links:
                logger.info(f"📋 Sample URLs found (first 5):")
                for i, link in enumerate(links[:5], 1):
                    url = link.get("source_url", "")
                    logger.info(f"   {i}. {url[:100]}")
        else:
            logger.info(
                f"✅ Accepted {len(valid_links)}/{len(links)} links for {movie.title}\n"
                f"   Rejected: YouTube={rejected_youtube}, Total Rejected={rejected_count}"
            )
        
        # Save links
        saved_count = 0
        for link in valid_links:
            source_url = link.get("source_url")
            
            # Double-check: NO YouTube links should reach here
            if 'youtube' in source_url.lower() or 'youtu.be' in source_url.lower():
                logger.error(f"🚨 CRITICAL: YouTube link reached save stage: {source_url}")
                continue
            
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