# File: scraper/scraper/spiders/diagnostic_spider.py
# NEW FILE - Create this alongside example_spider.py for debugging

import scrapy
from scrapy import Request
from scrapy.http import TextResponse
import logging
import json

logger = logging.getLogger(__name__)


class DiagnosticSpider(scrapy.Spider):
    """
    Diagnostic spider to understand what's happening on 1flix.to pages
    """
    
    name = "diagnostic"
    allowed_domains = ["1flix.to"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_url = kwargs.get('target_url', 'https://1flix.to/movie/watch-venom-the-last-dance-140207')
    
    def start_requests(self):
        logger.info(f"🔍 DIAGNOSTIC MODE: Testing {self.target_url}")
        
        yield Request(
            self.target_url,
            callback=self.parse_diagnostic,
            meta={
                "playwright": True,
                "playwright_page_goto_kwargs": {
                    "wait_until": "networkidle",
                    "timeout": 60000
                },
                "playwright_page_coroutines": [
                    # Wait for page to load
                    {"coroutine": "wait_for_timeout", "args": [3000]},
                    
                    # Take screenshot BEFORE clicking
                    {"coroutine": "screenshot", "args": [{"path": "before_click.png", "full_page": True}]},
                    
                    # Log all clickable elements
                    {
                        "coroutine": "evaluate",
                        "args": ["""
                            () => {
                                const serverSelectors = [
                                    'a[data-link]', 'button[data-link]',
                                    'a[data-server]', 'button[data-server]',
                                    '.server-item', '.server-btn',
                                    'button[onclick]', 'a[onclick]',
                                ];
                                
                                let found = [];
                                serverSelectors.forEach(selector => {
                                    const elements = document.querySelectorAll(selector);
                                    if (elements.length > 0) {
                                        found.push({
                                            selector: selector,
                                            count: elements.length,
                                            examples: Array.from(elements).slice(0, 3).map(el => ({
                                                tag: el.tagName,
                                                text: el.textContent?.trim().slice(0, 50),
                                                visible: el.offsetParent !== null,
                                                href: el.getAttribute('href'),
                                                dataLink: el.getAttribute('data-link'),
                                                dataServer: el.getAttribute('data-server'),
                                                onclick: el.getAttribute('onclick')?.slice(0, 100)
                                            }))
                                        });
                                    }
                                });
                                
                                console.log('FOUND SERVER ELEMENTS:', JSON.stringify(found, null, 2));
                                return found;
                            }
                        """]
                    },
                    
                    # Click ALL possible server elements
                    {
                        "coroutine": "evaluate",
                        "args": ["""
                            () => {
                                const selectors = [
                                    'a[data-link]', 'button[data-link]',
                                    'a[data-server]', 'button[data-server]',
                                    'a[data-embed]', 'button[data-embed]',
                                    '.server-item', '.server-btn', '.server',
                                    '[class*="server"]',
                                    'button[onclick]', 'a[onclick]',
                                ];
                                
                                let clicked = 0;
                                let details = [];
                                
                                for (let round = 0; round < 5; round++) {
                                    selectors.forEach(selector => {
                                        try {
                                            const elements = Array.from(document.querySelectorAll(selector));
                                            elements.forEach((el, idx) => {
                                                if (el.offsetParent !== null) {
                                                    try {
                                                        el.scrollIntoView({behavior: 'auto', block: 'center'});
                                                        el.click();
                                                        clicked++;
                                                        
                                                        if (round === 0 && idx < 3) {
                                                            details.push({
                                                                selector: selector,
                                                                text: el.textContent?.trim().slice(0, 30),
                                                                clicked: true
                                                            });
                                                        }
                                                    } catch(e) {
                                                        if (round === 0 && idx < 2) {
                                                            details.push({
                                                                selector: selector,
                                                                error: e.message
                                                            });
                                                        }
                                                    }
                                                }
                                            });
                                        } catch(e) {
                                            console.log('Selector error:', selector, e);
                                        }
                                    });
                                }
                                
                                console.log('CLICK RESULTS:', {total: clicked, details: details});
                                return {total: clicked, details: details};
                            }
                        """]
                    },
                    
                    # Wait for streams to load
                    {"coroutine": "wait_for_timeout", "args": [20000]},
                    
                    # Take screenshot AFTER clicking
                    {"coroutine": "screenshot", "args": [{"path": "after_click.png", "full_page": True}]},
                ]
            }
        )
    
    def parse_diagnostic(self, response: TextResponse):
        logger.info("="*80)
        logger.info("🔍 DIAGNOSTIC REPORT")
        logger.info("="*80)
        
        # 1. Check what Playwright found
        page = response.meta.get("playwright_page")
        if page:
            try:
                # Get all iframes
                iframes = page.evaluate("""
                    () => {
                        const iframes = Array.from(document.querySelectorAll('iframe'));
                        return iframes.map(iframe => ({
                            src: iframe.src,
                            dataSrc: iframe.getAttribute('data-src'),
                            id: iframe.id,
                            class: iframe.className,
                            visible: iframe.offsetParent !== null
                        }));
                    }
                """)
                logger.info(f"\n📺 FOUND {len(iframes)} IFRAMES:")
                for i, iframe in enumerate(iframes, 1):
                    logger.info(f"   {i}. Src: {iframe.get('src', 'NO SRC')[:100]}")
                    logger.info(f"      Data-src: {iframe.get('dataSrc', 'NONE')[:100]}")
                    logger.info(f"      Visible: {iframe.get('visible')}")
                
                # Get all data-link attributes
                data_links = page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('[data-link], [data-server], [data-embed]');
                        return Array.from(elements).map(el => ({
                            tag: el.tagName,
                            text: el.textContent?.trim().slice(0, 30),
                            dataLink: el.getAttribute('data-link'),
                            dataServer: el.getAttribute('data-server'),
                            dataEmbed: el.getAttribute('data-embed'),
                            visible: el.offsetParent !== null
                        }));
                    }
                """)
                logger.info(f"\n🔗 FOUND {len(data_links)} DATA-LINK ELEMENTS:")
                for i, link in enumerate(data_links[:10], 1):  # Show first 10
                    logger.info(f"   {i}. {link}")
                
                # Get all links from page
                all_links = page.evaluate("""
                    () => {
                        const links = Array.from(document.querySelectorAll('a[href]'));
                        return links
                            .map(a => a.href)
                            .filter(href => href && href.startsWith('http'));
                    }
                """)
                logger.info(f"\n🌐 FOUND {len(all_links)} TOTAL LINKS")
                
                # Categorize links
                youtube_links = [l for l in all_links if 'youtube' in l.lower() or 'youtu.be' in l.lower()]
                video_host_links = []
                other_links = []
                
                VIDEO_HOSTS = [
                    'vidoza', 'streamtape', 'mixdrop', 'doodstream', 'dood',
                    'filemoon', 'upstream', 'streamlare', 'voe', 'supervideo'
                ]
                
                for link in all_links:
                    link_lower = link.lower()
                    if any(host in link_lower for host in VIDEO_HOSTS):
                        video_host_links.append(link)
                    elif 'youtube' not in link_lower and 'youtu.be' not in link_lower:
                        other_links.append(link)
                
                logger.info(f"\n📊 LINK BREAKDOWN:")
                logger.info(f"   ❌ YouTube: {len(youtube_links)}")
                logger.info(f"   ✅ Video Hosts: {len(video_host_links)}")
                logger.info(f"   ❓ Other: {len(other_links)}")
                
                if video_host_links:
                    logger.info(f"\n✅ FOUND {len(video_host_links)} VIDEO HOST LINKS:")
                    for i, link in enumerate(video_host_links[:5], 1):
                        logger.info(f"   {i}. {link}")
                else:
                    logger.info("\n⚠️ NO VIDEO HOST LINKS FOUND!")
                    logger.info("\n📋 SAMPLE OTHER LINKS (first 10):")
                    for i, link in enumerate(other_links[:10], 1):
                        logger.info(f"   {i}. {link[:100]}")
                
            except Exception as e:
                logger.error(f"❌ Playwright evaluation error: {e}")
        
        # 2. Check static HTML
        logger.info("\n"+ "="*80)
        logger.info("📄 STATIC HTML ANALYSIS")
        logger.info("="*80)
        
        # Find all server-related elements in HTML
        server_elements = response.css('[data-link], [data-server], [data-embed], .server-item, .server-btn, [class*="server"]')
        logger.info(f"\n🎯 Found {len(server_elements)} server elements in HTML")
        
        for i, elem in enumerate(server_elements[:5], 1):
            logger.info(f"\n   Element {i}:")
            logger.info(f"      Tag: {elem.root.tag}")
            logger.info(f"      Classes: {elem.attrib.get('class', 'NONE')}")
            logger.info(f"      data-link: {elem.attrib.get('data-link', 'NONE')}")
            logger.info(f"      data-server: {elem.attrib.get('data-server', 'NONE')}")
            logger.info(f"      Text: {elem.css('::text').get('')[:50]}")
        
        # Find all iframes in HTML
        iframes_html = response.css('iframe')
        logger.info(f"\n📺 Found {len(iframes_html)} iframes in static HTML")
        for i, iframe in enumerate(iframes_html[:3], 1):
            logger.info(f"   {i}. src={iframe.attrib.get('src', 'NONE')[:100]}")
        
        logger.info("\n" + "="*80)
        logger.info("📸 Screenshots saved:")
        logger.info("   - before_click.png")
        logger.info("   - after_click.png")
        logger.info("="*80)
        
        # Don't yield any items - this is just diagnostics
        return None