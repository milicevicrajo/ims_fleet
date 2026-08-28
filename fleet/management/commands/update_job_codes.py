# your_app/management/commands/update_job_codes.py

from django.core.management.base import BaseCommand
from fleet.sync import update_job_codes_from_view

class Command(BaseCommand):
    help = "Azurira sifre posla za vozila na osnovu Vozila.dbo.sif_pos_trenutno view-a"

    def handle(self, *args, **kwargs):
        result = update_job_codes_from_view()
        self.stdout.write(self.style.SUCCESS(result))
