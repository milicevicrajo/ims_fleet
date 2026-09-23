"""Uloge koje su imale pravnu sluzbu zadrzavaju je posle selidbe u aplikaciju `pravna`.

Dozvola se izvodi iz imena rute, a rute su presle iz `naplata:pravna_*` u
`pravna:*`. Bez ovog preslikavanja svaka uloga osim Uprave bi izgubila pristup.

Stari kodovi se namerno NE brisu: nijedna ruta ih vise ne nosi, pa nikoga ne
propustaju, ali ih `potrazivanja.permissions.configure_permissions` cita da bi
prepoznala nasledjene uloge.
"""
from django.db import migrations


MAPA = {
    "naplata:pravna_cases_list": "pravna:cases_list",
    "naplata:pravna_izvestaj": "pravna:izvestaj",
    "naplata:pravna_izvestaj_excel": "pravna:izvestaj_excel",
    "naplata:pravna_detalj": "pravna:detalj",
    "naplata:pravna_dodaj": "pravna:dodaj",
    "naplata:pravna_izmeni": "pravna:izmeni",
    "naplata:pravna_obrisi": "pravna:obrisi",
    "naplata:pravna_arhiviraj": "pravna:arhiviraj",
    "naplata:pravna_dodaj_promenu": "pravna:dodaj_promenu",
    "naplata:pravna_obrisi_promenu": "pravna:obrisi_promenu",
}


def prenesi(apps, schema_editor):
    PermissionCode = apps.get_model("fleet", "PermissionCode")
    RolePermission = apps.get_model("fleet", "RolePermission")
    db = schema_editor.connection.alias

    for stari_kod, novi_kod in MAPA.items():
        stari = PermissionCode.objects.using(db).filter(code=stari_kod).first()
        if not stari:
            continue
        novi, _ = PermissionCode.objects.using(db).get_or_create(code=novi_kod)
        role_ids = RolePermission.objects.using(db).filter(permission=stari).values_list("role_id", flat=True)
        for role_id in list(role_ids):
            RolePermission.objects.using(db).get_or_create(role_id=role_id, permission=novi)


def skloni(apps, schema_editor):
    PermissionCode = apps.get_model("fleet", "PermissionCode")
    RolePermission = apps.get_model("fleet", "RolePermission")
    db = schema_editor.connection.alias

    novi_kodovi = list(MAPA.values())
    RolePermission.objects.using(db).filter(permission__code__in=novi_kodovi).delete()
    PermissionCode.objects.using(db).filter(code__in=novi_kodovi).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0078_lease_payment_basis"),
    ]

    operations = [
        migrations.RunPython(prenesi, skloni),
    ]
