import json
import sys
from django.core.management.base import BaseCommand, CommandError
from potrazivanja.services.sync import sync_collections


class Command(BaseCommand):
    help = "Puna sinhronizacija Potraživanja i poređenje sa starom Naplatom."

    def handle(self, *args, **options):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        try:
            run = sync_collections(trigger="import", progress=lambda message: self.stdout.write(message))
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps({"run_id": run.pk, "counts": run.source_counts,
                                      "controls": run.control_totals}, ensure_ascii=False, indent=2))
