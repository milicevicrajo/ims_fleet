"""Ispravka oznake centara poslovnog i naucnog bloka: `20` → `2`, `30` → `3`.

Odluka narucioca 25.09.2026. Centri su `2` i `3` (kao u sifarniku i u Floti); `20` i `30`
su samo jedinice knjizenja. Ovo je ispravka greske uvoza, ne promena organizacije, pa se
postojeca verzija ispravlja na mestu umesto da se pravi nova verzija sa laznom istorijom.
"""
from django.db import migrations

ISPRAVKA = {"20": "2", "30": "3"}
NAPOMENA = " Oznaka centra ispravljena 25.09.2026. (jedinica knjizenja {staro} = centar {novo})."


def ispravi(apps, schema_editor):
    Version = apps.get_model("organizacija", "OrgNodeVersion")
    db = schema_editor.connection.alias
    for version in Version.objects.using(db).filter(node__level=1, full_code__in=list(ISPRAVKA)):
        novo = ISPRAVKA[version.full_code]
        version.note = (version.note + NAPOMENA.format(staro=version.full_code, novo=novo))[:300]
        version.full_code = novo
        version.segment = novo
        version.save(update_fields=["full_code", "segment", "note"])


def vrati(apps, schema_editor):
    Version = apps.get_model("organizacija", "OrgNodeVersion")
    db = schema_editor.connection.alias
    for staro, novo in ISPRAVKA.items():
        Version.objects.using(db).filter(node__level=1, full_code=novo).update(full_code=staro, segment=staro)


class Migration(migrations.Migration):
    dependencies = [("organizacija", "0004_dozvola_registar_flota")]
    operations = [migrations.RunPython(ispravi, vrati)]
