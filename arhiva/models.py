"""Arhiva — kancelarijsko i arhivsko poslovanje (plan: dokumentacija/plan-arhive-overe-i-cuvanja.md).

Faza 1: šifarnik kategorija (Lista kategorija sa rokovima čuvanja), evidencione knjige,
delovodnik (predmet i akti sa podbrojem). Delovodni broj daje samo `services.delovodnik`;
brojevi se nikad ne brišu i ne koriste ponovo — pogrešan upis se stornira.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q


# ---------------------------------------------------------------- šifarnik kategorija

class VerzijaListe(models.Model):
    """Jedna doneta Lista kategorija. Nova verzija ne briše staru: predmet zadržava rok iz verzije
    koja je važila pri završetku."""

    naziv = models.CharField(max_length=200, verbose_name="Naziv")
    datum_donosenja = models.DateField(null=True, blank=True, verbose_name="Datum donošenja")
    broj_saglasnosti = models.CharField(max_length=100, blank=True, default="", verbose_name="Broj saglasnosti arhiva")
    datum_saglasnosti = models.DateField(null=True, blank=True, verbose_name="Datum saglasnosti")
    vazi_od = models.DateField(null=True, blank=True, verbose_name="Važi od")
    aktivna = models.BooleanField(default=False, verbose_name="Aktivna")
    izvor = models.CharField(max_length=255, blank=True, default="", verbose_name="Uvezeno iz fajla")
    uvezao = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="+")
    uvezeno_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "arhiva_verzija_liste"
        ordering = ["-datum_donosenja", "-pk"]
        verbose_name = "Verzija Liste kategorija"
        verbose_name_plural = "Verzije Liste kategorija"
        constraints = [models.UniqueConstraint(fields=["aktivna"], condition=Q(aktivna=True),
                                               name="arhiva_jedna_aktivna_lista")]

    def __str__(self):
        return self.naziv


class GrupaKategorija(models.Model):
    """Grupa u Listi (npr. „Pravni i opšti poslovi"). Klasifikaciona oznaka stoji na grupi, a ista
    oznaka se ponavlja u više grupa (20, 82)."""

    verzija = models.ForeignKey(VerzijaListe, on_delete=models.CASCADE, related_name="grupe")
    redosled = models.PositiveSmallIntegerField()
    klasifikaciona_oznaka = models.CharField(max_length=30, verbose_name="Klasifikaciona oznaka")
    naziv = models.CharField(max_length=500, verbose_name="Naziv grupe")

    class Meta:
        db_table = "arhiva_grupa_kategorija"
        ordering = ["verzija", "redosled"]
        verbose_name = "Grupa kategorija"
        verbose_name_plural = "Grupe kategorija"

    def __str__(self):
        return f"{self.klasifikaciona_oznaka} · {self.naziv}"


class Kategorija(models.Model):
    class PocetakRoka(models.TextChoices):
        ZAVRSETAK_PREDMETA = "zavrsetak_predmeta", "Od završetka predmeta"
        ISTEK_UGOVORA = "istek_ugovora", "Od isteka ugovora"
        PRESTANAK_VAZENJA = "prestanak_vazenja", "Od prestanka važenja"
        OKONCANJE_POSTUPKA = "okoncanje_postupka", "Po okončanju postupka"
        PRESTANAK_ZAKUPA = "prestanak_zakupa", "Od prestanka zakupa"
        PRESTANAK_RADNOG_ODNOSA = "prestanak_radnog_odnosa", "Od prestanka radnog odnosa"
        RUCNO = "rucno", "Određuje se pojedinačno"

    verzija = models.ForeignKey(VerzijaListe, on_delete=models.CASCADE, related_name="kategorije")
    grupa = models.ForeignKey(GrupaKategorija, on_delete=models.PROTECT, related_name="kategorije")
    redni_broj = models.PositiveSmallIntegerField(verbose_name="Redni broj")
    naziv = models.TextField(verbose_name="Kategorija dokumentarnog materijala")
    rok_tekst = models.CharField(max_length=200, verbose_name="Rok čuvanja (kako piše u Listi)")
    rok_godina = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Rok (godina)")
    trajno = models.BooleanField(default=False, verbose_name="Trajno")
    operativno = models.BooleanField(default=False, verbose_name="Trajno operativno")
    pocetak_roka = models.CharField(max_length=30, choices=PocetakRoka.choices,
                                    default=PocetakRoka.ZAVRSETAK_PREDMETA, verbose_name="Rok teče")
    napomena_roka = models.CharField(max_length=300, blank=True, default="", verbose_name="Napomena uz rok")
    duplikat_od = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="duplikati", verbose_name="Duplikat stavke")
    aktivna = models.BooleanField(default=True, verbose_name="Nudi se pri izboru")

    class Meta:
        db_table = "arhiva_kategorija"
        ordering = ["verzija", "redni_broj"]
        constraints = [models.UniqueConstraint(fields=["verzija", "redni_broj"], name="arhiva_kategorija_rb")]
        verbose_name = "Kategorija"
        verbose_name_plural = "Kategorije"

    def __str__(self):
        return f"{self.redni_broj}. {self.naziv[:80]} ({self.rok_tekst})"

    @property
    def klasifikaciona_oznaka(self):
        return self.grupa.klasifikaciona_oznaka


# ---------------------------------------------------------------- evidencione knjige i delovodnik

class EvidencionaKnjiga(models.Model):
    """Knjiga za kalendarsku godinu. Posle zaključenja se ne upisuje (službena zabeleška)."""

    class Vrsta(models.TextChoices):
        DELOVODNIK = "delovodnik", "Delovodnik"
        DOSTAVNA = "dostavna", "Dostavna knjiga"
        OTPREMNA = "otpremna", "Otpremna knjiga (P-3)"

    class Status(models.TextChoices):
        OTVORENA = "otvorena", "Otvorena"
        ZAKLJUCENA = "zakljucena", "Zaključena"

    vrsta = models.CharField(max_length=20, choices=Vrsta.choices, default=Vrsta.DELOVODNIK)
    godina = models.PositiveSmallIntegerField()
    oznaka = models.CharField(max_length=40, blank=True, default="",
                              help_text="Za dostavne knjige po OJ; delovodnik je jedan za ceo Institut.")
    naziv = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OTVORENA)
    istorijska = models.BooleanField(default=False, help_text="Uvezena iz ranijeg programa, samo za čitanje.")
    zakljucena_at = models.DateTimeField(null=True, blank=True)
    zakljucio = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    broj_akata_pri_zakljucenju = models.PositiveIntegerField(null=True, blank=True)
    zabeleska = models.TextField(blank=True, default="", verbose_name="Službena zabeleška")

    class Meta:
        db_table = "arhiva_evidenciona_knjiga"
        ordering = ["-godina", "vrsta", "oznaka"]
        constraints = [models.UniqueConstraint(fields=["vrsta", "godina", "oznaka"], name="arhiva_knjiga_godina")]
        verbose_name = "Evidenciona knjiga"
        verbose_name_plural = "Evidencione knjige"

    def __str__(self):
        return self.naziv or f"{self.get_vrsta_display()} {self.godina}"

    @property
    def zakljucena(self):
        return self.status == self.Status.ZAKLJUCENA


class BrojacKnjige(models.Model):
    """Poslednji dodeljeni osnovni broj u knjizi. Red se zaključava pri zavođenju (UPDLOCK na SQL Serveru)."""

    knjiga = models.OneToOneField(EvidencionaKnjiga, on_delete=models.CASCADE, related_name="brojac")
    poslednji_broj = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "arhiva_brojac_knjige"
        verbose_name = "Brojač knjige"
        verbose_name_plural = "Brojači knjiga"

    def __str__(self):
        return f"{self.knjiga}: {self.poslednji_broj}"


class Smer(models.TextChoices):
    ULAZNI = "ulazni", "Ulazni"
    IZLAZNI = "izlazni", "Izlazni"
    INTERNI = "interni", "Interni"


class Predmet(models.Model):
    class Status(models.TextChoices):
        ZAVEDEN = "zaveden", "Zaveden"
        RAZVEDEN = "razveden", "Razveden"
        U_RADU = "u_radu", "U radu"
        ZAVRSEN = "zavrsen", "Završen"
        STORNIRAN = "storniran", "Storniran"

    knjiga = models.ForeignKey(EvidencionaKnjiga, on_delete=models.PROTECT, related_name="predmeti")
    osnovni_broj = models.PositiveIntegerField(verbose_name="Osnovni broj")
    delovodni_broj = models.CharField(max_length=40, verbose_name="Delovodni broj")
    datum_zavodjenja = models.DateField(verbose_name="Datum zavođenja")
    naslov = models.CharField(max_length=500, verbose_name="Predmet")
    smer = models.CharField(max_length=10, choices=Smer.choices, default=Smer.ULAZNI, verbose_name="Smer")
    korespondent = models.CharField(max_length=255, blank=True, default="",
                                    verbose_name="Pošiljalac / primalac", help_text="Ime i prezime ili naziv")
    mesto = models.CharField(max_length=100, blank=True, default="", verbose_name="Mesto")
    broj_akta_posiljaoca = models.CharField(max_length=100, blank=True, default="", verbose_name="Broj akta pošiljaoca")
    datum_akta_posiljaoca = models.DateField(null=True, blank=True, verbose_name="Datum akta pošiljaoca")
    glavna_oj = models.ForeignKey("organizacija.OrgNode", on_delete=models.PROTECT, related_name="arhiva_predmeti",
                                  verbose_name="Organizaciona jedinica")
    oznaka_centra = models.CharField(max_length=40, verbose_name="Oznaka centra (u broju)",
                                     help_text="Snimak u trenutku zavođenja; ulazi u delovodni broj.")
    dodatne_oj = models.ManyToManyField("organizacija.OrgNode", blank=True, related_name="arhiva_predmeti_dodatno",
                                        verbose_name="Dodatne OJ")
    referent = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="arhiva_predmeti", verbose_name="Zaduženi referent")
    kategorija = models.ForeignKey(Kategorija, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="predmeti", verbose_name="Kategorija")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ZAVEDEN, db_index=True)
    napomena = models.TextField(blank=True, default="", verbose_name="Napomena")
    razlog_storna = models.TextField(blank=True, default="", verbose_name="Razlog storna")
    stornirao = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    stornirano_at = models.DateTimeField(null=True, blank=True)
    zaveo = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="+")
    zavedeno_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "arhiva_predmet"
        ordering = ["-knjiga__godina", "-osnovni_broj"]
        constraints = [
            models.UniqueConstraint(fields=["knjiga", "osnovni_broj"], name="arhiva_predmet_osnovni_broj"),
            models.UniqueConstraint(fields=["knjiga", "delovodni_broj"], name="arhiva_predmet_delovodni_broj"),
        ]
        indexes = [models.Index(fields=["datum_zavodjenja"])]
        verbose_name = "Predmet"
        verbose_name_plural = "Predmeti"

    def __str__(self):
        return f"{self.delovodni_broj} · {self.naslov[:60]}"

    @property
    def storniran(self):
        return self.status == self.Status.STORNIRAN


class Akt(models.Model):
    """Akt u predmetu. Podbroj 1 je osnovni akt (isti broj kao predmet); odgovori i dopisi su 2, 3, …"""

    predmet = models.ForeignKey(Predmet, on_delete=models.PROTECT, related_name="akti")
    podbroj = models.PositiveSmallIntegerField(verbose_name="Podbroj")
    delovodni_broj = models.CharField(max_length=50, verbose_name="Delovodni broj akta")
    datum = models.DateField(verbose_name="Datum")
    opis = models.CharField(max_length=500, verbose_name="Opis")
    smer = models.CharField(max_length=10, choices=Smer.choices, default=Smer.ULAZNI, verbose_name="Smer")
    zaveo = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="+")
    zavedeno_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "arhiva_akt"
        ordering = ["predmet", "podbroj"]
        constraints = [models.UniqueConstraint(fields=["predmet", "podbroj"], name="arhiva_akt_podbroj")]
        verbose_name = "Akt"
        verbose_name_plural = "Akti"

    def __str__(self):
        return f"{self.delovodni_broj} · {self.opis[:60]}"
