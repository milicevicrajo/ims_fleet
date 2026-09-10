"""Read-only audit before and after the onboarding migrations."""
from django.core.management.base import BaseCommand
from django.db.models import Count
from fleet.models import Vehicle, TrafficCard, Lease


class Command(BaseCommand):
    help = 'Provera šasija, tablica, homologacije i ugovora bez izmene podataka.'

    def handle(self, *args, **options):
        counters = {'homologation_conflicts': 0, 'without_lease_ownership_unknown': 0, 'lease_period_conflicts': 0, 'blank_inventory': 0}
        for vehicle in Vehicle.objects.only('id', 'inventory_number').iterator():
            values = {v.strip() for v in TrafficCard.objects.filter(vehicle_id=vehicle.pk).values_list('homologation_number', flat=True) if v and v.strip()}
            if len(values) > 1:
                counters['homologation_conflicts'] += 1
                self.stdout.write(f'Vehicle {vehicle.pk}: različiti homologacioni brojevi na dokumentima.')
            leases = list(Lease.objects.filter(vehicle_id=vehicle.pk).only('id', 'vehicle_id', 'start_date', 'end_date').order_by('start_date', 'pk'))
            if not leases:
                counters['without_lease_ownership_unknown'] += 1
            if any(x.end_date < x.start_date for x in leases) or any(b.start_date <= a.end_date for a, b in zip(leases, leases[1:])):
                counters['lease_period_conflicts'] += 1
                self.stdout.write(f'Vehicle {vehicle.pk}: proveriti periode ugovora.')
            if not vehicle.inventory_number:
                counters['blank_inventory'] += 1
        ambiguous = TrafficCard.objects.order_by().values('registration_number').annotate(vehicles=Count('vehicle_id', distinct=True)).filter(vehicles__gt=1).count()
        self.stdout.write(f'Registarske oznake povezane sa više vozila: {ambiguous}')
        for key, value in counters.items():
            self.stdout.write(f'{key}: {value}')
        self.stdout.write('Postojeće valid_until vrednosti nisu dokaz datuma isteka registracije. Bez automatskog zaključivanja vlasništva.')
