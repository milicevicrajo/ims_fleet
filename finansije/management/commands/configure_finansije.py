from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from core.management.commands.sync_celery_periodic_tasks import EXPECTED_PERIODIC_TASKS
from core.permissions import sync_finance_permissions


class Command(BaseCommand):
    help = "Registruje samo dozvole finansija; opciono aktivira raspored posle restarta Celery radnika."

    def add_arguments(self, parser):
        parser.add_argument("--enable-schedule", action="store_true")
        parser.add_argument("--enable-nalog-z-schedule", action="store_true",
                            help="Aktivira samo osvežavanje nalog_z u 10:00 i 11:00.")

    def handle(self, *args, **options):
        codes = sync_finance_permissions()
        self.stdout.write(f"Registrovano {len(codes)} dozvola finansija. Dodele uloga korisnicima nisu menjane.")
        if options["enable_schedule"] or options["enable_nalog_z_schedule"]:
            for spec in EXPECTED_PERIODIC_TASKS:
                if not spec["task"].startswith("finansije."):
                    continue
                if not options["enable_schedule"] and spec["task"] != "finansije.tasks.refresh_nalog_z_task":
                    continue
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    hour=spec["hour"], minute=spec["minute"], day_of_week="*",
                    day_of_month="*", month_of_year="*", timezone=spec.get("timezone", settings.CELERY_TIMEZONE),
                )
                PeriodicTask.objects.update_or_create(name=spec["name"], defaults={
                    "task": spec["task"], "crontab": schedule, "interval": None,
                    "solar": None, "clocked": None, "enabled": True, "queue": "sync",
                    "args": "[]", "kwargs": "{}", "one_off": False, "start_time": None,
                    "expires": None, "expire_seconds": None,
                })
                self.stdout.write(f"Aktiviran {spec['name']}.")
