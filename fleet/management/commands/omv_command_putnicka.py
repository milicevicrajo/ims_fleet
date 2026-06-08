from ...sync import omv_putnicka_data_import
from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help = 'Downloads a report from OMV website and imports data into the database'

    def handle(self, *args, **kwargs):
        rezultat = omv_putnicka_data_import(self, *args, **kwargs)
        self.stdout.write(self.style.SUCCESS(rezultat))
