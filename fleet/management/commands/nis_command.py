import datetime

from ...sync import format_nis_sync_result, nis_data_import
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Izvršava NIS komandu (podrazumevano od 1. dana prethodnog meseca)."

    def add_arguments(self, parser):
        parser.add_argument("--od", help="Dopuna starijeg perioda: datum od, npr. 2026-08-01.")

    def handle(self, *args, **options):
        od = datetime.date.fromisoformat(options["od"]) if options.get("od") else None
        rezultat = nis_data_import(date_from=od)
        self.stdout.write(self.style.SUCCESS(format_nis_sync_result(rezultat)))
