"""Editable evaluation dictionaries and immutable monthly evaluation snapshots."""
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class EvaluationGroup(models.Model):
    code = models.SlugField(max_length=40, unique=True, verbose_name='Oznaka')
    name = models.CharField(max_length=100, verbose_name='Naziv grupe')
    is_active = models.BooleanField(default=True, verbose_name='Aktivno')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class EvaluationCriterion(models.Model):
    code = models.PositiveSmallIntegerField(unique=True, verbose_name='Šifra merila')
    name = models.CharField(max_length=500, verbose_name='Naziv merila (ćirilica)')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Redosled')
    is_active = models.BooleanField(default=True, verbose_name='Aktivno')

    class Meta:
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f'{self.code}. {self.name}'


class EvaluationScale(models.Model):
    group = models.ForeignKey(EvaluationGroup, on_delete=models.PROTECT, related_name='scales', verbose_name='Grupa')
    criterion = models.ForeignKey(EvaluationCriterion, on_delete=models.PROTECT, related_name='scales', verbose_name='Merilo')
    points = models.PositiveSmallIntegerField(validators=[MaxValueValidator(4)], verbose_name='Bodovi (0–4)')
    coefficient = models.DecimalField(max_digits=8, decimal_places=5, verbose_name='Koeficijent stimulacije')
    description = models.TextField(blank=True, verbose_name='Opis osnove bodovanja (ćirilica)')
    is_active = models.BooleanField(default=True, verbose_name='Aktivno')

    class Meta:
        ordering = ['group__name', 'criterion__sort_order', '-points']
        constraints = [models.UniqueConstraint(fields=['group', 'criterion', 'points'], name='hr_evaluation_scale_key')]


class EvaluationUnitSetup(models.Model):
    unit_code = models.CharField(max_length=20, unique=True, verbose_name='Šifra OJ iz kadrovske evidencije')
    supervisor = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='+', verbose_name='Neposredni rukovodilac')
    director = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='+', verbose_name='Direktor centra')
    general_director = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='+', verbose_name='Generalni direktor')
    is_active = models.BooleanField(default=True, verbose_name='Aktivno')

    class Meta:
        ordering = ['unit_code']

    def __str__(self):
        return self.unit_code


class EvaluationEmployeeSetup(models.Model):
    employee = models.OneToOneField('fleet.Employee', on_delete=models.CASCADE, related_name='evaluation_setup', verbose_name='Zaposleni')
    group = models.ForeignKey(EvaluationGroup, on_delete=models.PROTECT, verbose_name='Grupa za ocenjivanje')

    class Meta:
        ordering = ['employee__last_name', 'employee__first_name']


class EmployeeEvaluation(models.Model):
    employee = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='evaluations')
    year = models.PositiveSmallIntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    revision = models.PositiveIntegerField(default=1)
    unit_code = models.CharField(max_length=20)
    supervisor = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='+')
    director = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='+')
    general_director = models.ForeignKey('fleet.Employee', on_delete=models.PROTECT, related_name='+')
    snapshot = models.JSONField()
    stimulation = models.DecimalField(max_digits=10, decimal_places=5)
    personal_coefficient = models.DecimalField(max_digits=10, decimal_places=5)
    request_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_evaluations')
    source_evaluation = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='revisions')

    class Meta:
        ordering = ['-year', '-month', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['employee', 'year', 'month', 'revision'], name='hr_evaluation_revision_key'),
            models.CheckConstraint(check=models.Q(month__gte=1, month__lte=12), name='hr_evaluation_valid_month'),
        ]


class EvaluationApproval(models.Model):
    class Stage(models.TextChoices):
        SUPERVISOR = 'supervisor', 'Непосредни руководилац'
        DIRECTOR = 'director', 'Директор центра'
        GENERAL = 'general_director', 'Генерални директор'

    evaluation = models.ForeignKey(EmployeeEvaluation, on_delete=models.PROTECT, related_name='approvals')
    stage = models.CharField(max_length=20, choices=Stage.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='evaluation_approvals')
    actor_name = models.CharField(max_length=255)
    document_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    coefficient = models.DecimalField(max_digits=10, decimal_places=5)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at', 'pk']
        constraints = [models.UniqueConstraint(fields=['evaluation', 'stage'], name='hr_evaluation_approval_key')]
