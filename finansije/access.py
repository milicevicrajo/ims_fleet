"""Obuhvat Finansija: ko vidi koja knjizenja i sifre posla.

Od 28.09.2026. (plan prelaska na registar, korak 5) Finansije su **na registru**: obuhvat daju
odobrene dodele uloga (Organizacija → Dodele uloga), a centar je centar sifre posla u registru na
datum knjizenja (`LedgerEntry.org_centar`). Prazan obuhvat znaci da korisnik ne vidi nista.
Iskljucen prekidac (`settings.PRAVA_PO_REGISTRU`) vraca stara pravila ispod.
"""
from django.db.models import Q

from core.mixins import user_has_role_permission

# Obuhvat daju dodele uloga koje imaju bilo koju dozvolu Finansija.
ULAZ = "finansije:"


def na_registru():
    from organizacija.services.prava import modul_na_registru

    return modul_na_registru("finansije")


def polje_centra():
    """Polje knjizenja po kome se filtrira i sabira po centru."""
    return "org_centar" if na_registru() else "center"


def uslov_centra(centar):
    """Uslov za izabrani centar; `__none__` su knjizenja bez centra."""
    polje = polje_centra()
    if centar == "__none__":
        return Q(**{f"{polje}__isnull": True}) | Q(**{polje: ""})
    return Q(**{polje: centar})


def centri_sifara(company=1):
    """Sifra posla → oznaka centra u registru danas (za sifarnik poslova, koji nema datum)."""
    from django.utils import timezone

    from organizacija.services import putanja

    return putanja.centri_sifara(company, timezone.localdate())


def centar_sifre(job, mapa=None):
    """Centar sifre posla za prikaz: iz registra kad su Finansije na registru, inace iz sifarnika."""
    if not na_registru():
        return job.center
    return (mapa if mapa is not None else centri_sifara(job.company)).get(job.code, "")


def _obuhvat(user):
    from organizacija.services.prava import obuhvat_zahteva

    return obuhvat_zahteva(user, ULAZ)


def can_view_all(user):
    if na_registru():
        return _obuhvat(user).cela_firma
    return user_has_role_permission(user, "finansije:view_all")


def visible_scope(queryset, user, job_field="job_code"):
    if na_registru():
        return _scope_po_registru(queryset, user, job_field)
    if can_view_all(user):
        return queryset
    raw = getattr(user, "allowed_center_codes", "") or ""
    centers = {value.strip() for value in raw.replace(";", ",").split(",") if value.strip()}
    units = list(user.allowed_centers.values_list("code", "center"))
    codes = {str(code).strip() for code, _ in units if code and str(code).strip()}
    centers.update(str(center).strip() for _, center in units if center and str(center).strip())
    if not centers and not codes:
        return queryset.none()
    return queryset.filter(Q(center__in=centers) | Q(**{f"{job_field}__in": codes}))


def _scope_po_registru(queryset, user, job_field):
    from finansije.models import LedgerEntry
    from organizacija.services import prava

    obuhvat = _obuhvat(user)
    if obuhvat.cela_firma:
        return queryset
    if queryset.model is LedgerEntry:
        # Pripadnost se gleda na datum knjizenja: posle promene centra stara knjizenja ostaju starom centru.
        return prava.ogranici(queryset, obuhvat, "org_node", "booking_date")
    if obuhvat.prazan:
        return queryset.none()
    return queryset.filter(**{f"{job_field}__in": prava.sifre_obuhvata(obuhvat)})
