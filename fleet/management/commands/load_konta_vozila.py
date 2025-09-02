from django.core.management.base import BaseCommand
from django.db import transaction
from fleet.models import KontaVozila  # prilagodi import ako je druga app

DATA = [
    ("53940", "Naknade za koriscenje autoputa"),
    ("53950", "Troskovi registracije vozila"),
    ("51300", "Utroseni naftni derivati"),
    ("53160", "Troskovi taxi i renta- car usluga"),
    ("53210", "Troskovi tekuceg odrzavanja automobila"),
    ("56220", "Kamate za lizing"),
    ("51460", "Troškovi za gume"),
    ("51210", "Utros.rez.delovi za tek.i invest.odrz.osnov.sred."),
    ("53311", "Zakupnina opreme"),
]

class Command(BaseCommand):
    help = "Popunjava tabelu KontaVozila osnovnim kontima."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Alias baze (podrazumevano: default).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Obriši postojeće zapise pre upisa.",
        )

    def handle(self, *args, **opts):
        db = opts["database"]
        qs = KontaVozila.objects.using(db)

        created = 0
        updated = 0

        with transaction.atomic(using=db):
            if opts["reset"]:
                deleted = qs.all().delete()[0]
                self.stdout.write(self.style.WARNING(f"Izbrisano: {deleted}"))

            for knt, naz in DATA:
                obj, is_created = qs.update_or_create(
                    knt=knt,
                    defaults={"naz_knt": naz},
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Gotovo. Kreirano: {created}, ažurirano: {updated} (baza: {db})."
        ))
