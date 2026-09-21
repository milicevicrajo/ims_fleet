from django.db import migrations, models


def classify_existing_amounts(apps, schema_editor):
    Lease = apps.get_model('fleet', 'Lease')
    rows = Lease.objects.using(schema_editor.connection.alias)
    # Existing entry forms document these meanings; explicitly adopted 21.09.2026.
    rows.filter(payment_basis='', lease_type='operativni').update(payment_basis='total')
    rows.filter(payment_basis='', lease_type__in=['dugorocni', 'dugoročni', 'dugoročnI']).update(payment_basis='monthly')
    # Financial lease principal is not an operating expense; do not reinterpret it.


class Migration(migrations.Migration):
    dependencies = [('fleet', '0077_vehicletravelorder_job_code_leasechargeperiod_and_more')]
    operations = [
        migrations.AddField(model_name='lease', name='payment_basis', field=models.CharField(blank=True, choices=[('', 'Nije određeno'), ('monthly', 'Mesečni iznos'), ('total', 'Ukupan iznos ugovora')], default='', max_length=10, verbose_name='Značenje iznosa')),
        migrations.AlterField(model_name='lease', name='current_payment_amount', field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Iznos (RSD)')),
        migrations.AlterField(model_name='vehicleeconomicassessment', name='methodology_version', field=models.CharField(default='IMS-FLOTA-2.1', editable=False, max_length=32)),
        migrations.RunPython(classify_existing_amounts, migrations.RunPython.noop),
    ]
