import re
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
        
        # On-demand scraping: if target_url is provided, only scrape that URL
        self.target_url = kwargs.get('target_url', None)
        if self.target_url:
            self.start_urls = [self.target_url]
            self.max_pages = 1  # Don't paginate for on-demand scraping
            self.logger.info(f"On-demand scraping mode: targeting {self.target_url}")

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
        
        # Process all links, not just new ones (to update existing movies with new links)
        new_links = [link for link in movie_detail_links if link]
        self.logger.info(f"Found {len(new_links)} movie links on {response.url} (processing all to update links)")
        
        for link in new_links:
            # Track but don't skip - allow re-processing
            if link not in self.seen_movies:
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
                            "args": [5000]  # Wait 5 seconds after networkidle for page to stabilize
                        },
                        {
                            "coroutine": "evaluate",
                            "args": ["""
                                () => {
                                    // Scroll to bottom to ensure all elements are loaded
                                    window.scrollTo(0, document.body.scrollHeight);
                                    return true;
                                }
                            """]
                        },
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [2000]  # Wait after scrolling
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
                                        '[data-id]', '.btn-server', '.server-btn',
                                        '[onclick*="server"]', '[onclick*="load"]',
                                        '.episode-server-item', '.server-list a',
                                        'button[onclick]', 'a[onclick]'
                                    ];
                                    
                                    let clicked = 0;
                                    selectors.forEach(selector => {
                                        const elements = Array.from(document.querySelectorAll(selector));
                                        elements.forEach((el, index) => {
                                            if (clicked < 20 && el.offsetParent !== null) { // Increased to 20, only visible elements
                                                try { 
                                                    el.scrollIntoView({behavior: 'auto', block: 'center'});
                                                    el.click();
                                                    clicked++;
                                                } catch(e) {
                                                    console.warn('Error clicking:', e);
                                                }
                                            }
                                        });
                                    });
                                    return clicked;
                                }
                            """]
                        },
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [8000]  # Increased to 8 seconds for video players to load after clicking
                        },
                        {
                            "coroutine": "evaluate",
                            "args": ["""
                                () => {
                                    // Scroll again to trigger lazy loading
                                    window.scrollTo(0, document.body.scrollHeight);
                                    return true;
                                }
                            """]
                        },
                        {
                            "coroutine": "wait_for_timeout",
                            "args": [3000]  # Final wait
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
        # Skip if already processed (but allow re-processing for link updates)
        movie_slug = response.url.rstrip("/").split("/")[-1]
        # Don't skip - allow re-processing to update links
        # if movie_slug in self.seen_movies:
        #     return
        
        self.logger.info(f"Parsing movie page: {response.url}")
        
        item = StreamingItem()

        # Store the original detail URL for on-demand scraping
        item["original_detail_url"] = response.url

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

        # Determine type from URL - check more patterns
        url_lower = response.url.lower()
        if "/tv/" in url_lower or "/tv-show/" in url_lower or "/series/" in url_lower or "/show/" in url_lower:
            item["type"] = "show"
            self.logger.info(f"Detected TV Show: {title}")
        else:
            item["type"] = "movie"
            self.logger.info(f"Detected Movie: {title}")

        # Poster from og:image or first image
        poster = response.css("meta[property='og:image']::attr(content)").get()
        if not poster:
            poster = response.css("img::attr(src)").get()
        item["poster_url"] = poster

        # Synopsis from meta description or first paragraph
        synopsis = response.css("meta[name='description']::attr(content)").get()
        if not synopsis:
            synopsis = response.css("p::text").get()
        item["synopsis"] = synopsis or ""
        
        # Filter out unwanted content - check title and synopsis
        title_lower = title.lower()
        synopsis_lower = (synopsis or "").lower()
        combined_text = f"{title_lower} {synopsis_lower}"
        
        # Skip unwanted content types - be less aggressive, only filter obvious non-content
        skip_keywords = [
            # Only filter obvious non-movie/TV content
            "podcast", "audio book", "audiobook",
            # Only filter if title starts with these (not if they appear anywhere)
            # "news", "sports" - removed, too aggressive
        ]
        
        # Check if title starts with skip keywords (less aggressive)
        should_skip = False
        title_lower_stripped = title_lower.strip()
        for keyword in skip_keywords:
            if title_lower_stripped.startswith(keyword) or f" {keyword} " in f" {title_lower_stripped} ":
                self.logger.info(f"Skipping {title}: starts with '{keyword}'")
                should_skip = True
                break
        
        # Additional check: Skip if title contains non-English characters (Chinese, Arabic, etc.)
        # Check for Chinese characters, Arabic script, etc.
        non_english_patterns = [
            r'[\u4e00-\u9fff]',  # Chinese characters
            r'[\u0600-\u06ff]',  # Arabic
            r'[\u0400-\u04ff]',  # Cyrillic
            r'[\u3040-\u309f]',  # Hiragana
            r'[\u30a0-\u30ff]',  # Katakana
            r'[\u0e00-\u0e7f]',  # Thai
            r'[\u1100-\u11ff]',  # Hangul
        ]
        
        for pattern in non_english_patterns:
            if re.search(pattern, title):
                self.logger.info(f"Skipping {title}: contains non-English characters")
                should_skip = True
                break
        
        # Check language metadata - skip if not English
        page_lang = response.css("html::attr(lang)").get() or ""
        meta_lang = response.css("meta[property='og:locale']::attr(content)").get() or ""
        meta_lang_alt = response.css("meta[http-equiv='content-language']::attr(content)").get() or ""
        
        # If language is explicitly set and not English, skip
        all_langs = f"{page_lang} {meta_lang} {meta_lang_alt}".lower()
        if all_langs and not any(lang in all_langs for lang in ["en", "english"]):
            # Check if it's explicitly a non-English language
            non_english_langs = ["zh", "chinese", "hi", "hindi", "ja", "japanese", "ko", "korean", 
                               "ar", "arabic", "es", "spanish", "fr", "french", "de", "german",
                               "it", "italian", "pt", "portuguese", "ru", "russian", "th", "thai"]
            if any(lang in all_langs for lang in non_english_langs):
                self.logger.info(f"Skipping {title}: non-English language detected ({all_langs})")
                return
        
        if should_skip:
            return  # Skip this item

        # Extract iframe sources from the detail page using Playwright page evaluation
        # This ensures we get links after JavaScript has rendered and server buttons are clicked
        detail_page_links = []
        page = response.meta.get("playwright_page")
        
        if page:
            try:
                # Use Playwright to extract all possible video hosting URLs from the rendered page
                extracted_urls = page.evaluate("""
                    () => {
                        const sources = [];
                        const videoHosts = ["vidoza", "streamtape", "mixdrop", "dood", "filemoon", "upstream", "streamlare", "streamhub", "streamwish", "videostr"];
                        
                        // Extract from all iframes
                        const iframes = Array.from(document.querySelectorAll('iframe'));
                        iframes.forEach(iframe => {
                            const src = iframe.src || iframe.getAttribute('data-src') || iframe.getAttribute('data-url') || iframe.getAttribute('src') || '';
                            if (src && src.startsWith('http') && !src.includes('recaptcha') && !src.includes('google.com') && !src.includes('youtube.com') && !src.includes('1flix.to')) {
                                sources.push(src);
                            }
                        });
                        
                        // Extract from data attributes on server buttons/links
                        const serverElements = Array.from(document.querySelectorAll('[data-link], [data-server], [data-embed], [data-player], [data-url], [data-video], [data-stream], [data-src]'));
                        serverElements.forEach(el => {
                            const link = el.getAttribute('data-link') || 
                                        el.getAttribute('data-server') || 
                                        el.getAttribute('data-embed') || 
                                        el.getAttribute('data-player') ||
                                        el.getAttribute('data-url') ||
                                        el.getAttribute('data-video') ||
                                        el.getAttribute('data-stream') ||
                                        el.getAttribute('data-src');
                            if (link && link.startsWith('http') && !link.includes('recaptcha') && !link.includes('google.com') && !link.includes('youtube.com') && !link.includes('1flix.to')) {
                                sources.push(link);
                            }
                        });
                        
                        // Extract from href attributes that contain video hosting service names
                        const hrefLinks = Array.from(document.querySelectorAll('a[href]'));
                        hrefLinks.forEach(el => {
                            const href = el.href || el.getAttribute('href');
                            if (href && href.startsWith('http') && videoHosts.some(host => href.toLowerCase().includes(host)) && !href.includes('recaptcha') && !href.includes('google.com') && !href.includes('youtube.com') && !href.includes('1flix.to')) {
                                sources.push(href);
                            }
                        });
                        
                        // Extract from onclick handlers
                        const onclickElements = Array.from(document.querySelectorAll('[onclick]'));
                        onclickElements.forEach(el => {
                            const onclick = el.getAttribute('onclick') || '';
                            const urlMatch = onclick.match(/['"](https?:\/\/[^'"]+)['"]/);
                            if (urlMatch && urlMatch[1] && videoHosts.some(host => urlMatch[1].toLowerCase().includes(host)) && !urlMatch[1].includes('recaptcha') && !urlMatch[1].includes('google.com') && !urlMatch[1].includes('youtube.com') && !urlMatch[1].includes('1flix.to')) {
                                sources.push(urlMatch[1]);
                            }
                        });
                        
                        // Extract from JavaScript code in script tags
                        const scripts = Array.from(document.querySelectorAll('script'));
                        scripts.forEach(script => {
                            const text = script.textContent || '';
                            // Look for video hosting URLs in JavaScript
                            const urlPattern = /['"](https?:\/\/[^'"]*(?:vidoza|streamtape|mixdrop|dood|filemoon|upstream|streamlare|streamhub|streamwish|videostr)[^'"]*)['"]/gi;
                            const matches = text.matchAll(urlPattern);
                            for (const match of matches) {
                                if (match[1] && !match[1].includes('recaptcha') && !match[1].includes('google.com') && !match[1].includes('youtube.com') && !match[1].includes('1flix.to')) {
                                    sources.push(match[1]);
                                }
                            }
                        });
                        
                        // Also check for video elements
                        const videos = Array.from(document.querySelectorAll('video source, video'));
                        videos.forEach(video => {
                            const src = video.src || video.getAttribute('src');
                            if (src && src.startsWith('http')) {
                                sources.push(src);
                            }
                        });
                        
                        return [...new Set(sources)]; // Remove duplicates
                    }
                """)
                
                if extracted_urls:
                    detail_page_links.extend(extracted_urls)
                    self.logger.info(f"Extracted {len(extracted_urls)} URLs from Playwright page evaluation")
            except Exception as e:
                self.logger.warning(f"Error extracting URLs from Playwright page: {e}")
        
        # Also extract from static HTML as fallback
        iframe_sources = response.css("iframe::attr(src)").getall()
        iframe_sources += response.css("iframe::attr(data-src)").getall()
        iframe_sources += response.css("iframe::attr(data-url)").getall()
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
        
        self.logger.info(f"Extracted {len(detail_page_links)} total video hosting URLs from detail page")

        # After page parse, attempt AJAX endpoint to fetch actual stream servers.
        # Try multiple methods to extract movie_id
        movie_id = None
        slug = item["imdb_id"]
        
        # Method 1: Extract from slug (e.g., "watch-12345-title" -> "12345")
        for part in slug.split("-"):
            if part.isdigit() and len(part) >= 4:  # At least 4 digits
                movie_id = part
                break
        
        # Method 2: Extract from URL directly
        if not movie_id:
            url_id_match = re.search(r'/(\d{4,})', response.url)
            if url_id_match:
                movie_id = url_id_match.group(1)
        
        # Method 3: Extract from page content (data attributes, IDs, etc.)
        if not movie_id:
            page = response.meta.get("playwright_page")
            if page:
                try:
                    extracted_id = page.evaluate("""
                        () => {
                            // Try to find movie ID in various data attributes
                            const idSelectors = [
                                '[data-id]', '[data-movie-id]', '[data-film-id]',
                                '[id*="movie"]', '[id*="film"]', '[class*="movie-id"]'
                            ];
                            for (const selector of idSelectors) {
                                const el = document.querySelector(selector);
                                if (el) {
                                    const id = el.getAttribute('data-id') || 
                                              el.getAttribute('data-movie-id') ||
                                              el.getAttribute('data-film-id') ||
                                              el.id;
                                    if (id && /^\d{4,}$/.test(id)) {
                                        return id;
                                    }
                                }
                            }
                            return null;
                        }
                    """)
                    if extracted_id:
                        movie_id = extracted_id
                except:
                    pass
        
        self.logger.info(f"Extracted movie_id: {movie_id} for {item.get('title', 'Unknown')}")

        # For TV shows, try to find and follow episode links first
        is_tv_show = item.get("type") == "show"
        episode_links = []
        
        if is_tv_show:
            # Extract episode links from the page
            page = response.meta.get("playwright_page")
            if page:
                try:
                    episode_urls = page.evaluate("""
                        () => {
                            const episodeLinks = [];
                            // Look for episode links - common patterns
                            const selectors = [
                                'a[href*="/episode/"]',
                                'a[href*="/ep/"]',
                                'a[href*="/watch/"]',
                                '.episode-item a',
                                '.episode-list a',
                                '[data-episode] a',
                                '.season-episode-list a'
                            ];
                            selectors.forEach(selector => {
                                const elements = Array.from(document.querySelectorAll(selector));
                                elements.forEach(el => {
                                    const href = el.href || el.getAttribute('href');
                                    if (href && href.includes('1flix.to') && (href.includes('/episode/') || href.includes('/ep/') || href.includes('/watch/'))) {
                                        episodeLinks.push(href);
                                    }
                                });
                            });
                            return [...new Set(episodeLinks)].slice(0, 5); // Get first 5 episodes
                        }
                    """)
                    if episode_urls:
                        episode_links = episode_urls
                        self.logger.info(f"Found {len(episode_links)} episode links for TV show: {item.get('title', 'Unknown')}")
                except Exception as e:
                    self.logger.warning(f"Error extracting episode links: {e}")
            
            # Also check static HTML for episode links
            episode_selectors = [
                'a[href*="/episode/"]::attr(href)',
                'a[href*="/ep/"]::attr(href)',
                '.episode-item a::attr(href)',
                '.episode-list a::attr(href)',
            ]
            for selector in episode_selectors:
                episode_links.extend(response.css(selector).getall())
            
            # Follow first episode link to get streaming links (episodes usually have the same servers)
            if episode_links:
                first_episode = episode_links[0]
                if first_episode.startswith('/'):
                    first_episode = f"https://1flix.to{first_episode}"
                elif not first_episode.startswith('http'):
                    first_episode = f"https://1flix.to/{first_episode}"
                
                self.logger.info(f"Following first episode link for TV show: {first_episode}")
                yield Request(
                    first_episode,
                    callback=self.parse_movie_page,  # Reuse same parser
                    meta={
                        "playwright": True,
                        "playwright_page_goto_kwargs": {"wait_until": "networkidle", "timeout": 30000},
                        "playwright_page_coroutines": [
                            {"coroutine": "wait_for_timeout", "args": [5000]},
                            {
                                "coroutine": "evaluate",
                                "args": ["""
                                    () => {
                                        window.scrollTo(0, document.body.scrollHeight);
                                        const selectors = ['a[data-link]', 'button[data-link]', 'a[data-server]', 'button[data-server]', '.server-item a', '.server-btn', '[class*="server"] a', '[class*="server"] button', '[data-id]', '.btn-server', '.episode-server-item', '.server-list a', '[onclick*="server"]', '[onclick*="load"]'];
                                        let clicked = 0;
                                        selectors.forEach(selector => {
                                            const elements = Array.from(document.querySelectorAll(selector));
                                            elements.forEach((el) => {
                                                if (clicked < 30 && el.offsetParent !== null) {
                                                    try { el.scrollIntoView({behavior: 'auto', block: 'center'}); el.click(); clicked++; } catch(e) {}
                                                }
                                            });
                                        });
                                        return clicked;
                                    }
                                """]
                            },
                            {"coroutine": "wait_for_timeout", "args": [10000]},
                        ],
                    },
                    dont_filter=True,
                )
                # Don't return yet - continue to extract links from main page too
        
        # Always filter detail page links first
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
        
        # If we found links from detail page, use them
        if filtered_links:
            item["links"] = [
                {
                    "quality": "HD",
                    "language": "EN",
                    "source_url": link,
                    "is_active": True,
                }
                for link in filtered_links[:5]
            ]
            self.logger.info(f"Found {len(filtered_links)} links from detail page for {item.get('title', 'Unknown')}")
            
            # If we have movie_id, also try AJAX to get MORE links (will merge in parse_ajax_links)
            if movie_id:
                yield Request(
                    f"https://1flix.to/ajax/episode/list/{movie_id}",
                    callback=self.parse_ajax_links,
                    meta={
                        "item": item,
                        "original_url": response.url,
                        "detail_page_links": filtered_links,  # Pass existing links to merge
                        "playwright": True,
                        "playwright_page_goto_kwargs": {"wait_until": "networkidle", "timeout": 30000},
                        "playwright_page_coroutines": [
                            {"coroutine": "wait_for_timeout", "args": [3000]},
                            {
                                "coroutine": "evaluate",
                                "args": ["""
                                    () => {
                                        const selectors = ['a[data-link]', 'button[data-link]', 'a[data-server]', 'button[data-server]', '.server-item a', '.server-btn', '[class*="server"] a', '[class*="server"] button', '[data-id]', '.btn-server', '.episode-server-item', '.server-list a', '[onclick*="server"]', '[onclick*="load"]'];
                                        let clicked = 0;
                                        selectors.forEach(selector => {
                                            const elements = Array.from(document.querySelectorAll(selector));
                                            elements.forEach((el) => {
                                                if (clicked < 20 && el.offsetParent !== null) {
                                                    try { el.scrollIntoView({behavior: 'auto', block: 'center'}); el.click(); clicked++; } catch(e) {}
                                                }
                                            });
                                        });
                                        return clicked;
                                    }
                                """]
                            },
                            {"coroutine": "wait_for_timeout", "args": [8000]},
                        ],
                    },
                    dont_filter=True,
                )
            else:
                # No movie_id but we have links, save immediately
                yield item
        elif movie_id:
            # No detail page links but we have movie_id, try AJAX
            yield Request(
                f"https://1flix.to/ajax/episode/list/{movie_id}",
                callback=self.parse_ajax_links,
                meta={
                    "item": item,
                    "original_url": response.url,
                    "detail_page_links": [],
                    "playwright": True,
                    "playwright_page_goto_kwargs": {"wait_until": "networkidle", "timeout": 30000},
                    "playwright_page_coroutines": [
                        {"coroutine": "wait_for_timeout", "args": [3000]},
                        {
                            "coroutine": "evaluate",
                            "args": ["""
                                () => {
                                    const selectors = ['a[data-link]', 'button[data-link]', 'a[data-server]', 'button[data-server]', '.server-item a', '.server-btn', '[class*="server"] a', '[class*="server"] button', '[data-id]', '.btn-server', '.episode-server-item', '.server-list a', '[onclick*="server"]', '[onclick*="load"]'];
                                    let clicked = 0;
                                    selectors.forEach(selector => {
                                        const elements = Array.from(document.querySelectorAll(selector));
                                        elements.forEach((el) => {
                                            if (clicked < 20 && el.offsetParent !== null) {
                                                try { el.scrollIntoView({behavior: 'auto', block: 'center'}); el.click(); clicked++; } catch(e) {}
                                            }
                                        });
                                    });
                                    return clicked;
                                }
                            """]
                        },
                        {"coroutine": "wait_for_timeout", "args": [8000]},
                    ],
                },
                dont_filter=True,
            )
        else:
            # No movie_id and no links - save without links
            self.logger.warning(f"No movie_id and no links found for {item.get('title', 'Unknown')} - saving without links")
            item["links"] = []
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

        # Merge AJAX links with detail page links (avoid duplicates)
        detail_page_links = response.meta.get("detail_page_links", [])
        all_links = links.copy() if links else []
        
        # Add detail page links that aren't already in links
        existing_urls = {link.get("source_url") for link in all_links}
        for detail_link in detail_page_links:
            if detail_link not in existing_urls:
                all_links.append({
                    "quality": "HD",
                    "language": "EN",
                    "source_url": detail_link,
                    "is_active": True,
                })
        
        # Save item with all links found
        if all_links:
            item["links"] = all_links
            self.logger.info(f"Found {len(all_links)} total stream links for {item.get('title', 'Unknown')} ({len(links)} from AJAX, {len(detail_page_links)} from detail page)")
        else:
            # Save movie without links - they can be updated later
            item["links"] = []
            self.logger.warning(f"No valid stream links found for {item.get('title', 'Unknown')} - saving without links")
        
        yield item

