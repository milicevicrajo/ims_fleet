from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import PermissionCode, Role
from core.permissions import sync_kadrovi_permissions


class Command(BaseCommand):
    help = 'Usklađuje ulogu Kadrovi i registruje ekran za upravljanje pristupom korisnika.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        result = sync_kadrovi_permissions()
        role = Role.objects.filter(slug='uprava').first()
        for code in ['user_list', 'user_access_edit']:
            permission, _ = PermissionCode.objects.get_or_create(code=code)
            if role:
                role.permissions.add(permission)
        self.stdout.write(f"Kadrovi: +{result['granted']} dozvola; spojeno članstava: {result['merged_users']}.")
        if options['dry_run']:
            transaction.set_rollback(True)
            self.stdout.write('Probni prikaz — izmene nisu sačuvane.')
        else:
            self.stdout.write(self.style.SUCCESS('Uloga Kadrovi i administracija korisnika su usklađene.'))
