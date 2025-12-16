# File: scraper/find_real_movies.py
# NEW FILE - Run this to find real movie URLs

import asyncio
from playwright.async_api import async_playwright
import sys

async def find_movies():
    """Find real movie URLs from 1flix.to homepage"""
    
    print("🔍 Searching for real movie URLs on 1flix.to...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to homepage
            print("\n📡 Loading 1flix.to homepage...")
            await page.goto("https://1flix.to/home", wait_until="networkidle", timeout=60000)
            
            # Wait for content to load
            await page.wait_for_timeout(3000)
            
            # Find all movie/show links
            print("\n🎬 Finding movie links...")
            
            movie_links = await page.evaluate("""
                () => {
                    const links = [];
                    
                    // Find all links that look like movie/show pages
                    document.querySelectorAll('a[href*="/movie/"], a[href*="/tv/"]').forEach(a => {
                        const href = a.href;
                        const title = a.textContent?.trim() || a.getAttribute('title') || a.getAttribute('alt') || 'Unknown';
                        
                        // Only get unique URLs
                        if (href && !links.find(l => l.url === href)) {
                            links.push({
                                url: href,
                                title: title.slice(0, 100),
                                type: href.includes('/movie/') ? 'movie' : 'show'
                            });
                        }
                    });
                    
                    return links;
                }
            """)
            
            if movie_links:
                print(f"\n✅ Found {len(movie_links)} movie/show URLs:\n")
                
                # Group by type
                movies = [l for l in movie_links if l['type'] == 'movie']
                shows = [l for l in movie_links if l['type'] == 'show']
                
                if movies:
                    print("🎬 MOVIES:")
                    for i, movie in enumerate(movies[:10], 1):  # Show first 10
                        print(f"   {i}. {movie['title']}")
                        print(f"      {movie['url']}")
                        print()
                
                if shows:
                    print("\n📺 TV SHOWS:")
                    for i, show in enumerate(shows[:10], 1):  # Show first 10
                        print(f"   {i}. {show['title']}")
                        print(f"      {show['url']}")
                        print()
                
                print("\n" + "=" * 60)
                print("📋 TESTING RECOMMENDATIONS:")
                print("=" * 60)
                
                # Test the first movie
                if movies:
                    test_url = movies[0]['url']
                    print(f"\n🧪 Testing first movie:")
                    print(f"   URL: {test_url}")
                    print(f"\n   To test this URL, run:")
                    print(f'\n   python -m scrapy crawl diagnostic -a target_url="{test_url}" -s LOG_LEVEL=INFO')
                    
                    # Save URLs to file
                    with open('found_movies.txt', 'w', encoding='utf-8') as f:
                        f.write("FOUND MOVIE URLs\n")
                        f.write("=" * 60 + "\n\n")
                        f.write("MOVIES:\n")
                        for movie in movies:
                            f.write(f"{movie['title']}\n{movie['url']}\n\n")
                        f.write("\nTV SHOWS:\n")
                        for show in shows:
                            f.write(f"{show['title']}\n{show['url']}\n\n")
                    
                    print(f"\n📄 URLs saved to: found_movies.txt")
            else:
                print("\n⚠️ No movie links found!")
                print("   The site might:")
                print("   1. Have changed its structure")
                print("   2. Be blocking automated access")
                print("   3. Require JavaScript to load content")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(find_movies())