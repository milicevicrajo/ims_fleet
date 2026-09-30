import datetime

from django.core.management.base import BaseCommand, CommandError

from finansije.sef_models import SefFaktura
from finansije.services import sef


class Command(BaseCommand):
    help = ("Preuzima sa SEF-a PDF-ove koji nedostaju (fakture vec preuzete u aplikaciju). "
            "Bez parametara: sve fakture bez PDF-a.")

    def add_arguments(self, parser):
        parser.add_argument("--od", type=datetime.date.fromisoformat, help="Datum od (YYYY-MM-DD)")
        parser.add_argument("--do", type=datetime.date.fromisoformat, help="Datum do (YYYY-MM-DD)")
        parser.add_argument("--smer", choices=SefFaktura.Smer.values)
        parser.add_argument("--najvise", type=int, help="Najvise faktura u jednom pokretanju")

    def handle(self, *args, **opts):
        qs = sef.sa_datumom(SefFaktura.objects.filter(pdf=""))
        if opts["od"]:
            qs = qs.filter(datum_dok__gte=opts["od"])
        if opts["do"]:
            qs = qs.filter(datum_dok__lte=opts["do"])
        if opts["smer"]:
            qs = qs.filter(smer=opts["smer"])
        fakture = list(qs.order_by("-datum_dok", "-sef_id")[:opts["najvise"]] if opts["najvise"] else qs)
        self.stdout.write(f"Bez PDF-a: {len(fakture)} faktura. SEF prima 3 zahteva u sekundi — oko "
                          f"{max(1, round(len(fakture) * 0.8 / 60))} min.")
        try:
            brojaci = sef.preuzmi_pdfove(fakture)
        except (sef.SefNijePodesen, sef.SefGreska) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(sef.poruka_pdf(brojaci)))
