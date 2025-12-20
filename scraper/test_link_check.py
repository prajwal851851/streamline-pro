"""Test link validation helper used by pipelines.py
Usage:
    python test_link_check.py urls.txt
or
    python test_link_check.py https://example.com https://example.org

Outputs whether each URL appears reachable/playable.
"""
import sys
import requests
from requests.exceptions import RequestException

VALID_VIDEO_HOSTS = [
    "vidoza", "streamtape", "mixdrop", "doodstream", "dood", 
    "filemoon", "upstream", "streamlare", "streamhub", "streamwish",
    "videostr", "voe", "streamvid", "mp4upload", "streamplay",
]


def is_link_working(url: str) -> bool:
    url = url.strip()
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        status = resp.status_code
        if status >= 400:
            print(f"  -> HTTP {status}")
            return False

        ctype = (resp.headers.get("content-type") or "").lower()
        if ctype.startswith("video/") or "application/vnd.apple.mpegurl" in ctype or ".m3u8" in url.lower():
            print(f"  -> content-type: {ctype}")
            return True

        body = resp.text.lower()
        if "proudly powered by litespeed" in body or "access denied" in body or "service unavailable" in body:
            print("  -> Blocked / placeholder page detected")
            return False

        if any(k in body for k in [".m3u8", ".mp4", "source src=", "player", "embed", "iframe src="]):
            print("  -> Streaming indicators found in HTML")
            return True

        if any(host in url.lower() for host in VALID_VIDEO_HOSTS):
            print("  -> Known video host domain (permissive)")
            return True

        print(f"  -> No streaming indicators (ctype={ctype})")
        return False
    except RequestException as e:
        print(f"  -> Request failed: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_link_check.py <url_or_file> [more urls]")
        sys.exit(1)

    inputs = sys.argv[1:]
    urls = []
    # If a single argument is a file, read it
    if len(inputs) == 1 and inputs[0].endswith('.txt'):
        try:
            with open(inputs[0], 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        urls.append(line)
        except Exception as e:
            print(f"Could not read file: {e}")
            sys.exit(1)
    else:
        urls = inputs

    for u in urls:
        print(f"Checking: {u}")
        ok = is_link_working(u)
        print(f"Result: {'OK' if ok else 'NOT OK'}\n")
