from django.db import migrations


def add_permissions(apps, schema_editor):
    Permission = apps.get_model('fleet', 'PermissionCode')
    Role = apps.get_model('fleet', 'Role')
    RolePermission = apps.get_model('fleet', 'RolePermission')
    alias = schema_editor.connection.alias
    role = Role.objects.using(alias).filter(slug='uprava').first()
    for code, label in [
        ('hr:work_time_catalog', 'Elementi radne liste — pregled šifrarnika'),
        ('hr:work_time_catalog_create', 'Elementi radne liste — dodavanje'),
        ('hr:work_time_catalog_edit', 'Elementi radne liste — izmena'),
    ]:
        permission, _ = Permission.objects.using(alias).get_or_create(code=code, defaults={'label': label})
        if role:
            RolePermission.objects.using(alias).get_or_create(role_id=role.pk, permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0006_recipienttype_worktimecategory_and_more'),
        ('fleet', '0076_employee_recipient_code_employee_recipient_name'),
    ]
    operations = [migrations.RunPython(add_permissions, migrations.RunPython.noop)]
