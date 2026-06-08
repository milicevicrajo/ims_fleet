from django.db import migrations, models
from django.db.models import Count


OMV_UNIQUE_FIELDS = (
    "license_plate_no",
    "transaction_date",
    "product_inv",
    "voucher",
    "quantity",
)


def dedupe_omv_transactions(apps, schema_editor):
    TransactionOMV = apps.get_model("fleet", "TransactionOMV")
    duplicate_groups = (
        TransactionOMV.objects.values(*OMV_UNIQUE_FIELDS)
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    for group in duplicate_groups.iterator():
        filters = {field: group[field] for field in OMV_UNIQUE_FIELDS}
        rows = TransactionOMV.objects.filter(**filters).order_by("-invoiced", "-invoice_date", "-id")
        keep_id = rows.values_list("id", flat=True).first()
        if keep_id:
            rows.exclude(id=keep_id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0057_customuser_must_change_password"),
    ]

    operations = [
        migrations.RunPython(dedupe_omv_transactions, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="transactionomv",
            name="unique_omv_transaction_line",
        ),
        migrations.AddConstraint(
            model_name="transactionomv",
            constraint=models.UniqueConstraint(
                fields=OMV_UNIQUE_FIELDS,
                name="unique_omv_transaction_line",
            ),
        ),
    ]
