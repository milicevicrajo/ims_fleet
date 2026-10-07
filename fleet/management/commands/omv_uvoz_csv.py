from django.core.management.base import BaseCommand, CommandError

from fleet.sync.selenium import import_omv_csv_data


class Command(BaseCommand):
    help = ("Uvozi OMV CSV (izvoz transakcija sa OMV portala) koji je vec preuzet: transakcije, potrosnja goriva i "
            "ciscenje duplikata — isto kao nocni posao, bez preuzimanja sa portala.")

    def add_arguments(self, parser):
        parser.add_argument("putanje", nargs="+", help="Jedan ili vise CSV fajlova (npr. putnicka i teretna).")

    def handle(self, *args, **options):
        import os

        for putanja in options["putanje"]:
            if not os.path.isfile(putanja):
                raise CommandError(f"Fajl ne postoji: {putanja}")
            rezultat = import_omv_csv_data(putanja)
            self.stdout.write(self.style.SUCCESS(f"{putanja}: {rezultat}"))
