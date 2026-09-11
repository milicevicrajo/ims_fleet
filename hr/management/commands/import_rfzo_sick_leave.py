from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from hr.services.sick_leave import import_rfzo_workbook


class Command(BaseCommand):
    help = 'Uvoz RFZO bolovanja iz .xlsx datoteke; povezivanje zaposlenih po JMBG-u.'

    def add_arguments(self, parser):
        parser.add_argument('file')
        parser.add_argument('--source-date', required=True, help='Datum RFZO izvoza, YYYY-MM-DD')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        try:
            day=date.fromisoformat(options['source_date'])
            if day>timezone.localdate(): raise ValueError
            path=Path(options['file'])
            if path.suffix.lower()!='.xlsx': raise CommandError('Potreban je .xlsx dokument.')
            result=import_rfzo_workbook(path.read_bytes(),filename=path.name,
                source_date=day,dry_run=options['dry_run'])
        except (OSError,ValueError,ValidationError) as exc:
            message='; '.join(exc.messages) if isinstance(exc,ValidationError) else 'Proverite datoteku i datum izvora.'
            raise CommandError(message) from exc
        counts=result if isinstance(result,dict) else {key:getattr(result,key) for key in (
            'row_count','created_count','updated_count','unchanged_count','unlinked_count')}
        self.stdout.write(('Provera bez upisa: ' if options['dry_run'] else 'Uvezeno: ')+str(counts))
