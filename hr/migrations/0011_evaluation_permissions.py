from django.db import migrations


def add_permissions(apps, schema_editor):
    Permission = apps.get_model('fleet','PermissionCode')
    Role = apps.get_model('fleet','Role')
    RolePermission = apps.get_model('fleet','RolePermission')
    db = schema_editor.connection.alias
    management = Role.objects.using(db).filter(slug='uprava').first()
    reviewer, _ = Role.objects.using(db).get_or_create(slug='ocenjivac',defaults={
        'name':'Ocenjivač','description':'Ocenjivanje zaposlenih u dodeljenim OJ i potvrda obrazaca u kojima je korisnik imenovan.'})
    for code,label in [
        ('evaluation_list','Ocenjivanje — pregled dostupnih obrazaca'),
        ('evaluation_create','Ocenjivanje — formiranje i nova verzija'),
        ('evaluation_approve','Ocenjivanje — saglasnost imenovanog ocenjivača'),
        ('evaluation_view_all','Ocenjivanje — pregled svih obrazaca'),
        ('evaluation_catalog','Ocenjivanje — podešavanje šifrarnika'),
    ]:
        permission,_ = Permission.objects.using(db).get_or_create(code='hr:'+code,defaults={'label':label})
        if management:
            RolePermission.objects.using(db).get_or_create(role_id=management.pk,permission_id=permission.pk)
        if code in ('evaluation_list','evaluation_create','evaluation_approve'):
            RolePermission.objects.using(db).get_or_create(role_id=reviewer.pk,permission_id=permission.pk)


class Migration(migrations.Migration):
    dependencies=[('hr','0010_evaluationcriterion_evaluationgroup_and_more')]
    operations=[migrations.RunPython(add_permissions,migrations.RunPython.noop)]
