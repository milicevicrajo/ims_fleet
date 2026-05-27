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
    needed_by = models.DateField(null=True, blank=True, verbose_name=_("Potrebno do"))
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

    def clean(self):
        if self.is_garage and not self.vehicle_id:
            raise ValidationError({"vehicle": _("Ako je predmet garažni, izbor vozila je obavezan.")})

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
    procurement_case = models.ForeignKey(
        ProcurementCase,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Predmet nabavke"),
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
