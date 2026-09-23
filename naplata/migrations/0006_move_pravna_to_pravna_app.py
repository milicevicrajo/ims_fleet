"""Postupak i PromenaPostupka prelaze u aplikaciju `pravna`.

Samo promena Django stanja - tabele `postupak` i `promena_postupka` ostaju
netaknute, a vlasnik im je od sada aplikacija `pravna`.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("naplata", "0005_alter_postupak_options_remove_postupak_mesto_and_more"),
        ("pravna", "0001_initial"),
        # Potrazivanja su do 0005 imala strani kljuc na naplata.postupak;
        # model sme da nestane iz stanja tek kada ta veza bude odvojena.
        ("potrazivanja", "0005_detach_legacy_case_link"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="promenapostupka", name="created_by"),
                migrations.RemoveField(model_name="promenapostupka", name="postupak"),
                migrations.RemoveField(model_name="postupak", name="created_by"),
                migrations.DeleteModel(name="PromenaPostupka"),
                migrations.DeleteModel(name="Postupak"),
            ],
        ),
    ]
