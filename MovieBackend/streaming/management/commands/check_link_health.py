import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from streaming.models import StreamingLink
from streaming.link_health import check_link_health

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check health of streaming links and mark inactive ones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of links to check'
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=None,
            help='Only check links older than N hours'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Request timeout in seconds'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        older_than = options['older_than']
        timeout = options['timeout']

        # Build queryset
        queryset = StreamingLink.objects.all()

        if older_than:
            cutoff = timezone.now() - timedelta(hours=older_than)
            queryset = queryset.filter(last_checked__lt=cutoff)
            self.stdout.write(f"Checking links older than {older_than} hours...")

        if limit:
            queryset = queryset[:limit]
            self.stdout.write(f"Limited to {limit} links...")

        total_links = queryset.count()
        self.stdout.write(f"Checking {total_links} links...")

        checked = 0
        deactivated = 0
        errors = 0

        for link in queryset:
            checked += 1
            if checked % 10 == 0:
                self.stdout.write(f"Checked {checked}/{total_links} links...")

            try:
                result = check_link_health(link.source_url, timeout=timeout)

                if result.is_healthy:
                    link.is_active = True
                    self.stdout.write(f"✅ {link.source_url[:60]}")
                else:
                    link.is_active = False
                    deactivated += 1
                    self.stdout.write(f"❌ {link.source_url[:60]}")

                link.last_checked = timezone.now()
                link.save(update_fields=['is_active', 'last_checked'])

            except Exception as e:
                errors += 1
                logger.error(f"Error checking {link.source_url}: {str(e)}")
                self.stdout.write(f"⚠️  Error: {link.source_url[:60]}")

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("LINK HEALTH CHECK COMPLETE")
        self.stdout.write("="*50)
        self.stdout.write(f"Total checked: {checked}")
        self.stdout.write(f"Deactivated: {deactivated}")
        self.stdout.write(f"Errors: {errors}")
        self.stdout.write(f"Still active: {checked - deactivated - errors}")