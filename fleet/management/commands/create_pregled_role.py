from __future__ import annotations

from typing import Iterable, List, Set

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import CustomUser, PermissionCode, Role
from core.permissions import collect_fleet_permission_codes
from fleet.models import (
    FuelConsumption,
    Insurance,
    JobCode,
    Kvar,
    Lease,
    Policy,
    ProcurementRequest,
    Requisition,
    ServiceTransaction,
    ServiceType,
    TrafficCard,
    Vehicle,
    VehicleTenderDocument,
    VehicleTravelOrder,
)


MUTATING_MARKERS = (
    "_create",
    "_update",
    "_delete",
    "_add",
    "_toggle",
    "_set_",
    "_storniraj",
    "_close",
    "_restore",
    "fetch_",
    "import_",
    "migrate_",
    "draft_",
    "sync_",
)

EXCLUDED_CODES = {
    "fetch_data",
    "insurance_migrate_one",
    "login",
    "logout",
    "user_list",
    "vehicle_restore",
    "vehicle_toggle_status",
}


def _is_read_only_code(code: str) -> bool:
    if code in EXCLUDED_CODES:
        return False
    return not any(marker in code for marker in MUTATING_MARKERS)


class Command(BaseCommand):
    help = "Kreira/azurira custom ulogu Pregled sa read-only fleet dozvolama i dozvoljenim preuzimanjem/exportom."

    def add_arguments(self, parser):
        parser.add_argument("--role-name", default="Pregled")
        parser.add_argument("--role-slug", default="pregled")
        parser.add_argument("--group-name", default="pregled")
        parser.add_argument(
            "--users",
            nargs="*",
            default=[],
            help="Korisnici kojima treba dodeliti ulogu/grupu. Podrzava razmak ili zarez.",
        )
        parser.add_argument(
            "--no-clear-existing",
            action="store_true",
            help="Ne skida postojece dozvole sa uloge/grupe, vec samo dodaje Pregled dozvole.",
        )

    def _normalize_usernames(self, values: Iterable[str]) -> List[str]:
        raw: List[str] = []
        for value in values:
            if not value:
                continue
            raw.extend(part.strip() for part in value.split(","))
        return sorted({username for username in raw if username})

    @transaction.atomic
    def handle(self, *args, **options):
        role_name = options["role_name"].strip()
        role_slug = options["role_slug"].strip()
        group_name = options["group_name"].strip()
        clear_existing = not options["no_clear_existing"]
        usernames = self._normalize_usernames(options["users"])

        fleet_codes: Set[str] = set(collect_fleet_permission_codes())
        for code in fleet_codes:
            PermissionCode.objects.get_or_create(code=code)

        selected_codes = sorted(code for code in fleet_codes if _is_read_only_code(code))
        permission_codes = list(PermissionCode.objects.filter(code__in=selected_codes))

        role, _ = Role.objects.get_or_create(
            slug=role_slug,
            defaults={
                "name": role_name,
                "description": (
                    "Read-only pristup floti: pregledi, liste, detalji, izvestaji, "
                    "stampa i preuzimanje/export. Bez kreiranja, izmena, brisanja i statusnih akcija."
                ),
                "is_active": True,
            },
        )
        role.name = role_name
        role.is_active = True
        role.save(update_fields=["name", "is_active"])

        if clear_existing:
            role.permissions.set(permission_codes)
        else:
            role.permissions.add(*permission_codes)

        group, _ = Group.objects.get_or_create(name=group_name)
        read_only_models = [
            Vehicle,
            TrafficCard,
            VehicleTenderDocument,
            JobCode,
            Lease,
            Policy,
            FuelConsumption,
            ServiceType,
            ServiceTransaction,
            Requisition,
            Insurance,
            Kvar,
            ProcurementRequest,
            VehicleTravelOrder,
        ]
        django_perms: List[Permission] = []
        for model in read_only_models:
            ct = ContentType.objects.get_for_model(model)
            django_perms.extend(
                Permission.objects.filter(
                    content_type=ct,
                    codename=f"view_{model._meta.model_name}",
                )
            )

        if clear_existing:
            group.permissions.set(django_perms)
        else:
            group.permissions.add(*django_perms)

        users_added = 0
        for username in usernames:
            user = CustomUser.objects.filter(username=username).first()
            if not user:
                self.stderr.write(self.style.WARNING(f"Korisnik ne postoji: {username}"))
                continue
            user.roles.add(role)
            user.groups.add(group)
            users_added += 1

        self.stdout.write(self.style.SUCCESS(f"Uloga '{role.name}' je azurirana."))
        self.stdout.write(f"Role dozvole: {len(permission_codes)}")
        self.stdout.write(f"Django group: {group.name}, view dozvole: {len(django_perms)}")
        if users_added:
            self.stdout.write(f"Dodeljeno korisnicima: {users_added}")
        self.stdout.write("Ukljucene su read-only, print, export i download dozvole.")
