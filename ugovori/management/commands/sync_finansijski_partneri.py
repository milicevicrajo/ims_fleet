from django.core.management.base import BaseCommand

from ugovori.services import sync_finance_partners


class Command(BaseCommand):
    help = "Sinhronizuje lokalne ugovori partnere iz finansijskog view-a dbo.partneri."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Upisuje izmene. Bez ove opcije komanda radi dry-run.",
        )
        parser.add_argument(
            "--source-db",
            default="server_db",
            help="Alias baze iz koje se cita finansijski view partneri. Default: server_db.",
        )
        parser.add_argument(
            "--target-db",
            default="default",
            help="Alias baze u koju se upisuju ugovori_partner. Default: default.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Ogranicava broj ucitanih partnera, korisno za probu.",
        )
        parser.add_argument(
            "--sif-par",
            type=int,
            default=None,
            help="Sinhronizuje samo jednog partnera po sifri.",
        )

    def handle(self, *args, **options):
        commit = options["commit"]
        result = sync_finance_partners(
            source_db=options["source_db"],
            target_db=options["target_db"],
            limit=options["limit"],
            sif_par=options["sif_par"],
            commit=commit,
        )

        self.stdout.write(
            self.style.SUCCESS("COMMIT: upisujem izmene.")
            if commit
            else self.style.WARNING("DRY-RUN: nema upisa.")
        )
        self.stdout.write(
            f"Ucitanih iz view-a: {result.loaded} | novo: {result.created} | "
            f"azuriranje: {result.updated} | bez izmene: {result.unchanged} | "
            f"preskoceno: {result.skipped}"
        )
        if not commit:
            self.stdout.write("Pokreni sa --commit kada zelis stvarni upis.")
