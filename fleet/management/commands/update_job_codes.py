# your_app/management/commands/update_job_codes.py

from django.core.management.base import BaseCommand
from fleet.utils import update_job_codes_from_view

class Command(BaseCommand):
    help = "Ažurira šifre posla za vozila na osnovu view-a sif_pos_trenutno"

    def handle(self, *args, **kwargs):
        count = update_job_codes_from_view()
        self.stdout.write(self.style.SUCCESS(f"Ažurirano {count} vozila."))
