import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ugovori", "0008_businessrequest_offer_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContractDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("contract", "Ugovor"),
                            ("annex", "Aneks"),
                            ("attachment", "Prilog"),
                            ("other", "Ostalo"),
                        ],
                        db_index=True,
                        default="contract",
                        max_length=20,
                        verbose_name="Vrsta dokumenta",
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=500, verbose_name="Opis"),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to="ugovori/dokumenti/%Y/%m/",
                        verbose_name="Fajl",
                    ),
                ),
                (
                    "original_filename",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Originalni naziv fajla",
                    ),
                ),
                (
                    "uploaded_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Postavljeno"),
                ),
                (
                    "contract",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to="ugovori.contract",
                        verbose_name="Ugovor",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ugovori_dokumenti_postavljeni",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Postavio",
                    ),
                ),
            ],
            options={
                "verbose_name": "Dokument uz ugovor",
                "verbose_name_plural": "Dokumenta uz ugovor",
                "db_table": "ugovori_contract_document",
                "ordering": ["-uploaded_at", "-pk"],
                "indexes": [
                    models.Index(
                        fields=["contract", "document_type"],
                        name="ugovori_con_contrac_aefa86_idx",
                    ),
                ],
            },
        ),
    ]
