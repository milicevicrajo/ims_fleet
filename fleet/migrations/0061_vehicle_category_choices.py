import unicodedata

from django.db import migrations, models


def _normalize(value):
    value = (value or "").strip().lower()
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    return " ".join(value.replace("-", " ").replace("_", " ").split())


def normalize_vehicle_categories(apps, schema_editor):
    Vehicle = apps.get_model("fleet", "Vehicle")

    for vehicle in Vehicle.objects.exclude(category__isnull=True).exclude(category=""):
        category = _normalize(vehicle.category)
        if "putnick" in category or category.startswith("putn"):
            normalized = "putnicko"
        elif "teret" in category:
            normalized = "teretno"
        elif "priklj" in category or "prikolic" in category or "poluprik" in category:
            normalized = "prikljucno"
        else:
            continue

        if vehicle.category != normalized:
            vehicle.category = normalized
            vehicle.save(update_fields=["category"])


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0060_putninalog_virman_generated_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_vehicle_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="vehicle",
            name="category",
            field=models.CharField(
                choices=[
                    ("putnicko", "Putničko vozilo"),
                    ("teretno", "Teretno vozilo"),
                    ("prikljucno", "Priključno vozilo"),
                ],
                max_length=50,
                verbose_name="Kategorija vozila",
            ),
        ),
    ]
