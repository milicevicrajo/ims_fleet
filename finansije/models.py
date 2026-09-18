from django.db import models


class FinanceJob(models.Model):
    company = models.PositiveIntegerField()
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100, blank=True)
    center = models.CharField(max_length=10, blank=True, db_index=True)
    active = models.BooleanField(default=True)
    profit_type = models.CharField(max_length=1, blank=True)

    class Meta:
        ordering = ["code"]
        constraints = [models.UniqueConstraint(fields=["company", "code"], name="fin_job_company_code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class LedgerEntry(models.Model):
    """One source posting; source identity never depends on amounts or descriptions."""

    company = models.PositiveIntegerField()
    year = models.PositiveSmallIntegerField()
    journal_type = models.CharField(max_length=3)
    journal_number = models.IntegerField()
    line_number = models.IntegerField()
    organizational_unit = models.IntegerField()
    organizational_unit_name = models.CharField(max_length=100, blank=True)
    account = models.CharField(max_length=6)
    account_name = models.CharField(max_length=100, blank=True)
    partner_group = models.IntegerField(null=True)
    partner_code = models.IntegerField(null=True)
    partner_name = models.CharField(max_length=255, blank=True)
    document_date = models.DateField()
    document_reference = models.CharField(max_length=20, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2)
    credit = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, blank=True)
    foreign_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    description = models.CharField(max_length=30, blank=True)
    linked_line = models.IntegerField(null=True)
    due_date = models.DateField(null=True)
    change_status = models.CharField(max_length=1, blank=True)
    job_code = models.CharField(max_length=10, blank=True)
    job_name = models.CharField(max_length=100, blank=True)
    center = models.CharField(max_length=10, blank=True)
    booking_date = models.DateField()
    debit_credit_flag = models.CharField(max_length=1, blank=True)
    source_paid_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    source_hash = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    changed_at = models.DateTimeField()
    removed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["company", "year", "journal_type", "journal_number", "line_number"],
            name="fin_ledger_source_key",
        )]
        indexes = [
            models.Index(fields=["company", "active", "booking_date"], name="fin_ledger_period"),
            models.Index(fields=["company", "center", "booking_date"], name="fin_ledger_center"),
            models.Index(fields=["company", "job_code", "booking_date"], name="fin_ledger_job"),
            models.Index(fields=["company", "account", "booking_date"], name="fin_ledger_account"),
            models.Index(fields=["company", "partner_code", "document_reference"], name="fin_ledger_document"),
        ]


class SyncRun(models.Model):
    STATUS = [("running", "U toku"), ("success", "Uspešno"), ("failed", "Neuspešno")]
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, choices=STATUS, default="running")
    company = models.PositiveIntegerField()
    year_from = models.PositiveSmallIntegerField()
    year_to = models.PositiveSmallIntegerField()
    source_rows = models.PositiveIntegerField(default=0)
    created = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    unchanged = models.PositiveIntegerField(default=0)
    removed = models.PositiveIntegerField(default=0)
    source_totals = models.JSONField(default=dict)
    latest_booking_date = models.DateField(null=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "-pk"]


class NalogZRefreshRun(models.Model):
    STATUS = [("running", "U toku"), ("success", "Uspešno"),
              ("failed", "Neuspešno"), ("skipped", "Preskočeno"), ("unknown", "Ishod nepoznat")]
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, choices=STATUS, default="running")
    trigger = models.CharField(max_length=10, choices=[("manual", "Ručno"), ("celery", "Celery")])
    requested_by = models.CharField(max_length=255, blank=True)
    task_id = models.CharField(max_length=255, blank=True)
    year_from = models.PositiveSmallIntegerField(null=True)
    year_to = models.PositiveSmallIntegerField(null=True)
    updated_rows = models.PositiveBigIntegerField(null=True)
    inserted_rows = models.PositiveBigIntegerField(null=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "-pk"]
