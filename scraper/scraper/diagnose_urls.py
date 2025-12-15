# File: scraper/diagnose_urls.py
# NEW FILE - Create this to diagnose link extraction issues

import subprocess
import sys
import re
from collections import defaultdict

def analyze_url(url):
    """Analyze a URL to determine why it might be rejected"""
    url_lower = url.lower()
    
    analysis = {
        'url': url,
        'is_youtube': 'youtube' in url_lower or 'youtu.be' in url_lower,
        'is_social': any(x in url_lower for x in ['facebook', 'twitter', 'instagram', 'tiktok']),
        'is_movie_info': any(x in url_lower for x in ['imdb', 'themoviedb', 'tvdb']),
        'is_navigation': '1flix.to/movie/' in url_lower or '1flix.to/tv/' in url_lower,
        'has_embed': 'embed' in url_lower,
        'has_player': 'player' in url_lower,
        'has_stream': 'stream' in url_lower,
        'has_video': 'video' in url_lower,
        'has_slash_e': '/e/' in url_lower,
        'is_http': url_lower.startswith('http'),
    }
    
    # Check against known video hosts
    video_hosts = [
        'vidoza', 'streamtape', 'mixdrop', 'doodstream', 'dood',
        'filemoon', 'upstream', 'streamlare', 'voe', 'supervideo',
        'vidcloud', 'fembed', 'mp4upload', 'streamplay', 'streamwish',
    ]
    analysis['known_host'] = any(host in url_lower for host in video_hosts)
    
    # Determine if should accept
    should_reject = (
        analysis['is_youtube'] or 
        analysis['is_social'] or 
        analysis['is_movie_info'] or 
        analysis['is_navigation'] or 
        not analysis['is_http']
    )
    
    should_accept = (
        analysis['known_host'] or 
        analysis['has_embed'] or 
        analysis['has_player'] or 
        analysis['has_stream'] or 
        analysis['has_slash_e']
    )
    
    analysis['verdict'] = 'REJECT' if should_reject else ('ACCEPT' if should_accept else 'MAYBE REJECT')
    
    return analysis

def run_diagnostic_scrape(movie_url):
    """Run scraper and capture all URLs found"""
    print(f"🔍 Running diagnostic scrape on: {movie_url}\n")
    
    cmd = [
        sys.executable,
        '-m', 'scrapy', 'crawl', 'oneflix',
        '-a', f'target_url={movie_url}',
        '-s', 'LOG_LEVEL=DEBUG',
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        output = result.stdout + result.stderr
        
        # Extract URLs from output
        url_pattern = r'https?://[^\s\'"<>]+'
        urls = set(re.findall(url_pattern, output))
        
        print(f"📊 Found {len(urls)} unique URLs\n")
        
        # Categorize URLs
        categories = defaultdict(list)
        
        for url in urls:
            analysis = analyze_url(url)
            
            if analysis['is_youtube']:
                categories['YouTube'].append(url)
            elif analysis['is_social']:
                categories['Social Media'].append(url)
            elif analysis['is_movie_info']:
                categories['Movie Info Sites'].append(url)
            elif analysis['is_navigation']:
                categories['Site Navigation'].append(url)
            elif analysis['known_host']:
                categories['Known Video Hosts'].append(url)
            elif analysis['has_embed'] or analysis['has_player'] or analysis['has_stream']:
                categories['Has Streaming Keywords'].append(url)
            else:
                categories['Unknown/Other'].append(url)
        
        # Print categories
        for category, url_list in sorted(categories.items()):
            print(f"\n{'='*60}")
            print(f"{category} ({len(url_list)} URLs)")
            print('='*60)
            
            for url in url_list[:5]:  # Show first 5
                analysis = analyze_url(url)
                print(f"\n{analysis['verdict']}: {url[:80]}")
                
                reasons = []
                if analysis['is_youtube']:
                    reasons.append("❌ YouTube")
                if analysis['is_social']:
                    reasons.append("❌ Social Media")
                if analysis['known_host']:
                    reasons.append("✅ Known Video Host")
                if analysis['has_embed']:
                    reasons.append("✅ Has 'embed'")
                if analysis['has_player']:
                    reasons.append("✅ Has 'player'")
                if analysis['has_stream']:
                    reasons.append("✅ Has 'stream'")
                    
                if reasons:
                    print(f"  Reasons: {', '.join(reasons)}")
            
            if len(url_list) > 5:
                print(f"\n  ... and {len(url_list) - 5} more")
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print('='*60)
        
        youtube_count = len(categories['YouTube'])
        video_host_count = len(categories['Known Video Hosts'])
        streaming_keyword_count = len(categories['Has Streaming Keywords'])
        
        print(f"\n❌ YouTube Trailers: {youtube_count}")
        print(f"✅ Known Video Hosts: {video_host_count}")
        print(f"✅ Has Streaming Keywords: {streaming_keyword_count}")
        print(f"❓ Unknown/Other: {len(categories['Unknown/Other'])}")
        
        if video_host_count > 0 or streaming_keyword_count > 0:
            print(f"\n✅ GOOD: Found {video_host_count + streaming_keyword_count} potential streaming links")
        else:
            print(f"\n⚠️ WARNING: No streaming links found!")
            print(f"\nPossible issues:")
            print(f"  1. Site structure changed - check manually")
            print(f"  2. Links are behind additional clicks - increase wait times")
            print(f"  3. New video hosts being used - check Unknown/Other category")
            
            if len(categories['Unknown/Other']) > 0:
                print(f"\n📋 Unknown URLs to investigate:")
                for url in categories['Unknown/Other'][:10]:
                    print(f"  {url[:80]}")
                print(f"\n  Consider adding these domains to VIDEO_HOSTS if they're streaming sites")
        
        if youtube_count > 0:
            print(f"\n✅ GOOD: YouTube filtering is working ({youtube_count} rejected)")
        
    except subprocess.TimeoutExpired:
        print("❌ ERROR: Scraping timeout (3 minutes)")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_urls.py <movie_url>")
        print("\nExample:")
        print('  python diagnose_urls.py "https://1flix.to/movie/watch-venom-140207"')
        sys.exit(1)
    
    movie_url = sys.argv[1]
    run_diagnostic_scrape(movie_url)