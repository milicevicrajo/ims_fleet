"""Dozvola za uporedni izvestaj Flote i registra (faza 2). Dobija je samo uloga Uprava."""
from django.db import migrations


def dodaj_dozvolu(apps, schema_editor):
    Permission = apps.get_model('fleet', 'PermissionCode')
    Role = apps.get_model('fleet', 'Role')
    RolePermission = apps.get_model('fleet', 'RolePermission')
    db = schema_editor.connection.alias
    dozvola, _ = Permission.objects.using(db).get_or_create(code='organizacija:flota',
        defaults={'label': 'Organizacija — registar i Flota (uporedni izveštaj)'})
    uprava = Role.objects.using(db).filter(slug='uprava').first()
    if uprava:
        RolePermission.objects.using(db).get_or_create(role_id=uprava.pk, permission_id=dozvola.pk)


class Migration(migrations.Migration):
    dependencies = [('organizacija', '0003_dozvola_organizaciona_sema')]
    operations = [migrations.RunPython(dodaj_dozvolu, migrations.RunPython.noop)]
