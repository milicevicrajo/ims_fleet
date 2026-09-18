from django.db import migrations


RULES = [
    ("not_due", "Nedospelo", None, 0, 0, "Bez aktivnosti"),
    ("days_1_30", "Kašnjenje 1–30 dana", 1, 30, 1, "Telefonski poziv"),
    ("days_31_45", "Kašnjenje 31–45 dana", 31, 45, 2, "Telefonski poziv ili pozivno pismo"),
    ("days_46_60", "Kašnjenje 46–60 dana", 46, 60, 3, "Pozivno pismo"),
    ("days_61_90", "Kašnjenje 61–90 dana", 61, 90, 4, "Opomena"),
    ("days_91_180", "Kašnjenje 91–180 dana", 91, 180, 5, "Opomena"),
    ("over_180", "Kašnjenje preko 180 dana", 181, None, 6, "Predlog za tužbu"),
]


def seed(apps, schema_editor):
    rule = apps.get_model("potrazivanja", "AgingRule")
    for code, name, minimum, maximum, order, action in RULES:
        rule.objects.using(schema_editor.connection.alias).get_or_create(code=code, defaults={
            "name": name, "min_days": minimum, "max_days": maximum,
            "sort_order": order, "suggested_action": action,
        })


def unseed(apps, schema_editor):
    apps.get_model("potrazivanja", "AgingRule").objects.using(schema_editor.connection.alias).filter(
        code__in=[row[0] for row in RULES],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("potrazivanja", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
