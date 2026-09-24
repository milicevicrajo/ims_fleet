from django.core.management.base import BaseCommand
from django.db import transaction

from core.permissions import sync_pravna_resenja_permissions


class Command(BaseCommand):
    help = 'Dopunjava Pravnu službu, rešenja Sekretarijata i objedinjenu ulogu Kadrovi.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Prikaži dopune bez čuvanja.')

    @transaction.atomic
    def handle(self, *args, **options):
        result = sync_pravna_resenja_permissions()
        self.stdout.write(f"Novi kodovi dozvola: {result['created']}")
        for slug, count in result['grants'].items():
            self.stdout.write(f'{slug}: +{count} dozvola')
        if options['dry_run']:
            transaction.set_rollback(True)
            self.stdout.write('Probni prikaz — izmene nisu sačuvane.')
        else:
            self.stdout.write(self.style.SUCCESS('Dozvole su dopunjene.'))
