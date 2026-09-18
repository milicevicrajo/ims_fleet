import json
import sys
from django.core.management.base import BaseCommand, CommandError
from potrazivanja.services.independence import initialize_independent_operations


class Command(BaseCommand):
    help = 'Završni prenos, uređivanje kontakata i aktiviranje samostalnih unosa Potraživanja.'

    def handle(self, *args, **options):
        if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
        try:
            result = initialize_independent_operations(progress=self.stdout.write)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
