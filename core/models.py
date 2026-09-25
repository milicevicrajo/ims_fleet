from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrganizationalUnit(models.Model):
    name = models.CharField(verbose_name=_("Naziv"), max_length=100)
    code = models.CharField(verbose_name=_("Šifra organizacione jedinice"), max_length=10, unique=True)
    center = models.CharField(verbose_name=_("Šifra centra"), max_length=10)

    class Meta:
        app_label = "fleet"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Naziv uloge"))
    slug = models.SlugField(max_length=120, unique=True, verbose_name=_("Slug"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Opis"))
    is_active = models.BooleanField(default=True, verbose_name=_("Aktivna"))
    permissions = models.ManyToManyField(
        "PermissionCode",
        through="RolePermission",
        blank=True,
        related_name="roles",
        verbose_name=_("Dozvole"),
    )

    class Meta:
        app_label = "fleet"
        verbose_name = _("Uloga")
        verbose_name_plural = _("Uloge")

    def __str__(self):
        return self.name


class PermissionCode(models.Model):
    code = models.CharField(max_length=150, unique=True, verbose_name=_("Kod dozvole"))
    label = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Naziv"))

    class Meta:
        app_label = "fleet"
        verbose_name = _("Kod dozvole")
        verbose_name_plural = _("Kodovi dozvola")

    def __str__(self):
        return self.label or self.code


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(PermissionCode, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        app_label = "fleet"
        verbose_name = _("Dozvola uloge")
        verbose_name_plural = _("Dozvole uloga")
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.slug}:{self.permission.code}"


class CustomUser(AbstractUser):
    employee = models.OneToOneField(
        "fleet.Employee",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_account",
        verbose_name=_("Zaposleni"),
    )

    allowed_centers = models.ManyToManyField(
        "OrganizationalUnit",
        blank=True,
        verbose_name=_("Dozvoljene organizacione jedinice"),
    )

    allowed_center_codes = models.CharField(
        _("Dozvoljeni centri (šifre)"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Unesi šifre centara odvojene zarezom, npr: 43, 12, 77"),
    )

    must_change_password = models.BooleanField(
        default=False,
        verbose_name=_("Mora promeniti lozinku"),
    )

    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name=_("Uloge"),
        related_name="users",
    )

    class Meta:
        app_label = "fleet"

    def __str__(self):
        return self.username


class ActivityLog(models.Model):
    ACTION_REQUEST = "request"
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_LOGIN_FAILED = "login_failed"
    ACTION_MANUAL = "manual"

    ACTION_CHOICES = [
        (ACTION_REQUEST, _("Akcija")),
        (ACTION_LOGIN, _("Prijava")),
        (ACTION_LOGOUT, _("Odjava")),
        (ACTION_LOGIN_FAILED, _("Neuspesna prijava")),
        (ACTION_MANUAL, _("Rucni zapis")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
        verbose_name=_("Korisnik"),
    )
    actor_username = models.CharField(max_length=150, blank=True, verbose_name=_("Username"))
    actor_display_name = models.CharField(max_length=255, blank=True, verbose_name=_("Ime korisnika"))
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        default=ACTION_REQUEST,
        db_index=True,
        verbose_name=_("Akcija"),
    )
    description = models.CharField(max_length=500, blank=True, verbose_name=_("Opis"))
    app_label = models.CharField(max_length=80, blank=True, db_index=True, verbose_name=_("Aplikacija"))
    view_name = models.CharField(max_length=150, blank=True, db_index=True, verbose_name=_("View"))
    method = models.CharField(max_length=10, blank=True, verbose_name=_("Metod"))
    path = models.CharField(max_length=500, blank=True, verbose_name=_("Putanja"))
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True, verbose_name=_("Status"))
    object_model = models.CharField(max_length=150, blank=True, verbose_name=_("Model"))
    object_pk = models.CharField(max_length=80, blank=True, verbose_name=_("ID zapisa"))
    object_repr = models.CharField(max_length=255, blank=True, verbose_name=_("Zapis"))
    changes = models.JSONField(default=dict, blank=True, verbose_name=_("Detalji"))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP adresa"))
    user_agent = models.CharField(max_length=500, blank=True, verbose_name=_("User agent"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Vreme"))

    class Meta:
        app_label = "fleet"
        db_table = "fleet_activity_log"
        ordering = ["-created_at", "-id"]
        verbose_name = _("Activity log")
        verbose_name_plural = _("Activity log")
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["app_label", "-created_at"]),
        ]

    def __str__(self):
        actor = self.actor_username or str(self.user or "")
        return f"{self.created_at:%Y-%m-%d %H:%M} {actor} {self.get_action_display()}"


class TaskHistory(models.Model):
    STATUS_STARTED = "started"
    STATUS_SUCCESS = "success"
    STATUS_SKIPPED = "skipped"
    STATUS_FAILURE = "failure"

    STATUS_CHOICES = [
        (STATUS_STARTED, _("Pokrenut")),
        (STATUS_SUCCESS, _("Uspesan")),
        (STATUS_SKIPPED, _("Preskocen")),
        (STATUS_FAILURE, _("Neuspesan")),
    ]

    task_id = models.CharField(max_length=255, unique=True, verbose_name=_("Task ID"))
    task_name = models.CharField(max_length=255, db_index=True, verbose_name=_("Task"))
    display_name = models.CharField(max_length=255, blank=True, verbose_name=_("Naziv"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_STARTED,
        db_index=True,
        verbose_name=_("Status"),
    )
    short_message = models.CharField(max_length=500, blank=True, verbose_name=_("Kratko obavestenje"))
    result = models.TextField(blank=True, verbose_name=_("Rezultat"))
    error = models.TextField(blank=True, verbose_name=_("Greska"))
    args = models.JSONField(default=list, blank=True, verbose_name=_("Argumenti"))
    kwargs = models.JSONField(default=dict, blank=True, verbose_name=_("Keyword argumenti"))
    started_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Pocetak"))
    finished_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=_("Kraj"))
    elapsed_seconds = models.FloatField(null=True, blank=True, verbose_name=_("Trajanje u sekundama"))
    details = models.JSONField(default=dict, blank=True, verbose_name=_("Detalji"))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Kreirano"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Azurirano"))

    class Meta:
        app_label = "fleet"
        db_table = "fleet_task_history"
        ordering = ["-started_at", "-created_at", "-id"]
        verbose_name = _("Task history")
        verbose_name_plural = _("Task history")
        indexes = [
            models.Index(fields=["status", "-started_at"]),
            models.Index(fields=["task_name", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.display_name or self.task_name} - {self.get_status_display()}"
