# fleet/management/commands/fetch_trebovanja.py
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from fleet.models import DraftRequisition, Requisition

DEFAULT_SOURCE_ALIAS = "test_db"
DEFAULT_TARGET_ALIAS = "server_db"
DEFAULT_SOURCE_OBJECT = "dbo.trebovanja"  # promeni na "dbo.trebovanja" po potrebi


class Command(BaseCommand):
    help = (
        "Povlači stavke trebovanja iz izvora (test_db) i upisuje u DraftRequisition na odredištu (server_db). "
        "Preskače duplikate (ako već postoji u Requisition ili DraftRequisition na targetu)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-alias",
            default=DEFAULT_SOURCE_ALIAS,
            help=f"Alias izvora iz settings.DATABASES (default: {DEFAULT_SOURCE_ALIAS})",
        )
        parser.add_argument(
            "--target-alias",
            default=DEFAULT_TARGET_ALIAS,
            help=f"Alias odredišta iz settings.DATABASES (default: {DEFAULT_TARGET_ALIAS})",
        )
        parser.add_argument(
            "--source-object",
            default=DEFAULT_SOURCE_OBJECT,
            help=f"SQL objekat iz kojeg se čita (default: {DEFAULT_SOURCE_OBJECT}). "
                 f"Stavi 'dbo.trebovanja' ako čitaš iz tabele.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="(Opcionalno) Dummy filter po danima (izvor nema datum u SELECT-u; zadržano radi kompatibilnosti).",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Ignoriše vremensko filtriranje (ionako nema datuma u SELECT-u).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ne upisuje ništa na odredištu; samo prikaže koliko bi se redova obradilo.",
        )

    def handle(self, *args, **opts):
        source_alias = opts["source_alias"]
        target_alias = opts["target_alias"]
        source_object = opts["source_object"]
        days = opts["days"]
        dry_run = opts["dry_run"]

        # Provera da aliasi postoje u settings.DATABASES
        for alias in (source_alias, target_alias):
            if alias not in connections.databases:
                raise CommandError(f"DB alias '{alias}' nije definisan u settings.DATABASES")

        self.stdout.write(self.style.NOTICE(
            f"Izvor: {source_alias} → Odredište: {target_alias}\n"
            f"Izvorni objekat: {source_object}\n"
            f"Filter: {'(nema)' if opts.get('all') or days is None else f'days={days}'}  Dry-run: {dry_run}"
        ))

        # Sastavi SELECT (isti redosled kolona kao u tvojoj funkciji)
        query = f"""
            SELECT
                sif_pred,         -- 0
                god,              -- 1
                br_dok,           -- 2
                sif_vrsart,       -- 3
                stavka,           -- 4
                sif_art,          -- 5
                naz_art,          -- 6
                kol,              -- 7
                cena,             -- 8
                vrednost_nab,     -- 9
                napomena          -- 10
            FROM {source_object}
        """

        # Nema realnog datuma u SELECT-u, ostavljamo dummy deo samo ako baš hoćeš da proslediš --days
        if days is not None and not opts.get("all"):
            query += f" WHERE GETDATE() - {int(days)} > '2000-01-01'"

        # Čitanje iz izvora
        with connections[source_alias].cursor() as src_cur:
            src_cur.execute(query)
            rows = src_cur.fetchall()

        self.stdout.write(self.style.SUCCESS(f"Povučeno redova: {len(rows)}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run je uključen — nema upisa na odredištu."))
            return

        created = 0
        skipped_existing = 0
        bad_rows = 0

        # Upis na target (server_db)
        for idx, row in enumerate(rows, start=1):
            try:
                if len(row) < 11:
                    bad_rows += 1
                    continue

                sif_pred = row[0] or None
                god = row[1] or None
                br_dok = row[2]
                sif_vrsart = row[3] or None
                stavka = row[4]
                sif_art = row[5]
                naz_art = row[6] or None

                # konverzije
                kol = float(row[7]) if row[7] is not None else None
                cena = float(row[8]) if row[8] is not None else None
                vrednost_nab = float(row[9]) if row[9] is not None else None
                napomena = row[10] or None

                # duplikat-check na TARGET-u (server_db)
                exists_in_main = (
                    Requisition.objects.using(target_alias)
                    .filter(br_dok=br_dok, sif_art=sif_art, stavka=stavka)
                    .exists()
                )
                exists_in_draft = (
                    DraftRequisition.objects.using(target_alias)
                    .filter(br_dok=br_dok, sif_art=sif_art, stavka=stavka)
                    .exists()
                )

                if exists_in_main or exists_in_draft:
                    skipped_existing += 1
                    continue

                DraftRequisition.objects.using(target_alias).create(
                    sif_pred=sif_pred,
                    god=god,
                    br_dok=br_dok,
                    sif_vrsart=sif_vrsart,
                    stavka=stavka,
                    sif_art=sif_art,
                    naz_art=naz_art,
                    kol=kol,
                    cena=cena,
                    vrednost_nab=vrednost_nab,
                    napomena=napomena,
                )
                created += 1

            except Exception as ex:
                bad_rows += 1
                self.stderr.write(f"[{idx}] Greška: {ex}")

        self.stdout.write(self.style.SUCCESS(
            f"Gotovo. Kreirano: {created}, preskočeno (postojeće): {skipped_existing}, neispravni redovi: {bad_rows}"
        ))
