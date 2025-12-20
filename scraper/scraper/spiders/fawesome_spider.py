import re
import logging
from typing import Optional

import scrapy
from scrapy import Request
from scrapy.http import TextResponse

try:
    from fake_useragent import UserAgent
except Exception:
    UserAgent = None

from scraper.items import StreamingItem

logger = logging.getLogger(__name__)


class FawesomeSpider(scrapy.Spider):
    name = "fawesome"
    allowed_domains = ["fawesome.tv"]

    sitemap_url = "https://fawesome.tv/sitemaps/movies-pages.xml"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.movie_pk = kwargs.get("movie_pk")
        self.imdb_id = kwargs.get("imdb_id")
        self.title = (kwargs.get("title") or "").strip()
        self.year = kwargs.get("year")
        self.max_pages = kwargs.get("max_pages")

        try:
            self.max_pages = int(self.max_pages) if self.max_pages is not None else 50
        except Exception:
            self.max_pages = 50

        self._seen = 0

        if isinstance(self.year, str) and self.year.isdigit():
            self.year = int(self.year)

        self.on_demand_mode = bool(self.imdb_id or self.title)

    def start_requests(self):
        ua = UserAgent().random if UserAgent else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        yield Request(
            self.sitemap_url,
            headers=headers,
            callback=self.parse_sitemap,
            dont_filter=True,
        )

    def parse_sitemap(self, response: TextResponse):
        # Full discovery crawl
        if not self.on_demand_mode:
            url_nodes = response.xpath("//*[local-name()='url']")
            logger.info(f"📄 FAWESOME sitemap urls found: {len(url_nodes)}")
            for url_node in url_nodes:
                if self._seen >= self.max_pages:
                    break
                loc = url_node.xpath("./*[local-name()='loc']/text()").get()
                if not loc:
                    continue
                self._seen += 1
                yield Request(
                    loc,
                    callback=self.parse_movie_page,
                    meta=self._get_playwright_meta(),
                )
            return

        # On-demand mode: match one page by title
        wanted = self._normalize_title(self.title)
        best_url: Optional[str] = None
        best_score = -1

        for url_node in response.xpath("//*[local-name()='url']"):
            loc = url_node.xpath("./*[local-name()='loc']/text()").get()
            if not loc:
                continue

            video_title = url_node.xpath(".//*[local-name()='video']/*[local-name()='title']/text()").get() or ""
            video_title_norm = self._normalize_title(video_title)

            score = self._match_score(wanted, video_title_norm)
            if score <= 0:
                continue

            # Prefer URLs that include the year when we have one
            if self.year and str(self.year) in (loc or ""):
                score += 2

            if score > best_score:
                best_score = score
                best_url = loc

            if best_score >= 10:
                break

        if not best_url:
            logger.warning(f"⚠️ FAWESOME: no match for title='{self.title}' year='{self.year}'")
            return

        logger.info(f"🎯 FAWESOME matched: {best_url} (score={best_score})")
        yield Request(
            best_url,
            callback=self.parse_movie_page,
            meta=self._get_playwright_meta(),
            dont_filter=True,
        )

    def _get_playwright_meta(self):
        return {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_goto_kwargs": {
                "wait_until": "domcontentloaded",
                "timeout": 60000,
            },
        }

    async def parse_movie_page(self, response: TextResponse):
        page = response.meta.get("playwright_page")

        item = StreamingItem()
        item["movie_pk"] = self.movie_pk
        extracted_tt = self._extract_imdb_tt(response)
        item_imdb = extracted_tt or self.imdb_id or ""
        if (not item_imdb) and (not self.on_demand_mode):
            # Discovery mode fallback: use fawesome numeric id to create a stable unique identifier
            # Example: https://fawesome.tv/movies/10589474/el-dorado -> fw10589474
            m = re.search(r"/movies/(\d+)", response.url)
            if m:
                item_imdb = f"fw{m.group(1)}"
        item["imdb_id"] = item_imdb

        if not item_imdb:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            return

        title_from_page = (
            response.css("h1::text").get()
            or response.css("meta[property='og:title']::attr(content)").get()
            or ""
        ).strip()
        item["title"] = self.title or title_from_page

        item["year"] = self.year
        if item["year"] is None:
            # best-effort year extraction
            m = re.search(r"\b(19\d{2}|20\d{2})\b", response.text or "")
            if m:
                try:
                    item["year"] = int(m.group(1))
                except Exception:
                    item["year"] = None
        item["type"] = "movie"
        item["poster_url"] = response.css("meta[property='og:image']::attr(content)").get()
        item["synopsis"] = response.css("meta[name='description']::attr(content)").get()
        item["original_detail_url"] = response.url

        links = []
        urls = set()

        try:
            if page:
                await page.wait_for_timeout(4000)
                # Try clicking the player if a play button exists
                try:
                    await page.click("text=Play", timeout=1500)
                except Exception:
                    pass

                await page.wait_for_timeout(4000)

                # Collect URLs from resource timing + DOM
                extracted = await page.evaluate(
                    """
                    () => {
                      const out = new Set();

                      // Resources
                      try {
                        performance.getEntriesByType('resource').forEach(r => {
                          if (r && r.name) out.add(r.name);
                        });
                      } catch (e) {}

                      // Video tags
                      document.querySelectorAll('video, source').forEach(el => {
                        const src = el.src || el.getAttribute('src');
                        if (src) out.add(src);
                      });

                      // Iframes
                      document.querySelectorAll('iframe').forEach(el => {
                        const src = el.src || el.getAttribute('src');
                        if (src) out.add(src);
                      });

                      // Scan scripts for video-ish urls
                      const text = document.documentElement.innerText || '';
                      const html = document.documentElement.outerHTML || '';
                      const combined = text + '\n' + html;
                      const re = /(https?:\\/\\/[^\\s"'<>]+?\.(?:m3u8|mp4|mpd))(?:\\?[^\\s"'<>]*)?/gi;
                      let m;
                      while ((m = re.exec(combined)) !== null) {
                        out.add(m[0]);
                      }

                      return Array.from(out);
                    }
                    """
                )

                for u in extracted or []:
                    if isinstance(u, str) and u.startswith(("http://", "https://")):
                        urls.add(u)
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

        # Filter to likely playable assets
        for u in sorted(urls):
            ul = u.lower()
            if any(x in ul for x in ["youtube.com", "youtu.be", "facebook.com", "instagram.com", "twitter.com"]):
                continue
            is_direct = any(ext in ul for ext in [".m3u8", ".mp4", ".mpd"])
            is_embed_like = any(k in ul for k in ["embed", "player", "/e/", "/v/"])
            if not (is_direct or is_embed_like):
                continue
            links.append({
                "quality": "HD",
                "language": "EN",
                "source_url": u,
                "is_active": True,
            })

        item["links"] = links

        if not links:
            logger.warning(f"⚠️ FAWESOME: no stream URLs extracted for {response.url}")
        else:
            logger.info(f"✅ FAWESOME: extracted {len(links)} stream URLs")

        yield item

    def _extract_imdb_tt(self, response: TextResponse) -> Optional[str]:
        text = response.text or ""
        m = re.search(r"imdb\.com/title/(tt\d{7,8})", text, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"\b(tt\d{7,8})\b", text)
        if m:
            return m.group(1)
        return None

    def _normalize_title(self, s: str) -> str:
        s = (s or "").lower()
        s = re.sub(r"\(\d{4}\)", "", s)
        s = re.sub(r"[^a-z0-9]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    def _match_score(self, wanted: str, candidate: str) -> int:
        if not wanted or not candidate:
            return 0
        if wanted == candidate:
            return 10
        if wanted in candidate or candidate in wanted:
            return 6
        wanted_tokens = set(wanted.split())
        cand_tokens = set(candidate.split())
        overlap = len(wanted_tokens & cand_tokens)
        if overlap == 0:
            return 0
        return min(5, overlap)
