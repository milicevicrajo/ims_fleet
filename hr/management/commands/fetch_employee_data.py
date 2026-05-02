from django.core.management.base import BaseCommand

from hr.sync import sync_employees_from_hr_view


class Command(BaseCommand):
    help = "Deprecated alias za sync_hr_employees; sinhronizuje zaposlene iz HR view-a"

    def add_arguments(self, parser):
        parser.add_argument(
            "--db",
            dest="db",
            default=None,
            help="Opcioni naziv baze iz settings.DATABASES",
        )

    def handle(self, *args, **options):
        result = sync_employees_from_hr_view(using=options.get("db"))
        self.stdout.write(
            self.style.WARNING(
                "Komanda 'fetch_employee_data' je zastarela. Koristi 'sync_hr_employees'."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Sinhronizacija zavrsena. "
                f"Ukupno: {result['total']}, "
                f"Kreirano: {result['created']}, "
                f"Azurirano: {result['updated']}, "
                f"Azurirano (neaktivni): {result['updated_inactive']}, "
                f"Preskoceno (neaktivni): {result['skipped_inactive']}"
            )
        )
