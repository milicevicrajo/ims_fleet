from __future__ import annotations

from typing import Iterable, List

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import URLPattern, URLResolver

from core.models import PermissionCode, Role
from ugovori import urls as ugovori_urls
from ugovori.models import BusinessRequest, Contract, ContractParty, ContractType, Offer, Partner


UGOVORI_MODELS = (
    BusinessRequest,
    Contract,
    ContractParty,
    ContractType,
    Offer,
    Partner,
)


def _collect_url_names(
    patterns: Iterable[URLPattern | URLResolver],
    namespace: str,
    acc: List[str] | None = None,
) -> List[str]:
    if acc is None:
        acc = []
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            if pattern.name:
                acc.append(f"{namespace}:{pattern.name}")
        elif isinstance(pattern, URLResolver):
            _collect_url_names(pattern.url_patterns, namespace, acc)
    return sorted(set(acc))


def _get_group(name: str) -> Group:
    group = Group.objects.filter(name__iexact=name).first()
    if group:
        return group
    return Group.objects.create(name=name)


class Command(BaseCommand):
    help = (
        "Dodeljuje grupi Sekretarijat sva ovlascenja za app ugovori i "
        "sinhronizuje custom role koji aplikacija koristi za pristup view-ovima."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--group-name",
            default="Sekretarijat",
            help="Naziv Django auth grupe (default: Sekretarijat).",
        )
        parser.add_argument(
            "--role-name",
            default="Sekretarijat",
            help="Naziv custom role (default: Sekretarijat).",
        )
        parser.add_argument(
            "--role-slug",
            default="sekretarijat",
            help="Slug custom role (default: sekretarijat).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Prikazuje rezultat bez trajnog upisa u bazu.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        group_name = options["group_name"].strip()
        role_name = options["role_name"].strip()
        role_slug = options["role_slug"].strip()
        dry_run = bool(options["dry_run"])

        if not group_name:
            raise CommandError("group-name ne sme biti prazan.")
        if not role_name:
            raise CommandError("role-name ne sme biti prazan.")
        if not role_slug:
            raise CommandError("role-slug ne sme biti prazan.")

        group = _get_group(group_name)
        role, role_created = Role.objects.get_or_create(
            slug=role_slug,
            defaults={
                "name": role_name,
                "description": "Puna ovlascenja za app ugovori.",
                "is_active": True,
            },
        )
        role.name = role_name
        role.is_active = True
        role.save(update_fields=["name", "is_active"])

        url_codes = _collect_url_names(ugovori_urls.urlpatterns, "ugovori")
        permission_codes = []
        created_codes = 0
        for code in url_codes:
            permission_code, was_created = PermissionCode.objects.get_or_create(code=code)
            permission_codes.append(permission_code)
            if was_created:
                created_codes += 1
        role.permissions.add(*permission_codes)

        django_permissions = []
        for model in UGOVORI_MODELS:
            content_type = ContentType.objects.get_for_model(model)
            model_name = model._meta.model_name
            django_permissions.extend(
                Permission.objects.filter(
                    content_type=content_type,
                    codename__in=[
                        f"view_{model_name}",
                        f"add_{model_name}",
                        f"change_{model_name}",
                        f"delete_{model_name}",
                    ],
                )
            )
        django_permission_ids = sorted({permission.id for permission in django_permissions})
        group.permissions.add(*django_permission_ids)

        group_users = list(group.user_set.all())
        for user in group_users:
            user.roles.add(role)

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Group '{group.name}' azurirana; "
                    f"Role '{role.slug}' {'created' if role_created else 'updated'}; "
                    f"ugovori URL dozvole: {len(url_codes)} "
                    f"(novo PermissionCode: {created_codes}); "
                    f"Django model perms: {len(django_permission_ids)}; "
                    f"korisnici sinhronizovani u role: {len(group_users)}."
                )
            )
        )
        if group_users:
            self.stdout.write(
                "Korisnici: " + ", ".join(sorted(user.username for user in group_users))
            )

        if dry_run:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("Dry-run: promene nisu upisane u bazu."))
