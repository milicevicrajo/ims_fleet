from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nabavka", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="procurementcase",
            name="is_garage",
            field=models.BooleanField(default=False, verbose_name="Garaža"),
        ),
    ]
