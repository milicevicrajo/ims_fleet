"""Local, explicit evidence for fleet analysis. No writes to legacy ERP objects."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.utils import timezone


class VehicleEvidence(models.Model):
    vehicle = models.ForeignKey('fleet.Vehicle', on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from fleet.models import Vehicle
        using = kwargs.get('using') or self._state.db or 'default'
        with transaction.atomic(using=using):
            Vehicle.objects.using(using).select_for_update().get(pk=self.vehicle_id)
            self.full_clean()
            return super().save(*args, **kwargs)


class VehicleAnalysisProfile(VehicleEvidence):
    class Purpose(models.TextChoices):
        LAB = 'laboratory', 'Prevoz laboratorijske ekipe i opreme'
        SUPERVISION = 'supervision', 'Nadzor i terenski rad'
        MANAGEMENT = 'management', 'Uprava i poslovna mobilnost'
        TRANSPORT = 'transport', 'Transport mašina i kontejnera'
        DRILLING = 'drilling', 'Vozilo sa bušećom mašinom'
        TOWING = 'towing', 'Prevoz / vuča SPT i druge opreme'
        TRAILER = 'trailer', 'Priključno vozilo'

    effective_from = models.DateField('Važi od', default=timezone.localdate)
    purpose = models.CharField('Poslovna namena', max_length=24, choices=Purpose.choices)
    criticality = models.CharField('Zahtev raspoloživosti / razlog zadržavanja', max_length=500, blank=True)
    fuel_source = models.CharField('Izvor goriva za analizu', max_length=16,
        choices=[('transactions', 'NIS / OMV transakcije'), ('legacy', 'Ranija evidencija goriva')], default='transactions')
    criterion_basis = models.CharField('Raspolaganje za koje važi kriterijum', max_length=16, blank=True,
        choices=[('owned', 'Vlasništvo IMS'), ('finansijski', 'Finansijski lizing'),
                 ('operativni', 'Operativni lizing'), ('dugorocni', 'Dugoročni najam')])
    cost_limit_km = models.DecimalField('Kontrolni prag RSD/km', max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    cost_limit_day = models.DecimalField('Kontrolni prag RSD/dan po nalogu', max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    criterion_source = models.TextField('Osnov kriterijuma i obuhvat troškova', blank=True,
        help_text='Navesti izvor, datum, namenu i zašto je prag uporediv sa obuhvaćenim troškovima. Prag je signal za pregled, ne odluka o zameni.')
    note = models.TextField('Napomena o podacima i režimu rada', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_from', '-pk']
        constraints = [models.UniqueConstraint(fields=['vehicle', 'effective_from'], name='unique_vehicle_analysis_date')]
        verbose_name = 'Profil analitike vozila'

    def clean(self):
        super().clean()
        if (self.cost_limit_km is not None or self.cost_limit_day is not None) and not self.criterion_source.strip():
            raise ValidationError({'criterion_source': 'Uz prag obavezno navedite osnov i obuhvat poređenja.'})
        if (self.cost_limit_km is not None or self.cost_limit_day is not None) and not self.criterion_basis:
            raise ValidationError({'criterion_basis': 'Uz prag izaberite i način raspolaganja na koji se odnosi.'})
        if self.purpose in (self.Purpose.DRILLING, self.Purpose.TRAILER) and self.cost_limit_km is not None:
            raise ValidationError({'cost_limit_km': 'Za ovu namenu kilometri nisu merodavan kriterijum opravdanosti.'})


class LeaseChargePeriod(models.Model):
    lease = models.ForeignKey('fleet.Lease', on_delete=models.CASCADE, related_name='analysis_charges', verbose_name='Ugovor')
    start = models.DateField('Važi od')
    end = models.DateField('Važi do (uključivo)')
    amount = models.DecimalField('Iznos RSD', max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    basis = models.CharField('Značenje iznosa', max_length=10, choices=[('monthly', 'Mesečna naknada'), ('total', 'Ukupno za ovaj period')])
    evidence = models.CharField('Dokument, obuhvat usluga i poreska osnova', max_length=500)

    class Meta:
        ordering = ['start', 'pk']

    def clean(self):
        super().clean()
        if self.start and self.end and self.end < self.start:
            raise ValidationError({'end': 'Završetak ne može biti pre početka.'})
        if self.lease_id and self.start and self.end:
            if self.start < self.lease.start_date or self.end > self.lease.end_date:
                raise ValidationError('Period naknade mora biti unutar ugovora.')
            if self.lease.lease_type == 'finansijski':
                raise ValidationError('Glavnica finansijskog lizinga ne ulazi u trošak perioda; kamate se vode zasebno.')
            if type(self).objects.filter(lease_id=self.lease_id, start__lte=self.end, end__gte=self.start).exclude(pk=self.pk).exists():
                raise ValidationError('Period naknade se preklapa sa postojećim periodom.')

    def save(self, *args, **kwargs):
        from fleet.models import Lease
        using = kwargs.get('using') or self._state.db or 'default'
        with transaction.atomic(using=using):
            Lease.objects.using(using).select_for_update().get(pk=self.lease_id)
            self.full_clean()
            return super().save(*args, **kwargs)


class VehicleDowntime(VehicleEvidence):
    start = models.DateField('Neupotrebljivo od')
    end = models.DateField('Poslednji dan neupotrebljivosti', null=True, blank=True)
    reason = models.CharField('Uzrok', max_length=200)
    incident = models.ForeignKey('fleet.Kvar', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Prijava / intervencija')
    note = models.TextField('Dokaz / napomena', blank=True)

    class Meta:
        ordering = ['-start', '-pk']

    def clean(self):
        super().clean()
        if (self.start and self.start > timezone.localdate()) or (self.end and self.end > timezone.localdate()):
            raise ValidationError('Evidencija stvarne neupotrebljivosti ne može biti u budućnosti.')
        if self.start and self.end and self.end < self.start:
            raise ValidationError({'end': 'Završetak ne može biti pre početka.'})
        if self.incident_id and self.incident.vehicle_id != self.vehicle_id:
            raise ValidationError({'incident': 'Prijava mora pripadati ovom vozilu.'})


class VehicleEconomicAssessment(VehicleEvidence):
    as_of = models.DateField('Datum procene', default=timezone.localdate)
    title = models.CharField('Naziv procene', max_length=160)
    years = models.PositiveSmallIntegerField('Zajednički horizont (godine)', validators=[MinValueValidator(1), MaxValueValidator(20)])
    discount_percent = models.DecimalField('Realna diskontna stopa (%)', max_digits=6, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    annual_km = models.PositiveIntegerField('Planirani km godišnje', null=True, blank=True)
    annual_days = models.PositiveSmallIntegerField('Planirani dani angažovanja godišnje', null=True, blank=True, validators=[MaxValueValidator(366)])
    scope = models.TextField('Isti posao, kapacitet, raspoloživost i obuhvat svih alternativa')
    assumptions = models.TextField('Izvori cena, poreska osnova i pretpostavke')
    snapshot = models.JSONField(default=dict, editable=False)
    methodology_version = models.CharField(max_length=32, default='IMS-FLOTA-2.0', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, editable=False)

    class Meta:
        ordering = ['-as_of', '-pk']


class VehicleEconomicScenario(models.Model):
    assessment = models.ForeignKey(VehicleEconomicAssessment, on_delete=models.CASCADE, related_name='scenarios')
    name = models.CharField('Alternativa', max_length=120)
    kind = models.CharField('Vrsta', max_length=16, choices=[('keep', 'Zadržavanje'), ('buy', 'Kupovina / zamena'), ('lease', 'Lizing / najam'), ('outsource', 'Spoljna usluga')])
    initial_cost = models.DecimalField('Početna vrednost / nepovratni početni izdatak RSD', max_digits=16, decimal_places=2, validators=[MinValueValidator(0)], help_text='Zadržavanje: današnja tržišna vrednost. Kupovina: nabavka i priprema. Najam: nepovratni početni izdaci. Bez ponovnog dodavanja glavnice.')
    annual_cost = models.DecimalField('Svi godišnji budući troškovi RSD', max_digits=16, decimal_places=2, validators=[MinValueValidator(0)], help_text='Stalan godišnji iznos u današnjim cenama za zajednički plan rada. Uključiti rad, održavanje, osiguranje i ugovorne naknade po potrebi. Ne dodavati amortizaciju ni kamatu već obuhvaćenu kapitalnim modelom.')
    residual_value = models.DecimalField('Neto preostala vrednost na kraju RSD', max_digits=16, decimal_places=2, validators=[MinValueValidator(0)], help_text='Prodajna vrednost umanjena za trošak prodaje; za najam / spoljnu uslugu najčešće 0.')
    feasible = models.BooleanField('Potvrđeno ispunjava isti posao i zahteve raspoloživosti', default=False)
    evidence = models.TextField('Ponuda / procena i obrazloženje troškova')

    class Meta:
        ordering = ['pk']
