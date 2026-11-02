from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finansije.services.sync import SyncBusy, sync_ledger, sync_po_godinu


class Command(BaseCommand):
    help = ("Sinhronizuje finansijska knjiženja od 2025; izvor se samo čita. Starije godine (od 2016) jednokratno: "
            "--year-from 2016 --year-to 2024 --po-godinu.")

    def add_arguments(self, parser):
        parser.add_argument("--year-from", type=int, default=2025)
        parser.add_argument("--year-to", type=int)
        parser.add_argument("--po-godinu", action="store_true",
                            help="Svaka godina u svojoj transakciji; zauzeta sinhronizacija se čeka.")

    def handle(self, *args, **options):
        try:
            if options["po_godinu"]:
                sync_po_godinu(options["year_from"], options["year_to"] or timezone.localdate().year,
                               javi=self.stdout.write)
                return
            run = sync_ledger(year_from=options["year_from"], year_to=options["year_to"])
        except SyncBusy as exc:
            raise CommandError(str(exc) or "Sinhronizacija je već pokrenuta.") from exc
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"Preuzeto {run.source_rows}; novo {run.created}; izmenjeno {run.updated}; "
            f"nepromenjeno {run.unchanged}; uklonjeno {run.removed}. Kontrolni zbirovi su usaglaseni."
        ))
