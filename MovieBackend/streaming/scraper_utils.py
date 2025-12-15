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
            
            if not os.path.exists(str(scraper_dir)):
                logger.error(f"Scraper directory not found at {scraper_dir}")
                return
            
            if not os.path.exists(venv_python):
                logger.error(f"Python executable not found at {venv_python}")
                return
            
            # Build Scrapy command
            # We'll modify the spider to accept a specific URL to scrape
            cmd = [
                venv_python,
                '-m', 'scrapy',
                'crawl',
                'oneflix',
                '-a', f'target_url={movie_url}',
                '-a', 'max_pages=1',  # Only scrape this one movie
                '-s', 'LOG_LEVEL=INFO',
                '-s', 'CONCURRENT_REQUESTS=1',
                '-s', 'DOWNLOAD_DELAY=2',
            ]
            
            logger.info(f"Starting on-demand scrape for: {movie_url}")
            
            # Run Scrapy in the scraper directory
            process = subprocess.Popen(
                cmd,
                cwd=str(scraper_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion (with timeout)
            try:
                stdout, stderr = process.communicate(timeout=120)  # 2 minute timeout
                if process.returncode == 0:
                    logger.info(f"Successfully scraped {movie_url}")
                else:
                    logger.warning(f"Scrapy returned non-zero exit code for {movie_url}: {stderr}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"Scrapy timeout for {movie_url}")
                
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

