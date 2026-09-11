from django.db import migrations


def add_permissions(apps, schema_editor):
    Permission = apps.get_model('fleet', 'PermissionCode')
    Role = apps.get_model('fleet', 'Role')
    RolePermission = apps.get_model('fleet', 'RolePermission')
    alias = schema_editor.connection.alias
    role = Role.objects.using(alias).filter(slug='uprava').first()
    for code,label in [('hr:sick_leave_list','Bolovanja — pregled'),
                       ('hr:sick_leave_import','Bolovanja — RFZO uvoz')]:
        permission,_ = Permission.objects.using(alias).get_or_create(code=code,defaults={'label':label})
        if role:
            RolePermission.objects.using(alias).get_or_create(role_id=role.pk,permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies=[('hr','0004_sickleaveimport_sickleave_and_more')]
    operations=[migrations.RunPython(add_permissions,migrations.RunPython.noop)]
