from django.core.management.base import BaseCommand

from menice.services import import_ulazne_menice_from_excel


class Command(BaseCommand):
    help = "Ucitava ulazne menice iz Excel fajla."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default="menice/Menice - za ucitavanje.xlsx",
            help="Putanja do Excel fajla. Default: menice/Menice - za ucitavanje.xlsx",
        )
        parser.add_argument("--sheet", default="ulazne menice")
        parser.add_argument("--header-row", type=int, default=1)
        parser.add_argument("--first-data-row", type=int, default=2)
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Upisuje izmene. Bez ove opcije komanda radi dry-run.",
        )

    def handle(self, *args, **options):
        result = import_ulazne_menice_from_excel(
            options["file_path"],
            sheet_name=options["sheet"],
            header_row=options["header_row"],
            first_data_row=options["first_data_row"],
            commit=options["commit"],
        )
        mode = "COMMIT" if result["commit"] else "DRY-RUN"
        self.stdout.write(self.style.WARNING(mode))
        self.stdout.write(
            (
                "Redova: {rows}, novo: {created}, azurirano: {updated}, "
                "bez izmene: {unchanged}, bez kljuca: {skipped_missing_key}"
            ).format(**result)
        )
        if not result["commit"]:
            self.stdout.write("Pokreni sa --commit za stvarni upis.")
