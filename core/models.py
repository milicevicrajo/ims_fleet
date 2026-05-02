from django.contrib.auth.models import AbstractUser
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
