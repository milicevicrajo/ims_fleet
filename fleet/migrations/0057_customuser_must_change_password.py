from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0056_employee_display_name_overrides"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="must_change_password",
            field=models.BooleanField(default=False, verbose_name="Mora promeniti lozinku"),
        ),
    ]
