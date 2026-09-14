from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from hr.services.evaluations import import_evaluation_catalog


class Command(BaseCommand):
    help = 'Početni uvoz šifrarnika ocenjivanja; postojeće lokalne izmene ostaju sačuvane.'

    def add_arguments(self, parser):
        parser.add_argument('file')

    def handle(self, *args, **options):
        try:
            result = import_evaluation_catalog(options['file'])
        except (ValidationError, ValueError, KeyError, OSError) as exc:
            raise CommandError('Uvoz šifrarnika nije uspeo: '+('; '.join(exc.messages) if isinstance(exc,ValidationError) else 'Proverite datoteku i strukturu listova.')) from exc
        self.stdout.write(str(result))
