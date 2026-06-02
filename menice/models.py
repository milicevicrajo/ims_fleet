from django.db import models
from django.urls import reverse


class Menica(models.Model):
    TIP_IZLAZNA = "izlazna"
    TIP_ULAZNA = "ulazna"

    TIP_CHOICES = [
        (TIP_IZLAZNA, "Izlazna menica"),
        (TIP_ULAZNA, "Ulazna menica"),
    ]

    STATUS_AKTIVNA = 0
    STATUS_OBRISANA = 1
    STATUS_NEPOZNAT = 2

    INTERNI_STATUS_CHOICES = [
        (STATUS_AKTIVNA, "Aktivna"),
        (STATUS_OBRISANA, "Obrisana"),
        (STATUS_NEPOZNAT, "Nepoznat"),
    ]

    LOKACIJA_CENTAR = "centar"
    LOKACIJA_BLAGAJNA = "blagajna"

    FIZICKA_LOKACIJA_CHOICES = [
        (LOKACIJA_CENTAR, "Centar"),
        (LOKACIJA_BLAGAJNA, "Blagajna"),
    ]

    tip = models.CharField(max_length=20, choices=TIP_CHOICES, db_index=True)

    sifra_partnera = models.IntegerField("Sifra partnera", blank=True, null=True, db_index=True)
    naziv_duznika = models.CharField("Naziv duznika", max_length=255, blank=True, null=True)
    maticni_broj_duznika = models.CharField("Maticni broj duznika", max_length=50, blank=True, null=True)
    poreski_broj_duznika = models.CharField("Poreski broj duznika", max_length=50, blank=True, null=True)
    strana_rezultata = models.PositiveIntegerField("Strana rezultata", blank=True, null=True)
    serijski_broj_menice = models.CharField("Serijski broj menice", max_length=100, blank=True, null=True, db_index=True)
    datum_izdavanja = models.DateField("Datum izdavanja", blank=True, null=True)
    iznos_menice = models.DecimalField("Iznos menice", max_digits=18, decimal_places=2, blank=True, null=True)
    valuta_menice = models.CharField("Valuta menice", max_length=10, blank=True, null=True)
    datum_dospeca = models.DateField("Datum dospeca", blank=True, null=True)
    izdavalac_menice = models.CharField("Izdavalac menice", max_length=255, blank=True, null=True)
    vrsta_menice = models.CharField("Vrsta menice", max_length=100, blank=True, null=True)
    redni_broj = models.PositiveIntegerField("Redni broj", blank=True, null=True)
    osnov_izdavanja = models.CharField("Osnov izdavanja", max_length=255, blank=True, null=True)
    iznos_iz_osnova = models.DecimalField("Iznos iz osnova", max_digits=18, decimal_places=2, blank=True, null=True)
    valuta_osnova = models.CharField("Valuta osnova", max_length=10, blank=True, null=True)
    datum_registracije = models.DateField("Datum registracije", blank=True, null=True)
    naziv_banke = models.CharField("Naziv banke", max_length=255, blank=True, null=True)
    status = models.CharField("Status", max_length=100, blank=True, null=True)
    avalisti_detalji = models.TextField("Avalisti detalji", blank=True, null=True)
    avalisti_broj_zapisa = models.PositiveIntegerField("Avalisti broj zapisa", blank=True, null=True)
    broj_ugovora = models.CharField("Broj ugovora", max_length=100, blank=True, null=True)
    datum_ugovora = models.DateField("Datum ugovora", blank=True, null=True)
    oj = models.CharField("OJ", max_length=100, blank=True, null=True)
    fizicka_lokacija = models.CharField(
        "Fizicka lokacija",
        max_length=20,
        choices=FIZICKA_LOKACIJA_CHOICES,
        blank=True,
        null=True,
        db_index=True,
    )
    napomena = models.TextField("Napomena", blank=True, null=True)
    interni_status = models.PositiveSmallIntegerField(
        "Status (0-aktivna, 1-obrisana,2-nepoznat)",
        choices=INTERNI_STATUS_CHOICES,
        default=STATUS_AKTIVNA,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "menica"
        ordering = ["-datum_registracije", "-created_at"]
        indexes = [
            models.Index(fields=["tip", "interni_status"]),
            models.Index(fields=["serijski_broj_menice"]),
        ]
        verbose_name = "Menica"
        verbose_name_plural = "Menice"

    def __str__(self):
        return self.serijski_broj_menice or self.naziv_duznika or f"Menica {self.pk}"

    def get_absolute_url(self):
        return reverse("menice:menica_list", kwargs={"tip": self.tip})


class UlaznaMenica(models.Model):
    JEDINICA_RSD = "RSD"
    JEDINICA_EUR = "EUR"
    JEDINICA_PROCENAT = "PROCENAT"
    JEDINICA_VREDNOSTI_CHOICES = [
        (JEDINICA_RSD, "RSD"),
        (JEDINICA_EUR, "EUR"),
        (JEDINICA_PROCENAT, "Procenat"),
    ]

    serijski_broj_menice = models.CharField("Serijski broj menice", max_length=100, db_index=True)
    osnov_izdavanja = models.CharField("Osnov izdavanja", max_length=255, blank=True, null=True)
    datum_prijema_menice = models.DateField("Datum prijema menice", blank=True, null=True)
    jedinica_vrednosti = models.CharField(
        "Jedinica vrednosti",
        max_length=10,
        choices=JEDINICA_VREDNOSTI_CHOICES,
        default=JEDINICA_PROCENAT,
    )
    procenat_iznos = models.DecimalField("Iznos", max_digits=18, decimal_places=2, blank=True, null=True)
    sifra_poslovnog_partnera = models.IntegerField("Sifra poslovnog partnera", blank=True, null=True, db_index=True)
    naziv_pravnog_lica = models.CharField("Naziv pravnog lica", max_length=255, blank=True, null=True)
    broj_naseg_ugovora = models.CharField("Broj naseg ugovora", max_length=100, blank=True, null=True)
    datum_ugovora = models.DateField("Datum ugovora", blank=True, null=True)
    ugovor_vazi_do = models.DateField("Ugovor vazi do", blank=True, null=True)
    lokacija_menice = models.CharField("Lokacija menice", max_length=100, blank=True, null=True)
    sifra_centra = models.CharField("Sifra centra", max_length=50, blank=True, null=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ulazna_menica"
        ordering = ["-datum_prijema_menice", "-created_at"]
        indexes = [
            models.Index(fields=["serijski_broj_menice"]),
            models.Index(fields=["sifra_poslovnog_partnera"]),
            models.Index(fields=["sifra_centra"]),
        ]
        verbose_name = "Ulazna menica"
        verbose_name_plural = "Ulazne menice"

    def __str__(self):
        return self.serijski_broj_menice

    def get_absolute_url(self):
        return reverse("menice:ulazna_menica_list")
