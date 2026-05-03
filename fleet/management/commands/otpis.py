from ...sync import process_vehicle_retirements
from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help = "Izvršava otpis komandu"

    def handle(self, *args, **options):
        rezultat = process_vehicle_retirements()
        self.stdout.write(self.style.SUCCESS(rezultat))
