"""Local collections ledger, immutable source captures and operational history."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Round
from django.utils import timezone


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserTracked(Timestamped):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_created")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_updated")

    class Meta:
        abstract = True


class CollectionSyncRun(Timestamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pripremljeno"
        RUNNING = "running", "U toku"
        SUCCESS = "success", "Uspešno"
        FAILED = "failed", "Neuspešno"
        SKIPPED = "skipped", "Preskočeno"

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    source_system = models.CharField(max_length=32, default="ims_erp")
    company = models.PositiveIntegerField(default=1)
    dataset = models.CharField(max_length=40)
    trigger = models.CharField(max_length=16, choices=[("manual", "Ručno"), ("celery", "Celery"), ("import", "Prenos")])
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    task_id = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    scope = models.JSONField(default=dict, blank=True)
    source_counts = models.JSONField(default=dict, blank=True)
    control_totals = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "-pk"]
        constraints = [models.CheckConstraint(check=Q(finished_at__isnull=True) | Q(finished_at__gte=F("started_at")), name="col_run_time_order")]


class CollectionSyncStep(Timestamped):
    run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="steps")
    code = models.CharField(max_length=40)
    status = models.CharField(max_length=10, choices=CollectionSyncRun.Status.choices, default=CollectionSyncRun.Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    source_rows = models.PositiveBigIntegerField(default=0)
    created_rows = models.PositiveBigIntegerField(default=0)
    updated_rows = models.PositiveBigIntegerField(default=0)
    inactive_rows = models.PositiveBigIntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["run", "code"], name="col_step_run_code")]


class FinancePartnerIdentity(Timestamped):
    source_system = models.CharField(max_length=32, default="baza_ims")
    company = models.PositiveIntegerField()
    partner_group = models.IntegerField()
    partner_code = models.IntegerField()
    partner = models.ForeignKey("ugovori.Partner", on_delete=models.PROTECT, null=True, blank=True,
                                related_name="finance_identities")
    source_name = models.CharField(max_length=255, blank=True)
    source_tax_id = models.CharField(max_length=50, blank=True)
    source_registration_number = models.CharField(max_length=50, blank=True)
    source_address = models.CharField(max_length=255, blank=True)
    source_city = models.CharField(max_length=100, blank=True)
    source_country = models.CharField(max_length=100, blank=True)
    source_hash = models.CharField(max_length=64, blank=True)
    active = models.BooleanField(default=True)
    last_seen_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_system", "company", "partner_group", "partner_code"], name="col_partner_source_key")]
        ordering = ["company", "partner_group", "partner_code"]

    def __str__(self):
        return f"{self.company}/{self.partner_group}/{self.partner_code} {self.source_name}"


class CollectionProfile(UserTracked):
    identity = models.OneToOneField(FinancePartnerIdentity, on_delete=models.PROTECT, related_name="collection_profile")
    important_customer = models.BooleanField(default=False)
    needs_review = models.BooleanField(default=False)
    review_note = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="collection_accounts")


class InvoiceDocument(Timestamped):
    source_system = models.CharField(max_length=32, default="baza_ims")
    company = models.PositiveIntegerField()
    source_key = models.CharField(max_length=150, help_text="Stalan ključ izvornog dokumenta; nije samo broj za prikaz.")
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, related_name="invoices")
    year = models.PositiveSmallIntegerField()
    document_type = models.CharField(max_length=20, default="IF")
    number = models.CharField(max_length=100)
    reference = models.CharField(max_length=255, blank=True)
    document_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    amount_rsd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    foreign_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    source_hash = models.CharField(max_length=64, blank=True)
    active = models.BooleanField(default=True)
    last_seen_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_system", "company", "source_key"], name="col_invoice_source_key")]
        indexes = [models.Index(fields=["identity", "year", "reference"], name="col_invoice_lookup")]

    def clean(self):
        super().clean()
        if self.identity_id and self.identity.company != self.company:
            raise ValidationError({"identity": "Partner i dokument moraju pripadati istoj firmi."})


class ReceivablePosting(Timestamped):
    source_system = models.CharField(max_length=32, default="baza_ims")
    company = models.PositiveIntegerField()
    year = models.PositiveSmallIntegerField()
    journal_type = models.CharField(max_length=3)
    journal_number = models.IntegerField()
    line_number = models.IntegerField()
    partner_group = models.IntegerField(null=True, blank=True)
    partner_code = models.IntegerField(null=True, blank=True)
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True,
                                related_name="receivable_postings")
    document = models.ForeignKey(InvoiceDocument, on_delete=models.PROTECT, null=True, blank=True, related_name="postings")
    account = models.CharField(max_length=10)
    account_name = models.CharField(max_length=255, blank=True)
    organizational_unit = models.CharField(max_length=50, blank=True)
    job_code = models.CharField(max_length=50, blank=True)
    center_code = models.CharField(max_length=50, blank=True)
    # Registar organizacije, faza 2: cvor sifre posla, postavlja se pri sinhronizaciji
    # (services/sync.py). Pristup i izvestaji i dalje rade po `job_code` / `center_code`.
    org_node = models.ForeignKey("organizacija.OrgNode", on_delete=models.PROTECT, null=True, blank=True,
                                 editable=False, related_name="potrazivanja_stavke")
    reference = models.CharField(max_length=255, blank=True)
    document_date = models.DateField(null=True, blank=True)
    booking_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2)
    credit = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, blank=True)
    foreign_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    change_status = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    source_hash = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    last_seen_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="postings")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_system", "company", "year", "journal_type", "journal_number", "line_number"], name="col_posting_source_key")]
        indexes = [models.Index(fields=["company", "active", "booking_date"], name="col_posting_period"),
                   models.Index(fields=["identity", "reference"], name="col_posting_reference"),
                   models.Index(fields=["company", "job_code", "booking_date"], name="col_posting_job"),
                   models.Index(fields=["company", "account", "year"], name="col_posting_account")]

    def clean(self):
        super().clean()
        if self.identity_id:
            key = (self.company, self.partner_group, self.partner_code, self.source_system)
            other = (self.identity.company, self.identity.partner_group, self.identity.partner_code, self.identity.source_system)
            if key != other:
                raise ValidationError({"identity": "Veza partnera ne odgovara izvornom ključu knjiženja."})
        if self.document_id and (self.document.company != self.company or self.document.identity_id != self.identity_id):
            raise ValidationError({"document": "Dokument i knjiženje moraju imati istu firmu i partnera."})


class DueDateEvidence(Timestamped):
    import_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="due_date_evidence")
    source_system = models.CharField(max_length=32, default="baza_ims")
    source_table = models.CharField(max_length=64)
    source_key = models.CharField(max_length=150, help_text="Ključ ili hash reda unutar nepromenljive uvozne serije.")
    occurrence = models.PositiveIntegerField(default=1)
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True)
    company = models.PositiveIntegerField(null=True, blank=True)
    partner_group = models.IntegerField(null=True, blank=True)
    partner_code = models.IntegerField(null=True, blank=True)
    year = models.PositiveSmallIntegerField()
    reference = models.CharField(max_length=255, blank=True)
    job_code = models.CharField(max_length=50, blank=True)
    organizational_unit = models.CharField(max_length=50, blank=True)
    document_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    legacy_balance = models.DecimalField(max_digits=38, decimal_places=2, null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["import_run", "source_table", "source_key", "occurrence"], name="col_due_source_row"),
                       models.CheckConstraint(check=Q(occurrence__gte=1), name="col_due_occurrence_positive")]
        indexes = [models.Index(fields=["partner_code", "reference", "year"], name="col_due_reference")]

    def clean(self):
        super().clean()
        if self.identity_id and (self.company, self.partner_group, self.partner_code) != (self.identity.company, self.identity.partner_group, self.identity.partner_code):
            raise ValidationError({"identity": "Pre povezivanja dospeća potvrdite firmu, grupu i partnera."})


class BalanceSnapshot(Timestamped):
    class Status(models.TextChoices):
        DRAFT = "draft", "U pripremi"
        VALIDATED = "validated", "Provereno"
        PUBLISHED = "published", "Objavljeno"

    run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="snapshots")
    company = models.PositiveIntegerField()
    as_of_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    source_observed_at = models.DateTimeField()
    published_at = models.DateTimeField(null=True, blank=True)
    rules_version = models.CharField(max_length=40)
    totals = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["run", "company", "as_of_date"], name="col_snapshot_run_date"),
                       models.CheckConstraint(check=(Q(status="published", published_at__isnull=False) | (~Q(status="published") & Q(published_at__isnull=True))), name="col_snapshot_published_time")]

    def clean(self):
        super().clean()
        if self.run_id and self.run.company != self.company:
            raise ValidationError({"company": "Firma snimka mora odgovarati obuhvatu sinhronizacije."})


class CollectionState(Timestamped):
    company = models.PositiveIntegerField(unique=True)
    current_snapshot = models.ForeignKey(BalanceSnapshot, on_delete=models.PROTECT, null=True, blank=True)
    operations_independent_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.current_snapshot_id and (self.current_snapshot.company != self.company or self.current_snapshot.status != BalanceSnapshot.Status.PUBLISHED):
            raise ValidationError({"current_snapshot": "Aktivno stanje mora biti objavljeni snimak iste firme."})


class ReceivablePosition(models.Model):
    snapshot = models.ForeignKey(BalanceSnapshot, on_delete=models.PROTECT, related_name="positions")
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT)
    document = models.ForeignKey(InvoiceDocument, on_delete=models.PROTECT, null=True, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    job_code = models.CharField(max_length=50, blank=True)
    center_code = models.CharField(max_length=50, blank=True)
    # Registar organizacije, faza 2: cvor sifre posla, postavlja se pri sinhronizaciji
    # (services/sync.py). Pristup i izvestaji i dalje rade po `job_code` / `center_code`.
    org_node = models.ForeignKey("organizacija.OrgNode", on_delete=models.PROTECT, null=True, blank=True,
                                 editable=False, related_name="potrazivanja_pozicije")
    account_family = models.CharField(max_length=3)
    debit = models.DecimalField(max_digits=18, decimal_places=2)
    credit = models.DecimalField(max_digits=18, decimal_places=2)
    balance = models.DecimalField(max_digits=18, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    due_date_method = models.CharField(max_length=32, blank=True)
    due_date_evidence = models.ForeignKey(DueDateEvidence, on_delete=models.PROTECT, null=True, blank=True)
    resolution_details = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["snapshot", "identity", "reference", "job_code", "account_family"], name="col_position_scope"),
                       models.CheckConstraint(check=Q(balance=Round(F("debit") - F("credit"), 2)), name="col_position_balance")]
        indexes = [models.Index(fields=["snapshot", "center_code", "job_code"], name="col_position_center"),
                   models.Index(fields=["snapshot", "due_date"], name="col_position_due")]

    def clean(self):
        super().clean()
        if self.snapshot_id and self.identity_id and self.snapshot.company != self.identity.company:
            raise ValidationError({"identity": "Partner i snimak moraju pripadati istoj firmi."})
        if self.document_id and self.document.identity_id != self.identity_id:
            raise ValidationError({"document": "Dokument mora pripadati partneru stavke."})
        if self.due_date_evidence_id and self.due_date_evidence.identity_id != self.identity_id:
            raise ValidationError({"due_date_evidence": "Dokaz dospeća mora biti povezan sa istim partnerom."})


class AgingRule(Timestamped):
    code = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=100)
    min_days = models.IntegerField(null=True, blank=True)
    max_days = models.IntegerField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(unique=True)
    suggested_action = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["sort_order"]
        constraints = [models.CheckConstraint(check=Q(min_days__isnull=True) | Q(max_days__isnull=True) | Q(max_days__gte=F("min_days")), name="col_aging_range")]


class CollectionContact(UserTracked):
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True, related_name="contacts")
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=255, blank=True, help_text="Originalni kontakt može sadržati više adresa; validacija pri novom unosu.")
    note = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    legacy_partner_name = models.CharField(max_length=255, blank=True)
    first_name = models.CharField("Ime", max_length=100, blank=True)
    last_name = models.CharField("Prezime", max_length=100, blank=True)
    position = models.CharField("Funkcija / odeljenje", max_length=100, blank=True)
    needs_review = models.BooleanField(default=False)
    original_data = models.JSONField(default=dict, blank=True)
    normalized_at = models.DateTimeField(null=True, blank=True)
    import_parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="separated_contacts")


class ContactPoint(Timestamped):
    contact = models.ForeignKey(CollectionContact, on_delete=models.CASCADE, related_name="points")
    kind = models.CharField("Vrsta", max_length=10, choices=[("phone", "Telefon"), ("mobile", "Mobilni"), ("email", "E-pošta")])
    value = models.CharField("Broj / adresa", max_length=255)
    label = models.CharField("Namena", max_length=100, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["contact", "kind", "value"], name="col_contact_point_unique")]


class CollectionActivity(UserTracked):
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True, related_name="activities")
    kind = models.CharField(max_length=20, choices=[("note", "Napomena"), ("phone", "Telefonski poziv")])
    occurred_at = models.DateTimeField(null=True, blank=True)
    text = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    next_action_date = models.DateField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    legacy_partner_name = models.CharField(max_length=255, blank=True)
    contact = models.ForeignKey(CollectionContact, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["identity", "occurred_at"], name="col_activity_partner")]


class CollectionNotice(UserTracked):
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True, related_name="notices")
    kind = models.CharField(max_length=20, choices=[("reminder", "Opomena"), ("letter", "Pozivno pismo"), ("legacy_claim", "Nasleđena evidencija tužbe")])
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    number = models.CharField(max_length=100, blank=True)
    issued_on = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    partner_name_snapshot = models.CharField(max_length=255, blank=True)
    original_invoice_text = models.TextField(blank=True)
    note = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    recipient = models.CharField("Primalac", max_length=255, blank=True)
    body = models.TextField("Tekst dokumenta", blank=True)
    response_due_date = models.DateField("Rok za odgovor / plaćanje", null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["identity", "issued_on"], name="col_notice_partner")]


class CollectionNoticeItem(models.Model):
    notice = models.ForeignKey(CollectionNotice, on_delete=models.PROTECT, related_name="items")
    line_number = models.PositiveIntegerField()
    document = models.ForeignKey(InvoiceDocument, on_delete=models.PROTECT, null=True, blank=True)
    original_reference = models.CharField(max_length=255, blank=True)
    job_code = models.CharField(max_length=50, blank=True)
    due_date_snapshot = models.DateField(null=True, blank=True)
    amount_snapshot = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["notice", "line_number"], name="col_notice_line"),
                       models.CheckConstraint(check=Q(line_number__gte=1), name="col_notice_line_positive")]

    def clean(self):
        super().clean()
        if self.notice_id and self.document_id and self.notice.identity_id != self.document.identity_id:
            raise ValidationError({"document": "Faktura mora pripadati partneru opomene ili pisma."})


class ElectronicInvoiceStatus(Timestamped):
    source_system = models.CharField(max_length=32, default="efaktura")
    source_id = models.BigIntegerField()
    company = models.PositiveIntegerField()
    eid = models.CharField(max_length=40)
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True)
    document = models.ForeignKey(InvoiceDocument, on_delete=models.PROTECT, null=True, blank=True)
    partner_code = models.IntegerField(null=True, blank=True)
    year = models.PositiveSmallIntegerField()
    organizational_unit = models.CharField(max_length=50, blank=True)
    source_document_type = models.IntegerField(null=True, blank=True)
    document_date = models.DateField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, blank=True)
    status_at = models.DateTimeField(null=True, blank=True)
    status_comment = models.TextField(blank=True)
    observed_at = models.DateTimeField()
    active = models.BooleanField(default=True)
    last_seen_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_system", "source_id"], name="col_sef_source_key")]
        indexes = [models.Index(fields=["company", "year", "status_code"], name="col_sef_status")]

    def clean(self):
        super().clean()
        if self.identity_id and (self.identity.company != self.company or self.identity.partner_code != self.partner_code):
            raise ValidationError({"identity": "SEF dokument mora odgovarati firmi i šifri partnera."})
        if self.document_id and (self.document.company != self.company or self.document.identity_id != self.identity_id):
            raise ValidationError({"document": "SEF i finansijski dokument moraju imati istog partnera i firmu."})


class LegalCaseLink(UserTracked):
    legacy_case_id = models.PositiveBigIntegerField(unique=True)
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT)
    note = models.TextField(blank=True)


class LegacyImportMap(Timestamped):
    source_system = models.CharField(max_length=32, default="ims_erp")
    source_table = models.CharField(max_length=64)
    source_key = models.CharField(max_length=150)
    target_model = models.CharField(max_length=100, help_text="Oznaka modela za kontrolu prenosa, npr. potrazivanja.collectioncontact.")
    target_pk = models.PositiveBigIntegerField()
    source_hash = models.CharField(max_length=64)
    raw_data = models.JSONField(default=dict, blank=True)
    first_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="initial_import_mappings")
    last_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="latest_import_mappings")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_system", "source_table", "source_key"], name="col_import_source_key")]
        indexes = [models.Index(fields=["target_model", "target_pk"], name="col_import_target")]


class ImportIssue(UserTracked):
    run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT, related_name="issues")
    code = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=[("warning", "Upozorenje"), ("error", "Greška")], default="error")
    source_table = models.CharField(max_length=64)
    source_key = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    raw_data = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["run", "severity", "resolved_at"], name="col_issue_review")]


class SourceDataset(Timestamped):
    """An immutable complete view/table capture, reused only for identical content."""
    name = models.CharField(max_length=64)
    fingerprint = models.CharField(max_length=64)
    row_count = models.PositiveBigIntegerField()
    first_run = models.ForeignKey(CollectionSyncRun, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "fingerprint"], name="col_dataset_fingerprint")]


class SourceRow(models.Model):
    dataset = models.ForeignKey(SourceDataset, on_delete=models.PROTECT, related_name="rows")
    ordinal = models.PositiveIntegerField()
    partner_code = models.IntegerField(null=True, blank=True)
    job_code = models.CharField(max_length=50, blank=True)
    raw_data = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["dataset", "ordinal"], name="col_source_ordinal")]
        indexes = [models.Index(fields=["dataset", "partner_code"], name="col_source_partner")]


class CollectionLegalCase(UserTracked):
    identity = models.ForeignKey(FinancePartnerIdentity, on_delete=models.PROTECT, null=True, blank=True)
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    original_data = models.JSONField(default=dict, blank=True)
    tip = models.CharField("Vrsta postupka", max_length=20, choices=[("tuzeni", "Tuženi"), ("tuzili", "Tužili"), ("stecaj", "Stečaj"), ("uppr", "UPPR")], default="tuzeni")
    sud = models.CharField("Sud", max_length=255, blank=True)
    broj_predmeta = models.CharField("Broj predmeta", max_length=100, blank=True)
    sifra_partnera = models.IntegerField(null=True, blank=True)
    naziv_partnera = models.CharField("Naziv partnera u evidenciji", max_length=255, blank=True)
    valuta = models.CharField("Valuta", max_length=10, default="RSD", choices=[("RSD", "RSD"), ("EUR", "EUR"), ("USD", "USD")])
    osnovni_dug = models.DecimalField("Osnovni dug", max_digits=18, decimal_places=2, null=True, blank=True)
    arhivirano = models.BooleanField(default=False)
    izvrsiteljski_broj = models.CharField("Izvršiteljski broj", max_length=100, blank=True)
    datum_pokretanja = models.DateField("Datum pokretanja", null=True, blank=True)
    predmet_spora = models.TextField("Predmet spora", blank=True)
    tuzilac = models.CharField("Tužilac", max_length=255, blank=True)
    vrednost_spora = models.DecimalField("Vrednost spora", max_digits=18, decimal_places=2, null=True, blank=True)
    datum_podnosenja_tuzbe = models.DateField("Datum podnošenja tužbe", null=True, blank=True)
    vece = models.CharField("Veće", max_length=100, blank=True)
    kamata = models.DecimalField("Kamata", max_digits=18, decimal_places=2, null=True, blank=True)
    troskovi = models.DecimalField("Troškovi", max_digits=18, decimal_places=2, null=True, blank=True)
    ukupan_dug = models.DecimalField("Ukupan dug", max_digits=18, decimal_places=2, null=True, blank=True)
    datum_otvaranja_stecaja = models.DateField("Datum otvaranja stečaja", null=True, blank=True)
    prijava_potrazivanja = models.TextField("Prijava potraživanja", blank=True)
    novi_broj = models.CharField("Novi broj", max_length=100, blank=True)
    pib = models.CharField("PIB", max_length=20, blank=True)


class CollectionLegalEvent(UserTracked):
    case = models.ForeignKey(CollectionLegalCase, on_delete=models.PROTECT, related_name="events")
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    date = models.DateField("Datum")
    text = models.TextField("Promena / beleška")
    archived = models.BooleanField(default=False)
    original_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date", "-pk"]


class CollectionAudit(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    entity = models.CharField(max_length=100)
    entity_id = models.PositiveBigIntegerField()
    action = models.CharField(max_length=30)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["entity", "entity_id", "created_at"], name="col_audit_entity")]


class CollectionFileImport(models.Model):
    """Completed local spreadsheet imports; repeated file content is idempotent."""
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    fingerprint = models.CharField(max_length=64, unique=True)
    filename = models.CharField(max_length=255)
    row_count = models.PositiveIntegerField()
    notice_ids = models.JSONField(default=list)
