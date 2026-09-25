"""Datum slave postaje jedno polje umesto dana i meseca.

Već upisani dan i mesec prenose se u datum sa godinom 2000 (prestupna, da prođe i 29. februar).
Godina se nigde ne koristi — slava se računa po danu i mesecu u svakoj godini.
"""
from datetime import date

from django.db import migrations, models


def prenesi(apps, schema_editor):
    Employee = apps.get_model('fleet', 'Employee')
    db = schema_editor.connection.alias
    for employee in Employee.objects.using(db).exclude(slava_dan__isnull=True).exclude(slava_mesec__isnull=True):
        try:
            employee.slava_datum = date(2000, employee.slava_mesec, employee.slava_dan)
        except ValueError:
            continue
        employee.save(update_fields=['slava_datum'])


def vrati(apps, schema_editor):
    Employee = apps.get_model('fleet', 'Employee')
    db = schema_editor.connection.alias
    for employee in Employee.objects.using(db).exclude(slava_datum__isnull=True):
        employee.slava_dan, employee.slava_mesec = employee.slava_datum.day, employee.slava_datum.month
        employee.save(update_fields=['slava_dan', 'slava_mesec'])


class Migration(migrations.Migration):

    dependencies = [
        ('fleet', '0082_employee_slava_datum'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='slava_datum',
            field=models.DateField(blank=True, help_text='Npr. Sveti Nikola: 19.12. Godina nije bitna. Ako je prazno, radna lista predlaže datum iz naziva slave.', null=True, verbose_name='Datum slave'),
        ),
        migrations.RunPython(prenesi, vrati),
        migrations.RemoveField(
            model_name='employee',
            name='slava_dan',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='slava_mesec',
        ),
    ]
