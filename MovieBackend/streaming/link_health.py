import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class LinkHealthResult:
    is_healthy: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


def check_link_health(url: str, timeout: int = 5) -> LinkHealthResult:
    """Lightweight health check for a streaming link.

    Uses HEAD with redirects. Returns healthy for HTTP 2xx/3xx.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
        status = resp.status_code
        if 200 <= status < 400:
            return LinkHealthResult(is_healthy=True, status_code=status)
        return LinkHealthResult(is_healthy=False, status_code=status)
    except requests.Timeout:
        return LinkHealthResult(is_healthy=False, error='timeout')
    except requests.RequestException as e:
        return LinkHealthResult(is_healthy=False, error=str(e)[:200])
    except Exception as e:
        logger.warning(f"Unexpected error checking {url[:80]}: {str(e)[:80]}")
        return LinkHealthResult(is_healthy=False, error=str(e)[:200])
