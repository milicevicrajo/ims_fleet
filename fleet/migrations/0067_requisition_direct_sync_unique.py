import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Count


REQUISITION_KEY_FIELDS = ["sif_pred", "god", "br_dok", "sif_vrsart", "stavka"]


def clean_text(value):
    return str(value or "").strip()


def normalize_and_dedupe_requisitions(apps, schema_editor):
    Requisition = apps.get_model("fleet", "Requisition")

    text_fields = ["br_dok", "sif_vrsart", "sif_art", "naz_art", "napomena"]
    for requisition in Requisition.objects.all().iterator(chunk_size=1000):
        changed_fields = []
        for field_name in text_fields:
            old_value = getattr(requisition, field_name)
            new_value = clean_text(old_value)
            if field_name == "napomena" and not new_value:
                new_value = None
            if old_value != new_value:
                setattr(requisition, field_name, new_value)
                changed_fields.append(field_name)
        if changed_fields:
            requisition.save(update_fields=changed_fields)

    duplicate_groups = (
        Requisition.objects.values(*REQUISITION_KEY_FIELDS)
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    for group in duplicate_groups:
        key_filter = {field: group[field] for field in REQUISITION_KEY_FIELDS}
        duplicates = list(Requisition.objects.filter(**key_filter).order_by("id"))
        if len(duplicates) < 2:
            continue

        keep = sorted(
            duplicates,
            key=lambda item: (
                item.vehicle_id is None,
                item.popravka_kategorija_id is None,
                item.kilometraza is None,
                item.kvar_id is None,
                item.id,
            ),
        )[0]
        Requisition.objects.filter(pk__in=[item.pk for item in duplicates if item.pk != keep.pk]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0066_update_fuel_consumption_unique_constraint"),
    ]

    operations = [
        migrations.AlterField(
            model_name="requisition",
            name="vehicle",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="requisitions",
                to="fleet.vehicle",
                verbose_name="Vozilo",
            ),
        ),
        migrations.AlterField(
            model_name="requisition",
            name="nije_garaza",
            field=models.BooleanField(default=False, verbose_name="Nije garaža"),
        ),
        migrations.RunPython(normalize_and_dedupe_requisitions, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="requisition",
            constraint=models.UniqueConstraint(
                fields=("sif_pred", "god", "br_dok", "sif_vrsart", "stavka"),
                name="uniq_requisition_source_line",
            ),
        ),
    ]
