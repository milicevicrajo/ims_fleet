from django.core.management.base import BaseCommand, CommandError

from finansije.services.sync import sync_ledger


class Command(BaseCommand):
    help = "Sinhronizuje finansijska knjiženja od 2025; izvor se samo čita."

    def add_arguments(self, parser):
        parser.add_argument("--year-from", type=int, default=2025)
        parser.add_argument("--year-to", type=int)

    def handle(self, *args, **options):
        try:
            run = sync_ledger(year_from=options["year_from"], year_to=options["year_to"])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"Preuzeto {run.source_rows}; novo {run.created}; izmenjeno {run.updated}; "
            f"nepromenjeno {run.unchanged}; uklonjeno {run.removed}. Kontrolni zbirovi su usaglaseni."
        ))
