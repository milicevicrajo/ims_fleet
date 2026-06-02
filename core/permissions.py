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


def collect_permission_codes():
    codes = set(collect_fleet_permission_codes())
    codes.update(collect_naplata_permission_codes())
    codes.update(collect_nabavka_permission_codes())
    codes.update(collect_menice_permission_codes())
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

    return {
        "synced": len(codes),
        "created": created,
        "role": role,
        "menice_role": menice_role,
    }
