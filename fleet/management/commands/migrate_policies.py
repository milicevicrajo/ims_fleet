from django.core.management.base import BaseCommand

from fleet.sync.external import fetch_policy_data


class Command(BaseCommand):
    help = "Sinhronizuje polise iz nabavka_invoice u fleet_policy."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=None, help="Povuci fakture iz poslednjih N dana.")
        parser.add_argument(
            "--last-24-hours",
            action="store_true",
            help="Povuci samo fakture od danasnjeg datuma.",
        )

    def handle(self, *args, **options):
        result = fetch_policy_data(
            last_24_hours=options["last_24_hours"],
            days=options["days"],
        )
        if result.startswith("Critical error:"):
            raise RuntimeError(result)
        self.stdout.write(self.style.SUCCESS(result))
