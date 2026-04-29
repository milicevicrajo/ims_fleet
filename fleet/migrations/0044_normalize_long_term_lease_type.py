from django.db import migrations, models


OLD_LONG_TERM_LEASE_TYPE_VALUES = (
    "dugoro\u010dni",
    "dugoro\u010dnI",
    "dugoro\u00c4\u008dni",
    "dugoro\u00c4\u008dnI",
)
NORMALIZED_LONG_TERM_LEASE_TYPE = "dugorocni"


def normalize_long_term_lease_type(apps, schema_editor):
    Lease = apps.get_model("fleet", "Lease")
    Lease.objects.filter(lease_type__in=OLD_LONG_TERM_LEASE_TYPE_VALUES).update(
        lease_type=NORMALIZED_LONG_TERM_LEASE_TYPE
    )


def restore_legacy_long_term_lease_type(apps, schema_editor):
    Lease = apps.get_model("fleet", "Lease")
    Lease.objects.filter(lease_type=NORMALIZED_LONG_TERM_LEASE_TYPE).update(
        lease_type="dugoro\u010dnI"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0043_alter_vehicletravelorder_created_at"),
    ]

    operations = [
        migrations.RunPython(
            normalize_long_term_lease_type,
            restore_legacy_long_term_lease_type,
        ),
        migrations.AlterField(
            model_name="lease",
            name="lease_type",
            field=models.CharField(
                choices=[
                    ("finansijski", "Finansijski"),
                    ("operativni", "Operativni"),
                    (NORMALIZED_LONG_TERM_LEASE_TYPE, "Dugoro\u010dni najam"),
                ],
                default="finansijski",
                max_length=20,
                verbose_name="Vrsta lizinga",
            ),
        ),
    ]
