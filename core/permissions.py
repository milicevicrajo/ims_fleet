from django.contrib.auth.models import Group
from django.urls import URLPattern, URLResolver

from core.models import PermissionCode, Role, RolePermission


def collect_url_pattern_names(patterns, prefix=None):
    names = set()
    _collect_url_pattern_names(patterns, names)
    if prefix:
        return sorted(f"{prefix}:{name}" for name in names)
    return sorted(names)


def _collect_url_pattern_names(patterns, acc):
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            if pattern.name:
                acc.add(pattern.name)
        elif isinstance(pattern, URLResolver):
            _collect_url_pattern_names(pattern.url_patterns, acc)
    return acc


def collect_fleet_permission_codes():
    from fleet import urls as fleet_urls

    return collect_url_pattern_names(fleet_urls.urlpatterns)


def collect_naplata_permission_codes():
    from naplata import urls as naplata_urls

    return collect_url_pattern_names(naplata_urls.urlpatterns, prefix="naplata")


def collect_nabavka_permission_codes():
    from nabavka import urls as nabavka_urls

    return collect_url_pattern_names(nabavka_urls.urlpatterns, prefix="nabavka")


def collect_menice_permission_codes():
    from menice import urls as menice_urls

    return collect_url_pattern_names(menice_urls.urlpatterns, prefix="menice")


def collect_isplate_permission_codes():
    from isplate import urls as isplate_urls

    return collect_url_pattern_names(isplate_urls.urlpatterns, prefix="isplate")


def collect_permission_codes():
    codes = set(collect_fleet_permission_codes())
    codes.update(collect_naplata_permission_codes())
    codes.update(collect_nabavka_permission_codes())
    codes.update(collect_menice_permission_codes())
    codes.update(collect_isplate_permission_codes())
    return sorted(codes)


def sync_permission_codes():
    codes = collect_permission_codes()
    created = 0

    for code in codes:
        _, was_created = PermissionCode.objects.get_or_create(code=code)
        if was_created:
            created += 1

    role, _ = Role.objects.get_or_create(name="Uprava", slug="uprava")
    for perm in PermissionCode.objects.all():
        RolePermission.objects.get_or_create(role=role, permission=perm)

    nabavka_codes = collect_nabavka_permission_codes()
    nabavka_role, _ = Role.objects.get_or_create(
        name="Nabavka",
        slug="nabavka",
        defaults={"description": "Pristup svim funkcijama aplikacije nabavka."},
    )
    RolePermission.objects.filter(role=nabavka_role).exclude(
        permission__code__in=nabavka_codes
    ).delete()
    for perm in PermissionCode.objects.filter(code__in=nabavka_codes):
        RolePermission.objects.get_or_create(role=nabavka_role, permission=perm)

    menice_codes = collect_menice_permission_codes()
    menice_role, _ = Role.objects.get_or_create(
        name="Menice",
        slug="menice",
        defaults={"description": "Pristup samo aplikaciji menice."},
    )
    RolePermission.objects.filter(role=menice_role).exclude(
        permission__code__in=menice_codes
    ).delete()
    for perm in PermissionCode.objects.filter(code__in=menice_codes):
        RolePermission.objects.get_or_create(role=menice_role, permission=perm)

    isplate_codes = collect_isplate_permission_codes()
    blagajna_role, _ = Role.objects.get_or_create(
        name="Blagajna",
        slug="blagajna",
        defaults={"description": "Pristup svim funkcijama aplikacije isplate."},
    )
    RolePermission.objects.filter(role=blagajna_role).exclude(
        permission__code__in=isplate_codes
    ).delete()
    for perm in PermissionCode.objects.filter(code__in=isplate_codes):
        RolePermission.objects.get_or_create(role=blagajna_role, permission=perm)

    zahtev_codes = [
        "nabavka:dashboard",
        "nabavka:case_list",
        "nabavka:case_data",
        "nabavka:case_create",
        "nabavka:case_detail",
        "nabavka:case_print",
        "nabavka:case_material_requisition_print",
        "nabavka:item_create",
        "nabavka:item_delete",
    ]
    zahtev_role, _ = Role.objects.get_or_create(
        name="Zahtev",
        slug="zahtev",
        defaults={"description": "Kreiranje zahteva sa stavkama i stampa, bez komercijalne obrade."},
    )
    RolePermission.objects.filter(role=zahtev_role).exclude(
        permission__code__in=zahtev_codes
    ).delete()
    for perm in PermissionCode.objects.filter(code__in=zahtev_codes):
        RolePermission.objects.get_or_create(role=zahtev_role, permission=perm)

    sekretarijat_codes = [
        "employee_list",
        "employee_sync",
    ]
    sekretarijat_role, _ = Role.objects.get_or_create(
        slug="sekretarijat",
        defaults={
            "name": "Sekretarijat",
            "description": "Pristup funkcijama sekretarijata.",
            "is_active": True,
        },
    )
    if sekretarijat_role.name != "Sekretarijat" or not sekretarijat_role.is_active:
        sekretarijat_role.name = "Sekretarijat"
        sekretarijat_role.is_active = True
        sekretarijat_role.save(update_fields=["name", "is_active"])
    for perm in PermissionCode.objects.filter(code__in=sekretarijat_codes):
        RolePermission.objects.get_or_create(role=sekretarijat_role, permission=perm)
    sekretarijat_group_users_synced = 0
    sekretarijat_group = Group.objects.filter(name__iexact="Sekretarijat").first()
    if sekretarijat_group:
        for user in sekretarijat_group.user_set.all():
            user.roles.add(sekretarijat_role)
            sekretarijat_group_users_synced += 1

    return {
        "synced": len(codes),
        "created": created,
        "role": role,
        "nabavka_role": nabavka_role,
        "menice_role": menice_role,
        "blagajna_role": blagajna_role,
        "zahtev_role": zahtev_role,
        "sekretarijat_role": sekretarijat_role,
        "sekretarijat_group_users_synced": sekretarijat_group_users_synced,
    }
