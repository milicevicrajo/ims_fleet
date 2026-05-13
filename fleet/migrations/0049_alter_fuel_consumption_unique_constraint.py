from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0048_remove_insurance_goddada"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="fuelconsumption",
            name="unique_fuel_consumption",
        ),
        migrations.AddConstraint(
            model_name="fuelconsumption",
            constraint=models.UniqueConstraint(
                fields=("vehicle", "supplier", "date", "cost_bruto", "amount"),
                name="unique_fuel_consumption_per_vehicle",
            ),
        ),
    ]
