from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from fleet.models import VehicleTravelOrder


class Command(BaseCommand):
    help = "Prijavljuje i cisti deterministicke konflikte u zaduzenjima vozila."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Upisuje izmene. Bez ovoga komanda radi dry-run.",
        )

    def handle(self, *args, **options):
        execute = options["execute"]
        self.write("REZIM: %s" % ("EXECUTE" if execute else "DRY-RUN"))

        with transaction.atomic():
            deleted = self.delete_same_employee_vehicle_day_duplicates(execute)
            closed_vehicle = self.close_open_vehicle_chains(execute)
            report = self.conflict_report()
            if not execute:
                transaction.set_rollback(True)

        self.write("")
        self.write("PREDLOZENO/URADJENO")
        self.write(f"  obrisani duplikati isti covek+auto+dan: {deleted}")
        self.write(f"  zatvoreni stariji otvoreni nalozi po autu: {closed_vehicle}")
        self.write("")
        self.write("PREOSTALI KONFLIKTI")
        for label, count in report["counts"].items():
            self.write(f"  {label}: {count}")
        for label, rows in report["examples"].items():
            if rows:
                self.write(f"  {label} primeri:")
                for row in rows:
                    self.write(f"    {row}")

    def write(self, message):
        self.stdout.write(str(message).encode("ascii", "replace").decode("ascii"))

    def delete_same_employee_vehicle_day_duplicates(self, execute):
        keys = (
            VehicleTravelOrder.objects.order_by()
            .values("employee_id", "vehicle_id", "created_at")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .values_list("employee_id", "vehicle_id", "created_at")
        )
        deleted = 0
        for employee_id, vehicle_id, created_at in keys:
            orders = list(
                VehicleTravelOrder.objects.filter(
                    employee_id=employee_id,
                    vehicle_id=vehicle_id,
                    created_at=created_at,
                ).order_by("pn_number", "id")
            )
            keep = orders[0]
            duplicates = orders[1:]
            deleted += len(duplicates)
            self.write(
                f"DUPLIKAT: cuvam PN {keep.pn_number}, brisem "
                f"{', '.join('PN %s' % order.pn_number for order in duplicates)}"
            )
            VehicleTravelOrder.objects.filter(pk__in=[order.pk for order in duplicates]).delete()
        return deleted

    def close_open_vehicle_chains(self, execute):
        vehicle_ids = (
            VehicleTravelOrder.objects.filter(closed_at__isnull=True)
            .order_by()
            .values("vehicle_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .values_list("vehicle_id", flat=True)
        )
        closed = 0
        for vehicle_id in vehicle_ids:
            orders = list(
                VehicleTravelOrder.objects.filter(vehicle_id=vehicle_id, closed_at__isnull=True)
                .select_related("vehicle", "employee")
                .order_by("created_at", "id")
            )
            for order, next_order in zip(orders, orders[1:]):
                update_fields = ["closed_at"]
                order.closed_at = next_order.created_at
                if order.end_mileage is None and next_order.start_mileage is not None:
                    order.end_mileage = next_order.start_mileage
                    update_fields.append("end_mileage")
                closed += 1
                self.write(
                    f"AUTO: zatvaram PN {order.pn_number} ({order.vehicle}) "
                    f"datumom PN {next_order.pn_number}: {next_order.created_at:%d.%m.%Y}"
                )
                order.save(update_fields=update_fields)
        return closed

    def conflict_report(self):
        counts = {
            "isti_auto_isti_dan": self.count_group_conflicts(["vehicle_id", "created_at"]),
            "vise_otvorenih_po_autu": self.count_group_conflicts(["vehicle_id"], open_only=True),
        }
        examples = {
            "isti_auto_isti_dan": self.example_same_day("vehicle_id", "vehicle"),
            "vise_otvorenih_po_autu": self.example_open("vehicle_id", "vehicle"),
        }
        return {"counts": counts, "examples": examples}

    def count_group_conflicts(self, fields, open_only=False):
        qs = VehicleTravelOrder.objects.all()
        if open_only:
            qs = qs.filter(closed_at__isnull=True)
        return (
            qs.order_by()
            .values(*fields)
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .count()
        )

    def example_same_day(self, group_field, label_attr):
        keys = list(
            VehicleTravelOrder.objects.order_by()
            .values(group_field, "created_at")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .values_list(group_field, "created_at")[:5]
        )
        return [self.format_orders(VehicleTravelOrder.objects.filter(**{group_field: key, "created_at": day}), label_attr) for key, day in keys]

    def example_open(self, group_field, label_attr):
        keys = list(
            VehicleTravelOrder.objects.filter(closed_at__isnull=True)
            .order_by()
            .values(group_field)
            .annotate(c=Count("id"))
            .filter(c__gt=1)
            .values_list(group_field, flat=True)[:5]
        )
        return [self.format_orders(VehicleTravelOrder.objects.filter(**{group_field: key, "closed_at__isnull": True}), label_attr) for key in keys]

    def format_orders(self, qs, label_attr):
        orders = list(qs.select_related("employee", "vehicle").order_by("created_at", "id"))
        label = getattr(orders[0], label_attr)
        parts = [
            f"PN {order.pn_number} {order.created_at:%d.%m.%Y}"
            f"-{order.closed_at:%d.%m.%Y}" if order.closed_at else f"PN {order.pn_number} {order.created_at:%d.%m.%Y}-otvoren"
            for order in orders
        ]
        return f"{label}: {', '.join(parts)}"
