"""Raspolaganje vozilom se vodi samo kroz ugovore o lizingu / najmu (05.10.2026.).

`VehicleHolding` je bio druga evidencija istog: zapisi „po ugovoru” su kopije ugovora (`Lease`), a
vlasništvo je i dalje „nema važećeg ugovora”. Jedino što ugovor nema — finansiranje nabavke — prelazi
na vozilo. `LeaseChargePeriod` je prazan i obračun ga nikad nije čitao.

Prenos pre brisanja:
- vlasništvo: finansiranje i ugovor o kreditu na vozilo; početak, ako datum nabavke nije upisan, postaje
  datum nabavke; dokument i napomena dopisuju se u opis vozila;
- po ugovoru: dokument / napomena koji nisu automatski tekst prenosa i period koji se razlikuje od
  ugovora dopisuju se u napomenu ugovora.

Povratak migracije vraća prazne tabele (podaci se ne vraćaju).
"""
import django.db.models.deletion
from django.db import migrations, models

AUTOMATSKI_TEKST = 'Preneto iz postojeće evidencije lizinga'


def _dopisi(postojece, *delovi):
    dodatak = ' · '.join(d.strip() for d in delovi if d and d.strip())
    if not dodatak:
        return postojece
    return '\n'.join(filter(None, [(postojece or '').rstrip(), dodatak]))


def prenesi(apps, schema_editor):
    db = schema_editor.connection.alias
    Holding = apps.get_model('fleet', 'VehicleHolding')
    Vehicle = apps.get_model('fleet', 'Vehicle')
    Lease = apps.get_model('fleet', 'Lease')
    vlasnistva = {}
    for zapis in Holding.objects.using(db).filter(basis='owned').order_by('start_date', 'pk'):
        vlasnistva[zapis.vehicle_id] = zapis  # poslednji po početku
    for vehicle_id, zapis in vlasnistva.items():
        vozilo = Vehicle.objects.using(db).get(pk=vehicle_id)
        if zapis.financing and not vozilo.financing:
            vozilo.financing = zapis.financing
        if zapis.financing_contract_id and not vozilo.financing_contract_id:
            vozilo.financing_contract_id = zapis.financing_contract_id
        if not vozilo.purchase_date:
            vozilo.purchase_date = zapis.start_date
        if zapis.evidence or zapis.note:
            vozilo.description = _dopisi(vozilo.description, 'Osnov raspolaganja (preneto 05.10.2026.)',
                                         zapis.evidence, zapis.note)
        vozilo.save(update_fields=['financing', 'financing_contract', 'purchase_date', 'description'])
    for zapis in Holding.objects.using(db).filter(basis='contract', lease__isnull=False).select_related('lease'):
        ugovor = zapis.lease
        dokaz = '' if (zapis.evidence or '').startswith(AUTOMATSKI_TEKST) else zapis.evidence
        period = ''
        if (zapis.start_date, zapis.end_date) != (ugovor.start_date, ugovor.end_date):
            kraj = zapis.end_date.strftime('%d.%m.%Y.') if zapis.end_date else 'do daljeg'
            period = f'Upisan osnov raspolaganja {zapis.start_date:%d.%m.%Y.} – {kraj}'
        if dokaz or zapis.note or period:
            ugovor.note = _dopisi(ugovor.note, 'Osnov raspolaganja (preneto 05.10.2026.)', dokaz, zapis.note, period)
            ugovor.save(update_fields=['note'])


class Migration(migrations.Migration):

    dependencies = [
        ('fleet', '0089_opomene_goriva'),
        ('ugovori', '0011_restore_contract_file_separation'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='financing',
            field=models.CharField(blank=True, choices=[('', 'Nije evidentirano'), ('own_funds', 'Sopstvena sredstva'), ('credit', 'Kredit')], default='', max_length=20, verbose_name='Finansiranje nabavke'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='financing_contract',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='financed_vehicles', to='ugovori.contract', verbose_name='Ugovor o finansiranju (kredit)'),
        ),
        migrations.RunPython(prenesi, migrations.RunPython.noop),
        migrations.DeleteModel(
            name='LeaseChargePeriod',
        ),
        migrations.DeleteModel(
            name='VehicleHolding',
        ),
    ]
