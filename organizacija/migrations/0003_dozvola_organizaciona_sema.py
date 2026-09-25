"""Dozvola za ekran organizacione šeme: dobija je svaka uloga koja već vidi stablo organizacije."""
from django.db import migrations


def dodaj_dozvolu(apps, schema_editor):
    Permission = apps.get_model('fleet', 'PermissionCode')
    RolePermission = apps.get_model('fleet', 'RolePermission')
    db = schema_editor.connection.alias
    sema, _ = Permission.objects.using(db).get_or_create(code='organizacija:sema',
        defaults={'label': 'Organizacija — organizaciona šema'})
    uloge = RolePermission.objects.using(db).filter(permission__code='organizacija:stablo').values_list('role_id', flat=True)
    for role_id in set(uloge):
        RolePermission.objects.using(db).get_or_create(role_id=role_id, permission_id=sema.pk)


class Migration(migrations.Migration):
    dependencies = [('organizacija', '0002_jobactivityreview'), ('fleet', '0081_customuser_allowed_hr_unit_codes')]
    operations = [migrations.RunPython(dodaj_dozvolu, migrations.RunPython.noop)]
