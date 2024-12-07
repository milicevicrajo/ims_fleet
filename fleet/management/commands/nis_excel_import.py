from django.core.management.base import BaseCommand
from ...utils import import_nis_transactions, import_nis_fuel_consumption

class Command(BaseCommand):
    help = 'Učitavanje transakcija NIS iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        file_path = 'Transakcije po klijentima - 2024-12-07_13-34.csv'  # Zamenite putanju do vaše Excel datoteke
        import_nis_transactions(file_path)
        import_nis_fuel_consumption(file_path)