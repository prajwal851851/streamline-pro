import os
import sys
from pathlib import Path
import django

# Add Django project to sys.path so Scrapy can import settings and models.
SCRAPER_DIR = Path(__file__).resolve().parent.parent.parent
DJANGO_PROJECT_PATH = SCRAPER_DIR / "MovieBackend"
sys.path.append(str(DJANGO_PROJECT_PATH))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MovieBackends.settings")
django.setup()


BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# The target site blocks crawling via robots.txt; disable obedience for this spider.
ROBOTSTXT_OBEY = False

# Limit concurrency to avoid hammering target site and reduce timeouts.
CONCURRENT_REQUESTS = 2
DOWNLOAD_DELAY = 0.5

ITEM_PIPELINES = {
    "scraper.pipelines.DjangoWriterPipeline": 300,
}

# Simple user agent; customize for your target site if required.
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en",
    # Set a reasonable default UA; spider overrides per request if fake_useragent is present.
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
}

# Playwright (for JS-rendered pages)
# Requires `scrapy-playwright` to be installed in the venv.
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000
# Limit concurrency to reduce timeouts and avoid hitting anti-bot too hard.
PLAYWRIGHT_MAX_CONTEXTS = 1
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 2

