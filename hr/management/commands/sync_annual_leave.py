import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from hr.services.annual_leave import sync_annual_leave


class Command(BaseCommand):
    help = 'Sinhronizuje IMS dodelu i rešenja godišnjih odmora iz Godmor/GodmorKor.'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, help='Godina prava; bez argumenta učitava celu istoriju.')
        parser.add_argument('--dry-run', action='store_true', help='Provera uz povrat svih lokalnih izmena.')

    def handle(self, *args, **options):
        try:
            result = sync_annual_leave(year=options['year'], dry_run=options['dry_run'])
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc
        except DatabaseError as exc:
            raise CommandError('Baza ili izvor godišnjih odmora nije dostupan. Sinhronizacija nije sačuvana.') from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False))
        if options['dry_run']:
            self.stdout.write('Provera: lokalne izmene nisu sačuvane.')
