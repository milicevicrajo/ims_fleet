from django.core.management.base import BaseCommand

from potrazivanja.services.alta_banka import preuzmi


class Command(BaseCommand):
    help = "Kupci koji su plaćali preko Alta banke i njihovi računi iz NBS registra (Potraživanja → Alta banka)."

    def add_arguments(self, parser):
        parser.add_argument("--fajl", help="JSONL sa ranije snimljenim NBS rezultatima (bez novih upita ka NBS)")
        parser.add_argument("--iznova", action="store_true", help="Pretraži ponovo i kupce koji već imaju snimak")

    def handle(self, *args, **options):
        if not options["fajl"]:
            try:  # sertifikat NBS se na nekim računarima proverava samo kroz Windows skladište sertifikata
                import truststore
                truststore.inject_into_ssl()
            except ImportError:
                pass
        preuzmi(fajl=options["fajl"], nastavi=not options["iznova"], javi=self.stdout.write)
