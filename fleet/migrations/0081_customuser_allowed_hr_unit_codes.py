from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('fleet', '0080_employee_full_name_cyrillic')]
    operations = [migrations.AddField(
        model_name='customuser', name='allowed_hr_unit_codes',
        field=models.JSONField(blank=True, default=list, verbose_name='Dozvoljene kadrovske OJ'),
    )]
