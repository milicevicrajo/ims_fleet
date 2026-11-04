import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from finansije.services import kursna_lista


class Command(BaseCommand):
    help = ("Istorija srednjeg kursa iz CSV izvoza NBS (kupovni i prodajni za devize; srednji = sredina, proverava se "
            "na ∓ 0,3 %). Prima fajlove ili folder sa .csv fajlovima. Postojeće liste i dani se ne menjaju; "
            "ponovno pokretanje ne duplira. Uvezene liste su bez broja (izvoz ga nema).")

    def add_arguments(self, parser):
        parser.add_argument("putanje", nargs="+", help="CSV fajlovi ili folder (npr. data)")

    def handle(self, *args, putanje, **options):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konzola
        fajlovi = []
        for p in map(Path, putanje):
            fajlovi += sorted(p.glob("*.csv")) if p.is_dir() else [p]
        if not fajlovi:
            raise CommandError("Nema CSV fajlova.")
        try:
            r = kursna_lista.uvezi_csv(fajlovi)
        except kursna_lista.LosCsv as exc:
            raise CommandError(f"Ništa nije uneto: {exc}") from exc
        for razlika in r["razlika"]:
            self.stdout.write(self.style.WARNING(f"Razlika, ostavljen kurs iz baze — {razlika}"))
        self.stdout.write(self.style.SUCCESS(
            f"Fajlova {len(fajlovi)}, redova {r['redova']}: novih lista {r['novih_lista']}, "
            f"novih kurseva {r['novih_kurseva']}, novih dana {r['novih_dana']}, razlika {len(r['razlika'])}."))
