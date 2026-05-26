from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


class Partner(models.Model):
    LEGAL_ENTITY = "legal_entity"
    PERSON = "person"
    BANK = "bank"
    PARTNER_TYPE_CHOICES = [
        (LEGAL_ENTITY, "Pravno lice"),
        (PERSON, "Fizicko lice"),
        (BANK, "Banka"),
    ]

    DOMESTIC = "domestic"
    FOREIGN = "foreign"
    RESIDENCY_CHOICES = [
        (DOMESTIC, "Domaći"),
        (FOREIGN, "Strani"),
    ]

    name = models.CharField(max_length=255, verbose_name="Naziv / Ime i prezime")
    partner_type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default=LEGAL_ENTITY,
        db_index=True,
        verbose_name="Tip partnera",
    )
    residency = models.CharField(
        max_length=20,
        choices=RESIDENCY_CHOICES,
        default=DOMESTIC,
        db_index=True,
        verbose_name="Rezidentnost",
    )
    external_sif_par = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Šifra (stari sistem)",
    )
    pib = models.CharField(max_length=50, blank=True, null=True, verbose_name="PIB")
    maticni_broj = models.CharField(max_length=20, blank=True, null=True, verbose_name="Matični broj")
    jmbg = models.CharField(max_length=13, blank=True, null=True, verbose_name="JMBG")
    passport_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Broj pasoša")
    foreign_tax_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Strani poreski ID"
    )
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zemlja")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Grad / Mesto")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresa")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telefon")
    contact_person = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Kontakt osoba"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Napomena")
    data_source = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Izvor podataka",
    )
    data_validated = models.BooleanField(default=False, db_index=True, verbose_name="Podaci validni")
    data_validated_at = models.DateTimeField(null=True, blank=True, verbose_name="Datum validacije")
    apr_status = models.CharField(max_length=100, blank=True, null=True, verbose_name="APR status")
    apr_checked_at = models.DateTimeField(null=True, blank=True, verbose_name="APR provera")
    is_active = models.BooleanField(default=True, verbose_name="Aktivan", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ugovori_partneri_kreirani",
    )

    class Meta:
        db_table = "ugovori_partner"
        verbose_name = "Partner"
        verbose_name_plural = "Partneri"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.partner_type == self.LEGAL_ENTITY and self.residency == self.DOMESTIC:
            if not self.pib and not self.maticni_broj:
                raise ValidationError(
                    "Domaće pravno lice treba da ima PIB i/ili matični broj."
                )
        if self.partner_type == self.PERSON and self.residency == self.DOMESTIC:
            if not self.jmbg:
                raise ValidationError("Domaće fizičko lice treba da ima JMBG.")


class ContractType(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Šifra")
    name = models.CharField(max_length=100, verbose_name="Naziv")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    is_active = models.BooleanField(default=True, verbose_name="Aktivan")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Redosled")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ugovori_contract_type"
        verbose_name = "Tip ugovora"
        verbose_name_plural = "Tipovi ugovora"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.code} – {self.name}"


class Contract(models.Model):
    MAIN = "MAIN"
    ANNEX = "ANNEX"
    KIND_CHOICES = [
        (MAIN, "Glavni ugovor"),
        (ANNEX, "Aneks"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_TERMINATED = "terminated"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Nacrt"),
        (STATUS_ACTIVE, "Aktivan"),
        (STATUS_EXPIRED, "Istekao"),
        (STATUS_TERMINATED, "Raskinut"),
        (STATUS_ARCHIVED, "Arhiviran"),
    ]

    CURRENCY_CHOICES = [
        ("RSD", "RSD"),
        ("EUR", "EUR"),
        ("USD", "USD"),
        ("CHF", "CHF"),
    ]
    VALUE_TYPE_FIXED = "fixed"
    VALUE_TYPE_HOURLY = "hourly"
    VALUE_TYPE_MONTHLY = "monthly"
    VALUE_TYPE_MAN_MONTH = "man_month"
    VALUE_TYPE_UNIT = "unit"
    VALUE_TYPE_UNDEFINED = "undefined"
    VALUE_TYPE_CHOICES = [
        (VALUE_TYPE_FIXED, "Fiksna vrednost"),
        (VALUE_TYPE_HOURLY, "Po radnom satu"),
        (VALUE_TYPE_MONTHLY, "Mesečno"),
        (VALUE_TYPE_MAN_MONTH, "Čovek mesec"),
        (VALUE_TYPE_UNIT, "Po jedinici"),
        (VALUE_TYPE_UNDEFINED, "Bez definisane vrednosti"),
    ]

    kind = models.CharField(
        max_length=10,
        choices=KIND_CHOICES,
        default=MAIN,
        db_index=True,
        verbose_name="Vrsta",
    )
    contract_type = models.ForeignKey(
        ContractType,
        on_delete=models.PROTECT,
        verbose_name="Tip ugovora",
        related_name="contracts",
    )
    parent_contract = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="annexes",
        verbose_name="Glavni ugovor",
    )
    contract_number = models.CharField(max_length=100, unique=True, verbose_name="Broj ugovora")
    title = models.CharField(max_length=255, verbose_name="Naslov")
    subject = models.TextField(blank=True, null=True, verbose_name="Predmet ugovora")
    contract_date = models.DateField(verbose_name="Datum ugovora")
    valid_from = models.DateField(null=True, blank=True, verbose_name="Važi od")
    valid_to = models.DateField(null=True, blank=True, verbose_name="Važi do")
    value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Vrednost"
    )
    value_type = models.CharField(
        max_length=20,
        choices=VALUE_TYPE_CHOICES,
        default=VALUE_TYPE_FIXED,
        db_index=True,
        verbose_name="Tip vrednosti",
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Cena po jedinici",
    )
    unit_label = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Jedinica",
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCY_CHOICES, default="RSD", verbose_name="Valuta"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        verbose_name="Status",
    )
    has_incoming_menice = models.BooleanField(
        default=False,
        verbose_name="Ima ulazne menice",
    )
    has_outgoing_menice = models.BooleanField(
        default=False,
        verbose_name="Ima izlazne menice",
    )
    has_guarantees = models.BooleanField(
        default=False,
        verbose_name="Ima garancije",
    )
    file = models.FileField(
        upload_to="ugovori/files/%Y/%m/", null=True, blank=True, verbose_name="Fajl ugovora"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Napomena")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ugovori_kreirani",
    )

    class Meta:
        db_table = "ugovori_contract"
        verbose_name = "Ugovor"
        verbose_name_plural = "Ugovori"
        ordering = ["-contract_date", "-created_at"]
        indexes = [
            models.Index(fields=["kind", "status"]),
        ]

    def __str__(self):
        return f"{self.contract_number} – {self.title}"

    @staticmethod
    def _delete_file_after_commit(file_field):
        if not file_field:
            return

        storage = file_field.storage
        name = file_field.name
        transaction.on_commit(lambda: storage.delete(name) if storage.exists(name) else None)

    def save(self, *args, **kwargs):
        old_file = None
        if self.pk:
            old_file = (
                type(self).objects.filter(pk=self.pk)
                .values_list("file", flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        new_file = self.file.name if self.file else ""
        if old_file and old_file != new_file:
            old_field = self._meta.get_field("file").attr_class(
                self,
                self._meta.get_field("file"),
                old_file,
            )
            self._delete_file_after_commit(old_field)

    def delete(self, *args, **kwargs):
        file_field = self.file
        super().delete(*args, **kwargs)
        self._delete_file_after_commit(file_field)

    def clean(self):
        if self.kind == self.ANNEX and not self.parent_contract_id:
            raise ValidationError({"parent_contract": "Aneks mora imati glavni ugovor."})
        if self.kind == self.MAIN and self.parent_contract_id:
            raise ValidationError(
                {"parent_contract": "Glavni ugovor ne sme imati nadređeni ugovor."}
            )
        if self.parent_contract_id:
            if self.pk and self.parent_contract_id == self.pk:
                raise ValidationError(
                    {"parent_contract": "Ugovor ne može biti parent sam sebi."}
                )
            if self.parent_contract.kind != self.MAIN:
                raise ValidationError(
                    {"parent_contract": "Nadređeni ugovor mora biti tipa 'Glavni ugovor'."}
                )
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError(
                {"valid_to": "Datum 'Važi do' ne sme biti pre datuma 'Važi od'."}
            )


class ContractParty(models.Model):
    ROLE_CHOICES = [
        ("kupac", "Kupac"),
        ("prodavac", "Prodavac"),
        ("zakupodavac", "Zakupodavac"),
        ("zakupac", "Zakupac"),
        ("izvođač", "Izvođač radova"),
        ("naručilac", "Naručilac"),
        ("garant", "Garant / Žirant"),
        ("ostalo", "Ostalo"),
    ]

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="parties",
        verbose_name="Ugovor",
    )
    partner = models.ForeignKey(
        Partner,
        on_delete=models.PROTECT,
        related_name="contract_parties",
        verbose_name="Partner",
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, verbose_name="Uloga")
    party_contract_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Broj ugovora kod stranke",
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name="Napomena")

    class Meta:
        db_table = "ugovori_contract_party"
        verbose_name = "Stranka ugovora"
        verbose_name_plural = "Stranke ugovora"
        unique_together = [("contract", "partner", "role")]

    def __str__(self):
        return f"{self.partner} – {self.get_role_display()}"


class ContractMenicaLink(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="menica_links",
        verbose_name="Ugovor",
    )
    menica = models.ForeignKey(
        "menice.Menica",
        on_delete=models.PROTECT,
        related_name="contract_links",
        null=True,
        blank=True,
        verbose_name="Menica",
    )
    ulazna_menica = models.ForeignKey(
        "menice.UlaznaMenica",
        on_delete=models.PROTECT,
        related_name="contract_links",
        null=True,
        blank=True,
        verbose_name="Ulazna menica",
    )
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name="Napomena")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ugovori_menica_linkovi_kreirani",
    )

    class Meta:
        db_table = "ugovori_contract_menica_link"
        verbose_name = "Veza ugovora i menice"
        verbose_name_plural = "Veze ugovora i menica"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contract.contract_number} - {self.instrument_serial()}"

    def clean(self):
        if bool(self.menica_id) == bool(self.ulazna_menica_id):
            raise ValidationError("Izaberite tacno jednu menicu.")

    def instrument_serial(self):
        if self.menica_id:
            return self.menica.serijski_broj_menice or f"Menica {self.menica_id}"
        if self.ulazna_menica_id:
            return self.ulazna_menica.serijski_broj_menice
        return "-"

    def instrument_type_display(self):
        if self.menica_id:
            return self.menica.get_tip_display()
        if self.ulazna_menica_id:
            return "Ulazna menica"
        return "-"

    def instrument_partner(self):
        if self.menica_id:
            return self.menica.naziv_duznika or self.menica.izdavalac_menice or "-"
        if self.ulazna_menica_id:
            return self.ulazna_menica.naziv_pravnog_lica or "-"
        return "-"

    def instrument_amount_display(self):
        if self.menica_id and self.menica.iznos_menice is not None:
            return f"{self.menica.iznos_menice:.2f} {self.menica.valuta_menice or ''}".strip()
        if self.ulazna_menica_id and self.ulazna_menica.procenat_iznos is not None:
            return f"{self.ulazna_menica.procenat_iznos:.2f}"
        return "-"


class ContractGuarantee(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_RETURNED = "returned"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Aktivna"),
        (STATUS_RETURNED, "Vracena"),
        (STATUS_EXPIRED, "Istekla"),
        (STATUS_CANCELLED, "Stornirana"),
    ]

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="guarantees",
        verbose_name="Ugovor",
    )
    guarantee_number = models.CharField(max_length=100, verbose_name="Broj garancije")
    issuer = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Izdavalac / banka",
    )
    beneficiary = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Korisnik garancije",
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Iznos",
    )
    currency = models.CharField(
        max_length=10,
        choices=Contract.CURRENCY_CHOICES,
        default="RSD",
        verbose_name="Valuta",
    )
    valid_from = models.DateField(blank=True, null=True, verbose_name="Vazi od")
    valid_to = models.DateField(blank=True, null=True, verbose_name="Vazi do")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
        verbose_name="Status",
    )
    note = models.TextField(blank=True, null=True, verbose_name="Napomena")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ugovori_garancije_kreirane",
    )

    class Meta:
        db_table = "ugovori_contract_guarantee"
        verbose_name = "Garancija uz ugovor"
        verbose_name_plural = "Garancije uz ugovore"
        ordering = ["-valid_to", "-created_at"]

    def __str__(self):
        return f"{self.guarantee_number} - {self.contract.contract_number}"

    def clean(self):
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError({"valid_to": "Datum 'Vazi do' ne sme biti pre datuma 'Vazi od'."})
