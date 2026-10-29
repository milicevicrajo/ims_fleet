from django.db import models
from django.conf import settings


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
    # Registar organizacije: cvor sifre posla, postavlja se pri objavi sinhronizacije
    # (services/sync.py) i komandom `povezi_flotu --modul finansije`. Od 28.09.2026. (korak 5)
    # pristup ide kroz ovu vezu i dodele uloga, a `center` ostaje izvorni podatak.
    org_node = models.ForeignKey("organizacija.OrgNode", on_delete=models.PROTECT, null=True, blank=True,
                                 editable=False, related_name="finansije_knjizenja", db_index=True)
    # Snimak centra iz registra na datum knjizenja (organizacija.services.putanja.osvezi_centre);
    # po njemu Finansije filtriraju i sabiraju kad su na registru (`finansije.access.polje_centra`).
    # Neobavezno polje, da stariji kod na serveru moze da upisuje knjizenja i pre isporuke.
    org_centar = models.CharField(max_length=40, null=True, blank=True, editable=False)
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
            models.Index(fields=["company", "org_centar", "booking_date"], name="fin_ledger_org_centar"),
            models.Index(fields=["company", "job_code", "booking_date"], name="fin_ledger_job"),
            models.Index(fields=["company", "account", "booking_date"], name="fin_ledger_account"),
            models.Index(fields=["company", "partner_code", "document_reference"], name="fin_ledger_document"),
            # SEF fakture: meka veza po broju dokumenta, bez partnera (od 30.09.2026.).
            models.Index(fields=["company", "document_reference"], name="fin_ledger_doc_ref"),
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


class BankContact(models.Model):
    company = models.PositiveIntegerField(default=1)
    bank_code = models.PositiveIntegerField()
    segment = models.CharField("Vrsta posla", max_length=120)
    name = models.CharField("Kontakt osoba", max_length=150, blank=True)
    position = models.CharField("Funkcija", max_length=150, blank=True)
    email = models.EmailField("Email osobe", blank=True)
    phone = models.CharField("Telefon", max_length=100, blank=True)
    shared_emails = models.TextField("Zajednički emailovi segmenta", blank=True)
    note = models.TextField("Napomena", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["segment", "name", "pk"]
        indexes = [models.Index(fields=["company", "bank_code"], name="fin_bank_contact")]


class BankAccountRule(models.Model):
    SEGMENTS = [
        ("dinar", "Dinarski račun"), ("foreign", "Devizni račun"),
        ("deposit", "Oročena sredstva"), ("guarantee", "Depozit za garanciju"),
        ("other", "Ostalo poslovanje"), ("excluded", "Nije račun banke"),
    ]
    company = models.PositiveIntegerField(default=1)
    account = models.CharField("Konto", max_length=6)
    bank_code = models.PositiveIntegerField("Banka", null=True, blank=True)
    segment = models.CharField("Vrsta posla", max_length=12, choices=SEGMENTS)
    note = models.CharField("Napomena", max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["account"]
        constraints = [models.UniqueConstraint(fields=["company", "account"], name="fin_bank_account_rule")]


class BankBillPlacement(models.Model):
    """Explicit custody; the NBS registration bank is not proof of delivery."""
    company = models.PositiveIntegerField(default=1)
    bank_code = models.PositiveIntegerField()
    bill = models.ForeignKey("menice.Menica", null=True, blank=True, on_delete=models.PROTECT)
    incoming_bill = models.ForeignKey("menice.UlaznaMenica", null=True, blank=True, on_delete=models.PROTECT)
    delivered_on = models.DateField("Datum predaje")
    returned_on = models.DateField("Datum vraćanja", null=True, blank=True)
    note = models.TextField("Namena / napomena", blank=True)

    class Meta:
        ordering = ["-delivered_on", "-pk"]
        constraints = [
            models.CheckConstraint(check=(models.Q(bill__isnull=False, incoming_bill__isnull=True) |
                                          models.Q(bill__isnull=True, incoming_bill__isnull=False)), name="fin_bank_bill_one_source"),
            models.CheckConstraint(check=models.Q(returned_on__isnull=True) | models.Q(returned_on__gte=models.F("delivered_on")), name="fin_bank_bill_dates"),
            models.UniqueConstraint(fields=["company", "bill"], condition=models.Q(returned_on__isnull=True, bill__isnull=False), name="fin_bank_bill_held"),
            models.UniqueConstraint(fields=["company", "incoming_bill"], condition=models.Q(returned_on__isnull=True, incoming_bill__isnull=False), name="fin_bank_incoming_held"),
        ]


class BankaNbs(models.Model):
    """Banka iz registra NBS (od 29.10.2026.): poslednje preuzeto stanje sa stranice „Detalji”.

    Vezuje se za partnere grupe 11 po PIB-u (pa po matičnom broju). Banka koja nestane sa spiska
    NBS ostaje kao istorijska (`aktivna=False`), sa datumom kada je nestala.
    """
    nbs_id = models.CharField(max_length=36, unique=True)
    naziv = models.CharField(max_length=255)
    grad = models.CharField(max_length=100, blank=True)
    adresa = models.CharField(max_length=255, blank=True)
    postanski_broj = models.CharField(max_length=20, blank=True)
    maticni_broj = models.CharField(max_length=10, blank=True)
    pib = models.CharField(max_length=12, blank=True, db_index=True)
    telefon = models.CharField(max_length=255, blank=True)
    telefaks = models.CharField(max_length=255, blank=True)
    web = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    swift = models.CharField(max_length=11, blank=True)
    resenje = models.CharField(max_length=150, blank=True)
    datum_resenja = models.DateField(null=True, blank=True)
    broj_zaposlenih = models.PositiveIntegerField(null=True, blank=True)
    napomena = models.TextField(blank=True)
    akcionari = models.JSONField(default=list)        # [{naziv, procenat}]
    upravni_odbor = models.JSONField(default=list)    # [{ime, funkcija}]
    izvrsni_odbor = models.JSONField(default=list)
    prilozi = models.JSONField(default=list)          # [{naziv, url}]
    aktivna = models.BooleanField(default=True)
    prvi_put = models.DateTimeField(auto_now_add=True)
    preuzeto = models.DateTimeField()
    promenjeno = models.DateTimeField(null=True, blank=True)
    nestala = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["naziv"]

    @property
    def nbs_url(self):
        return f"https://webappcenter.nbs.rs/WebApp/FinInstBank/LegalEntityFinInstitution/Details?id={self.nbs_id}"

    # Zbirni podaci kao u pregledu direktora („Banke_Srbija_NBS_podaci”), izvedeni iz preuzetih tabela.
    @staticmethod
    def _procenat(tekst):
        from decimal import Decimal, InvalidOperation

        try:
            return Decimal("".join(z for z in str(tekst) if z.isdigit() or z == ",").replace(",", "."))
        except InvalidOperation:
            return Decimal("0")

    @property
    def najveci_akcionar(self):
        return max(self.akcionari, key=lambda a: self._procenat(a.get("procenat")), default=None)

    @staticmethod
    def _predsednik(clanovi):
        return next((c["ime"] for c in clanovi if c.get("funkcija", "").lower().startswith("predsednik")), "")

    @property
    def predsednik_uo(self):
        return self._predsednik(self.upravni_odbor)

    @property
    def predsednik_io(self):
        return self._predsednik(self.izvrsni_odbor)

    @property
    def nezavisnih_uo(self):
        return sum(1 for c in self.upravni_odbor if "nezavisn" in c.get("funkcija", "").lower())

    @property
    def revizor(self):
        """NBS objavljuje izveštaj revizora kao prilog sa nazivom revizorske kuće."""
        return ", ".join(p["naziv"] for p in self.prilozi if "organizaciona struktura" not in p["naziv"].lower())


class BankaPartner(models.Model):
    """Lokalna kopija partnera grupe 11 iz Stankovog programa (od 29.10.2026.), uz naše oznake.

    Podaci partnera (`podaci`: polja kao u šifarniku) samo se preuzimaju — menjaju se u Stankovom
    programu. Ovde se ručno vode samo status, namena šifre i glavna šifra banke.
    """
    STATUSI = [("", "Automatski (po NBS spisku i prometu)"), ("aktivna", "Aktivna banka"),
               ("istorijska", "Istorijska — ne koristi se"), ("nije_banka", "Nije banka (npr. Uprava za trezor)")]
    NAMENE = [("", "—"), ("glavni", "Glavni račun"), ("bolovanja", "Račun za bolovanja"),
              ("namenski", "Namenski račun"), ("ostalo", "Ostalo")]
    company = models.PositiveIntegerField(default=1)
    sifra = models.PositiveIntegerField()
    naziv = models.CharField(max_length=255)
    pib = models.CharField(max_length=13, blank=True)
    maticni_broj = models.CharField(max_length=13, blank=True)
    podaci = models.JSONField(default=dict)
    u_izvoru = models.BooleanField(default=True)
    preuzeto = models.DateTimeField()
    promenjeno = models.DateTimeField(null=True, blank=True)
    nestala = models.DateTimeField(null=True, blank=True)
    status = models.CharField("Status", max_length=12, choices=STATUSI, blank=True)
    namena = models.CharField("Namena šifre", max_length=12, choices=NAMENE, blank=True)
    glavna = models.ForeignKey("self", verbose_name="Glavna šifra iste banke", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="dodatne")
    napomena = models.CharField("Napomena", max_length=255, blank=True)
    izmenio = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    izmenjeno = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sifra"]
        constraints = [models.UniqueConstraint(fields=["company", "sifra"], name="fin_banka_partner")]

    def __str__(self):
        return f"{self.sifra} — {self.naziv}"


class BankePreuzimanje(models.Model):
    """Jedno preuzimanje podataka banaka: sa sajta NBS ili iz šifarnika partnera (Stankov program)."""
    STATUS = [("running", "U toku"), ("success", "Uspešno"), ("failed", "Neuspešno")]
    IZVORI = [("nbs", "NBS"), ("sifarnik", "Šifarnik partnera")]
    izvor = models.CharField(max_length=10, choices=IZVORI, default="nbs")
    pocetak = models.DateTimeField(auto_now_add=True)
    kraj = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, choices=STATUS, default="running")
    pokretanje = models.CharField(max_length=10, choices=[("manual", "Ručno"), ("celery", "Zakazano")])
    korisnik = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    banaka = models.PositiveIntegerField(default=0)
    novih = models.PositiveIntegerField(default=0)
    promenjenih = models.PositiveIntegerField(default=0)
    nestalih = models.PositiveIntegerField(default=0)
    promene = models.JSONField(default=list)          # [{banka, polje, staro, novo}]
    greska = models.TextField(blank=True)

    class Meta:
        ordering = ["-pocetak", "-pk"]


class BankarskaGrupa(models.Model):
    """Grupe i povezana lica banaka po spisku direktora (od 29.10.2026.)."""
    naziv = models.CharField(max_length=100, unique=True)
    maticna_grupa = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["naziv"]

    def __str__(self):
        return self.naziv


class PovezanoLiceBanke(models.Model):
    """Član bankarske grupe: banka, lizing, DZU, osiguranje...; za nas se vezuje po PIB-u."""
    grupa = models.ForeignKey(BankarskaGrupa, on_delete=models.CASCADE, related_name="lica")
    vrsta = models.CharField(max_length=60)
    naziv = models.CharField(max_length=255)
    maticni_broj = models.CharField(max_length=10, blank=True)
    pib = models.CharField(max_length=12, unique=True)
    vlasnistvo = models.CharField(max_length=255, blank=True)
    izvor = models.CharField(max_length=100, blank=True)
    potvrda = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["grupa__naziv", "pk"]

    @property
    def je_banka(self):
        return self.vrsta == "Banka"

    @property
    def potvrdjeno(self):
        return self.potvrda.startswith("Da")


# SEF fakture (samo citanje, od 30.09.2026.) — modeli u posebnom fajlu.
from .sef_models import SefFaktura, SefPrilog, SefPromena, SefSinhronizacija  # noqa: E402,F401
