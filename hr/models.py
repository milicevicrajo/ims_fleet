from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .evaluation_models import (EvaluationGroup, EvaluationCriterion, EvaluationScale,
    EvaluationUnitSetup, EvaluationEmployeeSetup, EmployeeEvaluation, EvaluationApproval)
from .resenja_models import Pismo, VrstaResenja, Potpisnik, Resenje, ResenjeDan
from .zahtevi_models import VrstaZahteva, BrojacZahteva, Zahtev, ZahtevDan
from .ugovori_models import DodatnoRadnoMesto, UgovoriSinhronizacija, UgovorZaposlenog


class Osoba(models.Model):
    """Fizičko lice, jedinstveno po JMBG-u (od 06.10.2026.).

    Zaposlenje (`Employee`) je broj radnika u preduzeću; ista osoba posle ponovnog prijema ili uz rad van
    radnog odnosa ima više zaposlenja. Ime za prikaz i ćirilični oblik imena važe za osobu i prepisuju se
    na sva njena zaposlenja (`hr.services.osobe.prenesi_prikaz`). Ime, prezime, titulu, pol i datum
    rođenja upisuje HR sinhronizacija iz glavnog zaposlenja.
    """
    jmbg = models.CharField(max_length=13, blank=True, default="", verbose_name=_("JMBG"),
                            help_text=_("Prazno ako JMBG nije upisan u kadrovskoj bazi."))
    titula = models.CharField(max_length=20, blank=True, default="", verbose_name=_("Titula"))
    ime = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Ime"))
    prezime = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Prezime"))
    pol = models.CharField(max_length=1, blank=True, default="", verbose_name=_("Pol"))
    datum_rodjenja = models.DateField(null=True, blank=True, verbose_name=_("Datum rođenja"))
    ime_za_prikaz = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Ime za prikaz"))
    prezime_za_prikaz = models.CharField(max_length=50, blank=True, default="", verbose_name=_("Prezime za prikaz"))
    ime_cirilica = models.CharField(max_length=150, blank=True, default="", verbose_name=_("Ime i prezime (ćirilica)"))
    # Ukupan staž osobe iz kadrovske baze (`RadStaz`, sve šifre), računa HR sinhronizacija (od 06.10.2026.).
    staz_godina = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Ukupan staž — godina"))
    staz_meseci = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Ukupan staž — meseci"))
    staz_dana = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Ukupan staž — dana"))
    staz_ims_godina = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Staž u IMS — godina"))
    staz_ims_meseci = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Staž u IMS — meseci"))
    staz_ims_dana = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_("Staž u IMS — dana"))
    staz_preuzet = models.DateTimeField(null=True, blank=True, verbose_name=_("Staž preuzet iz kadrovske baze"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "fleet"
        verbose_name = _("Osoba")
        verbose_name_plural = _("Osobe")
        # `jmbg > ''`, ne `NOT (jmbg = '')`: SQL Server ne prima NOT u uslovu filtriranog indeksa.
        constraints = [models.UniqueConstraint(fields=["jmbg"], condition=models.Q(jmbg__gt=""),
                                               name="fleet_osoba_jmbg_jedinstven")]

    def __str__(self):
        return f"{self.prezime_za_prikaz or self.prezime} {self.ime_za_prikaz or self.ime}".strip()

    @staticmethod
    def _staz_tekst(godina, meseci, dana):
        if godina is None:
            return ""
        return f"{godina} god. {meseci} mes. {dana} dana"

    @property
    def ukupan_staz(self):
        return self._staz_tekst(self.staz_godina, self.staz_meseci, self.staz_dana)

    @property
    def staz_u_ims(self):
        return self._staz_tekst(self.staz_ims_godina, self.staz_ims_meseci, self.staz_ims_dana)


class Employee(models.Model):
    GENDER_CHOICES = [
        ("M", "Muški"),
        ("F", "Ženski"),
    ]

    class Preduzece(models.IntegerChoices):
        # `sif_pred` u kadrovskoj bazi; broj radnika je jedinstven samo unutar preduzeća.
        RADNI_ODNOS = 1, _("Radni odnos")
        VAN_RADNOG_ODNOSA = 2, _("Van radnog odnosa")

    employee_code = models.IntegerField(verbose_name=_("Šifra zaposlenog"))
    osoba = models.ForeignKey(Osoba, on_delete=models.PROTECT, null=True, blank=True, related_name="zaposlenja",
                              verbose_name=_("Osoba"))
    preduzece = models.PositiveSmallIntegerField(choices=Preduzece.choices, default=Preduzece.RADNI_ODNOS,
                                                 verbose_name=_("Preduzeće"))
    u_izvoru = models.BooleanField(default=True, verbose_name=_("Postoji u kadrovskoj bazi"),
                                   help_text=_("Isključeno kad broj radnika nestane iz kadrovske baze."))
    title = models.CharField(max_length=20, verbose_name=_("Titula"), blank=True, null=True)
    original_full_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Originalno ime i prezime"),
    )
    first_name = models.CharField(max_length=50, verbose_name=_("Ime"), blank=True, null=True)
    last_name = models.CharField(max_length=50, verbose_name=_("Prezime"), blank=True, null=True)
    display_first_name_override = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Ime za prikaz"),
    )
    display_last_name_override = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Prezime za prikaz"),
    )
    full_name_cyrillic = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Ime i prezime (ćirilica)"),
        help_text=_(
            "Koristi se u rešenjima koja se štampaju ćirilicom. Ostavi prazno za automatsko "
            "preslovljavanje, koje ume da pogreši kod slova lj, nj i dž."
        ),
    )
    position = models.CharField(max_length=100, verbose_name=_("Pozicija"))
    department_code = models.IntegerField(verbose_name=_("Šifra odeljenja"))
    org_unit_code = models.CharField(max_length=20, verbose_name=_("OJ"), blank=True, null=True)
    # Registar organizacije (korak 7, 28.09.2026.): cvor kome zaposleni pripada — izvodi se iz OJ
    # kadrovske baze (organizacija/services/zaposleni.py); po njemu Kadrovi ogranicavaju pristup.
    org_node = models.ForeignKey("organizacija.OrgNode", on_delete=models.PROTECT, null=True, blank=True,
                                 editable=False, related_name="zaposleni", verbose_name=_("Organizaciona jedinica (registar)"))
    system_code = models.CharField(max_length=10, verbose_name=_("Šifra sistema"), blank=True, null=True)
    system_name = models.CharField(max_length=255, verbose_name=_("Naziv sistema"), blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Pol"))
    skip_hr_identity_update = models.BooleanField(
        default=False,
        verbose_name=_("Ne azuriraj identitet iz HR-a"),
        help_text=_("Ako je ukljuceno, HR sinhronizacija ne menja titulu, ime, prezime i pol."),
    )
    date_of_birth = models.DateField(verbose_name=_("Datum rođenja"))
    date_of_joining = models.DateField(verbose_name=_("Datum zapošljavanja"))
    phone_number = models.CharField(max_length=20, verbose_name=_("Broj telefona"), blank=True, null=True)
    mobile_phone = models.CharField(max_length=50, verbose_name=_("Mobilni broj"), blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivan"))
    personal_number = models.CharField(max_length=13, verbose_name=_("Matični broj"), blank=True, null=True)
    account_number = models.CharField(max_length=50, verbose_name=_("Partija"), blank=True, null=True)
    address = models.CharField(max_length=255, verbose_name=_("Adresa"), blank=True, null=True)
    residence_municipality = models.CharField(
        max_length=100,
        verbose_name=_("Opstina boravka"),
        blank=True,
        null=True,
    )
    education = models.CharField(max_length=255, verbose_name=_("Škola"), blank=True, null=True)
    job_code = models.CharField(max_length=20, verbose_name=_("Šifra zanimanja"), blank=True, null=True)
    job_title = models.CharField(max_length=255, verbose_name=_("Naziv zanimanja"), blank=True, null=True)
    status_code = models.CharField(max_length=10, verbose_name=_("Šifra statusa"), blank=True, null=True)
    status_name = models.CharField(max_length=255, verbose_name=_("Naziv statusa"), blank=True, null=True)
    slava = models.CharField(max_length=100, verbose_name=_("Slava"), blank=True, null=True)
    # Slava se slavi svake godine istog dana: koriste se dan i mesec, godina iz datuma nije bitna.
    # HR sinhronizacija ga ne dira; naziv slave i dalje dolazi iz HR-a.
    slava_datum = models.DateField(blank=True, null=True, verbose_name=_("Datum slave"),
        help_text=_("Npr. Sveti Nikola: 19.12. Godina nije bitna. Ako je prazno, radna lista predlaže datum iz naziva slave."))
    recipient_code = models.CharField(max_length=20, blank=True, default="", verbose_name=_("Šifra vrste primaoca"))
    recipient_name = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Vrsta primaoca iz HR-a"))
    # Sva radna mesta na koja je radnik raspoređen (do 5, `radnik.sif_sis`, `sif_sis1`–`sif_sis4`), ravnopravna,
    # redom iz izvora;
    # [{sifra, naziv, oj, naziv_oj}] — puni sinhronizacija Kadrova (`hr/services/radna_mesta.py`), od 07.10.2026.
    radna_mesta = models.JSONField(default=list, blank=True, verbose_name=_("Radna mesta"))

    class Meta:
        app_label = "fleet"
        constraints = [models.UniqueConstraint(fields=["preduzece", "employee_code"],
                                               name="fleet_employee_preduzece_broj")]

    @property
    def display_first_name(self):
        return self.display_first_name_override or self.first_name or ""

    @property
    def display_last_name(self):
        return self.display_last_name_override or self.last_name or ""

    def __str__(self):
        return f"{self.display_last_name} {self.display_first_name}".strip()


class EmployeeCVItem(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="cv_items",
        verbose_name=_("Zaposleni"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Naziv posla ili projekta"))
    organization = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Organizacija / klijent"),
    )
    role = models.CharField(max_length=255, blank=True, verbose_name=_("Uloga"))
    start_date = models.DateField(blank=True, null=True, verbose_name=_("Period od"))
    end_date = models.DateField(blank=True, null=True, verbose_name=_("Period do"))
    description = models.TextField(verbose_name=_("Opis aktivnosti"))
    skills = models.TextField(blank=True, verbose_name=_("Znanja i vestine"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        app_label = "fleet"
        ordering = ["-start_date", "-id"]
        verbose_name = _("CV stavka")
        verbose_name_plural = _("CV stavke")

    def __str__(self):
        return f"{self.employee} - {self.title}"


class WorkTimeSheet(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Popunjava se")
        SUBMITTED = "submitted", _("Predato")
        APPROVED = "approved", _("Odobreno")

    employee = models.ForeignKey(
        "fleet.Employee",
        on_delete=models.CASCADE,
        related_name="work_time_sheets",
        verbose_name=_("Zaposleni"),
    )
    year = models.PositiveSmallIntegerField(
        verbose_name=_("Godina"),
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )
    month = models.PositiveSmallIntegerField(
        verbose_name=_("Mesec"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status"),
    )
    meal_days = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(31)],
        verbose_name=_("Topli obrok - broj dana"),
    )
    meal_organizational_unit = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="meal_work_time_sheets",
        verbose_name=_("Topli obrok - sifra posla"),
    )
    field_allowance_days = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(31)],
        verbose_name=_("Terenski dodatak - broj dana"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_work_time_sheets",
        verbose_name=_("Kreirao"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="updated_work_time_sheets",
        verbose_name=_("Azurirao"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))
    # Odobravanje (od 09.10.2026., Kadrovi → Pregled radnih lista): odobrena lista se više ne menja.
    odobrio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
                                related_name="+", verbose_name=_("Odobrio"))
    odobreno_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Odobreno"))

    class Meta:
        ordering = ["-year", "-month", "employee__last_name", "employee__first_name"]
        unique_together = ("employee", "year", "month")
        verbose_name = _("Radna lista")
        verbose_name_plural = _("Radne liste")

    @property
    def total_hours(self):
        return sum((line.total_hours for line in self.lines.all()), 0)

    def __str__(self):
        return f"{self.employee} - {self.month:02d}/{self.year}"


class RadnaListaPrilog(models.Model):
    """Skenirani dokument uz radnu listu (od 07.10.2026.): propusnice, finalna potpisana lista i drugo."""

    class Vrsta(models.TextChoices):
        PROPUSNICE = "propusnice", _("Skenirane propusnice")
        FINALNA = "finalna", _("Finalna (potpisana) radna lista")
        OSTALO = "ostalo", _("Ostalo")

    sheet = models.ForeignKey(WorkTimeSheet, on_delete=models.CASCADE, related_name="prilozi", verbose_name=_("Radna lista"))
    vrsta = models.CharField(max_length=20, choices=Vrsta.choices, default=Vrsta.PROPUSNICE, verbose_name=_("Vrsta"))
    fajl = models.FileField(upload_to="hr/radne_liste/%Y/%m/", max_length=255, verbose_name=_("Dokument"))
    naziv = models.CharField(max_length=255, verbose_name=_("Naziv fajla"))
    velicina = models.PositiveIntegerField(default=0)
    napomena = models.CharField(max_length=255, blank=True, verbose_name=_("Napomena"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+", verbose_name=_("Dodao"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Dodato"))

    class Meta:
        ordering = ["created_at", "pk"]
        verbose_name = _("Prilog radne liste")
        verbose_name_plural = _("Prilozi radne liste")

    def __str__(self):
        return self.naziv


class KomentarProlaza(models.Model):
    """Objašnjenje za dan bez prolaza ili sa problemom u prolazima (od 05.10.2026.).

    Upisuje ga zaposleni na svojoj radnoj listi ili ko sme da otvori tuđu radnu listu; prikazuje se uz
    evidenciju prolaza i u prilogu za štampu. Izvor prolazaka se ne menja — komentar je samo objašnjenje.
    """
    employee = models.ForeignKey("fleet.Employee", on_delete=models.CASCADE, related_name="komentari_prolaza",
                                 verbose_name=_("Zaposleni"))
    datum = models.DateField(verbose_name=_("Datum"))
    tekst = models.CharField(max_length=500, verbose_name=_("Komentar"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+", verbose_name=_("Upisao"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+", verbose_name=_("Izmenio"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Upisano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Izmenjeno"))

    class Meta:
        ordering = ["datum"]
        constraints = [models.UniqueConstraint(fields=["employee", "datum"], name="hr_komentar_prolaza_jedan_po_danu")]
        verbose_name = _("Komentar na prolaze")
        verbose_name_plural = _("Komentari na prolaze")

    def __str__(self):
        return f"{self.employee} · {self.datum:%d.%m.%Y}"


class WorkTimeSheetLine(models.Model):
    sheet = models.ForeignKey(
        WorkTimeSheet,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name=_("Radna lista"),
    )
    line_number = models.PositiveSmallIntegerField(verbose_name=_("R.b."))
    organizational_unit = models.ForeignKey(
        "fleet.OrganizationalUnit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="work_time_sheet_lines",
        verbose_name=_("Sifra posla"),
    )
    day_1 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_2 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_3 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_4 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_5 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_6 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_7 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_8 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_9 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_10 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_11 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_12 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_13 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_14 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_15 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_16 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_17 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_18 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_19 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_20 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_21 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_22 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_23 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_24 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_25 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_26 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_27 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_28 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_29 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_30 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    day_31 = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(24)])
    work_conditions = models.CharField(max_length=100, blank=True, verbose_name=_("Uslovi rada"))
    note = models.CharField(max_length=255, blank=True, verbose_name=_("Napomena"))
    work_category = models.ForeignKey("WorkTimeCategory", null=True, blank=True,
        on_delete=models.PROTECT, related_name="sheet_lines", verbose_name=_("Vrsta rada / odsustva"))

    class Meta:
        ordering = ["line_number"]
        unique_together = ("sheet", "line_number")
        verbose_name = _("Red radne liste")
        verbose_name_plural = _("Redovi radne liste")

    @property
    def total_hours(self):
        total = 0
        for day in range(1, 32):
            total += getattr(self, f"day_{day}") or 0
        return total

    @property
    def display_note(self):
        return self.work_category.name if self.work_category_id else ""

    def __str__(self):
        return f"{self.sheet} / {self.line_number}"


class AnnualLeaveSync(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="annual_leave_syncs")
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    counts = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("Sinhronizacija godišnjih odmora")


class AnnualLeaveSourceRecord(models.Model):
    company_code = models.PositiveIntegerField(default=1)
    year = models.PositiveSmallIntegerField(verbose_name=_("Godina prava"))
    employee_code = models.IntegerField(verbose_name=_("Šifra zaposlenog u izvoru"))
    employee = models.ForeignKey("fleet.Employee", null=True, blank=True, on_delete=models.SET_NULL)
    source_present = models.BooleanField(default=True, verbose_name=_("Prisutan u izvoru"))
    last_seen_at = models.DateTimeField()
    last_sync = models.ForeignKey(AnnualLeaveSync, null=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class AnnualLeaveAllowance(AnnualLeaveSourceRecord):
    source_employee_name = models.CharField(max_length=255, blank=True)
    allocated_days = models.PositiveIntegerField(verbose_name=_("Dodeljeno dana"))
    source_day_1 = models.IntegerField(null=True, blank=True)
    source_day_2 = models.IntegerField(null=True, blank=True)
    source_day_3 = models.IntegerField(null=True, blank=True)
    source_day_4 = models.IntegerField(null=True, blank=True)
    source_day_5 = models.IntegerField(null=True, blank=True)
    source_day_6 = models.IntegerField(null=True, blank=True)
    source_other = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-year", "employee_code"]
        constraints = [models.UniqueConstraint(fields=["company_code", "year", "employee_code"], name="hr_annual_allowance_source_key")]
        verbose_name = _("Dodela godišnjeg odmora")
        verbose_name_plural = _("Dodele godišnjeg odmora")


class AnnualLeaveDecision(AnnualLeaveSourceRecord):
    # Preserve the exact datetime portion of the source PK, independently of display dates/time zones.
    source_start_key = models.CharField(max_length=26)
    start_date = models.DateField(verbose_name=_("Od"))
    end_date = models.DateField(verbose_name=_("Do"))
    approved_days = models.PositiveIntegerField(verbose_name=_("Dana po rešenju"))
    source_comment = models.CharField(max_length=255, blank=True, verbose_name=_("Komentar iz rešenja"))

    class Meta:
        ordering = ["-year", "-start_date", "employee_code"]
        constraints = [
            models.UniqueConstraint(fields=["company_code", "year", "employee_code", "source_start_key"], name="hr_annual_decision_source_key"),
            models.CheckConstraint(check=models.Q(end_date__gte=models.F("start_date")), name="hr_annual_decision_valid_period"),
        ]
        verbose_name = _("Rešenje godišnjeg odmora")
        verbose_name_plural = _("Rešenja godišnjeg odmora")


class RecipientType(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Šifra primaoca"))
    name = models.CharField(max_length=255, verbose_name=_("Naziv vrste primaoca"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivno"))

    class Meta:
        ordering = ["code"]
        verbose_name = _("Vrsta primaoca")
        verbose_name_plural = _("Vrste primalaca")

    def __str__(self):
        return f"{self.code} — {self.name}"


class WorkTimeCategory(models.Model):
    code = models.SlugField(max_length=50, unique=True, verbose_name=_("Oznaka"))
    name = models.CharField(max_length=100, verbose_name=_("Napomena za radnu listu"))
    employee_selectable = models.BooleanField(default=True, verbose_name=_("Zaposleni bira u radnoj listi"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivno"))
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name=_("Redosled"))

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Vrsta rada / odsustva")
        verbose_name_plural = _("Vrste rada / odsustva")

    def __str__(self):
        return self.name


class WorkTimeElement(models.Model):
    recipient_type = models.ForeignKey(RecipientType, on_delete=models.PROTECT,
        related_name="elements", verbose_name=_("Vrsta primaoca"))
    category = models.ForeignKey(WorkTimeCategory, on_delete=models.PROTECT,
        related_name="elements", verbose_name=_("Napomena za radnu listu"))
    payroll_code = models.PositiveIntegerField(verbose_name=_("Šifra elementa (elsif)"))
    payroll_name = models.CharField(max_length=255, verbose_name=_("Naziv elementa (elnaz)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivno"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["recipient_type__code", "payroll_code"]
        constraints = [models.UniqueConstraint(fields=["recipient_type", "payroll_code"],name="hr_unique_recipient_payroll_element")]
        verbose_name = _("Element radne liste")
        verbose_name_plural = _("Elementi radne liste")

    def __str__(self):
        return f"{self.recipient_type.code} / {self.payroll_code} — {self.payroll_name}"


class SickLeaveImport(models.Model):
    filename = models.CharField(max_length=255, verbose_name=_("RFZO datoteka"))
    file_hash = models.CharField(max_length=64)
    source_date = models.DateField(verbose_name=_("Datum RFZO izvoza"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="sick_leave_imports")
    created_at = models.DateTimeField(auto_now_add=True)
    row_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    unchanged_count = models.PositiveIntegerField(default=0)
    unlinked_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = _("Uvoz bolovanja")
        verbose_name_plural = _("Uvozi bolovanja")


class SickLeave(models.Model):
    rfzo_id = models.CharField(max_length=64, unique=True, verbose_name=_("RFZO ID"))
    employee = models.ForeignKey("fleet.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="sick_leaves", verbose_name=_("Zaposleni"))
    personal_number = models.CharField(max_length=13, verbose_name=_("JMBG iz izvora"))
    start_date = models.DateField(db_index=True, verbose_name=_("Početak bolovanja"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("Završetak bolovanja"))
    source_status = models.CharField(max_length=50, verbose_name=_("Status RFZO"))
    source_total_days = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Ukupno dana RFZO"))
    source_date = models.DateField(verbose_name=_("Datum RFZO izvoza"))
    matching_note = models.CharField(max_length=100, blank=True, verbose_name=_("Povezivanje"))
    last_import = models.ForeignKey(SickLeaveImport, null=True, on_delete=models.SET_NULL,
                                    related_name="sick_leaves")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-pk"]
        verbose_name = _("Bolovanje")
        verbose_name_plural = _("Bolovanja")
        constraints = [models.CheckConstraint(
            check=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")),
            name="hr_sick_leave_valid_period")]

    @property
    def masked_personal_number(self):
        return "*********" + self.personal_number[-4:]

    def __str__(self):
        return f"Bolovanje {self.rfzo_id} ({self.start_date:%d.%m.%Y})"
