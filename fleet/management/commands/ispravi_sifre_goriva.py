from django.core.management.base import BaseCommand
from django.db import transaction

from fleet.models import FuelConsumption
from fleet.support.assignments import DodeleVozila

BATCH = 500


class Command(BaseCommand):
    help = (
        "Ispravlja FuelConsumption.job_code na sifru dodele vazece na dan tocenja. Menja samo "
        "pogresne zapise; ispravne i one bez dodele na taj dan ne dira. Posle ispravke osvezava "
        "vezu sa registrom organizacije za gorivo."
    )

    def add_arguments(self, parser):
        parser.add_argument("--proba", action="store_true", help="Samo prikazi sta bi se promenilo.")

    def handle(self, *args, proba=False, **options):
        dodele = DodeleVozila()
        izmene, ispravno, bez_dodele, primeri = {}, 0, 0, []
        for pk, vozilo, kada, sifra in FuelConsumption.objects.values_list("pk", "vehicle_id", "date", "job_code"):
            tacna = dodele.sifra(vozilo, kada)
            if tacna is None:
                bez_dodele += 1
                continue
            if (sifra or "").strip() == tacna.strip():
                ispravno += 1
                continue
            izmene.setdefault(tacna, []).append(pk)
            if len(primeri) < 10:
                primeri.append((pk, kada, sifra, tacna))

        ukupno = sum(len(v) for v in izmene.values())
        self.stdout.write(f"ispravno {ispravno}; za ispravku {ukupno}; bez dodele na taj dan (ne dira se) {bez_dodele}")
        for pk, kada, stara, nova in primeri:
            self.stdout.write(f"  #{pk} {kada:%d.%m.%Y}: {stara or '-'} -> {nova}")
        if proba or not ukupno:
            self.stdout.write(self.style.WARNING("PROBA — nista nije upisano.") if proba else "Nema izmena.")
            return
        with transaction.atomic():
            for tacna, pks in izmene.items():
                for pocetak in range(0, len(pks), BATCH):
                    FuelConsumption.objects.filter(pk__in=pks[pocetak:pocetak + BATCH]).update(job_code=tacna)
        from organizacija.services import flota

        veze = flota.povezi(modeli=["gorivo"])[0]
        self.stdout.write(self.style.SUCCESS(
            f"Ispravljeno {ukupno}. Veza sa registrom za gorivo: promenjeno {veze['promenjeno']}, "
            f"postavljeno {veze['postavljeno']}."))
