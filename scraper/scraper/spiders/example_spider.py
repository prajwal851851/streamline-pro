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
    Enhanced spider that filters out YouTube trailers and finds real streaming links
    """

    name = "oneflix"
    allowed_domains = ["1flix.to"]
    start_urls = ["https://1flix.to/home"]
    
    # CRITICAL: Patterns to REJECT (YouTube, social media, etc.)
    REJECT_PATTERNS = [
        'youtube.com',
        'youtu.be',
        'facebook.com',
        'twitter.com',
        'instagram.com',
        'tiktok.com',
        'reddit.com',
        'imdb.com',
        'themoviedb.org',
        'tvdb.com',
        'google.com',
        'recaptcha',
        '1flix.to/movie/',  # Don't save the listing page
        '1flix.to/tv/',     # Don't save the listing page
        'javascript:',
        'mailto:',
        '#',
        'void(0)',
    ]
    
    # CRITICAL: Patterns to ACCEPT (known video hosts)
    ACCEPT_PATTERNS = [
        'embed',
        'player',
        'stream',
        'video',
        'watch',
        '.m3u8',
        '.mp4',
        'vidoza',
        'streamtape',
        'mixdrop',
        'dood',
        'filemoon',
        'upstream',
        'streamlare',
        'voe',
        'supervideo',
        'vidcloud',
        'fembed',
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
        headers = {"User-Agent": ua}
        
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
        """Get Playwright configuration with aggressive server clicking"""
        base_meta = {
            "playwright": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "networkidle",
                "timeout": 60000
            },
        }
        
        if is_detail_page:
            base_meta["playwright_page_coroutines"] = [
                {"coroutine": "wait_for_timeout", "args": [3000]},
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight);
                            return true;
                        }
                    """]
                },
                {"coroutine": "wait_for_timeout", "args": [2000]},
                # CRITICAL: Click ALL server buttons multiple times
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            const selectors = [
                                'a[data-link]', 'button[data-link]',
                                'a[data-server]', 'button[data-server]',
                                '.server-item', '.server-btn', '.server',
                                '[class*="server"]', '[id*="server"]',
                                'button[onclick]', 'a[onclick]',
                                '.btn', 'button', 
                                'a[href*="embed"]', 
                                'a[href*="player"]',
                                '[data-embed]', '[data-player]',
                                '.link-item', '.link-btn',
                                '[class*="link"]',
                            ];
                            
                            let clicked = 0;
                            // Click each selector multiple times
                            for (let i = 0; i < 3; i++) {
                                selectors.forEach(selector => {
                                    const elements = Array.from(document.querySelectorAll(selector));
                                    elements.forEach((el) => {
                                        if (el.offsetParent !== null) {
                                            try {
                                                el.scrollIntoView({behavior: 'auto', block: 'center'});
                                                el.click();
                                                clicked++;
                                            } catch(e) {}
                                        }
                                    });
                                });
                            }
                            
                            return clicked;
                        }
                    """]
                },
                {"coroutine": "wait_for_timeout", "args": [15000]},  # Wait longer for streams to load
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight);
                            return true;
                        }
                    """]
                },
                {"coroutine": "wait_for_timeout", "args": [5000]},
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
        """Parse movie detail page and extract REAL streaming links (not YouTube)"""
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
            for link in links[:3]:  # Log first 3
                logger.info(f"   🔗 {link['source_url'][:100]}")
        
        item["links"] = links
        
        yield item

    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube link"""
        url_lower = url.lower()
        return 'youtube.com' in url_lower or 'youtu.be' in url_lower

    def _should_reject_url(self, url: str) -> bool:
        """Check if URL should be rejected"""
        url_lower = url.lower()
        
        # Reject YouTube and other non-streaming sites
        for pattern in self.REJECT_PATTERNS:
            if pattern in url_lower:
                return True
        
        return False

    def _should_accept_url(self, url: str) -> bool:
        """Check if URL looks like a real streaming link"""
        url_lower = url.lower()
        
        # Must contain at least one accept pattern
        for pattern in self.ACCEPT_PATTERNS:
            if pattern in url_lower:
                return True
        
        return False

    def _extract_streaming_links(self, response: TextResponse):
        """Extract ONLY real streaming links (NO YouTube)"""
        page = response.meta.get("playwright_page")
        all_urls = set()
        
        # Method 1: Playwright page evaluation
        if page:
            try:
                extracted_urls = page.evaluate("""
                    () => {
                        const sources = new Set();
                        
                        // Extract from iframes - CRITICAL for streaming
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const src = iframe.src || iframe.getAttribute('data-src') || 
                                       iframe.getAttribute('data-url') || iframe.getAttribute('data-lazy');
                            if (src && src.startsWith('http')) {
                                // Skip YouTube iframes
                                if (!src.includes('youtube.com') && !src.includes('youtu.be')) {
                                    sources.add(src);
                                }
                            }
                        });
                        
                        // Extract from data attributes (server links)
                        const dataAttrs = ['data-link', 'data-server', 'data-embed', 
                                          'data-player', 'data-url', 'data-video', 'data-src'];
                        dataAttrs.forEach(attr => {
                            document.querySelectorAll(`[${attr}]`).forEach(el => {
                                const link = el.getAttribute(attr);
                                if (link && link.startsWith('http')) {
                                    // Skip YouTube
                                    if (!link.includes('youtube.com') && !link.includes('youtu.be')) {
                                        sources.add(link);
                                    }
                                }
                            });
                        });
                        
                        // Extract from links (embed/player URLs)
                        document.querySelectorAll('a[href]').forEach(a => {
                            const href = a.href;
                            if (href && (href.includes('embed') || href.includes('player') || 
                                href.includes('watch') || href.includes('stream'))) {
                                // Skip YouTube
                                if (!href.includes('youtube.com') && !href.includes('youtu.be')) {
                                    sources.add(href);
                                }
                            }
                        });
                        
                        // Extract from onclick handlers
                        document.querySelectorAll('[onclick]').forEach(el => {
                            const onclick = el.getAttribute('onclick') || '';
                            const urlMatch = onclick.match(/['"](https?:\\/\\/[^'"]+)['"]/);
                            if (urlMatch && urlMatch[1]) {
                                const url = urlMatch[1];
                                // Skip YouTube
                                if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                                    sources.add(url);
                                }
                            }
                        });
                        
                        // Extract from script tags - VERY SELECTIVE
                        document.querySelectorAll('script').forEach(script => {
                            const text = script.textContent || '';
                            const urlPattern = /(https?:\\/\\/[^\\s"'<>]+)/gi;
                            const matches = text.matchAll(urlPattern);
                            for (const match of matches) {
                                const url = match[1];
                                // Only video-related URLs, NO YouTube
                                if ((url.includes('embed') || url.includes('player') || 
                                    url.includes('stream') || url.includes('video') ||
                                    url.includes('.m3u8') || url.includes('.mp4')) &&
                                    !url.includes('youtube.com') && !url.includes('youtu.be')) {
                                    sources.add(url);
                                }
                            }
                        });
                        
                        return Array.from(sources);
                    }
                """)
                
                if extracted_urls:
                    # Filter out YouTube URLs again (double check)
                    filtered = [url for url in extracted_urls if not self._is_youtube_url(url)]
                    all_urls.update(filtered)
                    logger.info(f"🔍 Playwright found {len(filtered)} non-YouTube URLs")
                    
            except Exception as e:
                logger.warning(f"⚠️ Playwright extraction failed: {e}")
        
        # Method 2: Static HTML extraction
        static_urls = self._extract_from_static_html(response)
        all_urls.update(static_urls)
        logger.info(f"🔍 Static HTML found {len(static_urls)} non-YouTube URLs")
        
        # CRITICAL: Filter and validate all URLs
        valid_links = []
        rejected_youtube = 0
        rejected_other = 0
        
        for url in all_urls:
            # Skip if should be rejected
            if self._should_reject_url(url):
                if self._is_youtube_url(url):
                    rejected_youtube += 1
                    logger.debug(f"❌ Rejected YouTube: {url[:80]}")
                else:
                    rejected_other += 1
                    logger.debug(f"❌ Rejected (other): {url[:80]}")
                continue
            
            # Accept if looks like streaming link
            if self._should_accept_url(url):
                valid_links.append({
                    "quality": self._detect_quality(url),
                    "language": "EN",
                    "source_url": url,
                    "is_active": True,
                })
                logger.info(f"✅ ACCEPTED: {url[:80]}")
        
        logger.info(f"📊 Filtering results: Accepted={len(valid_links)}, Rejected YouTube={rejected_youtube}, Rejected Other={rejected_other}")
        
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
        """Extract URLs from static HTML (NO YouTube)"""
        urls = set()
        
        # Extract from various sources
        selectors = [
            "iframe::attr(src)",
            "iframe::attr(data-src)",
            "iframe::attr(data-url)",
            "iframe::attr(data-lazy)",
            "[data-link]::attr(data-link)",
            "[data-server]::attr(data-server)",
            "[data-embed]::attr(data-embed)",
            "[data-player]::attr(data-player)",
            "a[href*='embed']::attr(href)",
            "a[href*='player']::attr(href)",
        ]
        
        for selector in selectors:
            found_urls = response.css(selector).getall()
            # Filter out YouTube
            filtered = [url for url in found_urls if not self._is_youtube_url(url)]
            urls.update(filtered)
        
        # Extract from script tags - VERY SELECTIVE
        scripts = response.css("script::text").getall()
        for script in scripts:
            # Find ALL HTTP URLs
            pattern = r'(https?://[^\s"\'<>]+)'
            matches = re.findall(pattern, script, re.IGNORECASE)
            for url in matches:
                # Only video-related, NO YouTube
                if (any(word in url.lower() for word in ['embed', 'player', 'stream', 'video', 'watch', '.m3u8', '.mp4']) and
                    not self._is_youtube_url(url)):
                    urls.add(url)
        
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