import datetime

from django.core.management.base import BaseCommand, CommandError

from finansije.services import sef


class Command(BaseCommand):
    help = "Preuzima ulazne i izlazne fakture sa SEF-a (samo citanje). Bez parametara: poslednjih 45 dana."

    def add_arguments(self, parser):
        parser.add_argument("--od", type=datetime.date.fromisoformat, help="Datum od (YYYY-MM-DD)")
        parser.add_argument("--do", type=datetime.date.fromisoformat, help="Datum do (YYYY-MM-DD)")
        parser.add_argument("--provera", action="store_true", help="Samo proveri vezu i kljuc (verzija SEF-a)")

    def handle(self, *args, **opts):
        try:
            klijent = sef.Klijent()
            if opts["provera"]:
                self.stdout.write(f"SEF {klijent.url} odgovara, verzija {klijent.verzija()}.")
                return
            run = sef.sinhronizuj(opts["od"], opts["do"], klijent=klijent)
        except (sef.SefNijePodesen, sef.SefGreska, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(sef.poruka(run)))
