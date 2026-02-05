from django.core.management.base import BaseCommand
from ...selenium_integrations import kerio_login

class Command(BaseCommand):
    help = 'Učitavanje transakcija NIS iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        kerio_login()