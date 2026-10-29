"""Lokalna kopija šifarnika banaka (`BankaPartner`) i zajednički zapis preuzimanja za NBS i šifarnik."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finansije', '0011_bankarske_grupe_pocetno'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name='NbsPreuzimanje', new_name='BankePreuzimanje'),
        migrations.AddField(
            model_name='bankepreuzimanje',
            name='izvor',
            field=models.CharField(choices=[('nbs', 'NBS'), ('sifarnik', 'Šifarnik partnera')], default='nbs', max_length=10),
        ),
        migrations.CreateModel(
            name='BankaPartner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.PositiveIntegerField(default=1)),
                ('sifra', models.PositiveIntegerField()),
                ('naziv', models.CharField(max_length=255)),
                ('pib', models.CharField(blank=True, max_length=13)),
                ('maticni_broj', models.CharField(blank=True, max_length=13)),
                ('podaci', models.JSONField(default=dict)),
                ('u_izvoru', models.BooleanField(default=True)),
                ('preuzeto', models.DateTimeField()),
                ('promenjeno', models.DateTimeField(blank=True, null=True)),
                ('nestala', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(blank=True, choices=[('', 'Automatski (po NBS spisku i prometu)'), ('aktivna', 'Aktivna banka'), ('istorijska', 'Istorijska — ne koristi se'), ('nije_banka', 'Nije banka (npr. Uprava za trezor)')], max_length=12, verbose_name='Status')),
                ('namena', models.CharField(blank=True, choices=[('', '—'), ('glavni', 'Glavni račun'), ('bolovanja', 'Račun za bolovanja'), ('namenski', 'Namenski račun'), ('ostalo', 'Ostalo')], max_length=12, verbose_name='Namena šifre')),
                ('napomena', models.CharField(blank=True, max_length=255, verbose_name='Napomena')),
                ('izmenjeno', models.DateTimeField(blank=True, null=True)),
                ('glavna', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dodatne', to='finansije.bankapartner', verbose_name='Glavna šifra iste banke')),
                ('izmenio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['sifra'],
            },
        ),
        migrations.AddConstraint(
            model_name='bankapartner',
            constraint=models.UniqueConstraint(fields=('company', 'sifra'), name='fin_banka_partner'),
        ),
    ]
