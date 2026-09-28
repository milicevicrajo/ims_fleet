"""Obuhvat Flote na registru organizacije (plan prelaska na registar, korak 6).

Kad je Flota na registru (`settings.PRAVA_PO_REGISTRU["flota"]`), obuhvat daju **odobrene dodele
uloga** koje imaju bilo koju dozvolu Flote (bez dozvola za zaposlene, naloge za vozilo i nalog
korisnika — to nisu podaci vozila). Stara prava (`allowed_center_codes`, `allowed_centers`) i
izuzetak za Upravu vise ne odlucuju; Uprava, Garaza, Nabavka i Blagajna imaju dodelu cele firme.

Pravila (odluke 25.09.2026.):

- **vozilo** i sve sto se na njega vezuje (saobracajne, polise, lizing, gorivo, servisi, kvarovi,
  trebovanja, osiguranje, dokumenti) vidi se ako je **danasnja dodela vozila** u obuhvatu; vozilo bez
  ijedne dodele vidi svako ko ima neki obuhvat, da tek uneto vozilo ne nestane;
- **putni nalog** se vidi ako mu je sifra posla u obuhvatu;
- izvestaji po centru i sifri posla filtriraju po siframa posla u obuhvatu (istorijska dodela na
  dan zapisa ostaje kao i do sada);
- prazan obuhvat — nista.

Nalozi za vozilo (`VehicleTravelOrder`) ne zavise od organizacije (zaposleni vidi svoje) i ovde
se ne ogranicavaju.
"""
from functools import lru_cache

from django.db.models import OuterRef, Subquery
from django.utils import timezone

ISKLJUCENE_DOZVOLE = ("employee", "vehicle_travel_order", "user", "login", "logout", "password", "my_",
                      "activity_log", "task_history")


def na_registru():
    from organizacija.services.prava import modul_na_registru

    return modul_na_registru("flota")


@lru_cache(maxsize=1)
def dozvole_flote():
    from core.permissions import collect_fleet_permission_codes

    return frozenset(c for c in collect_fleet_permission_codes() if not c.startswith(ISKLJUCENE_DOZVOLE))


def obuhvat(user):
    from organizacija.services.prava import obuhvat_zahteva

    return obuhvat_zahteva(user, dozvole_flote())


def _kes(user, kljuc, izracunaj):
    kes = user.__dict__.setdefault("_obuhvat_flote", {})
    if kljuc not in kes:
        kes[kljuc] = izracunaj()
    return kes[kljuc]


def jedinice(user):
    """Organizacione jedinice Flote (sifre posla) u obuhvatu danas; None znaci cela firma."""
    def izracunaj():
        from core.models import OrganizationalUnit
        from organizacija.models import LegacyOrgLink
        from organizacija.services.prava import sifre_obuhvata

        o = obuhvat(user)
        sifre_registra = sifre_obuhvata(o)
        if sifre_registra is None:
            return None
        from organizacija.services.prava import poslovi_obuhvata

        ids = set(LegacyOrgLink.objects.filter(legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT,
                                               node_id__in=poslovi_obuhvata(o)).values_list("legacy_id", flat=True))
        # Jedinica napravljena posle poslednjeg uvoza registra jos nema vezu — nalazi se po sifri.
        ids.update(pk for pk, code in OrganizationalUnit.objects.values_list("pk", "code")
                   if (code or "").strip() in sifre_registra)
        return ids

    return _kes(user, "jedinice", izracunaj)


def sifre(user):
    """Sifre posla (kako ih vodi Flota) u obuhvatu; None znaci cela firma."""
    def izracunaj():
        from core.models import OrganizationalUnit

        ids = jedinice(user)
        if ids is None:
            return None
        return {(c or "").strip() for c in OrganizationalUnit.objects.filter(pk__in=ids).values_list("code", flat=True)}

    return _kes(user, "sifre", izracunaj)


def centri(user):
    """Oznake centara koje su u obuhvatu cele (za analizu centra); None znaci cela firma."""
    def izracunaj():
        from organizacija.models import OrgNodeVersion

        o = obuhvat(user)
        if o.cela_firma:
            return None
        return set(OrgNodeVersion.objects.filter(node_id__in=o.centri, valid_to__isnull=True)
                   .values_list("full_code", flat=True))

    return _kes(user, "centri", izracunaj)


def vozila(user):
    """Vozila cija je danasnja dodela u obuhvatu (i vozila bez dodele); None znaci cela firma."""
    def izracunaj():
        from fleet.models import JobCode, Vehicle

        ids = jedinice(user)
        if ids is None:
            return None
        if obuhvat(user).prazan:
            return set()
        dodela = (JobCode.objects.filter(vehicle_id=OuterRef("pk"), assigned_date__lte=timezone.localdate())
                  .order_by("-assigned_date", "-pk").values("organizational_unit_id")[:1])
        return {pk for pk, jedinica in Vehicle.objects.annotate(jedinica=Subquery(dodela)).values_list("pk", "jedinica")
                if jedinica is None or jedinica in ids}

    return _kes(user, "vozila", izracunaj)


def aktivno(user):
    """Da li obuhvat Flote odlucuje za ovog korisnika (modul na registru, prijavljen, nije superuser)."""
    return na_registru() and getattr(user, "is_authenticated", False) and not user.is_superuser


def po_vozilu(queryset, user, polje="vehicle"):
    """Zapisi cije je vozilo u obuhvatu korisnika (`polje="pk"` za same vozila)."""
    if not aktivno(user):
        return queryset
    ids = vozila(user)
    if ids is None:
        return queryset
    return queryset.filter(**{"pk__in" if polje == "pk" else f"{polje}_id__in": ids})


def putni_nalozi(queryset, user):
    """Putni nalozi cija je sifra posla u obuhvatu korisnika."""
    if not aktivno(user):
        return queryset
    ids = jedinice(user)
    return queryset if ids is None else queryset.filter(job_code_id__in=ids)


def ogranici_jedinice(queryset, user, zadrzi=None):
    """Izbor sifre posla (OrganizationalUnit) u obuhvatu; vec upisana vrednost ostaje u izboru."""
    if not aktivno(user):
        return queryset
    ids = jedinice(user)
    if ids is None:
        return queryset
    ogranicen = queryset.filter(pk__in=ids)
    if zadrzi:
        ogranicen = ogranicen | queryset.filter(pk=zadrzi)
    return ogranicen.distinct()


def ogranici_po_vozilu(polje="vehicle"):
    """Dekorator klase prikaza: `get_queryset` (i sopstveni, ako ga klasa ima) samo u obuhvatu."""
    def dekorator(cls):
        izvorni = cls.get_queryset

        def get_queryset(self, *args, **kwargs):
            return po_vozilu(izvorni(self, *args, **kwargs), self.request.user, polje)

        cls.get_queryset = get_queryset
        return cls

    return dekorator


def ogranici_putne_naloge(cls):
    """Dekorator klase prikaza putnih naloga: samo nalozi sa sifrom posla u obuhvatu."""
    izvorni = cls.get_queryset

    def get_queryset(self, *args, **kwargs):
        return putni_nalozi(izvorni(self, *args, **kwargs), self.request.user)

    cls.get_queryset = get_queryset
    return cls
