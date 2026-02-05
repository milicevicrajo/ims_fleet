from django.core.management.base import BaseCommand

from fleet.sync.hr import sync_employees_from_hr_view


class Command(BaseCommand):
    help = "Sinhronizuje zaposlene iz dbo.hr_employee view-a"

    def add_arguments(self, parser):
        parser.add_argument(
            "--db",
            dest="db",
            default="server_db",
            help="Naziv baze iz settings.DATABASES",
        )

    def handle(self, *args, **options):
        db = options.get("db")
        result = sync_employees_from_hr_view(using=db)

        self.stdout.write(
            self.style.SUCCESS(
                "Sinhronizacija završena. "
                f"Ukupno: {result['total']}, "
                f"Kreirano: {result['created']}, "
                f"Ažurirano: {result['updated']}, "
                f"Ažurirano (neaktivni): {result['updated_inactive']}, "
                f"Preskočeno (neaktivni): {result['skipped_inactive']}"
            )
        )
