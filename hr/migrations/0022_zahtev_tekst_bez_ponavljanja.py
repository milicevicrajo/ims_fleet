"""Šifarnik zahteva: naslov bez reči „Захтев” i prva rečenica bez ponavljanja vrste rada.

Dokument zahteva već ima naslov „ЗАХТЕВ”, a ispod njega predmet. Predmet zato počinje sa
„за …” („за издавање решења за прековремени рад”), kao u rešenju („РЕШЕЊЕ / О ПРЕКОВРЕМЕНОМ
РАДУ”). Prva rečenica teksta je ponavljala vrstu rada iz predmeta („…издате решење за
прековремени рад за запослену…”); sada glasi „…издате решење за запослену…”, a vrsta rada
ostaje u predmetu i u drugoj rečenici.

Menja se samo tekst koji je još u podrazumevanom obliku; ručno izmenjen tekst se ne dira.
Podneti zahtevi čuvaju svoj zaključani tekst (snimak), pa se ne menjaju.
"""
import re

from django.db import migrations

PREFIKS = "Захтев за "
PONAVLJANJE = re.compile(r"издате решење за .+? за (\{rod:запосленог\|запослену\})")


def ispravi(apps, schema_editor):
    VrstaZahteva = apps.get_model("hr", "VrstaZahteva")
    for vrsta in VrstaZahteva.objects.using(schema_editor.connection.alias).all():
        polja = []
        if vrsta.predmet.startswith(PREFIKS):
            vrsta.predmet = vrsta.predmet[len("Захтев "):]
            polja.append("predmet")
        novi = PONAVLJANJE.sub(r"издате решење за \1", vrsta.tekst, count=1)
        if novi != vrsta.tekst:
            vrsta.tekst = novi
            polja.append("tekst")
        if polja:
            vrsta.save(update_fields=polja)


class Migration(migrations.Migration):
    dependencies = [("hr", "0021_ugovor_dodatno_radno_mesto")]

    operations = [migrations.RunPython(ispravi, migrations.RunPython.noop)]
