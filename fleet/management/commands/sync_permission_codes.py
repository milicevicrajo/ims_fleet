from django.core.management.base import BaseCommand

from core.models import PermissionCode, Role, RolePermission
from fleet.permissions import collect_fleet_permission_codes
from naplata.permissions import collect_naplata_permission_codes


class Command(BaseCommand):
    help = "Sync PermissionCode entries from fleet.urls (by URL name)."

    def handle(self, *args, **options):
        codes = set(collect_fleet_permission_codes())
        codes.update(collect_naplata_permission_codes())
        codes = sorted(codes)
        created = 0
        for code in codes:
            _, was_created = PermissionCode.objects.get_or_create(code=code)
            if was_created:
                created += 1

        role, _ = Role.objects.get_or_create(name="Uprava", slug="uprava")
        for perm in PermissionCode.objects.all():
            RolePermission.objects.get_or_create(role=role, permission=perm)

        self.stdout.write(self.style.SUCCESS(
            f"Synced {len(codes)} codes, created {created}. Uprava has all permissions."
        ))
