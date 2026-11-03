import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from finansije.services import kursna_lista


def _datum(tekst):
    return datetime.strptime(tekst.rstrip("."), "%d.%m.%Y").date()


class Command(BaseCommand):
    help = ("Srednji kurs NBS za sve valute, dan po dan: dopunjuje dane bez liste od 01.01.2016. "
            "Cela istorija (~4.000 stranica, pauza 3 s) traje oko 3,5 sata; ponovno pokretanje nastavlja gde je stalo. "
            "Zaštita od botova NBS zaustavlja preuzimanje — pokrenuti ponovo kasnije.")

    def add_arguments(self, parser):
        parser.add_argument("--od", type=_datum, default=kursna_lista.PRVI_DAN, help="dd.mm.gggg")
        parser.add_argument("--do", type=_datum, help="dd.mm.gggg; podrazumevano danas")
        parser.add_argument("--svi", action="store_true", help="Ponovo i dane koji već imaju listu.")

    def handle(self, *args, **options):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konzola
        rezultat = kursna_lista.preuzmi(options["od"], options["do"], svi=options["svi"], javi=self.stdout.write)
        self.stdout.write(self.style.SUCCESS(kursna_lista.poruka(rezultat)))
