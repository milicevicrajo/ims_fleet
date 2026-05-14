from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ugovori", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partner",
            name="partner_type",
            field=models.CharField(
                choices=[
                    ("legal_entity", "Pravno lice"),
                    ("person", "Fizicko lice"),
                    ("bank", "Banka"),
                ],
                db_index=True,
                default="legal_entity",
                max_length=20,
                verbose_name="Tip partnera",
            ),
        ),
    ]
