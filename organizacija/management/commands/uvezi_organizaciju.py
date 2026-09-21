from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from organizacija.services.importer import run_import
from organizacija.services.report import build_report


class Command(BaseCommand):
    help = (
        "Uvozi sifarnik u centralni registar organizacije. Cita finansije i flotu, "
        "pise iskljucivo u tabele aplikacije organizacija. Ponovljivo."
    )

    def add_arguments(self, parser):
        parser.add_argument("--firma", type=int, default=1)
        parser.add_argument(
            "--proba",
            action="store_true",
            help="Izvrsi uvoz pa ponisti izmene; sluzi za proveru bez upisa.",
        )
        parser.add_argument(
            "--bez-flote",
            action="store_true",
            help="Ne povezuje fleet.OrganizationalUnit sa cvorovima.",
        )

    def handle(self, *args, **options):
        company = options["firma"]
        link_fleet = not options["bez_flote"]
        try:
            if options["proba"]:
                self._dry_run(company, link_fleet)
            else:
                run = run_import(company=company, link_fleet_units=link_fleet)
                self._print_run(run)
                self._print_report(build_report(company, run))
        except Exception as exc:
            raise CommandError(str(exc)) from exc

    def _dry_run(self, company, link_fleet):
        class Rollback(Exception):
            pass

        try:
            with transaction.atomic():
                run = run_import(company=company, link_fleet_units=link_fleet)
                self._print_run(run)
                self._print_report(build_report(company, run))
                raise Rollback
        except Rollback:
            self.stdout.write(self.style.WARNING("PROBA — sve izmene su ponistene."))

    def _print_run(self, run):
        self.stdout.write(self.style.SUCCESS(f"Uvoz {run.pk}: {run.status}"))
        self.stdout.write(
            f"  procitano {run.source_rows}; novih cvorova {run.nodes_created}; "
            f"novih verzija {run.versions_created}; nepromenjeno {run.unchanged}; "
            f"za razresenje {run.unresolved}"
        )
        for line in run.report.splitlines():
            self.stdout.write(f"  {line}")

    def _print_report(self, report):
        structure = report["structure"]
        self.stdout.write("")
        self.stdout.write("Struktura stabla:")
        self.stdout.write(
            f"  nivo 1: {structure['centers']}   nivo 2: {structure['units']}   "
            f"nivo 3: {structure['jobs']}"
        )
        self._warn_list("ponovljene pune sifre", structure["duplicate_codes"])
        self._warn_list("cvorovi bez ispravnog roditelja", structure["orphans"])
        self._warn_list("poslovi bez naziva", structure["jobs_without_name"])

        self.stdout.write("")
        self.stdout.write("Lista za razresenje po porodici:")
        for family, count in sorted(report["unresolved"].items()):
            self.stdout.write(f"  porodica {family}: {count}")

        ledger = report["ledger"]
        self.stdout.write("")
        self.stdout.write("Knjizenja — sta se razresava preko registra:")
        self.stdout.write(
            f"  ukupno redova {ledger['total_rows']}, razreseno {ledger['resolved_rows']}, "
            f"nerazreseno {ledger['unresolved_rows']}"
        )
        self.stdout.write(
            f"  duguje ukupno {ledger['total_debit']}, razreseno {ledger['resolved_debit']}, "
            f"nerazreseno {ledger['unresolved_debit']}"
        )
        self.stdout.write(
            f"  potrazuje ukupno {ledger['total_credit']}, razreseno {ledger['resolved_credit']}, "
            f"nerazreseno {ledger['unresolved_credit']}"
        )
        if ledger["unresolved"]:
            self.stdout.write("  najveci nerazreseni (sifra, redova, duguje):")
            for item in ledger["unresolved"][:12]:
                self.stdout.write(
                    f"    {item['job_code'] or '(prazno)':<12} {item['rows']:>7}  {item['debit']}"
                )
        if ledger["per_center"]:
            self.stdout.write("  po centru:")
            for center, values in sorted(ledger["per_center"].items()):
                self.stdout.write(
                    f"    {center:<4} redova {values['rows']:>7}  duguje {values['debit']}"
                )

    def _warn_list(self, label, values):
        if not values:
            self.stdout.write(f"  {label}: nema")
            return
        self.stdout.write(self.style.WARNING(f"  {label}: {len(values)} — {', '.join(values[:10])}"))
