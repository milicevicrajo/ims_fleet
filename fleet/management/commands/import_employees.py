from django.core.management.base import BaseCommand
from ...utils import import_employee_data_from_excel
class Command(BaseCommand):
    help = 'Učitavanje podataka o vozilima iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        file_path = 'Baza 10 07 2024.xlsx'  # Zamenite putanju do vaše Excel datoteke
        import_employee_data_from_excel(file_path)