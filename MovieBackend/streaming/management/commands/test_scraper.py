# File: MovieBackend/streaming/management/commands/test_scraper.py
# REPLACE with this debugging version

import subprocess
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test the scraper with detailed debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='The movie URL to scrape',
        )

    def handle(self, *args, **options):
        url = options['url']
        
        self.stdout.write(self.style.SUCCESS(f'\n🎬 Testing scraper for: {url}\n'))
        
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
            '-s', 'LOG_LEVEL=DEBUG',  # Changed to DEBUG for more info
        ]
        
        self.stdout.write('📡 Running scraper with DEBUG logging...\n')
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(scraper_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Capture stderr too
                text=True
            )
            
            # Stream ALL output
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                    
                # Color code important lines
                if '✅' in line or 'ACCEPTED' in line:
                    self.stdout.write(self.style.SUCCESS(line))
                elif '⚠️' in line or 'WARNING' in line:
                    self.stdout.write(self.style.WARNING(line))
                elif '❌' in line or 'ERROR' in line or 'Rejected' in line:
                    self.stdout.write(self.style.ERROR(line))
                elif '📋' in line or 'Sample URLs' in line:
                    self.stdout.write(self.style.NOTICE(line))
                else:
                    self.stdout.write(line)
            
            process.wait()
            
            if process.returncode == 0:
                self.stdout.write(self.style.SUCCESS('\n✅ Scraping completed!'))
                self.stdout.write('\n💡 Check the database for scraped data.\n')
                self.stdout.write('💡 Check the logs above for "Sample URLs" to see what was found\n')
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Scraping failed (code {process.returncode})'))
                    
        except subprocess.TimeoutExpired:
            process.kill()
            self.stdout.write(self.style.ERROR('\n⏱️ Scraping timeout'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))