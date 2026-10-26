from django.core.management.base import BaseCommand

from promotions.models import Promotion, promotion_today


class Command(BaseCommand):
    help = "Delete promotions whose last valid day has passed in Brasília time."

    def handle(self, *args, **options):
        _, counts = Promotion.objects.filter(ends_on__lt=promotion_today()).delete()
        self.stdout.write(f"Deleted {counts.get('promotions.Promotion', 0)} expired promotions.")
