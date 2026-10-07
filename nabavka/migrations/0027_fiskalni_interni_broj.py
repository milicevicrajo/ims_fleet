from django.db import migrations, models


class Migration(migrations.Migration):
    """Interni broj računa (Isplate → ostali fiskalni računi, 07.10.2026.)."""

    dependencies = [
        ('nabavka', '0026_fiskalni_bez_sifre_posla'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiskalniracun',
            name='interni_broj',
            field=models.CharField(blank=True, db_default='', default='', max_length=50, verbose_name='Interni broj računa'),
        ),
    ]
