from django.db import migrations, models
from django.db.models import Count


def dedupe_fuel_consumption(apps, schema_editor):
    FuelConsumption = apps.get_model("fleet", "FuelConsumption")
    TransactionOMV = apps.get_model("fleet", "TransactionOMV")

    duplicate_groups = (
        FuelConsumption.objects.values("vehicle_id", "supplier", "date", "amount", "fuel_type")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    for group in duplicate_groups:
        rows = list(
            FuelConsumption.objects.filter(
                vehicle_id=group["vehicle_id"],
                supplier=group["supplier"],
                date=group["date"],
                amount=group["amount"],
                fuel_type=group["fuel_type"],
            ).order_by("-id")
        )
        if len(rows) < 2:
            continue

        keep = None
        if group["supplier"] == "OMV":
            source_gross_values = set(
                TransactionOMV.objects.filter(
                    vehicle_id=group["vehicle_id"],
                    transaction_date=group["date"],
                    quantity=group["amount"],
                    product_inv=group["fuel_type"],
                ).values_list("gross_cc", flat=True)
            )
            keep = next((row for row in rows if row.cost_bruto in source_gross_values), None)

        if keep is None:
            keep = next((row for row in rows if row.cost_bruto != row.cost_neto), rows[0])

        FuelConsumption.objects.filter(id__in=[row.id for row in rows if row.id != keep.id]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0065_putninalog_isplaceno"),
    ]

    operations = [
        migrations.RunPython(dedupe_fuel_consumption, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="fuelconsumption",
            name="unique_fuel_consumption_per_vehicle",
        ),
        migrations.AddConstraint(
            model_name="fuelconsumption",
            constraint=models.UniqueConstraint(
                fields=("vehicle", "supplier", "date", "amount", "fuel_type"),
                name="unique_fuel_consumption_per_vehicle",
            ),
        ),
    ]
