# File: scraper/scraper/spiders/example_spider.py
# REPLACE the entire file

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
    Improved spider with more aggressive URL extraction
    """

    name = "oneflix"
    allowed_domains = ["1flix.to"]
    start_urls = ["https://1flix.to/home"]
    
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
        """Get Playwright configuration"""
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
                {
                    "coroutine": "evaluate",
                    "args": ["""
                        () => {
                            const selectors = [
                                'a[data-link]', 'button[data-link]',
                                'a[data-server]', 'button[data-server]',
                                '.server-item', '.server-btn',
                                '[class*="server"]', '[id*="server"]',
                                'button[onclick]', 'a[onclick]',
                                '.btn', 'button', 'a[href*="embed"]'
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
                                        } catch(e) {}
                                    }
                                });
                            });
                            
                            return clicked;
                        }
                    """]
                },
                {"coroutine": "wait_for_timeout", "args": [10000]},
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
        """Parse movie detail page"""
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
        
        # Extract streaming links
        links = self._extract_streaming_links(response)
        
        if not links:
            logger.warning(f"⚠️ No streaming links found for {title}")
        else:
            logger.info(f"✅ Found {len(links)} streaming links for {title}")
        
        item["links"] = links
        
        yield item

    def _extract_streaming_links(self, response: TextResponse):
        """AGGRESSIVE URL extraction - gets ALL potential video URLs"""
        page = response.meta.get("playwright_page")
        all_urls = set()
        
        # Method 1: Playwright page evaluation
        if page:
            try:
                extracted_urls = page.evaluate("""
                    () => {
                        const sources = new Set();
                        
                        // Extract from iframes - VERY IMPORTANT
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const src = iframe.src || iframe.getAttribute('data-src') || 
                                       iframe.getAttribute('data-url') || iframe.getAttribute('data-lazy');
                            if (src && src.startsWith('http')) {
                                sources.add(src);
                            }
                        });
                        
                        // Extract from data attributes
                        const dataAttrs = ['data-link', 'data-server', 'data-embed', 
                                          'data-player', 'data-url', 'data-video', 'data-src'];
                        dataAttrs.forEach(attr => {
                            document.querySelectorAll(`[${attr}]`).forEach(el => {
                                const link = el.getAttribute(attr);
                                if (link && link.startsWith('http')) {
                                    sources.add(link);
                                }
                            });
                        });
                        
                        // Extract from links
                        document.querySelectorAll('a[href]').forEach(a => {
                            const href = a.href;
                            if (href && (href.includes('embed') || href.includes('player') || 
                                href.includes('watch') || href.includes('stream'))) {
                                sources.add(href);
                            }
                        });
                        
                        // Extract from onclick handlers
                        document.querySelectorAll('[onclick]').forEach(el => {
                            const onclick = el.getAttribute('onclick') || '';
                            const urlMatch = onclick.match(/['"](https?:\\/\\/[^'"]+)['"]/);
                            if (urlMatch && urlMatch[1]) {
                                sources.add(urlMatch[1]);
                            }
                        });
                        
                        // Extract from ALL script tags - VERY AGGRESSIVE
                        document.querySelectorAll('script').forEach(script => {
                            const text = script.textContent || '';
                            // Find all HTTP URLs in the script
                            const urlPattern = /(https?:\\/\\/[^\\s"'<>]+)/gi;
                            const matches = text.matchAll(urlPattern);
                            for (const match of matches) {
                                const url = match[1];
                                // Only add if it looks like a video URL
                                if (url.includes('embed') || url.includes('player') || 
                                    url.includes('stream') || url.includes('video') ||
                                    url.includes('.m3u8') || url.includes('.mp4')) {
                                    sources.add(url);
                                }
                            }
                        });
                        
                        return Array.from(sources);
                    }
                """)
                
                if extracted_urls:
                    all_urls.update(extracted_urls)
                    logger.info(f"🔍 Playwright found {len(extracted_urls)} URLs")
                    for url in extracted_urls[:5]:  # Log first 5
                        logger.info(f"   - {url[:100]}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Playwright extraction failed: {e}")
        
        # Method 2: Static HTML extraction
        static_urls = self._extract_from_static_html(response)
        all_urls.update(static_urls)
        logger.info(f"🔍 Static HTML found {len(static_urls)} URLs")
        
        # Convert to link format
        valid_links = []
        for url in all_urls:
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
        """Extract ALL possible URLs from static HTML"""
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
            urls.update(response.css(selector).getall())
        
        # Extract from ALL script tags - very aggressive
        scripts = response.css("script::text").getall()
        for script in scripts:
            # Find ALL HTTP URLs
            pattern = r'(https?://[^\s"\'<>]+)'
            matches = re.findall(pattern, script, re.IGNORECASE)
            for url in matches:
                # Only add if it looks video-related
                if any(word in url.lower() for word in ['embed', 'player', 'stream', 'video', 'watch', '.m3u8', '.mp4']):
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