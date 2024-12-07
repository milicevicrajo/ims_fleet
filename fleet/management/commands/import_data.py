from django.core.management.base import BaseCommand
from ...utils import import_job_codes_from_excel, import_lease_data_from_excel,import_policy_data_from_excel, populate_service_types,import_employee_data_from_excel,import_requisitions_from_excel

class Command(BaseCommand):
    help = 'Učitavanje podataka o vozilima iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        file_path = 'Baza 10 07 2024.xlsx'  # Zamenite putanju do vaše Excel datoteke
        # populate_service_types()
        # import_job_codes_from_excel(file_path)
        # import_lease_data_from_excel(file_path)
        # import_policy_data_from_excel(file_path)
        # import_requisitions_from_excel(file_path)
