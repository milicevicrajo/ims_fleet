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
            self.SOURCE_UF: self.uf_item_id,
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
        if self.source_type == self.SOURCE_UF and self.uf_item:
            return f"UF: {self.uf_item.invoice_number or self.uf_item.purchase_invoice_id or self.uf_item.source_key}"
        if self.source_type == self.SOURCE_GOODS and self.goods_item:
            return f"Roba: {self.goods_item.article_code or '/'} - {self.goods_item.article_name or ''}".strip()
        return ""

    @property
    def source_reference_id(self):
        return self.euf_invoice_id or self.uf_item_id or self.goods_item_id or ""

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


class EufItemSnapshot(models.Model):
    source_key = models.CharField(max_length=64, unique=True, verbose_name=_("Kljuc izvora"))
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
