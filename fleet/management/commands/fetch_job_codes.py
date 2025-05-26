from django.core.management.base import BaseCommand
from ...utils import sync_organizational_units_from_view
class Command(BaseCommand):
    help = 'Učitavanje podataka o vozilima iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        sync_organizational_units_from_view()