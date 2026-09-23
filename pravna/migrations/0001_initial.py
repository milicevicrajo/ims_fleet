"""Pravna sluzba dobija svoju aplikaciju.

Postupak i PromenaPostupka se ne prave iznova - tabele `postupak` i
`promena_postupka` vec postoje iz naplate. Ovde se menja samo Django stanje
(SeparateDatabaseAndState), pa podaci ostaju netaknuti. Uz njih se prave
stvarne tabele za disciplinski postupak.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("fleet", "0001_initial"),
        ("naplata", "0005_alter_postupak_options_remove_postupak_mesto_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Postupak",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("tip", models.CharField(choices=[("tuzeni", "Tuženi"), ("tuzili", "Tužili"), ("stecaj", "Stečaj"), ("uppr", "UPPR")], db_index=True, default="tuzeni", max_length=20)),
                        ("sud", models.CharField(blank=True, max_length=255, null=True, verbose_name="Sud")),
                        ("broj_predmeta", models.CharField(blank=True, max_length=100, null=True, verbose_name="Broj predmeta")),
                        ("sifra_partnera", models.IntegerField(blank=True, db_index=True, null=True, verbose_name="Šifra partnera")),
                        ("naziv_partnera", models.CharField(blank=True, max_length=255, null=True, verbose_name="Naziv partnera")),
                        ("valuta", models.CharField(choices=[("RSD", "RSD"), ("EUR", "EUR"), ("USD", "USD")], default="RSD", max_length=10, verbose_name="Valuta")),
                        ("osnovni_dug", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Osnovni dug (glavnica)")),
                        ("arhivirano", models.BooleanField(default=False, verbose_name="Arhivirano")),
                        ("izvrsiteljski_broj", models.CharField(blank=True, max_length=100, null=True, verbose_name="Izvršiteljski broj")),
                        ("datum_pokretanja", models.DateField(blank=True, null=True, verbose_name="Datum pokretanja postupka")),
                        ("predmet_spora", models.TextField(blank=True, null=True, verbose_name="Predmet spora")),
                        ("tuzilac", models.CharField(blank=True, max_length=255, null=True, verbose_name="Tužilac")),
                        ("vrednost_spora", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Vrednost spora")),
                        ("datum_podnosenja_tuzbe", models.DateField(blank=True, null=True, verbose_name="Datum podnošenja tužbe")),
                        ("vece", models.CharField(blank=True, max_length=100, null=True, verbose_name="Veće")),
                        ("kamata", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Kamata")),
                        ("troskovi", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Troškovi")),
                        ("ukupan_dug", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Ukupan dug")),
                        ("datum_otvaranja_stecaja", models.DateField(blank=True, null=True, verbose_name="Datum otvaranja stečajnog postupka")),
                        ("prijava_potrazivanja", models.TextField(blank=True, null=True, verbose_name="Prijava potraživanja")),
                        ("novi_broj", models.CharField(blank=True, max_length=100, null=True, verbose_name="Novi broj")),
                        ("pib", models.CharField(blank=True, max_length=20, null=True, verbose_name="PIB")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="postupci_kreirani", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        "verbose_name": "Postupak",
                        "verbose_name_plural": "Postupci",
                        "db_table": "postupak",
                        "ordering": ["-created_at"],
                    },
                ),
                migrations.CreateModel(
                    name="PromenaPostupka",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("datum", models.DateField(verbose_name="Datum")),
                        ("promena", models.TextField(verbose_name="Promena")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="promene_postupaka", to=settings.AUTH_USER_MODEL)),
                        ("postupak", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="promene", to="pravna.postupak", verbose_name="Postupak")),
                    ],
                    options={
                        "verbose_name": "Promena postupka",
                        "verbose_name_plural": "Promene postupaka",
                        "db_table": "promena_postupka",
                        "ordering": ["-datum", "-created_at"],
                    },
                ),
            ],
        ),
        migrations.CreateModel(
            name="DisciplinskiPostupak",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("centar", models.CharField(blank=True, max_length=10, verbose_name="Centar")),
                ("datum_podnosenja", models.DateField(verbose_name="Datum podnošenja zahteva")),
                ("mera_datum", models.DateField(blank=True, null=True, verbose_name="Datum disciplinske mere")),
                ("mera_opis", models.TextField(blank=True, verbose_name="Disciplinska mera")),
                ("arhivirano", models.BooleanField(default=False, verbose_name="Arhivirano")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="disciplinski_postupci_kreirani", to=settings.AUTH_USER_MODEL)),
                ("podnosilac", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="podneti_disciplinski_postupci", to="fleet.employee", verbose_name="Podnosilac")),
                ("zaposleni", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="disciplinski_postupci", to="fleet.employee", verbose_name="Zaposleni")),
            ],
            options={
                "verbose_name": "Disciplinski postupak",
                "verbose_name_plural": "Disciplinski postupci",
                "ordering": ["-datum_podnosenja", "-id"],
            },
        ),
        migrations.CreateModel(
            name="TokPostupka",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("datum", models.DateField(verbose_name="Datum")),
                ("opis", models.TextField(verbose_name="Opis")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tok_disciplinskih_postupaka", to=settings.AUTH_USER_MODEL)),
                ("postupak", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tok", to="pravna.disciplinskipostupak", verbose_name="Disciplinski postupak")),
            ],
            options={
                "verbose_name": "Tok postupka",
                "verbose_name_plural": "Tok postupka",
                "ordering": ["datum", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="disciplinskipostupak",
            index=models.Index(fields=["centar"], name="pravna_disc_centar_idx"),
        ),
        migrations.AddIndex(
            model_name="disciplinskipostupak",
            index=models.Index(fields=["datum_podnosenja"], name="pravna_disc_datum_idx"),
        ),
    ]
