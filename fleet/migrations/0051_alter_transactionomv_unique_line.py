from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0050_alter_transactionomv_unique_constraint"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="transactionomv",
            name="unique_license_plate_transaction_with_voucher",
        ),
        migrations.AddConstraint(
            model_name="transactionomv",
            constraint=models.UniqueConstraint(
                fields=("license_plate_no", "transaction_date", "product_inv", "voucher", "quantity", "gross_cc"),
                name="unique_omv_transaction_line",
            ),
        ),
    ]
