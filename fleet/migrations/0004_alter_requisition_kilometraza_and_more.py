# Generated by Django 5.0.9 on 2024-12-07 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fleet', '0003_alter_requisition_kilometraza_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisition',
            name='kilometraza',
            field=models.IntegerField(default=0, verbose_name='Kilometraža'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='requisition',
            name='nije_garaza',
            field=models.BooleanField(default=0, verbose_name='Nije garaža'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='servicetransaction',
            name='kilometraza',
            field=models.IntegerField(default=0, verbose_name='Kilometraža'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='servicetransaction',
            name='nije_garaza',
            field=models.BooleanField(default=0, verbose_name='Nije garaža'),
            preserve_default=False,
        ),
    ]
