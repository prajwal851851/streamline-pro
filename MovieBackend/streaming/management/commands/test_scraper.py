"""
Django management command to test the scraper with on-demand mode.

Usage:
    python manage.py test_scraper https://1flix.to/movie/watch-movie-name-123
"""
import subprocess
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test the scraper with a specific movie URL'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='The movie URL to scrape (e.g., https://1flix.to/movie/watch-...)',
        )

    def handle(self, *args, **options):
        url = options['url']
        
        self.stdout.write(self.style.SUCCESS(f'\n🎬 Testing scraper for: {url}\n'))
        
        # Path to scraper directory
        base_dir = Path(settings.BASE_DIR)
        project_root = base_dir.parent
        scraper_dir = project_root / 'scraper'
        
        # Path to Python executable in venv
        venv_python = project_root / 'venv' / 'Scripts' / 'python.exe'
        if not venv_python.exists():
            venv_python = project_root / 'venv' / 'bin' / 'python'
        
        if not scraper_dir.exists():
            self.stdout.write(
                self.style.ERROR(f'❌ Scraper directory not found at {scraper_dir}')
            )
            return
        
        if not venv_python.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Python executable not found at {venv_python}, using system python'
                )
            )
            venv_python = 'python'
        
        # Build Scrapy command
        cmd = [
            str(venv_python),
            '-m', 'scrapy',
            'crawl',
            'oneflix',
            '-a', f'target_url={url}',
            '-s', 'LOG_LEVEL=INFO',
        ]
        
        self.stdout.write('📡 Running scraper...\n')
        
        try:
            # Run Scrapy
            process = subprocess.Popen(
                cmd,
                cwd=str(scraper_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Stream output
            for line in process.stdout:
                if line.strip():
                    # Color code based on content
                    if '✅' in line or 'Found' in line:
                        self.stdout.write(self.style.SUCCESS(line.strip()))
                    elif '⚠️' in line or 'WARNING' in line:
                        self.stdout.write(self.style.WARNING(line.strip()))
                    elif '❌' in line or 'ERROR' in line:
                        self.stdout.write(self.style.ERROR(line.strip()))
                    else:
                        self.stdout.write(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Scraping completed successfully!')
                )
                self.stdout.write(
                    '\n💡 Check the database for the scraped movie and links.\n'
                )
            else:
                stderr = process.stderr.read()
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Scraping failed with return code {process.returncode}')
                )
                if stderr:
                    self.stdout.write(self.style.ERROR(f'Error: {stderr}'))
                    
        except subprocess.TimeoutExpired:
            process.kill()
            self.stdout.write(
                self.style.ERROR('\n⏱️  Scraping timeout (>2 minutes)')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error running scraper: {str(e)}')
            )