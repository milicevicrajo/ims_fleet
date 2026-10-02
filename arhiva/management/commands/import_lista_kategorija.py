"""Uvoz Liste kategorija sa rokovima čuvanja i izveštaj spornih stavki za arhivistu.

    manage.py import_lista_kategorija "Lista-kategorija 10.03.2023.docx" --izvestaj sporne.xlsx --samo-izvestaj
    manage.py import_lista_kategorija lista-ociscena.xlsx --naziv "Lista 2023" --datum 2023-03-10 --aktivna

Bez --samo-izvestaj pravi novu verziju Liste u bazi (stare verzije se ne menjaju).
"""
import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from arhiva.services import lista


class Command(BaseCommand):
    help = "Uvozi Listu kategorija (.docx ili .xlsx) i pravi izveštaj spornih stavki."

    def add_arguments(self, parser):
        parser.add_argument("putanja")
        parser.add_argument("--naziv", default="")
        parser.add_argument("--datum", help="Datum donošenja Liste, YYYY-MM-DD")
        parser.add_argument("--aktivna", action="store_true", help="Nova verzija postaje aktivna (nudi se pri izboru)")
        parser.add_argument("--izvestaj", help="Putanja .xlsx izveštaja spornih stavki")
        parser.add_argument("--samo-izvestaj", action="store_true", help="Samo proveri i napravi izveštaj, bez upisa")

    def handle(self, *args, **opts):
        putanja = Path(opts["putanja"])
        if not putanja.exists():
            raise CommandError(f"Fajl ne postoji: {putanja}")
        try:
            stavke = lista.procitaj(putanja)
            datum = datetime.date.fromisoformat(opts["datum"]) if opts["datum"] else None
        except ValueError as exc:
            raise CommandError(str(exc))
        sporne = lista.sporne_stavke(stavke)
        grupa = len({s.grupa_redosled for s in stavke})
        self.stdout.write(f"Pročitano: {len(stavke)} kategorija u {grupa} grupa, spornih stavki: {len(sporne)}.")
        po_vrsti = {}
        for s in sporne:
            po_vrsti[s.vrsta] = po_vrsti.get(s.vrsta, 0) + 1
        for kljuc, naziv, _ in lista.PRIORITETI:
            if po_vrsti.get(kljuc):
                self.stdout.write(f"  {naziv}: {po_vrsti[kljuc]}")
        if opts["izvestaj"]:
            lista.izvestaj_xlsx(stavke, sporne, opts["izvestaj"])
            self.stdout.write(f"Izveštaj: {opts['izvestaj']}")
        if opts["samo_izvestaj"]:
            return
        verzija = lista.uvezi(stavke, naziv=opts["naziv"] or putanja.stem, datum_donosenja=datum,
                              izvor=putanja.name, aktivna=opts["aktivna"])
        self.stdout.write(self.style.SUCCESS(
            f"Uvezena verzija „{verzija.naziv}” (id {verzija.pk}){' — aktivna' if verzija.aktivna else ''}."))
