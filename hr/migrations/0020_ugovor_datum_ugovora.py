from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0019_ugovori_zaposlenih'),
    ]

    operations = [
        migrations.AddField(
            model_name='ugovorzaposlenog',
            name='datum_ugovora',
            field=models.DateField(blank=True, null=True, verbose_name='Datum ugovora'),
        ),
    ]
