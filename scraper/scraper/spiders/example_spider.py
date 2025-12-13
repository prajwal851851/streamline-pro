import scrapy
from scrapy import Request

try:
    from fake_useragent import UserAgent
except Exception:  # pragma: no cover - optional dependency
    UserAgent = None

from scraper.items import StreamingItem


class OneFlixSpider(scrapy.Spider):
    """
    Playwright-enabled spider for 1flix.to.
    The site renders streaming info via JS, so we render pages with Playwright.
    """

    name = "oneflix"
    allowed_domains = ["1flix.to"]
    # Start from multiple pages to get more movies
    start_urls = [
        "https://1flix.to/home",
        "https://1flix.to/movie",
        "https://1flix.to/tv-show",
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_movies = set()  # Track crawled movies to avoid duplicates
        self.pages_crawled = 0  # Track pagination depth
        self.max_pages = int(kwargs.get('max_pages', 10))  # Limit pagination depth

    async def start(self):
        """
        Scrapy 2.13+ prefers start() (async) over start_requests().
        """
        ua = UserAgent().random if UserAgent else "Mozilla/5.0"
        headers = {"User-Agent": ua}
        for url in self.start_urls:
            yield Request(
                url,
                headers=headers,
                callback=self.parse_listing,
                meta={
                    "playwright": True,
                    "playwright_page_goto_kwargs": {"wait_until": "domcontentloaded", "timeout": 30000},  # Reduced timeout for listing pages
                },
            )

    def parse_listing(self, response):
        """
        Parse listing page: grab movie detail links and follow pagination.
        Using a broad selector to catch movie links.
        """
        self.logger.info(f"Parsing listing page: {response.url}")
        
        # Extract all movie links with multiple selectors
        movie_detail_links = set()
        movie_detail_links.update(response.css("a[href^='/movie/watch']::attr(href)").getall())
        movie_detail_links.update(response.css("a[href*='/movie/watch-']::attr(href)").getall())
        movie_detail_links.update(response.css("a[href*='/tv/watch-']::attr(href)").getall())
        
        new_links = [link for link in movie_detail_links if link and link not in self.seen_movies]
        self.logger.info(f"Found {len(new_links)} new movie links on {response.url} (total seen: {len(self.seen_movies)})")
        
        for link in new_links:
            self.seen_movies.add(link)
            yield response.follow(
                link,
                callback=self.parse_movie_page,
                meta={
                    "playwright": True,
                    "playwright_page_goto_kwargs": {
                        "wait_until": "networkidle", 
                        "timeout": 60000
                    },
                    # Use page coroutines to click server buttons and wait for video players
                    "playwright_page_coroutines": [
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [3000]  # Wait 3 seconds after networkidle for page to stabilize
                        },
                        {
                            "coroutine": "evaluate",
                            "args": ["""
                                () => {
                                    // Click on server buttons to reveal video players
                                    const selectors = [
                                        'a[data-link]', 'button[data-link]', 
                                        'a[data-server]', 'button[data-server]',
                                        '.server-item a', '.server-btn',
                                        '[class*="server"] a', '[class*="server"] button',
                                        '[data-id]', '.btn-server', '.server-btn'
                                    ];
                                    
                                    let clicked = 0;
                                    selectors.forEach(selector => {
                                        const elements = document.querySelectorAll(selector);
                                        elements.forEach((el, index) => {
                                            if (clicked < 10 && el.offsetParent !== null) { // Only visible elements
                                                try { 
                                                    el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                                    setTimeout(() => {
                                                        el.click();
                                                    }, index * 200);
                                                    clicked++;
                                                } catch(e) {}
                                            }
                                        });
                                    });
                                    return clicked;
                                }
                            """]
                        },
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [5000]  # Wait 5 seconds for video players to load after clicking
                        }
                    ],
                },
            )

        # Follow all pagination links to discover more items (with limit)
        if self.pages_crawled < self.max_pages:
            # Also check for "next" button and numbered pages
            pagination_links = set()
            pagination_links.update(response.css("nav .page-item a::attr(href)").getall())
            pagination_links.update(response.css("a[rel='next']::attr(href)").getall())
            pagination_links.update(response.css(".pagination a::attr(href)").getall())
            pagination_links.update(response.css(".pager a::attr(href)").getall())
            
            for nxt in pagination_links:
                if nxt and nxt not in ["#", "javascript:void(0)"]:
                    self.pages_crawled += 1
                    self.logger.info(f"Following pagination link: {nxt} (page {self.pages_crawled}/{self.max_pages})")
                    yield response.follow(
                        nxt,
                        callback=self.parse_listing,
                        meta={
                            "playwright": True,
                            "playwright_page_goto_kwargs": {"wait_until": "domcontentloaded", "timeout": 30000},
                        },
                    )
        else:
            self.logger.info(f"Reached max pages limit ({self.max_pages}), stopping pagination")

    def parse_movie_page(self, response):
        """
        Parse an individual movie detail page and collect streaming links.
        Many elements are dynamically injected; we rely on rendered HTML and multiple fallbacks.
        """
        # Skip if already processed
        movie_slug = response.url.rstrip("/").split("/")[-1]
        if movie_slug in self.seen_movies:
            return
        
        self.logger.info(f"Parsing movie page: {response.url}")
        
        item = StreamingItem()

        # Title fallback: first h1
        title = (response.css("h1::text").get() or "").strip()
        item["title"] = title
        item["imdb_id"] = movie_slug
        
        self.logger.info(f"Extracted movie: {title} (ID: {movie_slug})")

        # Year: first 4-digit number in spans
        year_texts = [t.strip() for t in response.css("span::text").getall() if t and t.strip().isdigit()]
        year = None
        for t in year_texts:
            if len(t) == 4 and t.isdigit():
                year = int(t)
                break
        item["year"] = year

        # Type is always movie on this site
        item["type"] = "movie"

        # Poster from og:image or first image
        poster = response.css("meta[property='og:image']::attr(content)").get()
        if not poster:
            poster = response.css("img::attr(src)").get()
        item["poster_url"] = poster

        # Synopsis from meta description or first paragraph
        synopsis = response.css("meta[name='description']::attr(content)").get()
        if not synopsis:
            synopsis = response.css("p::text").get()
        item["synopsis"] = synopsis

        # Extract iframe sources from the detail page
        # Server buttons should already be clicked by page coroutines
        detail_page_links = []
        
        # Extract from rendered HTML (after server buttons were clicked by coroutines)
        iframe_sources = response.css("iframe::attr(src)").getall()
        iframe_sources += response.css("iframe::attr(data-src)").getall()
        iframe_sources += response.css("iframe::attr(data-url)").getall()
        
        # Also extract from data attributes on server buttons/links
        data_links = response.css("[data-link]::attr(data-link)").getall()
        data_links += response.css("[data-server]::attr(data-server)").getall()
        data_links += response.css("[data-embed]::attr(data-embed)").getall()
        data_links += response.css("[data-player]::attr(data-player)").getall()
        iframe_sources.extend(data_links)
        
        # Known video hosting domains that we want to extract (actual video hosts, not YouTube)
        video_hosts = ["vidoza", "streamtape", "mixdrop", "dood", "filemoon", "upstream", "streamlare", "streamhub", "streamwish", "videostr"]
        
        for iframe_src in iframe_sources:
            if not iframe_src or not isinstance(iframe_src, str):
                continue
                
            iframe_src = iframe_src.strip()
            if not iframe_src or iframe_src.startswith("javascript:") or iframe_src == "javascript:;":
                continue
            
            # Must be HTTP/HTTPS URL
            if not iframe_src.startswith(("http://", "https://")):
                continue
            
            url_lower = iframe_src.lower()
            
            # Aggressively filter out bad URLs
            bad_patterns = [
                "recaptcha", "google.com", "gstatic.com", "ads", "advertising", 
                "analytics", "doubleclick", "googletagmanager", "sharethis", "1flix.to"
            ]
            if any(bad in url_lower for bad in bad_patterns):
                continue
            
            # Only include URLs from known video hosting services (NOT 1flix.to, NOT YouTube)
            # YouTube embeds are just trailers, not actual movies
            if (any(host in url_lower for host in video_hosts) and 
                "1flix.to" not in url_lower and 
                "youtube.com" not in url_lower and 
                "youtu.be" not in url_lower):
                if iframe_src not in detail_page_links:
                    detail_page_links.append(iframe_src)
        
        self.logger.info(f"Extracted {len(detail_page_links)} video hosting URLs from detail page")

        # After page parse, attempt AJAX endpoint to fetch actual stream servers.
        movie_id = None
        slug = item["imdb_id"]
        for part in slug.split("-"):
            if part.isdigit():
                movie_id = part
                break

        if movie_id:
            # Use Playwright to interact with the page and extract video hosting URLs
            # Request the AJAX endpoint with Playwright to render it
            ajax_url = f"https://1flix.to/ajax/episode/list/{movie_id}"
            yield Request(
                ajax_url,
                callback=self.parse_ajax_links,
                meta={
                    "item": item, 
                    "original_url": response.url, 
                    "detail_page_links": detail_page_links,
                    "playwright": True,
                    "playwright_page_goto_kwargs": {"wait_until": "networkidle", "timeout": 30000},
                    "playwright_page_coroutines": [
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [3000]  # Wait 3 seconds for server buttons to load
                        },
                        {
                            "coroutine": "evaluate",
                            "args": ["""
                                () => {
                                    // Click on all server buttons to reveal video players
                                    const selectors = [
                                        'a[data-link]', 'button[data-link]', 
                                        'a[data-server]', 'button[data-server]',
                                        '.server-item a', '.server-btn',
                                        '[class*="server"] a', '[class*="server"] button',
                                        '[data-id]', '.btn-server',
                                        '.episode-server-item', '.server-list a',
                                        '[onclick*="server"]', '[onclick*="load"]'
                                    ];
                                    
                                    let clicked = 0;
                                    selectors.forEach(selector => {
                                        const elements = Array.from(document.querySelectorAll(selector));
                                        elements.forEach((el, index) => {
                                            if (clicked < 15 && el.offsetParent !== null) { // Only visible elements
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
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [5000]  # Wait 5 seconds for video players to load after clicking
                        }
                    ],
                },
                dont_filter=True,
            )
        else:
            # If no movie_id found, use detail page links if any (but filter them first)
            filtered_links = []
            for link in detail_page_links:
                link_lower = link.lower()
                # Exclude YouTube (trailers) and 1flix.to
                if "youtube.com" in link_lower or "youtu.be" in link_lower or "1flix.to" in link_lower:
                    continue
                # Only include actual video hosting services
                video_hosts = ["vidoza", "streamtape", "mixdrop", "dood", "filemoon", "upstream", "streamlare", "streamhub", "streamwish", "videostr"]
                if any(host in link_lower for host in video_hosts):
                    filtered_links.append(link)
            
            if filtered_links:
                item["links"] = [
                    {
                        "quality": "HD",
                        "language": "EN",
                        "source_url": link,
                        "is_active": True,
                    }
                    for link in filtered_links[:3]  # Limit to first 3
                ]
            # Don't yield item if no valid links found - we don't want movies without playable links
            if item.get("links"):
                yield item

    def parse_ajax_links(self, response):
        """
        Parse the AJAX episode list to extract stream URLs/iframes.
        Uses Playwright to click server buttons and extract actual video hosting URLs.
        """
        from parsel import Selector
        import re

        item = response.meta["item"]
        detail_page_links = response.meta.get("detail_page_links", [])
        self.logger.info(f"Parsing AJAX links for: {item.get('title', 'Unknown')}")
        
        links = []
        seen = set()
        
        # Extract iframe sources using Playwright page evaluation (after clicking server buttons)
        page = response.meta.get("playwright_page")
        video_hosting_urls = []
        
        if page:
            try:
                # Extract all iframe sources and video hosting URLs from the page (after server buttons were clicked)
                extracted_data = page.evaluate("""
                    () => {
                        const sources = [];
                        
                        // Extract from all iframes
                        const iframes = Array.from(document.querySelectorAll('iframe'));
                        iframes.forEach(iframe => {
                            const src = iframe.src || iframe.getAttribute('data-src') || iframe.getAttribute('data-url') || '';
                            if (src && src.startsWith('http')) {
                                sources.push(src);
                            }
                        });
                        
                        // Extract from data attributes on server buttons/links
                        const serverElements = Array.from(document.querySelectorAll('[data-link], [data-server], [data-embed], [data-player], [data-url], [data-video]'));
                        serverElements.forEach(el => {
                            const link = el.getAttribute('data-link') || 
                                        el.getAttribute('data-server') || 
                                        el.getAttribute('data-embed') || 
                                        el.getAttribute('data-player') ||
                                        el.getAttribute('data-url') ||
                                        el.getAttribute('data-video');
                            if (link && link.startsWith('http')) {
                                sources.push(link);
                            }
                        });
                        
                        // Extract from href attributes on server links
                        const serverLinks = Array.from(document.querySelectorAll('a[href*="vidoza"], a[href*="streamtape"], a[href*="mixdrop"], a[href*="dood"], a[href*="filemoon"], a[href*="videostr"]'));
                        serverLinks.forEach(el => {
                            const href = el.getAttribute('href');
                            if (href && href.startsWith('http')) {
                                sources.push(href);
                            }
                        });
                        
                        // Extract from onclick handlers
                        const onclickElements = Array.from(document.querySelectorAll('[onclick]'));
                        onclickElements.forEach(el => {
                            const onclick = el.getAttribute('onclick') || '';
                            const urlMatch = onclick.match(/['"](https?:\/\/[^'"]+)['"]/);
                            if (urlMatch && urlMatch[1]) {
                                sources.push(urlMatch[1]);
                            }
                        });
                        
                        // Extract from JavaScript variables in script tags
                        const scripts = Array.from(document.querySelectorAll('script'));
                        scripts.forEach(script => {
                            const text = script.textContent || '';
                            // Look for video hosting URLs in JavaScript
                            const urlPattern = /['"](https?:\/\/[^'"]*(?:vidoza|streamtape|mixdrop|dood|filemoon|upstream|streamlare|streamhub|streamwish|videostr)[^'"]*)['"]/gi;
                            const matches = text.matchAll(urlPattern);
                            for (const match of matches) {
                                if (match[1]) {
                                    sources.push(match[1]);
                                }
                            }
                        });
                        
                        return [...new Set(sources)]; // Remove duplicates
                    }
                """)
                
                video_hosting_urls = extracted_data if extracted_data else []
                self.logger.info(f"Extracted {len(video_hosting_urls)} URLs from Playwright page")
            except Exception as e:
                self.logger.warning(f"Error extracting URLs from Playwright page: {e}")
        
        # Start with detail page iframe links (they might be valid video hosting URLs)
        # Exclude YouTube (just trailers) and 1flix.to
        for link in detail_page_links:
            if link not in seen:
                link_lower = link.lower()
                # Skip YouTube (trailers only) and 1flix.to
                if "youtube.com" in link_lower or "youtu.be" in link_lower or "1flix.to" in link_lower:
                    continue
                seen.add(link)
                # Check if it's a valid video hosting URL (actual video hosts, not YouTube)
                valid_domains = ["vidoza", "streamtape", "mixdrop", "dood", "filemoon", "upstream", "streamlare", "streamhub", "streamwish", "videostr"]
                if any(domain in link_lower for domain in valid_domains):
                    links.append({
                        "quality": "HD",
                        "language": "EN",
                        "source_url": link,
                        "is_active": True,
                    })
        
        # Add video hosting URLs extracted from Playwright
        # Exclude YouTube (trailers) and 1flix.to
        for url in video_hosting_urls:
            if url and url not in seen:
                url_lower = url.lower()
                # Skip YouTube (trailers only) and 1flix.to
                if "youtube.com" in url_lower or "youtu.be" in url_lower or "1flix.to" in url_lower:
                    continue
                seen.add(url)
                # Only accept actual video hosting services
                valid_domains = ["vidoza", "streamtape", "mixdrop", "dood", "filemoon", "upstream", "streamlare", "streamhub", "streamwish", "videostr"]
                if any(domain in url_lower for domain in valid_domains):
                    links.append({
                        "quality": "HD",
                        "language": "EN",
                        "source_url": url,
                        "is_active": True,
                    })
        
        # Also parse static HTML as fallback
        sel = Selector(text=response.text)
        item["links"] = []

        # Extract all potential URLs from various sources
        candidates = []
        
        # Look for server links in data attributes and hrefs (common pattern on streaming sites)
        candidates += sel.css("a[data-link]::attr(data-link)").getall()
        candidates += sel.css("a[data-server]::attr(data-server)").getall()
        candidates += sel.css("button[data-link]::attr(data-link)").getall()
        candidates += sel.css("button[data-server]::attr(data-server)").getall()
        candidates += sel.css("div[data-link]::attr(data-link)").getall()
        candidates += sel.css("div[data-server]::attr(data-server)").getall()
        candidates += sel.css("a[href]::attr(href)").getall()
        candidates += sel.css("iframe::attr(src)").getall()
        candidates += sel.css("iframe::attr(data-src)").getall()
        candidates += sel.css("iframe::attr(data-url)").getall()
        candidates += sel.css("source::attr(src)").getall()
        candidates += sel.css("[data-url]::attr(data-url)").getall()
        candidates += sel.css("[data-embed]::attr(data-embed)").getall()
        candidates += sel.css("[data-player]::attr(data-player)").getall()
        candidates += sel.css("[data-video]::attr(data-video)").getall()
        candidates += sel.css("[data-stream]::attr(data-stream)").getall()
        
        # Look for video hosting service URLs in href attributes specifically
        candidates += sel.css('a[href*="vidoza"]::attr(href)').getall()
        candidates += sel.css('a[href*="streamtape"]::attr(href)').getall()
        candidates += sel.css('a[href*="mixdrop"]::attr(href)').getall()
        candidates += sel.css('a[href*="dood"]::attr(href)').getall()
        candidates += sel.css('a[href*="filemoon"]::attr(href)').getall()
        candidates += sel.css('a[href*="videostr"]::attr(href)').getall()
        
        # Also extract URLs from onclick handlers and data attributes
        onclick_attrs = sel.css("[onclick]::attr(onclick)").getall()
        for onclick in onclick_attrs:
            # Extract URLs from onclick="window.open('url')" or similar
            url_matches = re.findall(r"['\"](https?://[^'\"]+)['\"]", onclick)
            candidates.extend(url_matches)
        
        # Extract URLs from JavaScript code in script tags
        script_texts = sel.css("script::text").getall()
        for script in script_texts:
            # Look for URLs in JavaScript variables (e.g., var url = "https://...")
            js_urls = re.findall(r"['\"](https?://[^'\"]+)['\"]", script)
            candidates.extend(js_urls)
            
            # Specifically look for video hosting service URLs in JavaScript
            video_host_pattern = r"['\"](https?://[^'\"]*(?:vidoza|streamtape|mixdrop|dood|filemoon|upstream|streamlare|streamhub|streamwish|videostr)[^'\"]*)['\"]"
            video_host_urls = re.findall(video_host_pattern, script, re.IGNORECASE)
            candidates.extend(video_host_urls)

        # Filter and add valid stream URLs - be very strict
        bad_patterns = [
            "recaptcha",
            "google.com",
            "youtube.com",
            "youtu.be",
            "javascript:",
            "sysmeasuring",
            "wlmghqpmob",
            "oamoameevee",
            "axgbr.com",
            "fedoq.com",
            "sharethis",
            "google-analytics",
            "googletagmanager",
            "cloudflare",
            "animecrush",
            "my.rtmark",
            "count-server.sharethis",
            "platform-cdn.sharethis",
            "buttons-config.sharethis",
            "l.sharethis.com",
            "gstatic.com",
            "doubleclick",
            "ads",
            "advertising",
            "analytics",
        ]

        for url in candidates:
            if not url or not isinstance(url, str):
                continue
            
            # Skip empty or invalid URLs
            url = url.strip()
            if not url or url.startswith("#") or url == "javascript:;":
                continue
            
            # Skip bad patterns
            url_lower = url.lower()
            if any(bad in url_lower for bad in bad_patterns):
                continue
            
            # Must be HTTP/HTTPS URL
            if not url.startswith(("http://", "https://")):
                # Try to make it absolute
                full = response.urljoin(url)
                if not full.startswith(("http://", "https://")):
                    continue
            else:
                full = url
            
            # Skip if already seen
            if full in seen:
                continue
            
            # Additional validation: should look like a stream/player URL
            # Reject if it's from google, youtube (trailers), or other ad/analytics domains
            if "google" in url_lower or "gstatic" in url_lower or "youtube.com" in url_lower or "youtu.be" in url_lower:
                continue
            
            # Exclude ALL 1flix.to URLs - they can't be embedded
            if "1flix.to" in url_lower:
                continue
            
            # Only accept URLs from actual video hosting services (not YouTube trailers)
            valid_domains = [
                "vidoza",
                "streamtape",
                "mixdrop",
                "dood",
                "filemoon",
                "upstream",
                "streamlare",
                "streamhub",
                "streamwish",
                "videostr",
                "mp4",
                "m3u8",
                "mpeg",
                "mov",
                "avi",
                "mkv",
            ]
            
            # Check if URL contains any valid domain/keyword
            is_valid = any(domain in url_lower for domain in valid_domains)
            
            # Only accept URLs from actual video hosting services
            if is_valid:
                seen.add(full)
                # Try to detect quality from URL or text
                quality = "HD"
                if "720" in url_lower or "720p" in url_lower:
                    quality = "720p"
                elif "1080" in url_lower or "1080p" in url_lower:
                    quality = "1080p"
                elif "4k" in url_lower or "2160" in url_lower:
                    quality = "4K"
                elif "cam" in url_lower:
                    quality = "CAM"
                
                links.append(
                    {
                        "quality": quality,
                        "language": "EN",
                        "source_url": full,
                        "is_active": True,
                    }
                )

        # Only save if we found real video hosting links
        # Never save 1flix.to detail pages or reCAPTCHA URLs
        if links:
            item["links"] = links
            self.logger.info(f"Found {len(links)} stream links for {item.get('title', 'Unknown')}")
            yield item
        else:
            # Don't save movies without valid playable links
            self.logger.warning(f"No valid stream links found for {item.get('title', 'Unknown')} - skipping movie")

