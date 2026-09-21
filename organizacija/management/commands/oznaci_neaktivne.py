from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from organizacija.services import activity


class Command(BaseCommand):
    help = (
        "Utvrdjuje koji poslovi nemaju obrt u posmatranom prozoru i gasi ih u registru. "
        "Cita finansijska knjizenja, pise iskljucivo u tabele aplikacije organizacija."
    )

    def add_arguments(self, parser):
        parser.add_argument("--firma", type=int, default=1)
        parser.add_argument("--meseci", type=int, default=activity.DEFAULT_MONTHS)
        parser.add_argument(
            "--proba",
            action="store_true",
            help="Samo prikazi sta bi se promenilo, bez ijednog upisa.",
        )

    def handle(self, *args, **options):
        company, months, proba = options["firma"], options["meseci"], options["proba"]
        try:
            if proba:
                summary = activity.summarize(activity.measure(company, months))
                result = activity.measure(company, months)
                summary["window_from"] = result["window_from"]
                summary["window_to"] = result["window_to"]
                summary["versions_changed"] = None
            else:
                summary = activity.apply_reviews(company, months)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self._print(summary, months, proba)

    def _print(self, summary, months, proba):
        self.stdout.write(
            f"Prozor {summary['window_from']} – {summary['window_to']} ({months} meseci)"
        )
        self.stdout.write(
            f"  poslova u stablu {summary['jobs']}; "
            f"sa obrtom {summary['with_turnover']}; bez obrta {summary['without_turnover']}"
        )
        self.stdout.write(
            self.style.WARNING(f"  gasi se: {len(summary['to_deactivate'])}")
            if summary["to_deactivate"]
            else "  gasi se: nijedan"
        )
        for item in summary["to_deactivate"][:20]:
            self.stdout.write(f"    {item['code']:<10} {item['name'][:48]}")
        if len(summary["to_deactivate"]) > 20:
            self.stdout.write(f"    ... jos {len(summary['to_deactivate']) - 20}")

        self.stdout.write(f"  vec neaktivni i bez obrta: {len(summary['already_inactive'])}")

        if summary["to_activate"]:
            self.stdout.write(
                self.style.SUCCESS(f"  pali se: {len(summary['to_activate'])}")
            )
            for item in summary["to_activate"]:
                self.stdout.write(
                    f"    {item['code']:<10} {item['name'][:34]:<34} "
                    f"{item['rows']} knjizenja, duguje {item['debit']}"
                )

        if summary["disagreements"]:
            self.stdout.write(
                f"  razilazenje sa izvornim sifarnikom: {len(summary['disagreements'])} "
                "(obrt je merodavan, ali razlika ostaje vidljiva)"
            )

        if proba:
            self.stdout.write(self.style.WARNING("PROBA — nista nije upisano."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Izmenjenih verzija: {summary['versions_changed']}")
            )
