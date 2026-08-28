from django.core.management.base import BaseCommand

from ...sync import sync_vehicle_job_codes_with_org_units


class Command(BaseCommand):
    help = "Povlaci organizacione jedinice i sifre posla vozila iz baze Vozila"

    def handle(self, *args, **kwargs):
        result = sync_vehicle_job_codes_with_org_units()
        self.stdout.write(self.style.SUCCESS(result))
