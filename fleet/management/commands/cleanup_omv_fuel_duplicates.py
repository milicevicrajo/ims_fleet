from django.core.management.base import BaseCommand

from fleet.support.fuel_cleanup import cleanup_omv_fuel_data


class Command(BaseCommand):
    help = "Cisti duple i neispravne OMV redove goriva."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Primeni brisanje. Bez ove opcije komanda radi samo pregled.",
        )
        parser.add_argument(
            "--vehicle-id",
            type=int,
            default=None,
            help="Opciono cisti samo jedno vozilo po ID-u.",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="Django DB alias koji se cisti.",
        )

    def handle(self, *args, **options):
        result = cleanup_omv_fuel_data(
            apply=options["apply"],
            using=options["database"],
            vehicle_id=options["vehicle_id"],
        )

        mode = "APPLY" if result["apply"] else "DRY-RUN"
        self.stdout.write(f"OMV fuel cleanup {mode} database={result['using']}")
        if result["vehicle_id"]:
            self.stdout.write(f"vehicle_id={result['vehicle_id']}")
        self.stdout.write(f"stale_omv_transactions={result['stale_omv_transactions']}")
        self.stdout.write(f"duplicate_omv_transactions={result['duplicate_omv_transactions']}")
        self.stdout.write(f"omv_transactions_to_delete={result['omv_transactions_to_delete']}")
        self.stdout.write(
            "fuel_consumptions_from_deleted_transactions="
            f"{result['fuel_consumptions_from_deleted_transactions']}"
        )
        self.stdout.write(f"non_fuel_consumptions={result['non_fuel_consumptions']}")
        self.stdout.write(
            f"orphan_duplicate_fuel_consumptions={result['orphan_duplicate_fuel_consumptions']}"
        )
        self.stdout.write(f"fuel_consumptions_to_delete={result['fuel_consumptions_to_delete']}")
        self.stdout.write(f"deleted_omv_transactions={result['deleted_omv_transactions']}")
        self.stdout.write(f"deleted_fuel_consumptions={result['deleted_fuel_consumptions']}")
