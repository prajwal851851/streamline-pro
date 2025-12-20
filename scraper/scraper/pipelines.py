# File: scraper/scraper/pipelines.py
# REPLACE the entire file

from datetime import datetime
from typing import Any, Dict, List
import logging
import re
import threading
from django.apps import apps
from django.utils import timezone


logger = logging.getLogger(__name__)


class DjangoWriterPipeline:
    """
    Persist scraped movie data with STRICT filtering - NO YouTube
    """

    def process_item(self, item: Dict[str, Any], spider):
        # Use Twisted's deferToThread when available for Scrapy compatibility.
        # If Twisted isn't available (import errors), fall back to starting a
        # background thread so the pipeline doesn't block the reactor.
        try:
            from twisted.internet.threads import deferToThread as _defer
        except Exception:
            _defer = None

        if _defer:
            return _defer(self._save_item, item)
        else:
            threading.Thread(target=self._save_item, args=(item,), daemon=True).start()
            return item

    def _save_item(self, item: Dict[str, Any]):
      
        movie_pk = item.get("movie_pk")
        imdb_id = item.get("imdb_id")
        if not imdb_id and not movie_pk:
            raise ValueError("Either imdb_id or movie_pk is required")

        defaults = {
            "title": item.get("title") or "",
            "year": item.get("year"),
            "type": item.get("type") or "movie",
            "poster_url": item.get("poster_url"),
            "synopsis": item.get("synopsis"),
            "original_detail_url": item.get("original_detail_url"),
        }

        update_defaults = {k: v for k, v in defaults.items() if v not in (None, "")}
        # Import models via apps.get_model to avoid import-time errors
        # if Django settings aren't fully configured at module import.
        Movie = apps.get_model('streaming', 'Movie')
        StreamingLink = apps.get_model('streaming', 'StreamingLink')

        created = False
        movie = None
        if movie_pk:
            try:
                movie = Movie.objects.get(pk=movie_pk)
                created = False
                # Update imdb_id if this scrape found a real tt... id (for cross-source merging)
                if isinstance(imdb_id, str) and imdb_id.startswith("tt") and movie.imdb_id != imdb_id:
                    # If another Movie already has this tt id, merge it into the current movie
                    conflict = Movie.objects.filter(imdb_id=imdb_id).exclude(pk=movie.pk).first()
                    if conflict:
                        StreamingLink.objects.filter(movie=conflict).update(movie=movie)
                        conflict.delete()
                    Movie.objects.filter(pk=movie.pk).update(imdb_id=imdb_id)
                    movie.imdb_id = imdb_id

                if update_defaults:
                    Movie.objects.filter(pk=movie.pk).update(**update_defaults)
                    for k, v in update_defaults.items():
                        setattr(movie, k, v)
            except Movie.DoesNotExist:
                movie = None

        if movie is None:
            if not imdb_id:
                raise ValueError("imdb_id is required when movie_pk is not provided")
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

            # AD SITES & REDIRECTS (NEW - blocking ad domains)
            "111movies.com", "123movies", "watchmovies", "putlocker",
            "gomovies", "yesmovies", "solarmovies", "moviesjoy",
            "fmovies.to", "fmovies.se", "fmovies.ws", "fmovies.io",
            "1flix.to", "flixhq.to", "flixhq.com", "flixhq.ws",
            "soap2day", "s2dfree", "vidplay", "vidplay.online",
            "vidsrc.me", "vidsrc.to", "vidsrc.pro", "vidsrc.com",
            "embedsoap", "multiembed.mov", "player-cdn.com",

            # Other (captcha, tracking, non-streaming, banners)
            "google.com", "recaptcha", "sysmeasuring.net", "anicrush.to",
            # fmovies site navigation (not real streams)
            "fmovies-co.net/home", "fmovies-co.net/movie", "fmovies-co.net/tv", "fmovies-co.net/tv-show",
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
            
            # Accept based on heuristic only; Link Health Checks will determine is_active later.
            if is_video_host or has_streaming_keyword:
                valid_links.append(link)
                logger.info(f"✅ ACCEPTED: {source_url[:100]}")
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