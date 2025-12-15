# File: scraper/scraper/spiders/example_spider.py
# REPLACE the entire file with this improved version

import re
import scrapy
from scrapy import Request
from scrapy.http import TextResponse
import logging

try:
    from fake_useragent import UserAgent
except Exception:
    UserAgent = None

from scraper.items import StreamingItem

logger = logging.getLogger(__name__)


class OneFlixSpider(scrapy.Spider):
    """
    Enhanced spider that finds REAL streaming links (not YouTube trailers)
    """

    name = "oneflix"
    allowed_domains = ["1flix.to"]
    start_urls = ["https://1flix.to/home"]
    
    # CRITICAL: Patterns to REJECT
    REJECT_PATTERNS = [
        # Social media & trailers (NOT streaming hosts)
        'youtube.com', 'youtu.be', 'youtube-nocookie.com',
        'facebook.com', 'fb.com',
        'twitter.com', 'x.com',
        'instagram.com', 'tiktok.com',
        'dailymotion.com', 'vimeo.com',  # Usually trailers, not full movies
        
        # Movie info sites (not streaming)
        'imdb.com', 'themoviedb.org', 'tvdb.com', 'rottentomatoes.com',
        
        # Site navigation
        '1flix.to/movie/', '1flix.to/tv/', '1flix.to/search',
        '1flix.to/home', '1flix.to/genre', '1flix.to/trending',
        'javascript:', 'mailto:', '#', 'void(0)',
    ]
    
    # CRITICAL: Known video hosting domains
    VIDEO_HOSTS = [
        # Reliable streaming hosts
        'vidoza', 'streamtape', 'mixdrop', 'doodstream', 'dood.', 
        'filemoon', 'upstream', 'streamlare', 'streamhub', 'streamwish',
        'videostr', 'voe.', 'streamvid', 'mp4upload', 'streamplay',
        'supervideo', 'gounlimited', 'jetload', 'vidcloud', 'mystream',
        'vidstream', 'fembed', 'streamango', 'rapidvideo', 'vidlox',
        'clipwatching', 'verystream', 'streammango', 'netu', 'fastplay',
        'powvideo', 'aparat', 'vup', 'vshare', 'tune', 'woof', 'waaw',
        'hqq', 'thevideo', 'vidup', 'streamz', 'vidfast', 'vidoo',
        'vidbam', 'vidbull', 'vidto', 'vidsrc', 'fmovies',
        
        # Additional hosts
        'streamtape.com', 'streamta.pe', 'stape.fun',
        'mixdrop.co', 'mixdrop.to', 'mixdrop.sx',
        'doodstream.com', 'dood.watch', 'dood.to', 'dood.so',
        'vidoza.net', 'vidoza.co',
        'upstream.to',
        'filemoon.sx', 'filemoon.in',
        'streamlare.com',
        'voe.sx',
    ]
    
    # CRITICAL: URL patterns that indicate streaming
    STREAM_PATTERNS = [
        'embed', 'player', 'watch', 'stream', 'video', 'play',
        '/e/', '/v/', '/f/', '/d/',  # Common embed paths
        '.m3u8', '.mp4', '.mkv', '.avi', '.webm',
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_movies = set()
        
        # On-demand scraping mode
        self.target_url = kwargs.get('target_url', None)
        self.on_demand_mode = bool(self.target_url)
        
        if self.on_demand_mode:
            self.start_urls = [self.target_url]
            logger.info(f"🎯 ON-DEMAND MODE: Scraping {self.target_url}")

    def start_requests(self):
        """Start scraping with proper headers"""
        ua = UserAgent().random if UserAgent else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        for url in self.start_urls:
            if self.on_demand_mode:
                yield Request(
                    url,
                    headers=headers,
                    callback=self.parse_movie_page,
                    meta=self._get_playwright_meta(is_detail_page=True),
                    dont_filter=True
                )
            else:
                yield Request(
                    url,
                    headers=headers,
                    callback=self.parse_listing,
                    meta=self._get_playwright_meta(is_detail_page=False),
                )

    def _get_playwright_meta(self, is_detail_page=False):
        """Get Playwright configuration with VERY aggressive server clicking"""
        base_meta = {
            "playwright": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "networkidle",
                "timeout": 60000
            },
        }
        
        if is_detail_page:
            base_meta["playwright_page_coroutines"] = [
                # Initial wait
                {"coroutine": "wait_for_timeout", "args": [3000]},
                
                # Scroll to load lazy content
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight / 2);
                            return true;
                        }
                    """]
                },
                {"coroutine": "wait_for_timeout", "args": [2000]},
                
                # CRITICAL: Click ALL possible server/link elements
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            const selectors = [
                                // Server selectors
                                'a[data-link]', 'button[data-link]',
                                'a[data-server]', 'button[data-server]',
                                'a[data-embed]', 'button[data-embed]',
                                'a[data-player]', 'button[data-player]',
                                'a[data-url]', 'button[data-url]',
                                'a[data-video]', 'button[data-video]',
                                'a[data-src]', 'button[data-src]',
                                
                                // Class-based selectors
                                '.server-item', '.server-btn', '.server',
                                '[class*="server"]', '[id*="server"]',
                                '.link-item', '.link-btn', '[class*="link"]',
                                '.player-item', '.player-btn', '[class*="player"]',
                                '.episode-server', '.episode-link',
                                
                                // Generic buttons and links
                                'button[onclick]', 'a[onclick]',
                                'button.btn', 'a.btn',
                                'a[href*="embed"]', 'a[href*="player"]',
                                'a[href*="watch"]', 'a[href*="stream"]',
                                
                                // Tab systems
                                'button[role="tab"]', 'a[role="tab"]',
                                '[data-toggle="tab"]', '[data-bs-toggle="tab"]',
                            ];
                            
                            let clicked = 0;
                            const clickedElements = new Set();
                            
                            // Click each selector type 5 TIMES (very aggressive)
                            for (let round = 0; round < 5; round++) {
                                selectors.forEach(selector => {
                                    try {
                                        const elements = Array.from(document.querySelectorAll(selector));
                                        elements.forEach((el) => {
                                            // Check if visible
                                            if (el.offsetParent !== null) {
                                                try {
                                                    // Scroll into view
                                                    el.scrollIntoView({behavior: 'auto', block: 'center'});
                                                    
                                                    // Click in multiple ways
                                                    el.click();  // Normal click
                                                    
                                                    // Dispatch event
                                                    const event = new MouseEvent('click', {
                                                        view: window,
                                                        bubbles: true,
                                                        cancelable: true
                                                    });
                                                    el.dispatchEvent(event);
                                                    
                                                    clicked++;
                                                    clickedElements.add(el.tagName + ':' + el.className);
                                                } catch(e) {
                                                    console.log('Click error:', e);
                                                }
                                            }
                                        });
                                    } catch(e) {
                                        console.log('Selector error:', e);
                                    }
                                });
                                
                                // Wait between rounds
                                if (round < 4) {
                                    // Short delay
                                }
                            }
                            
                            console.log('Clicked', clicked, 'elements across', clickedElements.size, 'types');
                            return clicked;
                        }
                    """]
                },
                
                # Wait LONGER for streams to load (20 seconds)
                {"coroutine": "wait_for_timeout", "args": [20000]},
                
                # Final scroll to reveal any lazy-loaded iframes
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight);
                            window.scrollTo(0, 0);
                            window.scrollTo(0, document.body.scrollHeight / 2);
                            return true;
                        }
                    """]
                },
                
                # Final wait
                {"coroutine": "wait_for_timeout", "args": [3000]},
            ]
        
        return base_meta

    def parse_listing(self, response):
        """Parse listing page"""
        if self.on_demand_mode:
            return
        
        logger.info(f"📋 Parsing listing: {response.url}")
        
        movie_links = set()
        movie_links.update(response.css("a[href*='/movie/']::attr(href)").getall())
        movie_links.update(response.css("a[href*='/tv/']::attr(href)").getall())
        
        for link in movie_links:
            if link and link not in self.seen_movies:
                self.seen_movies.add(link)
                full_url = response.urljoin(link)
                yield Request(
                    full_url,
                    callback=self.parse_movie_page,
                    meta=self._get_playwright_meta(is_detail_page=True),
                )

    def parse_movie_page(self, response: TextResponse):
        """Parse movie detail page and extract REAL streaming links"""
        logger.info(f"🎬 Parsing movie: {response.url}")
        
        item = StreamingItem()
        item["original_detail_url"] = response.url
        
        # Extract title
        title = response.css("h1::text").get() or response.css("h1 *::text").get() or ""
        title = title.strip()
        item["title"] = title
        
        # Extract IMDB ID from URL
        movie_slug = response.url.rstrip("/").split("/")[-1]
        item["imdb_id"] = movie_slug
        
        logger.info(f"📝 Title: {title} | ID: {movie_slug}")
        
        # Extract year
        year = None
        year_texts = response.css("span::text, div::text").getall()
        for text in year_texts:
            text = text.strip()
            if text.isdigit() and len(text) == 4 and 1900 <= int(text) <= 2030:
                year = int(text)
                break
        item["year"] = year
        
        # Determine type
        url_lower = response.url.lower()
        if "/tv/" in url_lower or "/show/" in url_lower:
            item["type"] = "show"
        else:
            item["type"] = "movie"
        
        # Extract poster
        poster = (
            response.css("meta[property='og:image']::attr(content)").get() or
            response.css("img[class*='poster']::attr(src)").get() or
            response.css("img::attr(src)").get()
        )
        item["poster_url"] = poster
        
        # Extract synopsis
        synopsis = (
            response.css("meta[name='description']::attr(content)").get() or
            response.css("p::text").get() or
            ""
        )
        item["synopsis"] = synopsis.strip()
        
        # Extract streaming links (FILTERED)
        links = self._extract_streaming_links(response)
        
        if not links:
            logger.warning(f"⚠️ No valid streaming links found for {title}")
        else:
            logger.info(f"✅ Found {len(links)} streaming links for {title}")
            for i, link in enumerate(links[:3], 1):
                logger.info(f"   {i}. {link['source_url'][:100]}")
        
        item["links"] = links
        
        yield item

    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube link"""
        url_lower = url.lower()
        return 'youtube.com' in url_lower or 'youtu.be' in url_lower

    def _should_reject_url(self, url: str) -> bool:
        """Check if URL should be rejected"""
        url_lower = url.lower()
        
        # Reject bad patterns
        for pattern in self.REJECT_PATTERNS:
            if pattern in url_lower:
                return True
        
        return False

    def _is_video_host_url(self, url: str) -> bool:
        """Check if URL is from a known video hosting site"""
        url_lower = url.lower()
        
        # Check against known video hosts
        for host in self.VIDEO_HOSTS:
            if host in url_lower:
                return True
        
        return False

    def _has_stream_patterns(self, url: str) -> bool:
        """Check if URL has patterns indicating it's a streaming link"""
        url_lower = url.lower()
        
        # Check for streaming patterns
        for pattern in self.STREAM_PATTERNS:
            if pattern in url_lower:
                return True
        
        return False

    def _extract_streaming_links(self, response: TextResponse):
        """Extract ONLY real streaming links"""
        page = response.meta.get("playwright_page")
        all_urls = set()
        
        # Method 1: Playwright page evaluation (most reliable after clicking)
        if page:
            try:
                extracted_urls = page.evaluate("""
                    () => {
                        const sources = new Set();
                        
                        // 1. IFRAMES - Most important for streaming
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const attrs = ['src', 'data-src', 'data-url', 'data-lazy', 
                                          'data-embed', 'data-player', 'data-video'];
                            attrs.forEach(attr => {
                                const src = iframe.getAttribute(attr);
                                if (src && src.startsWith('http')) {
                                    sources.add(src);
                                }
                            });
                        });
                        
                        // 2. DATA ATTRIBUTES on all elements
                        const dataAttrs = ['data-link', 'data-server', 'data-embed', 
                                          'data-player', 'data-url', 'data-video', 'data-src',
                                          'data-stream', 'data-file', 'data-source'];
                        dataAttrs.forEach(attr => {
                            document.querySelectorAll(`[${attr}]`).forEach(el => {
                                const link = el.getAttribute(attr);
                                if (link && link.startsWith('http')) {
                                    sources.add(link);
                                }
                            });
                        });
                        
                        // 3. LINKS with embed/player/stream keywords
                        document.querySelectorAll('a[href]').forEach(a => {
                            const href = a.href;
                            if (href && (
                                href.includes('embed') || href.includes('player') || 
                                href.includes('watch') || href.includes('stream') ||
                                href.includes('/e/') || href.includes('/v/') ||
                                href.includes('/f/') || href.includes('/d/')
                            )) {
                                sources.add(href);
                            }
                        });
                        
                        // 4. ONCLICK handlers
                        document.querySelectorAll('[onclick]').forEach(el => {
                            const onclick = el.getAttribute('onclick') || '';
                            const urlMatches = onclick.matchAll(/['"](https?:\\/\\/[^'"]+)['"]/g);
                            for (const match of urlMatches) {
                                const url = match[1];
                                if (url.includes('embed') || url.includes('player') || 
                                    url.includes('stream') || url.includes('/e/') ||
                                    url.includes('/v/') || url.includes('/f/')) {
                                    sources.add(url);
                                }
                            }
                        });
                        
                        // 5. SCRIPT tags - Look for video sources
                        document.querySelectorAll('script').forEach(script => {
                            const text = script.textContent || '';
                            // Look for common streaming patterns in scripts
                            const patterns = [
                                /(https?:\\/\\/[^\\s"']+?(?:embed|player|stream|video|\/e\/|\/v\/)[^\\s"'<>]*)/gi,
                                /(https?:\\/\\/(?:streamtape|mixdrop|dood|vidoza|upstream)[^\\s"'<>]+)/gi
                            ];
                            patterns.forEach(pattern => {
                                const matches = text.matchAll(pattern);
                                for (const match of matches) {
                                    sources.add(match[1]);
                                }
                            });
                        });
                        
                        console.log('Found', sources.size, 'potential URLs');
                        return Array.from(sources);
                    }
                """)
                
                if extracted_urls:
                    logger.info(f"🔍 Playwright extracted {len(extracted_urls)} URLs")
                    all_urls.update(extracted_urls)
                    
            except Exception as e:
                logger.warning(f"⚠️ Playwright extraction failed: {e}")
        
        # Method 2: Static HTML extraction (backup)
        static_urls = self._extract_from_static_html(response)
        all_urls.update(static_urls)
        logger.info(f"🔍 Static HTML found {len(static_urls)} additional URLs")
        
        # CRITICAL: Filter and validate all URLs
        valid_links = []
        rejected_youtube = 0
        rejected_other = 0
        
        for url in all_urls:
            # Must be HTTP/HTTPS
            if not url.startswith(('http://', 'https://')):
                rejected_other += 1
                continue
            
            # Reject bad patterns
            if self._should_reject_url(url):
                if self._is_youtube_url(url):
                    rejected_youtube += 1
                    logger.debug(f"❌ Rejected YouTube: {url[:80]}")
                else:
                    rejected_other += 1
                    logger.debug(f"❌ Rejected (bad pattern): {url[:60]}")
                continue
            
            # Accept if from known video host OR has stream patterns
            is_video_host = self._is_video_host_url(url)
            has_stream_pattern = self._has_stream_patterns(url)
            
            if is_video_host or has_stream_pattern:
                valid_links.append({
                    "quality": self._detect_quality(url),
                    "language": "EN",
                    "source_url": url,
                    "is_active": True,
                })
                logger.info(f"✅ ACCEPTED: {url[:80]}")
            else:
                rejected_other += 1
                logger.debug(f"❌ Rejected (not video-like): {url[:60]}")
        
        logger.info(f"📊 Filtering: Accepted={len(valid_links)}, YouTube={rejected_youtube}, Other={rejected_other}")
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in valid_links:
            url = link["source_url"]
            if url not in seen:
                seen.add(url)
                unique_links.append(link)
        
        return unique_links

    def _extract_from_static_html(self, response: TextResponse):
        """Extract URLs from static HTML"""
        urls = set()
        
        # Extract from various sources
        selectors = [
            "iframe::attr(src)", "iframe::attr(data-src)", "iframe::attr(data-url)",
            "iframe::attr(data-lazy)", "iframe::attr(data-embed)",
            "[data-link]::attr(data-link)", "[data-server]::attr(data-server)",
            "[data-embed]::attr(data-embed)", "[data-player]::attr(data-player)",
            "[data-stream]::attr(data-stream)", "[data-video]::attr(data-video)",
            "a[href*='embed']::attr(href)", "a[href*='player']::attr(href)",
            "a[href*='stream']::attr(href)", "a[href*='/e/']::attr(href)",
            "a[href*='/v/']::attr(href)", "a[href*='/f/']::attr(href)",
        ]
        
        for selector in selectors:
            found_urls = response.css(selector).getall()
            urls.update(found_urls)
        
        # Extract from script tags
        scripts = response.css("script::text").getall()
        for script in scripts:
            # Find streaming URLs in scripts
            patterns = [
                r'(https?://[^\s"\']+?(?:embed|player|stream|video|/e/|/v/)[^\s"\'<>]*)',
                r'(https?://(?:streamtape|mixdrop|dood|vidoza|upstream)[^\s"\'<>]+)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script, re.IGNORECASE)
                urls.update(matches)
        
        return urls

    def _detect_quality(self, url: str) -> str:
        """Detect video quality from URL"""
        url_lower = url.lower()
        
        if '4k' in url_lower or '2160' in url_lower:
            return '4K'
        elif '1080' in url_lower:
            return '1080p'
        elif '720' in url_lower:
            return '720p'
        elif 'cam' in url_lower:
            return 'CAM'
        else:
            return 'HD'