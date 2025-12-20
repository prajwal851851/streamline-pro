"""
Utility functions to trigger Scrapy spider on-demand for specific movies.
"""
import subprocess
import os
import sys
import logging
from threading import Thread
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)


def scrape_movie_on_demand(movie_url, movie_id=None):
    """
    Trigger Scrapy spider to scrape a specific movie URL on-demand.
    This runs in a separate thread to avoid blocking the Django request.
    
    Args:
        movie_url: The URL of the movie to scrape (e.g., "https://1flix.to/movie/watch-12345-title")
        movie_id: Optional movie ID to track which movie is being scraped
    
    Returns:
        Thread object (caller can join() if needed)
    """
    def run_scraper():
        try:
            # Path to scraper directory (assuming MovieBackend is in streamline-pro/MovieBackend)
            # and scraper is in streamline-pro/scraper
            base_dir = Path(settings.BASE_DIR)  # MovieBackend directory
            project_root = base_dir.parent  # streamline-pro directory
            scraper_dir = project_root / 'scraper'
            
            # Path to Python executable in venv
            venv_python = project_root / 'venv' / 'Scripts' / 'python.exe'

            python_exe = Path(sys.executable) if sys.executable else venv_python
            if python_exe and not python_exe.exists():
                python_exe = venv_python
            
            if not os.path.exists(str(scraper_dir)):
                logger.error(f"Scraper directory not found at {scraper_dir}")
                return
            
            if not python_exe or not python_exe.exists():
                logger.error(f"Python executable not found (sys.executable={sys.executable}, venv={venv_python})")
                return
            
            movie_pk = str(movie_id) if movie_id is not None else None

            def _run_spider(cmd, label: str):
                logger.info(f"Starting on-demand scrape ({label})")
                logger.info(f"Running command: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    cwd=str(scraper_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                timeout_seconds = int(os.environ.get("STREAMLINE_SCRAPE_TIMEOUT", "240"))
                try:
                    stdout, stderr = process.communicate(timeout=timeout_seconds)
                    if process.returncode == 0:
                        logger.info(f"Successfully scraped ({label})")
                    else:
                        logger.warning(f"Scrapy non-zero exit code ({label}): {stderr}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning(f"Scrapy timeout ({label})")

            # 1) Primary source: 1flix.to via 'oneflix' spider
            # Only run oneflix when we have a real tt... imdb_id or the provided URL is on 1flix.to.
            oneflix_target_url = movie_url
            movie_imdb_id = None
            movie_type = None
            if movie_id is not None:
                try:
                    from streaming.models import Movie
                    m = Movie.objects.get(pk=movie_id)
                    movie_imdb_id = m.imdb_id
                    movie_type = m.type
                except Exception:
                    movie_imdb_id = None
                    movie_type = None

            should_run_oneflix = False
            if isinstance(oneflix_target_url, str) and '1flix.to' in oneflix_target_url:
                should_run_oneflix = True
            elif isinstance(movie_imdb_id, str) and movie_imdb_id.startswith('tt'):
                should_run_oneflix = True
                # Prefer a constructed 1flix URL if the current url is a different domain
                if isinstance(movie_type, str) and movie_type == 'show':
                    oneflix_target_url = f"https://1flix.to/tv/{movie_imdb_id}"
                else:
                    oneflix_target_url = f"https://1flix.to/movie/{movie_imdb_id}"

            if should_run_oneflix:
                cmd_oneflix = [
                    str(python_exe),
                    '-m', 'scrapy',
                    'crawl',
                    'oneflix',
                    '-a', f'target_url={oneflix_target_url}',
                    '-a', 'max_pages=1',
                    '-s', 'LOG_LEVEL=INFO',
                    '-s', 'CONCURRENT_REQUESTS=1',
                    '-s', 'DOWNLOAD_DELAY=2',
                ]
                if movie_pk:
                    cmd_oneflix += ['-a', f'movie_pk={movie_pk}']
                if isinstance(movie_imdb_id, str) and movie_imdb_id:
                    cmd_oneflix += ['-a', f'imdb_id={movie_imdb_id}']

                _run_spider(cmd_oneflix, label='oneflix')

            # 2) Backup source: fawesome.tv via 'fawesome' spider
            # We pass title/year by looking up the Movie if movie_pk was provided.
            title = None
            year = None
            imdb_id = None
            if movie_id is not None:
                try:
                    from streaming.models import Movie
                    m = Movie.objects.get(pk=movie_id)
                    title = m.title
                    year = m.year
                    imdb_id = m.imdb_id
                except Exception:
                    title = None
                    year = None
                    imdb_id = None

            cmd_fawesome = [
                str(python_exe),
                '-m', 'scrapy',
                'crawl',
                'fawesome',
                '-s', 'LOG_LEVEL=INFO',
                '-s', 'CONCURRENT_REQUESTS=1',
                '-s', 'DOWNLOAD_DELAY=1',
            ]
            if movie_pk:
                cmd_fawesome += ['-a', f'movie_pk={movie_pk}']
            if imdb_id:
                cmd_fawesome += ['-a', f'imdb_id={imdb_id}']
            if title:
                cmd_fawesome += ['-a', f'title={title}']
            if year:
                cmd_fawesome += ['-a', f'year={year}']

            _run_spider(cmd_fawesome, label='fawesome')
                
        except Exception as e:
            logger.error(f"Error running on-demand scraper for {movie_url}: {str(e)}")
    
    # Run in background thread
    thread = Thread(target=run_scraper, daemon=True)
    thread.start()
    return thread


def scrape_movie_by_imdb_id(imdb_id):
    """
    Scrape a movie by searching for it on 1flix.to using the IMDB ID.
    This is a fallback if we don't have the direct URL.
    
    Args:
        imdb_id: The movie slug/ID (e.g., "watch-12345-title")
    
    Returns:
        Thread object
    """
    # Try to construct URL - this is a best guess
    # The actual URL format might need adjustment based on your site structure
    search_url = f"https://1flix.to/search?q={imdb_id}"
    return scrape_movie_on_demand(search_url, movie_id=imdb_id)

