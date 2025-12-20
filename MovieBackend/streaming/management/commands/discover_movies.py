import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Discover new movies by running full crawls for all spiders"

    def add_arguments(self, parser):
        parser.add_argument(
            "--oneflix_pagecount",
            type=int,
            default=200,
            help="Max pages/responses for the oneflix crawl (CLOSESPIDER_PAGECOUNT)",
        )
        parser.add_argument(
            "--fawesome_pages",
            type=int,
            default=50,
            help="Max sitemap movie pages to visit for the fawesome crawl (max_pages)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=1800,
            help="Timeout per spider run in seconds",
        )
        parser.add_argument(
            "--only",
            type=str,
            default="all",
            choices=["all", "oneflix", "fawesome"],
            help="Run only a specific spider",
        )
        parser.add_argument(
            "--log_level",
            type=str,
            default="INFO",
            help="Scrapy log level",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)  # MovieBackend directory
        project_root = base_dir.parent  # streamline-pro
        scraper_dir = project_root / "scraper"

        if not scraper_dir.exists():
            self.stderr.write(self.style.ERROR(f"Scraper directory not found at {scraper_dir}"))
            return

        venv_python = project_root / "venv" / "Scripts" / "python.exe"
        python_exe = Path(sys.executable) if sys.executable else venv_python
        if not python_exe.exists():
            python_exe = venv_python

        if not python_exe.exists():
            self.stderr.write(self.style.ERROR(f"Python executable not found (venv={venv_python}, sys={sys.executable})"))
            return

        timeout = int(options["timeout"])
        only = options["only"]
        log_level = options["log_level"]

        def run_spider(cmd, label: str):
            self.stdout.write(self.style.NOTICE(f"\n🕷️  Running {label}..."))
            self.stdout.write(" ".join(cmd))
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(scraper_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"},
                )
                try:
                    for line in proc.stdout:
                        self.stdout.write(line.rstrip())
                finally:
                    proc.wait(timeout=timeout)

                if proc.returncode == 0:
                    self.stdout.write(self.style.SUCCESS(f"✅ {label} finished"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ {label} failed (code={proc.returncode})"))
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    pass
                self.stdout.write(self.style.ERROR(f"⏱️  {label} timeout after {timeout}s"))

        if only in ("all", "oneflix"):
            oneflix_pagecount = int(options["oneflix_pagecount"])
            cmd_oneflix = [
                str(python_exe),
                "-m",
                "scrapy",
                "crawl",
                "oneflix",
                "-s",
                f"LOG_LEVEL={log_level}",
                "-s",
                "CONCURRENT_REQUESTS=2",
                "-s",
                "DOWNLOAD_DELAY=1",
                "-s",
                f"CLOSESPIDER_PAGECOUNT={oneflix_pagecount}",
            ]
            run_spider(cmd_oneflix, label="oneflix")

        if only in ("all", "fawesome"):
            fawesome_pages = int(options["fawesome_pages"])
            cmd_fawesome = [
                str(python_exe),
                "-m",
                "scrapy",
                "crawl",
                "fawesome",
                "-a",
                f"max_pages={fawesome_pages}",
                "-s",
                f"LOG_LEVEL={log_level}",
                "-s",
                "CONCURRENT_REQUESTS=1",
                "-s",
                "DOWNLOAD_DELAY=1",
            ]
            run_spider(cmd_fawesome, label="fawesome")

        self.stdout.write(self.style.SUCCESS("\n✅ Discovery run complete"))
