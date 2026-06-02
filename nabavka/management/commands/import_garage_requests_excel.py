from django.core.management.base import BaseCommand

from nabavka.services.excel_requests import (
    DEFAULT_REPORT_PATH,
    import_garage_requests_from_excel,
)


class Command(BaseCommand):
    help = "Ucitava validne garazne zahteve i stavke iz Excel evidencije."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default="Pracenje nabavke za garazu.xlsx",
            help="Putanja do Excel fajla.",
        )
        parser.add_argument("--sheet", default="zahtevi")
        parser.add_argument("--report", default=DEFAULT_REPORT_PATH)
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Upisuje validne zahteve. Bez ove opcije komanda radi dry-run.",
        )

    def handle(self, *args, **options):
        result = import_garage_requests_from_excel(
            options["file_path"],
            sheet_name=options["sheet"],
            report_path=options["report"],
            commit=options["commit"],
        )
        mode = "COMMIT" if result["commit"] else "DRY-RUN"
        self.stdout.write(self.style.WARNING(mode))
        self.stdout.write(
            (
                "Zahteva: {requests}, stavki: {items}, moguce za uvoz: {importable}, "
                "kreirano zahteva: {created}, kreirano stavki: {created_items}, "
                "vec uvezeno: {already_imported}, korigovano datuma: {updated_dates}, "
                "ispravljeno datuma iz izvora: {corrected_input_dates}, "
                "ispravljeno registracija: {corrected_plates}, "
                "magacin garaze: {garage_warehouse_requests}, "
                "preskoceno: {skipped}, "
                "stavki bez zahteva: {orphan_items}"
            ).format(**result)
        )
        self.stdout.write(f"Izvestaj: {result['report_path']}")
        if result["skip_reasons"]:
            self.stdout.write("Razlozi preskakanja:")
            for reason, count in sorted(result["skip_reasons"].items()):
                self.stdout.write(f"- {reason}: {count}")
        if not result["commit"]:
            self.stdout.write("Pokreni sa --commit za stvarni upis.")
