from django.core.management.base import BaseCommand

from menice.services import sync_izlazne_menice


class Command(BaseCommand):
    help = "Povlaci izlazne menice iz NBS registra i azurira samo NBS polja."

    def add_arguments(self, parser):
        parser.add_argument("--tax-code", default="100223617")
        parser.add_argument("--national-code", default="")
        parser.add_argument("--serial-number", default="")
        parser.add_argument("--registration-date", default="")
        parser.add_argument("--page-size", type=int, default=100)
        parser.add_argument("--max-pages", type=int, default=None)
        parser.add_argument("--timeout", type=int, default=30)
        parser.add_argument("--skip-avalists", action="store_false", dest="include_avalists")
        parser.set_defaults(include_avalists=True)

    def handle(self, *args, **options):
        sync_options = {
            key: options[key]
            for key in (
                "tax_code",
                "national_code",
                "serial_number",
                "registration_date",
                "page_size",
                "include_avalists",
                "max_pages",
                "timeout",
            )
        }
        result = sync_izlazne_menice(**sync_options)
        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Povuceno: {fetched}, novo: {created}, azurirano: {updated}, "
                    "bez izmene: {unchanged}, preskoceno: {skipped}"
                ).format(**result)
            )
        )
