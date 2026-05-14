from django.core.management.base import BaseCommand

from ugovori.services import import_contracts_from_excel


class Command(BaseCommand):
    help = "Ucitava ugovore i stranke ugovora iz Excel fajla."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default="ugovori/Ugovori_sredjivanje (version 1).xlsx",
            help="Putanja do Excel fajla.",
        )
        parser.add_argument("--contracts-sheet", default="contracts_import")
        parser.add_argument("--parties-sheet", default="contract_parties_import")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Upisuje izmene. Bez ove opcije komanda radi dry-run.",
        )

    def handle(self, *args, **options):
        result = import_contracts_from_excel(
            options["file_path"],
            contracts_sheet=options["contracts_sheet"],
            parties_sheet=options["parties_sheet"],
            commit=options["commit"],
        )
        mode = "COMMIT" if result.commit else "DRY-RUN"
        self.stdout.write(self.style.WARNING(mode))
        self.stdout.write(
            (
                "Ugovori - redova: {rows}, novo: {created}, azurirano: {updated}, "
                "bez izmene: {unchanged}, duplikati preskoceni: {skipped_duplicate}, "
                "neispravni/preskoceni: {skipped_invalid}"
            ).format(**result.__dict__)
        )
        self.stdout.write(
            (
                "Stranke - redova: {parties_rows}, novo: {parties_created}, "
                "bez izmene: {parties_unchanged}, preskoceno: {parties_skipped}"
            ).format(**result.__dict__)
        )
        if not result.commit:
            self.stdout.write("Pokreni sa --commit za stvarni upis.")
