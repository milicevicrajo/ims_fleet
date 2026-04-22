from __future__ import annotations

from typing import Iterable, List, Set, Tuple

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.urls import URLPattern, URLResolver

from fleet import urls as fleet_urls
from fleet.models import (
    CustomUser,
    FuelConsumption,
    Insurance,
    JobCode,
    Kvar,
    Lease,
    PermissionCode,
    Policy,
    ProcurementRequest,
    Requisition,
    Role,
    ServiceTransaction,
    ServiceType,
    TrafficCard,
    Vehicle,
    VehicleTravelOrder,
)
from fleet.permissions import collect_fleet_permission_codes


READ_ONLY_PREFIXES = (
    "vehicle_",
    "trafficcard_",
    "jobcode_",
    "lease_",
    "policy_",
    "fuelconsumption_",
    "service_transaction_",
    "requisition_",
    "servicetype_",
    "konta_",
    "insurance_",
    "putninalog_",
    "reports_",
    "omv_",
    "nis_",
    "tro_",
    "troskovi_",
    "kasko_",
    "potrazivanje_",
    "po_dobavljacima",
    "magacin",
    "otpis",
    "zatvoreni_putni",
    "export_",
)

READ_ONLY_EXACT = {
    "dashboard",
    "center_statistics",
    "expiring_and_not_renewed_policies",
    "fuel_transactions_list",
    "service_list",
    "reports_index",
}

MUTATING_MARKERS = (
    "_create",
    "_update",
    "_delete",
    "_add",
    "_toggle",
    "_set_",
    "_storniraj",
    "fetch_",
    "import_",
    "migrate_",
    "draft_",
    "_close",
    "_request",
)

EXCLUDED_CODES = {"login", "logout", "user_list"}


def _collect_named_routes(
    patterns: Iterable[URLPattern | URLResolver],
    prefix: str = "",
    acc: List[Tuple[str, str]] | None = None,
) -> List[Tuple[str, str]]:
    if acc is None:
        acc = []
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            if pattern.name:
                route = f"{prefix}{pattern.pattern}"
                acc.append((pattern.name, str(route)))
        elif isinstance(pattern, URLResolver):
            nested_prefix = f"{prefix}{pattern.pattern}"
            _collect_named_routes(pattern.url_patterns, str(nested_prefix), acc)
    return acc


def _is_candidate_read_only_code(code: str) -> bool:
    if code in READ_ONLY_EXACT:
        return True
    return any(code.startswith(prefix) for prefix in READ_ONLY_PREFIXES)


def _is_mutating_code(code: str) -> bool:
    return any(marker in code for marker in MUTATING_MARKERS)


class Command(BaseCommand):
    help = (
        "Kreira/azurira garaza grupu i custom ulogu sa dozvolama: "
        "Fleet read-only + puna ovlascenja u Garaza delu."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--group-name",
            default="garaza",
            help="Naziv Django auth grupe (default: garaza).",
        )
        parser.add_argument(
            "--role-name",
            default="Garaza",
            help="Naziv custom role (default: Garaza).",
        )
        parser.add_argument(
            "--role-slug",
            default="garaza",
            help="Slug custom role (default: garaza).",
        )
        parser.add_argument(
            "--users",
            nargs="*",
            default=[],
            help=(
                "Lista korisnickih imena za dodelu role/grupe. "
                "Podrzani format: --users korisnik1 korisnik2 ili --users korisnik1,korisnik2"
            ),
        )
        parser.add_argument(
            "--no-clear-existing",
            action="store_true",
            help="Ne brise postojeca ovlascenja sa role/grupe, vec samo dodaje nova.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Prikazuje rezultat bez trajnog upisa u bazu.",
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
        group_name = options["group_name"].strip()
        role_name = options["role_name"].strip()
        role_slug = options["role_slug"].strip()
        clear_existing = not options["no_clear_existing"]
        dry_run = bool(options.get("dry_run"))
        usernames = self._normalize_usernames(options.get("users") or [])

        if not group_name:
            raise ValueError("group-name ne sme biti prazan.")
        if not role_name:
            raise ValueError("role-name ne sme biti prazan.")
        if not role_slug:
            raise ValueError("role-slug ne sme biti prazan.")

        # 1) Osvezi PermissionCode listu za fleet URL name-ove.
        fleet_codes = set(collect_fleet_permission_codes())
        for code in fleet_codes:
            PermissionCode.objects.get_or_create(code=code)

        # 2) Izracunaj skup dozvola:
        #    - puni pristup svim URL-ovima koji su u /garaza/ delu
        #    - read-only pristup za fleet/lizing/gorivo/popravke van garaze
        named_routes = _collect_named_routes(fleet_urls.urlpatterns)
        garaza_codes: Set[str] = {
            name for name, route in named_routes if route.startswith("garaza/")
        }
        read_only_codes: Set[str] = {
            code
            for code in fleet_codes
            if _is_candidate_read_only_code(code)
            and not _is_mutating_code(code)
            and code not in EXCLUDED_CODES
        }
        selected_codes = sorted((garaza_codes | read_only_codes) & fleet_codes)

        permission_codes = list(PermissionCode.objects.filter(code__in=selected_codes))

        # 3) Custom Role (ovo aplikacija koristi za pristup view-ovima).
        role, role_created = Role.objects.get_or_create(
            slug=role_slug,
            defaults={
                "name": role_name,
                "description": (
                    "Fleet read-only + puna ovlascenja za Garaza deo. "
                    "Generisano komandom create_garaza_group."
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

        # 4) Django Group (za admin konzistentnost).
        group, group_created = Group.objects.get_or_create(name=group_name)

        read_only_models = [
            Vehicle,
            TrafficCard,
            JobCode,
            Lease,
            Policy,
            FuelConsumption,
            ServiceType,
            ServiceTransaction,
            Requisition,
            Insurance,
        ]
        full_garaza_models = [
            Kvar,
            ProcurementRequest,
            VehicleTravelOrder,
        ]

        django_perms: List[Permission] = []
        for model in read_only_models:
            ct = ContentType.objects.get_for_model(model)
            view_perm = Permission.objects.filter(
                content_type=ct,
                codename=f"view_{model._meta.model_name}",
            )
            django_perms.extend(list(view_perm))

        for model in full_garaza_models:
            ct = ContentType.objects.get_for_model(model)
            full_perm = Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f"view_{model._meta.model_name}",
                    f"add_{model._meta.model_name}",
                    f"change_{model._meta.model_name}",
                    f"delete_{model._meta.model_name}",
                ],
            )
            django_perms.extend(list(full_perm))

        unique_perm_ids = sorted({perm.id for perm in django_perms})
        if clear_existing:
            group.permissions.set(unique_perm_ids)
        else:
            group.permissions.add(*unique_perm_ids)

        # 5) Opcionalno dodeli korisnicima.
        assigned_users = []
        missing_users = []
        if usernames:
            existing_users = {
                user.username: user for user in CustomUser.objects.filter(username__in=usernames)
            }
            for username in usernames:
                user = existing_users.get(username)
                if not user:
                    missing_users.append(username)
                    continue
                user.roles.add(role)
                user.groups.add(group)
                assigned_users.append(username)

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Role '{role.slug}' {'created' if role_created else 'updated'}; "
                    f"Group '{group.name}' {'created' if group_created else 'updated'}; "
                    f"URL dozvole: {len(selected_codes)} "
                    f"(garaza full: {len(garaza_codes)}, read-only: {len(read_only_codes)}); "
                    f"Django model perms: {len(unique_perm_ids)}."
                )
            )
        )

        if assigned_users:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dodeljeno korisnicima: {', '.join(assigned_users)}"
                )
            )
        if missing_users:
            self.stdout.write(
                self.style.WARNING(
                    f"Korisnici nisu pronadjeni: {', '.join(missing_users)}"
                )
            )

        if dry_run:
            transaction.set_rollback(True)
            self.stdout.write(
                self.style.WARNING("Dry-run: promene nisu upisane u bazu.")
            )
