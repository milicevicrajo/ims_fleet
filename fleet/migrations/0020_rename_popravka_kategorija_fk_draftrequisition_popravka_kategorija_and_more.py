# Generated by Django 5.0.9 on 2025-03-20 10:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fleet', '0019_remove_draftrequisition_popravka_kategorija_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='draftrequisition',
            old_name='popravka_kategorija_fk',
            new_name='popravka_kategorija',
        ),
        migrations.RenameField(
            model_name='draftservicetransaction',
            old_name='popravka_kategorija_fk',
            new_name='popravka_kategorija',
        ),
        migrations.RenameField(
            model_name='requisition',
            old_name='popravka_kategorija_fk',
            new_name='popravka_kategorija',
        ),
        migrations.RenameField(
            model_name='servicetransaction',
            old_name='popravka_kategorija_fk',
            new_name='popravka_kategorija',
        ),
    ]
