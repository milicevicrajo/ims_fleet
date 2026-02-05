from ...selenium_integrations import nis_data_import
from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help = "Izvršava NIS komandu"

    def handle(self, *args, **options):
        rezultat = nis_data_import()
        self.stdout.write(self.style.SUCCESS(rezultat))