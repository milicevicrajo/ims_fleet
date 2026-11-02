import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finansije.services.sync import SyncBusy, sync_ledger


class Command(BaseCommand):
    help = ("Sinhronizuje finansijska knjiženja od 2025; izvor se samo čita. Starije godine (od 2016) jednokratno: "
            "--year-from 2016 --year-to 2024 --po-godinu.")

    def add_arguments(self, parser):
        parser.add_argument("--year-from", type=int, default=2025)
        parser.add_argument("--year-to", type=int)
        # Svaka godina je posebna transakcija (~4–5 min za ~95.000 stavki); dok traje, ekrani Finansija čekaju.
        parser.add_argument("--po-godinu", action="store_true",
                            help="Godinu po godinu; zauzeta sinhronizacija se čeka (npr. ona u :20 svakog sata).")

    def handle(self, *args, **options):
        if not options["po_godinu"]:
            self.ispisi(self.sinhronizuj(options["year_from"], options["year_to"]))
            return
        year_to = options["year_to"] or timezone.localdate().year
        for godina in range(options["year_from"], year_to + 1):
            for _ in range(30):
                try:
                    run = self.sinhronizuj(godina, godina, busy_raise=True)
                    break
                except SyncBusy:
                    self.stdout.write(f"{godina}: sinhronizacija je zauzeta, ponovo za 60 s.")
                    time.sleep(60)
            else:
                raise CommandError(f"{godina}: sinhronizacija je stalno zauzeta; godine od {godina} nisu preuzete.")
            self.ispisi(run, f"{godina}: ")

    def sinhronizuj(self, year_from, year_to, busy_raise=False):
        try:
            return sync_ledger(year_from=year_from, year_to=year_to)
        except SyncBusy:
            if busy_raise:
                raise
            raise CommandError("Sinhronizacija je već pokrenuta.")
        except Exception as exc:
            raise CommandError(str(exc)) from exc

    def ispisi(self, run, prefiks=""):
        self.stdout.write(self.style.SUCCESS(
            f"{prefiks}Preuzeto {run.source_rows}; novo {run.created}; izmenjeno {run.updated}; "
            f"nepromenjeno {run.unchanged}; uklonjeno {run.removed}. Kontrolni zbirovi su usaglaseni."
        ))
