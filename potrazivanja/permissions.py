from core.models import PermissionCode, Role, RolePermission

PERMISSIONS = ("dashboard", "partner_detail", "table_data", "sync_status", "view_all", "export", "print", "review_update", "notice_import") + tuple(
    f'{kind}_{action}' for kind in ('contact', 'activity', 'notice', 'legal') for action in ('create', 'update', 'archive'))


def configure_permissions():
    management, _ = Role.objects.get_or_create(slug="uprava", defaults={"name": "Uprava"})
    for code in PERMISSIONS:
        permission, _ = PermissionCode.objects.get_or_create(code=f"potrazivanja:{code}")
        RolePermission.objects.get_or_create(role=management, permission=permission)
    # Add corresponding grants in this application's namespace, idempotently.
    # Keep old grants and the limited-review role's scope unchanged.
    for role in Role.objects.exclude(pk=management.pk):
        old = set(role.permissions.values_list('code', flat=True))
        if not any(code.startswith('naplata:') for code in old):
            continue
        grants = {'dashboard', 'partner_detail', 'table_data', 'export', 'print'}
        if 'naplata:lista_dugovanja_po_bucketima' in old and role.slug != 'pregled-naplate':
            grants.add('view_all')
        if 'naplata:toggle_avans_klijent' in old: grants.add('review_update')
        for action, prefix in [('create', 'dodaj'), ('update', 'izmeni'), ('archive', 'obrisi')]:
            for kind, suffixes in [('contact', ['kontakt']), ('activity', ['napomenu', 'poziv']), ('notice', ['opomenu', 'poziv_pismo', 'tuzbu'])]:
                if all(f'naplata:{prefix}_{suffix}' in old for suffix in suffixes): grants.add(f'{kind}_{action}')
            if f'naplata:pravna_{prefix}' in old: grants.add(f'legal_{action}')
        if 'notice_create' in grants: grants.add('notice_import')
        for code in grants:
            permission = PermissionCode.objects.get(code=f'potrazivanja:{code}')
            RolePermission.objects.get_or_create(role=role, permission=permission)
