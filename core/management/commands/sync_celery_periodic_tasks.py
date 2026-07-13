from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


EXPECTED_PERIODIC_TASKS = [
    {
        "name": "Flota - provera otpisa vozila",
        "aliases": ["Provera otpisa"],
        "task": "fleet.tasks.proveri_otpis",
        "hour": "1",
        "minute": "20",
    },
    {
        "name": "Flota - sinhronizacija sifri poslova i OJ",
        "aliases": ["Povlacenje sifri posla"],
        "task": "fleet.tasks.fetch_job_codes",
        "hour": "1",
        "minute": "30",
    },
    {
        "name": "Flota - sinhronizacija trebovanja",
        "aliases": ["Trebovanja"],
        "task": "fleet.tasks.fetch_requisition_data_task",
        "hour": "1",
        "minute": "45",
    },
    {
        "name": "Administracija - sinhronizacija dozvola",
        "aliases": ["Sync permissions"],
        "task": "core.tasks.sync_permission_codes_task",
        "hour": "1",
        "minute": "0",
    },
    {
        "name": "Kadrovi - sinhronizacija zaposlenih",
        "aliases": ["Sinhronizacija zaposlenih", "Sinhronizacia zaposlenih"],
        "task": "fleet.tasks.sync_hr_employees_task",
        "hour": "1",
        "minute": "10",
    },
    {
        "name": "Flota - sinhronizacija polisa",
        "aliases": ["Polise"],
        "task": "fleet.tasks.fetch_policy_data_task",
        "hour": "2",
        "minute": "0",
    },
    {
        "name": "Flota - sinhronizacija servisa",
        "aliases": ["Servisi"],
        "task": "fleet.tasks.fetch_service_data_task",
        "hour": "3",
        "minute": "15",
    },
    {
        "name": "Flota - DDOR osiguranja",
        "aliases": ["DDOR"],
        "task": "fleet.tasks.fetch_ddor_data_task",
        "hour": "3",
        "minute": "35",
    },
    {
        "name": "Gorivo - NIS transakcije",
        "aliases": ["Nis"],
        "task": "fleet.tasks.run_nis_command",
        "hour": "4",
        "minute": "20",
    },
    {
        "name": "Gorivo - OMV putnicka vozila",
        "aliases": ["OMV Putnicka"],
        "task": "fleet.tasks.run_omv_putnicka_command",
        "hour": "5",
        "minute": "10",
    },
    {
        "name": "Gorivo - OMV teretna vozila",
        "aliases": ["OMV Teretna"],
        "task": "fleet.tasks.run_omv_teretna_command",
        "hour": "6",
        "minute": "10",
    },
    {
        "name": "Putni nalozi - azuriranje isplacenog iznosa",
        "aliases": ["Putni nalozi isplaceno"],
        "task": "fleet.tasks.sync_putni_nalozi_isplaceno_task",
        "hour": "12",
        "minute": "30",
    },
    {
        "name": "Nabavka - EUF fakture",
        "aliases": ["Nabavka EUF fakture"],
        "task": "nabavka.tasks.sync_euf_invoices_task",
        "hour": "2",
        "minute": "20",
    },
    {
        "name": "Nabavka - UF stavke",
        "aliases": ["Nabavka UF stavke"],
        "task": "nabavka.tasks.sync_uf_items_task",
        "hour": "2",
        "minute": "45",
    },
    {
        "name": "Nabavka - roba",
        "aliases": ["Nabavka roba"],
        "task": "nabavka.tasks.sync_goods_task",
        "hour": "7",
        "minute": "10",
    },
]

STALE_TASK_NAMES = ["dodaj grupe One time"]


class Command(BaseCommand):
    help = "Kreira/azurira django-celery-beat periodic taskove za IMS Flotu."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Samo prikazuje sta bi bilo promenjeno.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        timezone = getattr(settings, "CELERY_TIMEZONE", getattr(settings, "TIME_ZONE", "CET"))
        created = 0
        updated = 0

        self.stdout.write(f"Celery periodic sync timezone={timezone} dry_run={dry_run}")

        for spec in EXPECTED_PERIODIC_TASKS:
            crontab, _ = CrontabSchedule.objects.get_or_create(
                minute=spec["minute"],
                hour=spec["hour"],
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
                timezone=timezone,
            )
            lookup_names = [spec["name"], *spec.get("aliases", [])]
            existing = PeriodicTask.objects.filter(name__in=lookup_names).first()
            changes = {}
            if existing is None:
                if not dry_run:
                    PeriodicTask.objects.create(
                        name=spec["name"],
                        task=spec["task"],
                        crontab=crontab,
                        enabled=True,
                    )
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"CREATE {spec['name']} -> {spec['task']} @ {spec['hour']}:{spec['minute']}"
                    )
                )
                continue

            if existing.task != spec["task"]:
                changes["task"] = spec["task"]
            if existing.name != spec["name"]:
                changes["name"] = spec["name"]
            if existing.crontab_id != crontab.id or existing.interval_id or existing.solar_id or existing.clocked_id:
                changes["crontab"] = crontab
                changes["interval"] = None
                changes["solar"] = None
                changes["clocked"] = None
            if not existing.enabled:
                changes["enabled"] = True

            if changes:
                updated += 1
                if not dry_run:
                    for field, value in changes.items():
                        setattr(existing, field, value)
                    existing.save(update_fields=list(changes.keys()))
                self.stdout.write(
                    self.style.WARNING(
                        f"UPDATE {spec['name']}: {', '.join(changes.keys())}"
                    )
                )
            else:
                self.stdout.write(f"OK {spec['name']} -> {spec['task']}")

        stale_qs = PeriodicTask.objects.filter(name__in=STALE_TASK_NAMES)
        stale_count = stale_qs.count()
        if stale_count:
            if not dry_run:
                stale_qs.delete()
            self.stdout.write(self.style.WARNING(f"DELETE stale periodic tasks: {stale_count}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Celery periodic sync done. created={created}, updated={updated}, stale_deleted={stale_count}"
            )
        )
