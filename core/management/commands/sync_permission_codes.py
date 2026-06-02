from django.core.management.base import BaseCommand

from core.permissions import sync_permission_codes


class Command(BaseCommand):
    help = "Sync PermissionCode entries from configured URL names."

    def handle(self, *args, **options):
        result = sync_permission_codes()
        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {result['synced']} codes, created {result['created']}. "
                "Uprava has all permissions. Menice role has only menice permissions."
            )
        )
