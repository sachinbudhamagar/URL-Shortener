from django.core.management.base import BaseCommand
from django.utils import timezone
from shortener.models import URL


class Command(BaseCommand):
    help = "Delete expired URLs"

    def handle(self, *args, **options):
        # Find expired URLs
        expired_urls = URL.objects.filter(
            expiration_date__isnull=False, expiration_date__lt=timezone.now()
        )

        count = expired_urls.count()
        expired_urls.delete()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {count} expired URLs")
        )
