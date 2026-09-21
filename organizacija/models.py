"""Central organizational registry.

Faza 1: registar se puni i poredi, ali ga nijedan obracun ne cita. Postojeci modeli
(`fleet.OrganizationalUnit`, `finansije.FinanceJob`) ostaju netaknuti i merodavni.

Identitet cvora je stalan i nikad se ne menja. Sifra, naziv, roditelj i oznake su
promenljivi podaci i zive u verzijama, svaka sa periodom vazenja. Zato promena sifre
ili naziva ne pravi novi posao, nego novu verziju istog.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class OrgNode(models.Model):
    """Stalni identitet organizacionog cvora. Nista u ovom modelu se ne menja."""

    LEVEL_CENTER = 1
    LEVEL_UNIT = 2
    LEVEL_JOB = 3
    LEVEL_CHOICES = [
        (LEVEL_CENTER, "1 — centar"),
        (LEVEL_UNIT, "2 — organizaciona jedinica"),
        (LEVEL_JOB, "3 — sifra posla"),
    ]

    company = models.PositiveIntegerField(verbose_name="Firma")
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, verbose_name="Nivo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Organizacioni cvor"
        verbose_name_plural = "Organizacioni cvorovi"
        indexes = [models.Index(fields=["company", "level"])]

    def __str__(self):
        version = self.current_version
        if version is None:
            return f"cvor {self.pk} (nivo {self.level}, bez verzije)"
        return f"{version.full_code} — {version.name or 'bez naziva'}"

    @property
    def current_version(self):
        return self.versions.filter(valid_to__isnull=True).order_by("-valid_from").first()

    def version_on(self, day):
        """Verzija koja je vazila na dati dan. Interval je od ukljucivo do iskljucivo."""
        return (
            self.versions.filter(valid_from__lte=day)
            .filter(Q(valid_to__isnull=True) | Q(valid_to__gt=day))
            .order_by("-valid_from")
            .first()
        )


class OrgNodeVersion(models.Model):
    """Jedno vazenje cvora. Objavljena verzija se ne prepravlja — pravi se nova.

    Interval je `valid_from` ukljucivo, `valid_to` iskljucivo; `valid_to = NULL` znaci
    da verzija jos vazi.
    """

    node = models.ForeignKey(OrgNode, on_delete=models.PROTECT, related_name="versions")
    parent = models.ForeignKey(
        OrgNode,
        on_delete=models.PROTECT,
        related_name="child_versions",
        null=True,
        blank=True,
        verbose_name="Nadredjeni cvor",
        help_text="Prazno samo za prvi nivo.",
    )
    segment = models.CharField(max_length=20, verbose_name="Segment sifre")
    full_code = models.CharField(max_length=40, db_index=True, verbose_name="Puna sifra")
    name = models.CharField(max_length=200, blank=True, verbose_name="Naziv")
    is_active = models.BooleanField(default=True, verbose_name="Aktivan")
    is_profit = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Profitni",
        help_text="Samo za treci nivo. Prazno znaci da oznaka nije poznata, ne da je neprofitan.",
    )
    valid_from = models.DateField(verbose_name="Vazi od")
    valid_to = models.DateField(null=True, blank=True, verbose_name="Vazi do (iskljucivo)")
    note = models.CharField(max_length=300, blank=True, verbose_name="Napomena")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Verzija cvora"
        verbose_name_plural = "Verzije cvorova"
        ordering = ["full_code", "valid_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["node", "valid_from"], name="orgver_node_valid_from"
            ),
            models.UniqueConstraint(
                fields=["node"],
                condition=Q(valid_to__isnull=True),
                name="orgver_one_open_per_node",
            ),
            models.CheckConstraint(
                check=Q(valid_to__isnull=True) | Q(valid_to__gt=models.F("valid_from")),
                name="orgver_valid_range",
            ),
        ]
        indexes = [models.Index(fields=["full_code", "valid_from"])]

    def __str__(self):
        return f"{self.full_code} ({self.valid_from} → {self.valid_to or 'i dalje'})"

    def clean(self):
        if self.parent_id and self.parent_id == self.node_id:
            raise ValidationError({"parent": "Cvor ne moze biti sam sebi nadredjen."})
        if self.node_id and self.node.level == OrgNode.LEVEL_CENTER and self.parent_id:
            raise ValidationError({"parent": "Prvi nivo nema nadredjeni cvor."})
        if self.node_id and self.node.level != OrgNode.LEVEL_CENTER and not self.parent_id:
            raise ValidationError({"parent": "Drugi i treci nivo moraju imati nadredjeni cvor."})
        if self.parent_id and self.node_id and self.parent.company != self.node.company:
            raise ValidationError({"parent": "Nadredjeni cvor mora biti u istoj firmi."})
        if self.parent_id and self.node_id and self.parent.level != self.node.level - 1:
            raise ValidationError({"parent": "Nadredjeni cvor mora biti tacno jedan nivo iznad."})


class ExternalOrgMapping(models.Model):
    """Veza spoljne sifre sa cvorom. Sirova vrednost se cuva neobradjena.

    Ovo je i kljuc za ponovljiv uvoz: isti `source_key` uvek vodi na isti cvor, pa
    ponovljeni uvoz ne pravi duplikate.
    """

    SOURCE_FINANCE_JOB = "finansije.FinanceJob"
    SOURCE_FLEET_UNIT = "fleet.OrganizationalUnit"
    SOURCE_LEDGER_UNIT = "finansije.LedgerEntry.organizational_unit"
    SOURCE_DERIVED = "izvedeno"

    source = models.CharField(max_length=80, verbose_name="Izvor")
    company = models.PositiveIntegerField(verbose_name="Firma")
    source_key = models.CharField(max_length=60, verbose_name="Kljuc u izvoru")
    raw_value = models.CharField(
        max_length=60,
        blank=True,
        verbose_name="Sirova vrednost",
        help_text="Neobradjena, sa rubnim razmacima kakvi su u izvoru.",
    )
    node = models.ForeignKey(OrgNode, on_delete=models.PROTECT, related_name="external_mappings")
    valid_from = models.DateField(verbose_name="Vazi od")
    valid_to = models.DateField(null=True, blank=True, verbose_name="Vazi do (iskljucivo)")

    class Meta:
        verbose_name = "Veza sa spoljnom sifrom"
        verbose_name_plural = "Veze sa spoljnim siframa"
        ordering = ["source", "source_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "company", "source_key"],
                condition=Q(valid_to__isnull=True),
                name="orgmap_open_source_key",
            )
        ]
        indexes = [models.Index(fields=["source", "source_key"])]

    def __str__(self):
        return f"{self.source}:{self.source_key} → cvor {self.node_id}"


class LegacyOrgLink(models.Model):
    """Veza sa redom u starom modelu, po njegovom primarnom kljucu.

    Odvojeno od `ExternalOrgMapping` namerno: sifra se moze promeniti, primarni kljuc ne.
    Vise starih redova sme voditi na isti cvor.
    """

    LEGACY_FLEET_UNIT = "fleet.OrganizationalUnit"
    LEGACY_FINANCE_JOB = "finansije.FinanceJob"

    legacy_label = models.CharField(max_length=80, verbose_name="Stari model")
    legacy_id = models.BigIntegerField(verbose_name="Primarni kljuc u starom modelu")
    node = models.ForeignKey(OrgNode, on_delete=models.PROTECT, related_name="legacy_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Veza sa starim modelom"
        verbose_name_plural = "Veze sa starim modelima"
        constraints = [
            models.UniqueConstraint(
                fields=["legacy_label", "legacy_id"], name="orglegacy_label_id"
            )
        ]

    def __str__(self):
        return f"{self.legacy_label}#{self.legacy_id} → cvor {self.node_id}"


class OrgImportRun(models.Model):
    """Zapis jednog uvoza. Uvoz koji nije zavrsen ostaje vidljiv kao takav."""

    STATUS_RUNNING = "u toku"
    STATUS_DONE = "zavrseno"
    STATUS_FAILED = "prekinuto"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "U toku"),
        (STATUS_DONE, "Zavrseno"),
        (STATUS_FAILED, "Prekinuto"),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RUNNING)
    source_rows = models.IntegerField(default=0, verbose_name="Procitano iz izvora")
    nodes_created = models.IntegerField(default=0)
    versions_created = models.IntegerField(default=0)
    unchanged = models.IntegerField(default=0)
    unresolved = models.IntegerField(default=0, verbose_name="Na listi za razresenje")
    report = models.TextField(blank=True, verbose_name="Izvestaj")

    class Meta:
        verbose_name = "Uvoz organizacije"
        verbose_name_plural = "Uvozi organizacije"
        ordering = ["-started_at"]

    def __str__(self):
        return f"uvoz {self.pk} ({self.status})"


class UnresolvedOrgCode(models.Model):
    """Sifra koja nije rasporedjena u stablo. Cuva se, ne izmislja joj se mesto.

    Prazan red ovde nije greska uvoza — to je spisak za odluku narucioca.
    """

    FAMILY_SCIENCE = "B"
    FAMILY_EXCEPTION = "C"
    FAMILY_CHOICES = [
        (FAMILY_SCIENCE, "B — nauka (zaseban sifarnik)"),
        (FAMILY_EXCEPTION, "C — izuzetak"),
    ]

    run = models.ForeignKey(
        OrgImportRun, on_delete=models.CASCADE, related_name="unresolved_codes"
    )
    company = models.PositiveIntegerField(verbose_name="Firma")
    code = models.CharField(max_length=40, verbose_name="Sifra")
    raw_code = models.CharField(max_length=40, blank=True, verbose_name="Sirova sifra")
    name = models.CharField(max_length=200, blank=True, verbose_name="Naziv u izvoru")
    source_center = models.CharField(max_length=10, blank=True, verbose_name="Centar u izvoru")
    family = models.CharField(max_length=1, choices=FAMILY_CHOICES)
    reason = models.CharField(max_length=300, verbose_name="Razlog")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Nerazresena sifra"
        verbose_name_plural = "Nerazresene sifre"
        ordering = ["family", "code"]
        indexes = [models.Index(fields=["run", "family"])]

    def __str__(self):
        return f"{self.code} ({self.family})"
