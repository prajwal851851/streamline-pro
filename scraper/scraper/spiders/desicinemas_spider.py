# scraper/spiders/desicinemas_spider.py
"""
Spider for DesiCinemas.to - Bollywood and Indian Movies
Supports multiple streaming servers with smart scraping
"""
import scrapy
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from scraper.items import StreamingItem
import time
import re
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieBackends.settings')
django.setup()

from streaming.models import Movie, StreamingLink

class DesiCinemasSpider(scrapy.Spider):
    name = 'desicinemas'
    allowed_domains = ['desicinemas.to']
    
    # Start URLs - Different categories
    start_urls = [
        'https://desicinemas.to/category/bollywood/',
        'https://desicinemas.to/category/hollywood/',
        'https://desicinemas.to/category/south-indian/',
        'https://desicinemas.to/category/web-series/',
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """Setup Selenium WebDriver"""
        self.logger.info('Initializing Selenium WebDriver...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info('✓ Selenium WebDriver initialized')
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def __init__(self, limit=200, start_page=1, end_page=None, max_pages=5, 
                 rescrape_broken=True, category='all', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.start_page = int(start_page)
        self.end_page = int(end_page) if end_page else None
        self.max_pages = int(max_pages)
        self.rescrape_broken = rescrape_broken
        self.category = category.lower()
        self.count = 0
        self.seen_urls = set()
        self.pages_scraped = {}
        
        # Filter start URLs based on category
        if self.category != 'all':
            self.start_urls = [url for url in self.start_urls if self.category in url.lower()]
            if not self.start_urls:
                self.logger.warning(f'No URLs found for category: {self.category}')
                self.start_urls = ['https://desicinemas.to/category/bollywood/']
        
        # Calculate effective max_pages if end_page is specified
        if self.end_page:
            self.max_pages = self.end_page - self.start_page + 1
            self.logger.info(f'Page range: {self.start_page} to {self.end_page} ({self.max_pages} pages)')
        else:
            self.logger.info(f'Starting from page {self.start_page}, scraping {self.max_pages} pages')
        
        # Load existing movies from database
        self.existing_movie_urls = set()
        self.broken_link_movies = set()
        self._load_existing_movies()

    def _load_existing_movies(self):
        """Load existing movies from database to optimize scraping"""
        try:
            existing_movies = Movie.objects.filter(
                source_site='desicinemas.to'
            ).values_list('source_url', flat=True)
            
            for url in existing_movies:
                if url:
                    self.existing_movie_urls.add(url)
            
            # Get movies with broken links
            if self.rescrape_broken:
                broken_links = StreamingLink.objects.filter(
                    is_active=False,
                    movie__source_site='desicinemas.to'
                ).values_list('movie__source_url', flat=True).distinct()
                
                for url in broken_links:
                    if url:
                        self.broken_link_movies.add(url)
            
            self.logger.info(f'Loaded {len(self.existing_movie_urls)} existing movies')
            self.logger.info(f'Found {len(self.broken_link_movies)} movies with broken links to re-scrape')
            
        except Exception as e:
            self.logger.warning(f'Could not load existing movies: {e}')

    def parse(self, response):
        """Parse category listing page"""
        self.logger.info(f'Parsing category: {response.url}')
        
        try:
            # Determine current page from URL or start from start_page
            base_url = response.url.split('/page/')[0].rstrip('/')
            
            if base_url not in self.pages_scraped:
                current_page = self.start_page
                self.pages_scraped[base_url] = current_page
            else:
                current_page = self.pages_scraped[base_url]
            
            # Build paginated URL
            if current_page == 1:
                page_url = f"{base_url}/"
            else:
                page_url = f"{base_url}/page/{current_page}/"
            
            self.logger.info(f'Loading page {current_page}: {page_url}')
            
            self.driver.get(page_url)
            time.sleep(3)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=page_url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Find movie links - DesiCinemas uses article cards with links
            # Actual structure: <article class="TPost C"><h2 class="Title"><a href="...">
            movie_links = sel_response.css('article.TPost h2.Title a::attr(href)').getall()
            
            # Alternative: Get all article links
            if not movie_links:
                movie_links = sel_response.css('article.TPost a.TPlay::attr(href)').getall()
            
            self.logger.info(f'Found {len(movie_links)} movie links on page {current_page}')
            
            movies_found = 0
            for link in movie_links:
                if self.count >= self.limit:
                    self.logger.info(f'Reached limit of {self.limit} movies')
                    return
                
                if not link:
                    continue
                
                full_url = response.urljoin(link)
                
                # Skip if already seen
                if full_url in self.seen_urls:
                    continue
                
                # Smart scraping
                if full_url in self.existing_movie_urls and full_url not in self.broken_link_movies:
                    self.logger.info(f'Skipping already scraped: {full_url}')
                    continue
                
                self.seen_urls.add(full_url)
                movies_found += 1
                self.count += 1
                
                if full_url in self.broken_link_movies:
                    self.logger.info(f'Re-scraping broken link movie {self.count}: {full_url}')
                else:
                    self.logger.info(f'Queuing movie {self.count}: {full_url}')
                
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_movie,
                    dont_filter=True
                )
            
            self.logger.info(f'Queued {movies_found} movies from page {current_page} (Total: {self.count}/{self.limit})')
            
            # Pagination
            if movies_found > 0 and self.count < self.limit:
                should_continue = current_page < (self.start_page + self.max_pages - 1)
                
                if self.end_page:
                    should_continue = should_continue and (current_page < self.end_page)
                
                if should_continue:
                    next_page = current_page + 1
                    self.pages_scraped[base_url] = next_page
                    self.logger.info(f'Moving to page {next_page}')
                    yield scrapy.Request(
                        url=response.url,  # Pass base URL, parse will handle pagination
                        callback=self.parse,
                        dont_filter=True
                    )
                else:
                    self.logger.info(f'Pagination complete for {base_url}')
            
        except Exception as e:
            self.logger.error(f'Error parsing category page: {e}')
            import traceback
            self.logger.error(traceback.format_exc())

    def parse_movie(self, response):
        """Parse individual movie page and extract streaming links"""
        self.logger.info(f'Parsing movie: {response.url}')
        
        try:
            self.driver.get(response.url)
            time.sleep(3)
            
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Extract movie info
            # Title is in h1.Title
            title = sel_response.css('h1.Title::text').get()
            if not title:
                title = sel_response.css('h1::text').get()
            
            title = title.strip() if title else 'Unknown'
            
            # Extract year from title or meta
            year = None
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                year = int(year_match.group(1))
                title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
            
            # Try to get year from meta
            if not year:
                year_text = sel_response.css('.year::text, .date::text').get()
                if year_text:
                    year_match = re.search(r'\d{4}', year_text)
                    if year_match:
                        year = int(year_match.group())
            
            # Synopsis - look in Description div or meta
            synopsis = sel_response.css('.Description p::text').get()
            if not synopsis:
                synopsis = sel_response.css('meta[property="og:description"]::attr(content)').get()
            if not synopsis:
                synopsis = sel_response.css('meta[name="description"]::attr(content)').get()
            synopsis = synopsis.strip() if synopsis else ''
            
            # Poster - look in TPMvCn or meta
            poster = sel_response.css('.TPMvCn img::attr(data-src)').get()
            if not poster:
                poster = sel_response.css('.TPMvCn img::attr(src)').get()
            if not poster:
                poster = sel_response.css('meta[property="og:image"]::attr(content)').get()
            poster_url = response.urljoin(poster) if poster else ''
            
            # Extract streaming links
            # DesiCinemas embeds streaming links in various ways
            streaming_links = []
            
            # Method 1: Look for iframes (most common)
            iframes = sel_response.css('iframe::attr(src)').getall()
            for iframe_src in iframes:
                if iframe_src and 'desicinemas' not in iframe_src.lower():
                    streaming_links.append({
                        'source_url': response.urljoin(iframe_src),
                        'quality': 'HD',
                        'language': 'Hindi',
                        'is_active': True
                    })
            
            # Method 2: Look for player links in article content
            player_links = sel_response.css('article a[href*="http"]::attr(href)').getall()
            for link in player_links:
                link_lower = link.lower()
                # Check if it's a known streaming domain
                if any(domain in link_lower for domain in ['streamtape', 'doodstream', 'dood', 'vidsrc', 'mixdrop', 'upstream', 'filemoon', 'streamwish']):
                    streaming_links.append({
                        'source_url': link,
                        'quality': 'HD',
                        'language': 'Hindi',
                        'is_active': True
                    })
            
            # Remove duplicates
            seen = set()
            unique_links = []
            for link in streaming_links:
                if link['source_url'] not in seen:
                    seen.add(link['source_url'])
                    unique_links.append(link)
            
            streaming_links = unique_links
            
            if not streaming_links:
                self.logger.warning(f'No streaming links found for: {title}')
                return
            
            # Generate unique ID
            movie_id = response.url.split('/')[-2] if response.url.endswith('/') else response.url.split('/')[-1]
            imdb_id = f'desicinemas_{movie_id}'
            
            # Yield items for each streaming link
            for stream_link in streaming_links:
                item = StreamingItem()
                item['original_detail_url'] = response.url
                item['imdb_id'] = imdb_id
                item['title'] = title
                item['year'] = year
                item['type'] = 'movie'
                item['synopsis'] = synopsis
                item['poster_url'] = poster_url
                item['links'] = [stream_link]  # StreamingItem expects a list of links
                
                self.logger.info(f'✓ {title} - {stream_link["quality"]}')
                yield item
                
        except Exception as e:
            self.logger.error(f'Error parsing movie page: {e}')
            import traceback
            self.logger.error(traceback.format_exc())