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
    Improved Playwright-enabled spider for 1flix.to with on-demand scraping.
    """

    name = "oneflix"
    allowed_domains = ["1flix.to"]
    start_urls = ["https://1flix.to/home"]
    
    # Known working video hosting domains
    VALID_VIDEO_HOSTS = [
        "vidoza.net", "streamtape.com", "mixdrop.co", "doodstream.com",
        "filemoon.sx", "upstream.to", "streamlare.com", "streamhub.to",
        "streamwish.to", "videostr.me", "voe.sx", "streamvid.net"
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
        """Start scraping with proper headers and Playwright configuration."""
        ua = UserAgent().random if UserAgent else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        headers = {"User-Agent": ua}
        
        for url in self.start_urls:
            if self.on_demand_mode:
                # For on-demand, go directly to the movie page
                yield Request(
                    url,
                    headers=headers,
                    callback=self.parse_movie_page,
                    meta=self._get_playwright_meta(is_detail_page=True),
                    dont_filter=True
                )
            else:
                # For regular scraping, parse listing first
                yield Request(
                    url,
                    headers=headers,
                    callback=self.parse_listing,
                    meta=self._get_playwright_meta(is_detail_page=False),
                )

    def _get_playwright_meta(self, is_detail_page=False):
        """Get Playwright configuration based on page type."""
        base_meta = {
            "playwright": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "networkidle",
                "timeout": 60000
            },
        }
        
        if is_detail_page:
            # For movie detail pages, click server buttons and wait for video players
            base_meta["playwright_page_coroutines"] = [
                # Wait for page to stabilize
                {"coroutine": "wait_for_timeout", "args": [3000]},
                
                # Scroll to load lazy content
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
                
                # Click ALL server buttons to reveal video players
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            const selectors = [
                                'a[data-link]', 'button[data-link]',
                                'a[data-server]', 'button[data-server]',
                                '.server-item', '.server-btn',
                                '[class*="server"]', '[id*="server"]',
                                'button[onclick]', 'a[onclick]'
                            ];
                            
                            let clicked = 0;
                            selectors.forEach(selector => {
                                const elements = Array.from(document.querySelectorAll(selector));
                                elements.forEach((el) => {
                                    if (el.offsetParent !== null) {
                                        try {
                                            el.scrollIntoView({behavior: 'auto', block: 'center'});
                                            el.click();
                                            clicked++;
                                        } catch(e) {
                                            console.warn('Click failed:', e);
                                        }
                                    }
                                });
                            });
                            
                            console.log('Clicked ' + clicked + ' server buttons');
                            return clicked;
                        }
                    """]
                },
                
                # Wait longer for video players to load
                {"coroutine": "wait_for_timeout", "args": [10000]},
                
                # Scroll again to trigger more lazy loading
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight);
                            return true;
                        }
                    """]
                },
                {"coroutine": "wait_for_timeout", "args": [3000]},
            ]
        
        return base_meta

    def parse_listing(self, response):
        """Parse listing page (only used in regular mode)."""
        if self.on_demand_mode:
            return
        
        logger.info(f"📋 Parsing listing: {response.url}")
        
        # Extract movie links
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
        """Parse movie detail page and extract streaming links."""
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
        
        # Extract streaming links using Playwright page
        links = self._extract_streaming_links(response)
        
        if not links:
            logger.warning(f"⚠️  No valid streaming links found for {title}")
        else:
            logger.info(f"✅ Found {len(links)} streaming links for {title}")
        
        item["links"] = links
        
        yield item

    def _extract_streaming_links(self, response: TextResponse):
        """Extract and validate streaming links from the page."""
        page = response.meta.get("playwright_page")
        all_urls = set()
        
        # Method 1: Extract from Playwright page evaluation
        if page:
            try:
                extracted_urls = page.evaluate("""
                    () => {
                        const sources = new Set();
                        
                        // Extract from iframes
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const src = iframe.src || iframe.getAttribute('data-src') || 
                                       iframe.getAttribute('data-url') || '';
                            if (src && src.startsWith('http')) {
                                sources.add(src);
                            }
                        });
                        
                        // Extract from data attributes
                        const dataAttrs = ['data-link', 'data-server', 'data-embed', 
                                          'data-player', 'data-url', 'data-video'];
                        dataAttrs.forEach(attr => {
                            document.querySelectorAll(`[${attr}]`).forEach(el => {
                                const link = el.getAttribute(attr);
                                if (link && link.startsWith('http')) {
                                    sources.add(link);
                                }
                            });
                        });
                        
                        // Extract from onclick handlers
                        document.querySelectorAll('[onclick]').forEach(el => {
                            const onclick = el.getAttribute('onclick') || '';
                            const urlMatch = onclick.match(/['"](https?:\\/\\/[^'"]+)['"]/);
                            if (urlMatch && urlMatch[1]) {
                                sources.add(urlMatch[1]);
                            }
                        });
                        
                        // Extract from script tags
                        document.querySelectorAll('script').forEach(script => {
                            const text = script.textContent || '';
                            const urlPattern = /['"](https?:\\/\\/[^'"]*(?:vidoza|streamtape|mixdrop|dood|filemoon|upstream|streamlare|streamhub|streamwish|videostr|voe|streamvid)[^'"]*)['"]/gi;
                            const matches = text.matchAll(urlPattern);
                            for (const match of matches) {
                                if (match[1]) {
                                    sources.add(match[1]);
                                }
                            }
                        });
                        
                        return Array.from(sources);
                    }
                """)
                
                if extracted_urls:
                    all_urls.update(extracted_urls)
                    logger.info(f"🔍 Playwright found {len(extracted_urls)} URLs")
                    
            except Exception as e:
                logger.warning(f"⚠️  Playwright extraction failed: {e}")
        
        # Method 2: Extract from static HTML
        static_urls = self._extract_from_static_html(response)
        all_urls.update(static_urls)
        logger.info(f"🔍 Static HTML found {len(static_urls)} URLs")
        
        # Filter and validate URLs
        valid_links = []
        for url in all_urls:
            if self._is_valid_video_url(url):
                valid_links.append({
                    "quality": self._detect_quality(url),
                    "language": "EN",
                    "source_url": url,
                    "is_active": True,
                })
        
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
        """Extract URLs from static HTML."""
        urls = set()
        
        # Extract from various sources
        selectors = [
            "iframe::attr(src)",
            "iframe::attr(data-src)",
            "iframe::attr(data-url)",
            "[data-link]::attr(data-link)",
            "[data-server]::attr(data-server)",
            "[data-embed]::attr(data-embed)",
            "[data-player]::attr(data-player)",
        ]
        
        for selector in selectors:
            urls.update(response.css(selector).getall())
        
        # Extract from script tags
        scripts = response.css("script::text").getall()
        for script in scripts:
            # Look for video hosting URLs in JavaScript
            pattern = r'["\']((https?://[^"\']*(?:' + '|'.join([
                host.replace('.', r'\.') for host in self.VALID_VIDEO_HOSTS
            ]) + r')[^"\']*))["\']'
            matches = re.findall(pattern, script, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    urls.add(match[0])
                else:
                    urls.add(match)
        
        return urls

    def _is_valid_video_url(self, url: str) -> bool:
        """Check if URL is a valid video hosting URL."""
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # Must be HTTP/HTTPS
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Must not be empty or placeholder
        if url in ['javascript:;', 'javascript:void(0)', '#']:
            return False
        
        url_lower = url.lower()
        
        # Block bad patterns
        bad_patterns = [
            'recaptcha', 'google.com', 'gstatic.com', 'youtube.com', 'youtu.be',
            '1flix.to', 'ads', 'advertising', 'analytics', 'facebook.com',
            'twitter.com', 'instagram.com', 'sharethis'
        ]
        
        if any(bad in url_lower for bad in bad_patterns):
            return False
        
        # Must be from a known video hosting service
        if not any(host in url_lower for host in self.VALID_VIDEO_HOSTS):
            return False
        
        logger.debug(f"✅ Valid URL: {url[:80]}...")
        return True

    def _detect_quality(self, url: str) -> str:
        """Detect video quality from URL."""
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