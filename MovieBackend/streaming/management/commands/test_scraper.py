# File: MovieBackend/streaming/management/commands/test_scraper_debug.py
# NEW FILE - Create this for better debugging

import subprocess
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from streaming.models import Movie, StreamingLink


class Command(BaseCommand):
    help = 'Test scraper with detailed URL analysis'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='Movie URL to scrape')

    def handle(self, *args, **options):
        url = options['url']
        
        self.stdout.write(self.style.SUCCESS(f'\n🎬 Testing scraper for: {url}\n'))
        
        # Extract movie ID from URL
        movie_id = url.rstrip('/').split('/')[-1]
        
        # Check if movie already exists
        try:
            existing = Movie.objects.get(imdb_id=movie_id)
            self.stdout.write(self.style.WARNING(f'ℹ️ Movie already in DB: {existing.title}'))
            self.stdout.write(f'   - Current links: {existing.links.count()}')
            
            # Show existing links
            if existing.links.exists():
                self.stdout.write('\n📎 Existing links:')
                for i, link in enumerate(existing.links.all()[:5], 1):
                    url_display = link.source_url[:100]
                    is_youtube = 'youtube.com' in link.source_url.lower() or 'youtu.be' in link.source_url.lower()
                    status = '❌ YOUTUBE' if is_youtube else '✅ Valid'
                    self.stdout.write(f'   {i}. [{status}] {url_display}')
                
                youtube_count = sum(1 for link in existing.links.all() 
                                  if 'youtube' in link.source_url.lower())
                if youtube_count > 0:
                    self.stdout.write(self.style.ERROR(f'\n⚠️ WARNING: {youtube_count} YouTube links found!'))
        except Movie.DoesNotExist:
            self.stdout.write('ℹ️ Movie not in DB yet')
        
        # Paths
        base_dir = Path(settings.BASE_DIR)
        project_root = base_dir.parent
        scraper_dir = project_root / 'scraper'
        
        venv_python = project_root / 'venv' / 'Scripts' / 'python.exe'
        if not venv_python.exists():
            venv_python = project_root / 'venv' / 'bin' / 'python'
        
        if not scraper_dir.exists():
            self.stdout.write(self.style.ERROR(f'❌ Scraper directory not found'))
            return
        
        if not venv_python.exists():
            self.stdout.write(self.style.WARNING('⚠️ Using system python'))
            venv_python = 'python'
        
        # Build command with DEBUG logging
        cmd = [
            str(venv_python),
            '-m', 'scrapy',
            'crawl',
            'oneflix',
            '-a', f'target_url={url}',
            '-s', 'LOG_LEVEL=INFO',
        ]
        
        self.stdout.write('\n📡 Running scraper...\n')
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(scraper_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            youtube_urls = []
            valid_urls = []
            
            # Stream output and analyze
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                # Track URLs
                if 'ACCEPTED:' in line:
                    valid_urls.append(line)
                    self.stdout.write(self.style.SUCCESS(line))
                elif 'Rejected YOUTUBE:' in line:
                    youtube_urls.append(line)
                    self.stdout.write(self.style.ERROR(line))
                elif '⚠️' in line or 'WARNING' in line:
                    self.stdout.write(self.style.WARNING(line))
                elif '❌' in line or 'ERROR' in line:
                    self.stdout.write(self.style.ERROR(line))
                elif '✅' in line or '📋' in line or '🔍' in line:
                    self.stdout.write(self.style.NOTICE(line))
                else:
                    self.stdout.write(line)
            
            process.wait()
            
            # Analysis
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('\n📊 SCRAPING ANALYSIS\n'))
            self.stdout.write('='*60)
            
            self.stdout.write(f'\n✅ Valid streaming links found: {len(valid_urls)}')
            self.stdout.write(f'❌ YouTube links rejected: {len(youtube_urls)}')
            
            if youtube_urls:
                self.stdout.write(self.style.ERROR('\n⚠️ YouTube links were found and rejected (GOOD):'))
                for i, url_line in enumerate(youtube_urls[:3], 1):
                    self.stdout.write(f'   {i}. {url_line}')
            
            if valid_urls:
                self.stdout.write(self.style.SUCCESS('\n✅ Valid links accepted:'))
                for i, url_line in enumerate(valid_urls[:5], 1):
                    self.stdout.write(f'   {i}. {url_line}')
            
            # Check database after scraping
            try:
                movie = Movie.objects.get(imdb_id=movie_id)
                links = movie.links.all()
                youtube_in_db = sum(1 for link in links if 'youtube' in link.source_url.lower())
                
                self.stdout.write(f'\n💾 Database status:')
                self.stdout.write(f'   - Movie: {movie.title}')
                self.stdout.write(f'   - Total links: {links.count()}')
                self.stdout.write(f'   - YouTube links: {youtube_in_db}')
                
                if youtube_in_db > 0:
                    self.stdout.write(self.style.ERROR(f'\n❌ ERROR: YouTube links in database!'))
                elif links.count() == 0:
                    self.stdout.write(self.style.WARNING(f'\n⚠️ WARNING: No links saved'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ SUCCESS: {links.count()} valid links saved'))
                
                # Show sample links
                if links.exists():
                    self.stdout.write('\n📎 Sample links in database:')
                    for i, link in enumerate(links[:3], 1):
                        url_display = link.source_url[:80]
                        self.stdout.write(f'   {i}. {url_display}')
                        
            except Movie.DoesNotExist:
                self.stdout.write(self.style.ERROR('\n❌ Movie not found in database after scraping'))
            
            self.stdout.write('\n' + '='*60 + '\n')
            
            if process.returncode == 0:
                self.stdout.write(self.style.SUCCESS('✅ Scraping completed successfully\n'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Scraping failed (code {process.returncode})\n'))
                    
        except subprocess.TimeoutExpired:
            process.kill()
            self.stdout.write(self.style.ERROR('\n⏱️ Scraping timeout'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))