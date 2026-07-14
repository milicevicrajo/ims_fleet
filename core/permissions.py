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

    pregled_naplate_codes = [
        "naplata:lista_dugovanja",
        "naplata:lista_dugovanja_po_bucketima",
        "naplata:lista_avans_klijenti",
        "naplata:detalji_partner",
        "naplata:izvestaj_po_siframa_posla",
        "naplata:neodobrene_if_izvestaj",
        "naplata:lista_tuzenih",
        "naplata:lista_kontakata",
        "naplata:lista_napomena",
        "naplata:lista_opomena",
        "naplata:lista_poziva",
        "naplata:lista_pozivnih_pisma",
        "naplata:lista_tuzbi",
        "naplata:pravna_cases_list",
        "naplata:pravna_izvestaj",
        "naplata:pravna_izvestaj_excel",
        "naplata:pravna_detalj",
        "naplata:export_dugovanja_excel",
        "naplata:export_neodobrene_if_excel",
        "naplata:export_partner_baketi_excel",
        "naplata:export_utuzene_fakture",
        "naplata:export_opomene_fakture",
        "naplata:export_baket_90_excel",
        "naplata:export_baket_60_excel",
    ]
    pregled_naplate_role, _ = Role.objects.get_or_create(
        slug="pregled-naplate",
        defaults={
            "name": "Pregled naplate",
            "description": "Pregled lista, detalja i Excel izvoza u aplikaciji naplate, bez izmena i provere.",
            "is_active": True,
        },
    )
    role_changes = []
    if pregled_naplate_role.name != "Pregled naplate":
        pregled_naplate_role.name = "Pregled naplate"
        role_changes.append("name")
    if not pregled_naplate_role.is_active:
        pregled_naplate_role.is_active = True
        role_changes.append("is_active")
    if role_changes:
        pregled_naplate_role.save(update_fields=role_changes)
    RolePermission.objects.filter(role=pregled_naplate_role).exclude(
        permission__code__in=pregled_naplate_codes
    ).delete()
    for perm in PermissionCode.objects.filter(code__in=pregled_naplate_codes):
        RolePermission.objects.get_or_create(role=pregled_naplate_role, permission=perm)

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
        "putninalog_foreign_print",
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

    pregled_naplate_group_users_synced = 0
    pregled_naplate_group = Group.objects.filter(name__iexact="Pregled naplate").first()
    if pregled_naplate_group:
        for user in pregled_naplate_group.user_set.all():
            user.roles.add(pregled_naplate_role)
            pregled_naplate_group_users_synced += 1

    return {
        "synced": len(codes),
        "created": created,
        "role": role,
        "nabavka_role": nabavka_role,
        "menice_role": menice_role,
        "blagajna_role": blagajna_role,
        "pregled_naplate_role": pregled_naplate_role,
        "zahtev_role": zahtev_role,
        "sekretarijat_role": sekretarijat_role,
        "sekretarijat_group_users_synced": sekretarijat_group_users_synced,
        "pregled_naplate_group_users_synced": pregled_naplate_group_users_synced,
    }
