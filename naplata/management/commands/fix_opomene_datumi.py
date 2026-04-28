from django.core.management.base import BaseCommand
from django.db import OperationalError
from django.db import transaction
from django.db.models import Q

from naplata.models import Opomene


class Command(BaseCommand):
    help = (
        "Postavlja godinu na 2024 za polja 'datum' i 'god' u tabeli opomene "
        "gde je godina veca od 2026."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="server_db",
            help="DB alias iz settings.DATABASES (podrazumevano: server_db).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Samo prikazi koliko zapisa bi bilo izmenjeno, bez upisa u bazu.",
        )

    def handle(self, *args, **options):
        db_alias = options["database"]
        dry_run = options["dry_run"]

        queryset = Opomene.objects.using(db_alias).filter(
            Q(datum__year__gt=2026) | Q(god__gt=2026)
        )

        try:
            total = queryset.count()
        except OperationalError:
            self.stdout.write(
                self.style.ERROR(
                    f"Tabela 'opomene' nije dostupna na bazi '{db_alias}'. "
                    "Proveri DATABASES podešavanje i konekciju ka server bazi."
                )
            )
            return

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nema zapisa za izmenu."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] Pronadjeno {total} zapisa u opomene sa godinom > 2026 "
                    "(u polju 'datum' i/ili 'god')."
                )
            )
            return

        updated_rows = 0
        updated_datum = 0
        updated_god = 0

        with transaction.atomic(using=db_alias):
            for record in queryset.iterator(chunk_size=500):
                update_fields = []

                if record.datum and record.datum.year > 2026:
                    try:
                        record.datum = record.datum.replace(year=2024)
                    except ValueError:
                        record.datum = record.datum.replace(year=2024, day=28)
                    update_fields.append("datum")
                    updated_datum += 1

                if record.god and record.god > 2026:
                    record.god = 2024
                    update_fields.append("god")
                    updated_god += 1

                if update_fields:
                    record.save(using=db_alias, update_fields=update_fields)
                    updated_rows += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Uspesno izmenjeno {updated_rows} zapisa: 'datum' korigovan {updated_datum} puta, "
                f"'god' korigovan {updated_god} puta (na 2024)."
            )
        )
