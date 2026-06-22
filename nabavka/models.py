from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ProcurementCase(models.Model):
    class CaseType(models.TextChoices):
        PROCUREMENT = "nabavka", _("Zahtev za nabavku")
        SERVICE = "usluga", _("Zahtev za uslugu")
        EQUIPMENT = "oprema", _("Predlog za nabavku opreme")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Nacrt")
        SUBMITTED = "submitted", _("Podneto")
        IN_PROGRESS = "in_progress", _("U obradi")
        WAITING_INVOICE = "waiting_invoice", _("Čeka fakturu")
        INVOICE_LINKED = "invoice_linked", _("Faktura povezana")
        COMPLETED = "completed", _("Završeno")
        CANCELLED = "cancelled", _("Otkazano")

    CURRENCY_CHOICES = [
        ("RSD", "RSD"),
        ("EUR", "EUR"),
        ("USD", "USD"),
        ("CHF", "CHF"),
    ]
    CASE_TYPE_PREFIXES = {
        CaseType.PROCUREMENT: "ZN",
        CaseType.SERVICE: "ZU",
        CaseType.EQUIPMENT: "PLN",
    }
    GARAGE_CASE_TYPE_PREFIXES = {
        CaseType.PROCUREMENT: "ZNG",
        CaseType.SERVICE: "ZUG",
    }
    case_number = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Broj predmeta"),
    )
    case_type = models.CharField(
        max_length=30,
        choices=CaseType.choices,
        default=CaseType.PROCUREMENT,
        db_index=True,
        verbose_name=_("Tip"),
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name=_("Status"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Naziv"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))
    is_garage = models.BooleanField(default=False, verbose_name=_("Garaža"))
    job_code = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.SET_NULL,
        null=True,
        related_name="nabavka_cases",
        verbose_name=_("OJ / šifra posla"),
    )
    supplier = models.ForeignKey(
        "ugovori.Partner",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="nabavka_cases",
        verbose_name=_("Dobavljač"),
    )
    contract = models.ForeignKey(
        "ugovori.Contract",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="nabavka_cases",
        verbose_name=_("Osnovni ugovor"),
    )
    vehicle = models.ForeignKey(
        "fleet.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_cases",
        verbose_name=_("Vozilo"),
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_responsible_cases",
        verbose_name=_("Odgovorno lice"),
    )
    estimated_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Procenjena vrednost"),
    )
    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default="RSD",
        verbose_name=_("Valuta"),
    )
    needed_by = models.DateField(null=True, blank=True, verbose_name=_("Datum zahteva"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Ažurirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_created_cases",
        verbose_name=_("Kreirao"),
    )

    class Meta:
        db_table = "nabavka_procurement_case"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Predmet nabavke")
        verbose_name_plural = _("Predmeti nabavke")
        indexes = [
            models.Index(fields=["case_type", "status"]),
            models.Index(fields=["needed_by"]),
        ]

    def __str__(self):
        return f"{self.case_number or 'NAB'} - {self.title}"

    def get_sequence_year(self):
        return (self.created_at.date() if self.created_at else timezone.localdate()).year

    def get_case_type_prefix(self):
        if self.is_garage:
            return self.GARAGE_CASE_TYPE_PREFIXES.get(
                self.case_type,
                self.CASE_TYPE_PREFIXES.get(self.case_type, "ZN"),
            )
        return self.CASE_TYPE_PREFIXES.get(self.case_type, "ZN")

    def get_center_code(self):
        center_code = getattr(self.job_code, "center", None)
        if not center_code:
            raise ValidationError({"job_code": _("Nedostaje sifra centra za broj zahteva.")})
        return str(center_code).strip()

    def generate_case_number(self):
        year = self.get_sequence_year()
        center_code = self.get_center_code()
        type_prefix = self.get_case_type_prefix()
        prefix = f"{type_prefix}-{center_code}/{year}-"
        existing = ProcurementCase.objects.filter(case_number__startswith=prefix).values_list(
            "case_number", flat=True
        )
        max_number = 0
        for case_number in existing:
            try:
                num_part = case_number.split(prefix, 1)[1]
                max_number = max(max_number, int(num_part))
            except Exception:
                continue

        return f"{prefix}{max_number + 1}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            self.case_number = self.generate_case_number()
        super().save(*args, **kwargs)


class ProcurementItem(models.Model):
    SOURCE_EUF = "euf"
    SOURCE_UF = "uf"
    SOURCE_GOODS = "goods"
    SOURCE_CHOICES = [
        ("", _("Bez povezivanja")),
        (SOURCE_EUF, "EUF"),
        (SOURCE_UF, "UF"),
        (SOURCE_GOODS, _("Roba")),
    ]

    procurement_case = models.ForeignKey(
        ProcurementCase,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Predmet nabavke"),
    )
    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        blank=True,
        verbose_name=_("Tip povezivanja"),
    )
    euf_invoice = models.ForeignKey(
        "ProcurementInvoice",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="procurement_items",
        verbose_name=_("EUF"),
    )
    uf_item = models.ForeignKey(
        "EufItemSnapshot",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="procurement_items",
        verbose_name=_("UF"),
    )
    uf_invoice = models.ForeignKey(
        "UfInvoiceSnapshot",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="procurement_items",
        verbose_name=_("UF faktura"),
    )
    goods_item = models.ForeignKey(
        "GoodsSnapshot",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="procurement_items",
        verbose_name=_("Roba"),
    )
    name = models.CharField(max_length=255, verbose_name=_("Naziv"))
    uom = models.CharField(max_length=30, verbose_name=_("Jedinica mere"))
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Količina"))
    estimated_unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Procenjena cena"),
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Napomena"))

    class Meta:
        db_table = "nabavka_procurement_item"
        verbose_name = _("Stavka nabavke")
        verbose_name_plural = _("Stavke nabavke")

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.uom})"

    def clean(self):
        super().clean()
        source_fields = {
            self.SOURCE_EUF: self.euf_invoice_id,
            self.SOURCE_UF: self.uf_invoice_id,
            self.SOURCE_GOODS: self.goods_item_id,
        }
        selected_fields = [source for source, value in source_fields.items() if value]
        if self.source_type:
            if source_fields.get(self.source_type) is None or len(selected_fields) != 1:
                raise ValidationError(_("Izaberite jedan zapis koji odgovara tipu povezivanja."))
        elif selected_fields:
            raise ValidationError(_("Izaberite tip povezivanja za povezani zapis."))

    @property
    def source_reference_label(self):
        if self.source_type == self.SOURCE_EUF and self.euf_invoice:
            return f"EUF: {self.euf_invoice.invoice_number}"
        if self.source_type == self.SOURCE_UF and self.uf_invoice:
            return f"UF: {self.uf_invoice.invoice_number or self.uf_invoice.purchase_invoice_id or self.uf_invoice.source_key}"
        if self.source_type == self.SOURCE_UF and self.uf_item:
            return f"UF: {self.uf_item.invoice_number or self.uf_item.purchase_invoice_id or self.uf_item.source_key}"
        if self.source_type == self.SOURCE_GOODS and self.goods_item:
            invoice_number = self.goods_item.linked_document or "/"
            return (
                f"Roba: {self.goods_item.article_code or '/'} - "
                f"{self.goods_item.article_name or ''} "
                f"(Faktura: {invoice_number})"
            ).strip()
        return ""

    @property
    def source_reference_id(self):
        if self.source_type == self.SOURCE_EUF:
            return self.euf_invoice_id or ""
        if self.source_type == self.SOURCE_UF:
            return self.uf_invoice_id or self.uf_item_id or ""
        if self.source_type == self.SOURCE_GOODS:
            return self.goods_item_id or ""
        return ""

    @property
    def estimated_total(self):
        if self.estimated_unit_price is None or self.quantity is None:
            return None
        return self.estimated_unit_price * self.quantity

    @property
    def invoice_assignment(self):
        try:
            return self.invoice_link
        except ProcurementItemInvoiceLink.DoesNotExist:
            return None

    @property
    def linked_invoice(self):
        assignment = self.invoice_assignment
        return assignment.invoice if assignment else None


class ProcurementInvoiceLink(models.Model):
    SOURCE_EUF = "euf"
    SOURCE_CHOICES = [
        (SOURCE_EUF, "EUF"),
    ]

    procurement_case = models.ForeignKey(
        ProcurementCase,
        on_delete=models.CASCADE,
        related_name="invoice_links",
        verbose_name=_("Predmet nabavke"),
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_EUF,
        db_index=True,
        verbose_name=_("Izvor"),
    )
    euf_key = models.CharField(max_length=64, db_index=True, verbose_name=_("EUF ključ"))
    invoice_number = models.CharField(max_length=100, verbose_name=_("Broj fakture"))
    invoice_date = models.DateField(null=True, blank=True, verbose_name=_("Datum fakture"))
    supplier_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Naziv partnera"))
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Iznos"),
    )
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_invoice_links",
        verbose_name=_("Povezao"),
    )

    class Meta:
        db_table = "nabavka_invoice_link"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Veza fakture")
        verbose_name_plural = _("Veze faktura")
        constraints = [
            models.UniqueConstraint(
                fields=["procurement_case", "source", "euf_key"],
                name="uniq_nabavka_case_invoice_source_key",
            )
        ]

    def __str__(self):
        return f"{self.invoice_number} -> {self.procurement_case}"


class ProcurementInvoice(models.Model):
    SOURCE_EUF = "euf"
    JOB_CODE_SOURCE_VEHICLE_SNAPSHOT = "vehicle_snapshot"
    JOB_CODE_SOURCE_CHOICES = [
        (JOB_CODE_SOURCE_VEHICLE_SNAPSHOT, _("Sifra posla automobila - snapshot")),
    ]
    SOURCE_CHOICES = [
        (SOURCE_EUF, "EUF"),
    ]

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_EUF,
        db_index=True,
        verbose_name=_("Izvor"),
    )
    euf_key = models.CharField(max_length=64, db_index=True, verbose_name=_("EUF kljuc"))
    invoice_number = models.CharField(max_length=100, db_index=True, verbose_name=_("Broj fakture"))
    invoice_date = models.DateField(null=True, blank=True, db_index=True, verbose_name=_("Datum fakture"))
    invoice_date_raw = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Datum iz izvora"))
    supplier_name = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name=_("Naziv partnera"))
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name=_("Iznos"))
    center = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Centar"))
    warehouse = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Magacin"))
    registration = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Registracija"))
    center_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Naziv centra"))
    job_code = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_invoices",
        verbose_name=_("OJ / sifra posla"),
    )
    job_code_source = models.CharField(
        max_length=30,
        choices=JOB_CODE_SOURCE_CHOICES,
        blank=True,
        default="",
        verbose_name=_("Izvor sifre posla"),
    )
    vehicle_job_code_assigned_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Datum dodele sifre posla vozilu"),
    )
    is_garage = models.BooleanField(default=False, verbose_name=_("Garaza"))
    vehicle = models.ForeignKey(
        "fleet.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_invoices",
        verbose_name=_("Vozilo"),
    )
    goes_to_warehouse = models.BooleanField(default=False, verbose_name=_("Ide u magacin"))
    is_returned = models.BooleanField(default=False, verbose_name=_("Vraceno"))
    internal_note = models.TextField(blank=True, null=True, verbose_name=_("Interna napomena"))
    synced_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Sinhronizovano"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        db_table = "nabavka_invoice"
        ordering = ["-invoice_date", "-id"]
        verbose_name = _("Faktura nabavke")
        verbose_name_plural = _("Fakture nabavke")
        constraints = [
            models.UniqueConstraint(fields=["source", "euf_key"], name="uniq_nabavka_invoice_source_key")
        ]
        indexes = [
            models.Index(fields=["invoice_number", "supplier_name"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier_name or ''}".strip()

    @property
    def is_garage_related(self):
        return self.item_links.filter(procurement_item__procurement_case__is_garage=True).exists()

    @property
    def job_code_is_vehicle_snapshot(self):
        return self.job_code_source == self.JOB_CODE_SOURCE_VEHICLE_SNAPSHOT

    @property
    def job_code_source_label(self):
        if self.job_code_is_vehicle_snapshot:
            return _("Sifra posla automobila - snapshot")
        return ""

    def sync_primary_job_code_link(self, created_by=None):
        if not self.pk:
            return None
        primary_links = self.job_code_links.filter(
            kind=ProcurementInvoiceJobCodeLink.KIND_PRIMARY
        )
        if not self.job_code_id:
            primary_links.filter(is_returned=False).delete()
            primary_links.filter(is_returned=True).update(
                kind=ProcurementInvoiceJobCodeLink.KIND_ADDITIONAL
            )
            return None

        link, created = ProcurementInvoiceJobCodeLink.objects.get_or_create(
            invoice=self,
            job_code=self.job_code,
            defaults={
                "kind": ProcurementInvoiceJobCodeLink.KIND_PRIMARY,
                "created_by": created_by,
            },
        )
        update_fields = []
        if link.kind != ProcurementInvoiceJobCodeLink.KIND_PRIMARY:
            link.kind = ProcurementInvoiceJobCodeLink.KIND_PRIMARY
            update_fields.append("kind")
        if created_by and not link.created_by_id:
            link.created_by = created_by
            update_fields.append("created_by")
        if update_fields:
            link.save(update_fields=update_fields)

        old_primary_links = primary_links.exclude(pk=link.pk)
        old_primary_links.filter(is_returned=False).delete()
        old_primary_links.filter(is_returned=True).update(
            kind=ProcurementInvoiceJobCodeLink.KIND_ADDITIONAL
        )
        return link


class EufItemSnapshot(models.Model):
    source_key = models.CharField(max_length=64, unique=True, verbose_name=_("Kljuc izvora"))
    uf_invoice = models.ForeignKey(
        "UfInvoiceSnapshot",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="items",
        verbose_name=_("UF faktura"),
    )
    purchase_invoice_id = models.CharField(max_length=40, blank=True, null=True, db_index=True, verbose_name=_("UF ID"))
    creation_date = models.DateField(blank=True, null=True, db_index=True, verbose_name=_("Datum kreiranja"))
    document_date = models.DateField(blank=True, null=True, db_index=True, verbose_name=_("Datum dokumenta"))
    due_date = models.DateField(blank=True, null=True, verbose_name=_("Datum dospeca"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    contract_document_reference = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Referenca ugovora"))
    invoice_number = models.CharField(max_length=120, blank=True, null=True, db_index=True, verbose_name=_("Broj fakture"))
    tender_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Broj tendera"))
    partner_pib = models.CharField(max_length=15, blank=True, null=True, db_index=True, verbose_name=_("PIB partnera"))
    partner_mb = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("MB partnera"))
    partner_name = models.CharField(max_length=400, blank=True, null=True, db_index=True, verbose_name=_("Partner"))
    total = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Ukupno"))
    base_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Osnovica"))
    payment_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Placanje"))
    uom = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("JM"))
    item_name = models.TextField(blank=True, null=True, verbose_name=_("Naziv stavke"))
    quantity = models.DecimalField(max_digits=18, decimal_places=3, blank=True, null=True, verbose_name=_("Kolicina"))
    price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Cena"))
    value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Vrednost"))
    account = models.CharField(max_length=6, blank=True, null=True, db_index=True, verbose_name=_("Konto"))
    synced_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Sinhronizovano"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        db_table = "nabavka_euf_item_snapshot"
        ordering = ["-document_date", "-id"]
        verbose_name = _("UF stavka")
        verbose_name_plural = _("UF stavke")
        indexes = [
            models.Index(fields=["invoice_number", "partner_name"]),
        ]

    def __str__(self):
        return f"{self.invoice_number or '/'} - {self.item_name or ''}".strip()


class UfInvoiceSnapshot(models.Model):
    source_key = models.CharField(max_length=64, unique=True, verbose_name=_("Kljuc izvora"))
    purchase_invoice_id = models.CharField(max_length=40, blank=True, null=True, db_index=True, verbose_name=_("UF ID"))
    invoice_number = models.CharField(max_length=120, blank=True, null=True, db_index=True, verbose_name=_("Broj fakture"))
    partner_pib = models.CharField(max_length=15, blank=True, null=True, db_index=True, verbose_name=_("PIB partnera"))
    partner_mb = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("MB partnera"))
    partner_name = models.CharField(max_length=400, blank=True, null=True, db_index=True, verbose_name=_("Partner"))
    document_date = models.DateField(blank=True, null=True, db_index=True, verbose_name=_("Datum dokumenta"))
    creation_date = models.DateField(blank=True, null=True, verbose_name=_("Datum kreiranja"))
    due_date = models.DateField(blank=True, null=True, verbose_name=_("Datum dospeca"))
    total = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Ukupno"))
    base_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Osnovica"))
    payment_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Placanje"))
    item_value_total = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Vrednost stavki"))
    item_count = models.PositiveIntegerField(default=0, verbose_name=_("Broj stavki"))
    accounts = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Konta"))
    synced_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Sinhronizovano"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        db_table = "nabavka_uf_invoice_snapshot"
        ordering = ["-document_date", "-id"]
        verbose_name = _("UF faktura")
        verbose_name_plural = _("UF fakture")
        indexes = [
            models.Index(fields=["invoice_number", "partner_name"]),
        ]

    def __str__(self):
        return f"{self.invoice_number or self.purchase_invoice_id or '/'} - {self.partner_name or ''}".strip()


class GoodsSnapshot(models.Model):
    source_key = models.CharField(max_length=64, unique=True, verbose_name=_("Kljuc izvora"))
    year = models.CharField(max_length=4, blank=True, null=True, db_index=True, verbose_name=_("Godina"))
    document_number = models.IntegerField(blank=True, null=True, db_index=True, verbose_name=_("Broj dokumenta"))
    document_type = models.CharField(max_length=3, blank=True, null=True, db_index=True, verbose_name=_("Vrsta dokumenta"))
    organizational_unit = models.IntegerField(blank=True, null=True, db_index=True, verbose_name=_("OJ"))
    partner_code = models.IntegerField(blank=True, null=True, db_index=True, verbose_name=_("Sifra partnera"))
    partner_name = models.CharField(max_length=400, blank=True, null=True, db_index=True, verbose_name=_("Partner"))
    document_date = models.DateField(blank=True, null=True, db_index=True, verbose_name=_("Datum"))
    linked_document = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Vezni dokument"))
    debit = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Potrazuje"))
    currency = models.CharField(max_length=3, blank=True, null=True, verbose_name=_("Valuta"))
    foreign_currency_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Devize"))
    subject_code = models.IntegerField(blank=True, null=True, verbose_name=_("Sifra predmeta"))
    line_number = models.IntegerField(blank=True, null=True, verbose_name=_("Stavka"))
    article_code = models.CharField(max_length=20, blank=True, null=True, db_index=True, verbose_name=_("Sifra artikla"))
    article_type = models.CharField(max_length=8, blank=True, null=True, db_index=True, verbose_name=_("Vrsta artikla"))
    article_name = models.CharField(max_length=80, blank=True, null=True, db_index=True, verbose_name=_("Naziv artikla"))
    quantity = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Kolicina"))
    price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, verbose_name=_("Cena"))
    synced_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Sinhronizovano"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        db_table = "nabavka_goods_snapshot"
        ordering = ["-document_date", "-id"]
        verbose_name = _("Roba")
        verbose_name_plural = _("Roba")
        indexes = [
            models.Index(fields=["document_number", "partner_name"]),
            models.Index(fields=["article_code", "article_name"]),
        ]

    def __str__(self):
        return f"{self.document_number or '/'} - {self.article_name or ''}".strip()


class ProcurementItemInvoiceLink(models.Model):
    procurement_item = models.OneToOneField(
        ProcurementItem,
        on_delete=models.CASCADE,
        related_name="invoice_link",
        verbose_name=_("Stavka nabavke"),
    )
    invoice = models.ForeignKey(
        ProcurementInvoice,
        on_delete=models.CASCADE,
        related_name="item_links",
        verbose_name=_("Faktura"),
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_item_invoice_links",
        verbose_name=_("Povezao"),
    )

    class Meta:
        db_table = "nabavka_item_invoice_link"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Veza stavke i fakture")
        verbose_name_plural = _("Veze stavki i faktura")

    def __str__(self):
        return f"{self.procurement_item} -> {self.invoice}"


class ProcurementInvoiceJobCodeLink(models.Model):
    KIND_PRIMARY = "primary"
    KIND_ADDITIONAL = "additional"
    KIND_CHOICES = [
        (KIND_PRIMARY, _("Osnovna")),
        (KIND_ADDITIONAL, _("Dodatna")),
    ]

    invoice = models.ForeignKey(
        ProcurementInvoice,
        on_delete=models.CASCADE,
        related_name="job_code_links",
        verbose_name=_("Faktura"),
    )
    job_code = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.PROTECT,
        related_name="nabavka_invoice_job_code_links",
        verbose_name=_("OJ / sifra posla"),
    )
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        default=KIND_ADDITIONAL,
        db_index=True,
        verbose_name=_("Tip veze"),
    )
    is_returned = models.BooleanField(default=False, db_index=True, verbose_name=_("Vraceno"))
    returned_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Vraceno u"))
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_returned_invoice_job_code_links",
        verbose_name=_("Oznacio kao vraceno"),
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_invoice_job_code_links",
        verbose_name=_("Povezao"),
    )

    class Meta:
        db_table = "nabavka_invoice_job_code_link"
        ordering = ["job_code__code", "id"]
        verbose_name = _("Veza fakture i sifre posla")
        verbose_name_plural = _("Veze faktura i sifara posla")
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "job_code"],
                name="uniq_nabavka_invoice_job_code",
            )
        ]

    def __str__(self):
        return f"{self.invoice} -> {self.job_code}"


class ProcurementContractLink(models.Model):
    procurement_case = models.ForeignKey(
        ProcurementCase,
        on_delete=models.CASCADE,
        related_name="contract_links",
        verbose_name=_("Predmet nabavke"),
    )
    contract = models.ForeignKey(
        "ugovori.Contract",
        on_delete=models.PROTECT,
        related_name="nabavka_links",
        verbose_name=_("Ugovor"),
    )
    invoice_link = models.ForeignKey(
        ProcurementInvoiceLink,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="contract_links",
        verbose_name=_("Faktura"),
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_contract_links",
        verbose_name=_("Povezao"),
    )

    class Meta:
        db_table = "nabavka_contract_link"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Veza ugovora")
        verbose_name_plural = _("Veze ugovora")
        constraints = [
            models.UniqueConstraint(
                fields=["procurement_case", "contract"],
                name="uniq_nabavka_case_contract",
            )
        ]

    def __str__(self):
        return f"{self.contract} -> {self.procurement_case}"


class ProcurementInvoiceContractLink(models.Model):
    invoice = models.ForeignKey(
        ProcurementInvoice,
        on_delete=models.CASCADE,
        related_name="contract_links",
        verbose_name=_("Faktura"),
    )
    contract = models.ForeignKey(
        "ugovori.Contract",
        on_delete=models.PROTECT,
        related_name="nabavka_invoice_links",
        verbose_name=_("Kupovni ugovor"),
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_invoice_contract_links",
        verbose_name=_("Povezao"),
    )

    class Meta:
        db_table = "nabavka_invoice_contract_link"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Veza fakture i ugovora")
        verbose_name_plural = _("Veze faktura i ugovora")
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "contract"],
                name="uniq_nabavka_invoice_contract",
            )
        ]

    def __str__(self):
        return f"{self.invoice} -> {self.contract}"


class PublicProcurementPlanVersion(models.Model):
    year = models.PositiveIntegerField(db_index=True, verbose_name=_("Godina"))
    version_number = models.PositiveIntegerField(verbose_name=_("Verzija"))
    source_filename = models.CharField(max_length=255, verbose_name=_("Excel fajl"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    imported_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Ucitano"))
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="public_procurement_plan_imports",
        verbose_name=_("Uvezao"),
    )
    total_rows = models.PositiveIntegerField(default=0, verbose_name=_("Ukupno stavki"))
    added_count = models.PositiveIntegerField(default=0, verbose_name=_("Dodato"))
    changed_count = models.PositiveIntegerField(default=0, verbose_name=_("Izmenjeno"))
    unchanged_count = models.PositiveIntegerField(default=0, verbose_name=_("Bez izmene"))
    removed_count = models.PositiveIntegerField(default=0, verbose_name=_("Uklonjeno"))

    class Meta:
        db_table = "nabavka_public_procurement_plan_version"
        ordering = ["-year", "-version_number"]
        verbose_name = _("Verzija plana javnih nabavki")
        verbose_name_plural = _("Verzije plana javnih nabavki")
        constraints = [
            models.UniqueConstraint(
                fields=["year", "version_number"],
                name="uniq_nabavka_public_procurement_plan_version_year_number",
            )
        ]

    def __str__(self):
        return f"{self.year} v{self.version_number}"


class PublicProcurementPlanItem(models.Model):
    class PlanType(models.TextChoices):
        PUBLIC = "public", _("Javna nabavka")
        EXEMPT = "exempt", _("Nabavka bez primene ZJN")

    class DiffStatus(models.TextChoices):
        ADDED = "added", _("Dodato")
        CHANGED = "changed", _("Izmenjeno")
        UNCHANGED = "unchanged", _("Bez izmene")
        REMOVED = "removed", _("Uklonjeno")

    version = models.ForeignKey(
        PublicProcurementPlanVersion,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Verzija"),
    )
    previous_item = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="next_version_items",
        verbose_name=_("Prethodna stavka"),
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PlanType.choices,
        db_index=True,
        verbose_name=_("Tip plana"),
    )
    diff_status = models.CharField(
        max_length=20,
        choices=DiffStatus.choices,
        db_index=True,
        verbose_name=_("Status razlike"),
    )
    stable_key = models.CharField(max_length=120, db_index=True, verbose_name=_("Kljuc stavke"))
    content_hash = models.CharField(max_length=64, db_index=True, verbose_name=_("Hash sadrzaja"))
    source_sheet = models.CharField(max_length=120, verbose_name=_("Sheet"))
    source_row = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Excel red"))
    item_number = models.CharField(max_length=50, blank=True, null=True, db_index=True, verbose_name=_("Redni broj"))
    subject_type = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Vrsta predmeta"))
    title = models.TextField(verbose_name=_("Predmet nabavke"))
    estimated_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Procenjena vrednost"),
    )
    procurement_category = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Predmet"))
    procedure_type = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Vrsta postupka"))
    quarter = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Okvirno vreme / kvartal"))
    cpv = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("CPV"))
    nuts = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("NSTJ"))
    technique = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Tehnika / organizacioni deo"))
    conducted_by_other = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Sprovodi drugi narucilac"))
    exemption_basis = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Osnov izuzeca"))
    valuation_method = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Nacin procene vrednosti"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    raw_data = models.JSONField(default=dict, blank=True, verbose_name=_("Izvorni podaci"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))

    class Meta:
        db_table = "nabavka_public_procurement_plan_item"
        ordering = ["plan_type", "source_sheet", "item_number", "id"]
        verbose_name = _("Stavka plana javnih nabavki")
        verbose_name_plural = _("Stavke plana javnih nabavki")
        constraints = [
            models.UniqueConstraint(
                fields=["version", "stable_key"],
                name="uniq_nabavka_public_procurement_plan_item_version_key",
            )
        ]
        indexes = [
            models.Index(fields=["plan_type", "diff_status"]),
        ]

    def __str__(self):
        return f"{self.item_number or '/'} - {self.title}"


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Nacrt")
        SENT = "sent", _("Poslato")
        CONFIRMED = "confirmed", _("Potvrđeno")
        CLOSED = "closed", _("Zatvoreno")
        CANCELLED = "cancelled", _("Otkazano")

    procurement_case = models.ForeignKey(
        ProcurementCase,
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Predmet nabavke"),
    )
    order_number = models.CharField(max_length=100, unique=True, verbose_name=_("Broj narudžbenice"))
    order_date = models.DateField(default=timezone.localdate, verbose_name=_("Datum narudžbenice"))
    supplier = models.ForeignKey(
        "ugovori.Partner",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_orders",
        verbose_name=_("Dobavljač"),
    )
    contract = models.ForeignKey(
        "ugovori.Contract",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_orders",
        verbose_name=_("Ugovor"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name=_("Status"),
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Iznos"),
    )
    currency = models.CharField(
        max_length=10,
        choices=ProcurementCase.CURRENCY_CHOICES,
        default="RSD",
        verbose_name=_("Valuta"),
    )
    note = models.TextField(blank=True, null=True, verbose_name=_("Napomena"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_purchase_orders",
        verbose_name=_("Kreirao"),
    )

    class Meta:
        db_table = "nabavka_purchase_order"
        ordering = ["-order_date", "-id"]
        verbose_name = _("Narudžbenica")
        verbose_name_plural = _("Narudžbenice")

    def __str__(self):
        return self.order_number


class ProcurementStatusLog(models.Model):
    procurement_case = models.ForeignKey(
        ProcurementCase,
        on_delete=models.CASCADE,
        related_name="status_logs",
        verbose_name=_("Predmet nabavke"),
    )
    old_status = models.CharField(
        max_length=30,
        choices=ProcurementCase.Status.choices,
        blank=True,
        null=True,
        verbose_name=_("Stari status"),
    )
    new_status = models.CharField(
        max_length=30,
        choices=ProcurementCase.Status.choices,
        verbose_name=_("Novi status"),
    )
    comment = models.TextField(blank=True, null=True, verbose_name=_("Komentar"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nabavka_status_logs",
        verbose_name=_("Korisnik"),
    )

    class Meta:
        db_table = "nabavka_status_log"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Promena statusa")
        verbose_name_plural = _("Promene statusa")

    def __str__(self):
        return f"{self.procurement_case} -> {self.new_status}"
