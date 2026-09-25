from django.db import migrations, models
import django.db.models.deletion


def proveri_veze(apps, schema_editor):
    resenja = apps.get_model('hr', 'Resenje').objects.using(schema_editor.connection.alias)
    if resenja.filter(zahtev__isnull=True).exists() or resenja.values('zahtev').annotate(
            broj=models.Count('pk')).filter(broj__gt=1).exists():
        raise RuntimeError('Pre migracije napravite rezervni izvoz i razrešite rešenja bez zahteva ili duple veze.')


class Migration(migrations.Migration):
    dependencies = [('hr', '0017_zahtevi_sifrarnik_i_dozvole')]
    operations = [
        migrations.RunPython(proveri_veze, migrations.RunPython.noop),
        migrations.AlterField(model_name='resenje', name='zahtev', field=models.ForeignKey(
            on_delete=django.db.models.deletion.PROTECT, related_name='resenja', to='hr.zahtev', verbose_name='Zahtev')),
        migrations.AlterField(model_name='resenje', name='broj', field=models.CharField(max_length=40,
            verbose_name='Broj rešenja', help_text='Rešenje dobija broj automatski, kao podbroj zahteva (npr. 43-17/1).')),
        migrations.AddConstraint(model_name='resenje', constraint=models.UniqueConstraint(
            fields=('zahtev',), name='hr_resenje_jedan_po_zahtevu')),
    ]
