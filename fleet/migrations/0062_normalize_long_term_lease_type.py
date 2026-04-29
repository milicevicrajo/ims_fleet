from django.db import migrations, models


def normalize_long_term_lease_type(apps, schema_editor):
    Lease = apps.get_model("fleet", "Lease")
    Lease.objects.filter(lease_type__in=["dugoročni", "dugoročnI"]).update(lease_type="dugorocni")


def restore_legacy_long_term_lease_type(apps, schema_editor):
    Lease = apps.get_model("fleet", "Lease")
    Lease.objects.filter(lease_type="dugorocni").update(lease_type="dugoročnI")


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0061_alter_vehicletravelorder_created_at"),
    ]

    operations = [
        migrations.RunPython(normalize_long_term_lease_type, restore_legacy_long_term_lease_type),
        migrations.AlterField(
            model_name="lease",
            name="lease_type",
            field=models.CharField(
                choices=[
                    ("finansijski", "Finansijski"),
                    ("operativni", "Operativni"),
                    ("dugorocni", "Dugoročni najam"),
                ],
                default="finansijski",
                max_length=20,
                verbose_name="Vrsta lizinga",
            ),
        ),
    ]
