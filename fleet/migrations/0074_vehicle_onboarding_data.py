from django.db import migrations


def copy_unambiguous_data(apps, schema_editor):
    alias = schema_editor.connection.alias
    Vehicle = apps.get_model('fleet', 'Vehicle')
    TrafficCard = apps.get_model('fleet', 'TrafficCard')
    Lease = apps.get_model('fleet', 'Lease')
    Holding = apps.get_model('fleet', 'VehicleHolding')
    # Preserve the old document values as evidence, including conflicts.
    for vehicle in Vehicle.objects.using(alias).all().iterator():
        values = {value.strip() for value in TrafficCard.objects.using(alias).filter(vehicle_id=vehicle.pk).values_list('homologation_number', flat=True) if value and value.strip()}
        if len(values) == 1 and not vehicle.homologation_number:
            Vehicle.objects.using(alias).filter(pk=vehicle.pk).update(homologation_number=values.pop())
        leases = list(Lease.objects.using(alias).filter(vehicle_id=vehicle.pk).order_by('start_date', 'pk'))
        # An invalid/overlapping history needs a person to reconcile it.
        if any(lease.end_date < lease.start_date for lease in leases):
            continue
        if any(right.start_date <= left.end_date for left, right in zip(leases, leases[1:])):
            continue
        for lease in leases:
            Holding.objects.using(alias).get_or_create(
                vehicle_id=vehicle.pk, lease_id=lease.pk,
                defaults={'basis': 'contract', 'start_date': lease.start_date, 'end_date': lease.end_date, 'evidence': 'Preneto iz postojeće evidencije lizinga / najma; proveriti datum preuzimanja.'},
            )
    # No inference of ownership, registration expiry, credit or market value.


class Migration(migrations.Migration):
    dependencies = [('fleet', '0073_vehicle_onboarding')]
    operations = [migrations.RunPython(copy_unambiguous_data, migrations.RunPython.noop)]
