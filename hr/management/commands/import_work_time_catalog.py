from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand,CommandError
from hr.services.work_time_catalog import import_work_time_catalog,sync_employee_recipient_types


class Command(BaseCommand):
    help='Početno učitavanje elemenata RL; postojeće lokalne izmene ostaju sačuvane.'

    def add_arguments(self,parser):
        parser.add_argument('file')
        parser.add_argument('--sync-recipients',action='store_true')

    def handle(self,*args,**options):
        try:
            self.stdout.write(str(import_work_time_catalog(options['file'])))
            if options['sync_recipients']:
                self.stdout.write(str(sync_employee_recipient_types()))
        except (ValidationError,OSError) as exc:
            raise CommandError('; '.join(exc.messages) if isinstance(exc,ValidationError) else 'Datoteka nije dostupna.') from exc
