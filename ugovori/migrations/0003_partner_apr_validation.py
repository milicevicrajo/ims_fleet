from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ugovori", "0002_partner_bank_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="partner",
            name="data_source",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=50,
                verbose_name="Izvor podataka",
            ),
        ),
        migrations.AddField(
            model_name="partner",
            name="data_validated",
            field=models.BooleanField(db_index=True, default=False, verbose_name="Podaci validni"),
        ),
        migrations.AddField(
            model_name="partner",
            name="data_validated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Datum validacije"),
        ),
        migrations.AddField(
            model_name="partner",
            name="apr_status",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="APR status"),
        ),
        migrations.AddField(
            model_name="partner",
            name="apr_checked_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="APR provera"),
        ),
    ]
