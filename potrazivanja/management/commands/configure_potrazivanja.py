from django.core.management.base import BaseCommand
from potrazivanja.permissions import configure_permissions


class Command(BaseCommand):
    help = "Registruje dozvole Potraživanja bez menjanja stare Naplate."

    def handle(self, *args, **options):
        configure_permissions()
        self.stdout.write("Potraživanja: dozvole registrovane; pristup Naplati ostaje nepromenjen.")
