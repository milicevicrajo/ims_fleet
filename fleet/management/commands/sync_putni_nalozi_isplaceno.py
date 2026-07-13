from django.core.management.base import BaseCommand

from fleet.services.putni_nalozi_payments import sync_putni_nalozi_paid_amounts


class Command(BaseCommand):
    help = "Azurira polje isplaceno na putnim nalozima iz view-a dbo.fleet_zatvoren_putni."

    def add_arguments(self, parser):
        parser.add_argument(
            "--order-number",
            help="Azuriraj samo jedan putni nalog, npr. 41/2026-101.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Procitaj podatke i prikazi sazetak bez upisa.",
        )

    def handle(self, *args, **options):
        result = sync_putni_nalozi_paid_amounts(
            order_number=options.get("order_number"),
            dry_run=options["dry_run"],
        )
        self.stdout.write(self.style.SUCCESS(f"Sync isplaceno putni nalozi: {result.summary()}"))
