from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("fleet", "0053_trafficcard_traffic_card_back_image_and_more"),
        ("ugovori", "0005_alter_contract_value_type"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcurementCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("case_number", models.CharField(blank=True, db_index=True, max_length=32, null=True, unique=True, verbose_name="Broj predmeta")),
                ("case_type", models.CharField(choices=[("nabavka", "Zahtev za nabavku"), ("usluga", "Zahtev za uslugu"), ("oprema", "Predlog za nabavku opreme"), ("garaza_nabavka", "Garaža - nabavka"), ("garaza_usluga", "Garaža - usluga"), ("narudzbenica", "Nabavka po narudžbenici")], db_index=True, default="nabavka", max_length=30, verbose_name="Tip")),
                ("status", models.CharField(choices=[("draft", "Nacrt"), ("submitted", "Podneto"), ("in_progress", "U obradi"), ("waiting_invoice", "Čeka fakturu"), ("invoice_linked", "Faktura povezana"), ("completed", "Završeno"), ("cancelled", "Otkazano")], db_index=True, default="draft", max_length=30, verbose_name="Status")),
                ("title", models.CharField(max_length=255, verbose_name="Naziv")),
                ("description", models.TextField(blank=True, null=True, verbose_name="Opis")),
                ("estimated_value", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Procenjena vrednost")),
                ("currency", models.CharField(choices=[("RSD", "RSD"), ("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF")], default="RSD", max_length=10, verbose_name="Valuta")),
                ("needed_by", models.DateField(blank=True, null=True, verbose_name="Potrebno do")),
                ("note", models.TextField(blank=True, null=True, verbose_name="Napomena")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Kreirano")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Ažurirano")),
                ("contract", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="nabavka_cases", to="ugovori.contract", verbose_name="Osnovni ugovor")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_created_cases", to=settings.AUTH_USER_MODEL, verbose_name="Kreirao")),
                ("fleet_procurement_request", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_cases", to="fleet.procurementrequest", verbose_name="GZN iz garaže")),
                ("job_code", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_cases", to="fleet.organizationalunit", verbose_name="OJ / šifra posla")),
                ("responsible", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_responsible_cases", to=settings.AUTH_USER_MODEL, verbose_name="Odgovorno lice")),
                ("supplier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="nabavka_cases", to="ugovori.partner", verbose_name="Dobavljač")),
                ("vehicle", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_cases", to="fleet.vehicle", verbose_name="Vozilo")),
            ],
            options={
                "verbose_name": "Predmet nabavke",
                "verbose_name_plural": "Predmeti nabavke",
                "db_table": "nabavka_procurement_case",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="ProcurementInvoiceLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("euf", "EUF")], db_index=True, default="euf", max_length=20, verbose_name="Izvor")),
                ("euf_key", models.CharField(db_index=True, max_length=64, verbose_name="EUF ključ")),
                ("invoice_number", models.CharField(max_length=100, verbose_name="Broj fakture")),
                ("invoice_date", models.DateField(blank=True, null=True, verbose_name="Datum fakture")),
                ("supplier_name", models.CharField(blank=True, max_length=255, null=True, verbose_name="Naziv partnera")),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Iznos")),
                ("note", models.TextField(blank=True, null=True, verbose_name="Napomena")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Kreirano")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_invoice_links", to=settings.AUTH_USER_MODEL, verbose_name="Povezao")),
                ("procurement_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invoice_links", to="nabavka.procurementcase", verbose_name="Predmet nabavke")),
            ],
            options={
                "verbose_name": "Veza fakture",
                "verbose_name_plural": "Veze faktura",
                "db_table": "nabavka_invoice_link",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="ProcurementItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Naziv")),
                ("uom", models.CharField(max_length=30, verbose_name="Jedinica mere")),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Količina")),
                ("estimated_unit_price", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Procenjena cena")),
                ("note", models.CharField(blank=True, max_length=255, null=True, verbose_name="Napomena")),
                ("procurement_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="nabavka.procurementcase", verbose_name="Predmet nabavke")),
            ],
            options={
                "verbose_name": "Stavka nabavke",
                "verbose_name_plural": "Stavke nabavke",
                "db_table": "nabavka_procurement_item",
            },
        ),
        migrations.CreateModel(
            name="ProcurementStatusLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("old_status", models.CharField(blank=True, choices=[("draft", "Nacrt"), ("submitted", "Podneto"), ("in_progress", "U obradi"), ("waiting_invoice", "Čeka fakturu"), ("invoice_linked", "Faktura povezana"), ("completed", "Završeno"), ("cancelled", "Otkazano")], max_length=30, null=True, verbose_name="Stari status")),
                ("new_status", models.CharField(choices=[("draft", "Nacrt"), ("submitted", "Podneto"), ("in_progress", "U obradi"), ("waiting_invoice", "Čeka fakturu"), ("invoice_linked", "Faktura povezana"), ("completed", "Završeno"), ("cancelled", "Otkazano")], max_length=30, verbose_name="Novi status")),
                ("comment", models.TextField(blank=True, null=True, verbose_name="Komentar")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Kreirano")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_status_logs", to=settings.AUTH_USER_MODEL, verbose_name="Korisnik")),
                ("procurement_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_logs", to="nabavka.procurementcase", verbose_name="Predmet nabavke")),
            ],
            options={
                "verbose_name": "Promena statusa",
                "verbose_name_plural": "Promene statusa",
                "db_table": "nabavka_status_log",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(max_length=100, unique=True, verbose_name="Broj narudžbenice")),
                ("order_date", models.DateField(default=django.utils.timezone.localdate, verbose_name="Datum narudžbenice")),
                ("status", models.CharField(choices=[("draft", "Nacrt"), ("sent", "Poslato"), ("confirmed", "Potvrđeno"), ("closed", "Zatvoreno"), ("cancelled", "Otkazano")], db_index=True, default="draft", max_length=20, verbose_name="Status")),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name="Iznos")),
                ("currency", models.CharField(choices=[("RSD", "RSD"), ("EUR", "EUR"), ("USD", "USD"), ("CHF", "CHF")], default="RSD", max_length=10, verbose_name="Valuta")),
                ("note", models.TextField(blank=True, null=True, verbose_name="Napomena")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Kreirano")),
                ("contract", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="purchase_orders", to="ugovori.contract", verbose_name="Ugovor")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_purchase_orders", to=settings.AUTH_USER_MODEL, verbose_name="Kreirao")),
                ("procurement_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchase_orders", to="nabavka.procurementcase", verbose_name="Predmet nabavke")),
                ("supplier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="purchase_orders", to="ugovori.partner", verbose_name="Dobavljač")),
            ],
            options={
                "verbose_name": "Narudžbenica",
                "verbose_name_plural": "Narudžbenice",
                "db_table": "nabavka_purchase_order",
                "ordering": ["-order_date", "-id"],
            },
        ),
        migrations.CreateModel(
            name="ProcurementContractLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.CharField(blank=True, max_length=255, null=True, verbose_name="Napomena")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Kreirano")),
                ("contract", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="nabavka_links", to="ugovori.contract", verbose_name="Ugovor")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nabavka_contract_links", to=settings.AUTH_USER_MODEL, verbose_name="Povezao")),
                ("invoice_link", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="contract_links", to="nabavka.procurementinvoicelink", verbose_name="Faktura")),
                ("procurement_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contract_links", to="nabavka.procurementcase", verbose_name="Predmet nabavke")),
            ],
            options={
                "verbose_name": "Veza ugovora",
                "verbose_name_plural": "Veze ugovora",
                "db_table": "nabavka_contract_link",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="procurementcase",
            index=models.Index(fields=["case_type", "status"], name="nabavka_pro_case_ty_9acd10_idx"),
        ),
        migrations.AddIndex(
            model_name="procurementcase",
            index=models.Index(fields=["needed_by"], name="nabavka_pro_needed__b85efe_idx"),
        ),
        migrations.AddConstraint(
            model_name="procurementinvoicelink",
            constraint=models.UniqueConstraint(fields=("procurement_case", "source", "euf_key"), name="uniq_nabavka_case_invoice_source_key"),
        ),
        migrations.AddConstraint(
            model_name="procurementcontractlink",
            constraint=models.UniqueConstraint(fields=("procurement_case", "contract"), name="uniq_nabavka_case_contract"),
        ),
    ]
