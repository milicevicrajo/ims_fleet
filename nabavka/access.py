"""Obuhvat Nabavke: koje predmete i fakture korisnik vidi (plan prelaska na registar, korak 5).

Do 28.09.2026. Nabavka nije ogranicavala po centru — svako sa dozvolom video je sve. Na registru
(`settings.PRAVA_PO_REGISTRU["nabavka"]`) obuhvat daju odobrene dodele uloga: predmet i faktura se
vide ako im je sifra posla u obuhvatu, po danasnjoj pripadnosti sifre u registru. Predmet koji je
korisnik sam napravio uvek vidi. Zapis bez sifre posla vidi samo obuhvat cele firme.

Dokumenti bez sifre posla po prirodi (UF stavke, roba, ugovori, javne nabavke, narudzbenice) nisu
vezani za organizaciju i ne ogranicavaju se.
"""
from django.db.models import Q

# Obuhvat daju dodele uloga koje imaju bilo koju dozvolu Nabavke (i onaj ko ima samo detalj predmeta).
PREDMETI = FAKTURE = "nabavka:"


def na_registru():
    from organizacija.services.prava import modul_na_registru

    return modul_na_registru("nabavka")


def _obuhvat(user, kod):
    from organizacija.services.prava import obuhvat_zahteva

    return obuhvat_zahteva(user, kod)


def predmeti(queryset, user):
    """Predmeti nabavke u obuhvatu korisnika (i njegovi sopstveni)."""
    if not na_registru() or not user.is_authenticated:  # neprijavljenog zaustavlja LoginRequiredMixin
        return queryset
    from organizacija.services.prava import ogranici

    return ogranici(queryset, _obuhvat(user, PREDMETI), "org_node", ili=Q(created_by=user))


def fiskalni_racuni(queryset, user):
    """Fiskalni racuni cija je sifra posla u obuhvatu korisnika (i oni koje je sam ucitao)."""
    if not na_registru() or not user.is_authenticated:
        return queryset
    from organizacija.services.prava import ogranici

    return ogranici(queryset, _obuhvat(user, FAKTURE), "org_node", ili=Q(created_by=user))


def sifre_za_izbor(queryset, user):
    """Izbor sifre posla u Nabavci: samo iz obuhvata korisnika (na registru)."""
    if not na_registru() or not user.is_authenticated or user.is_superuser:
        return queryset
    from organizacija.services.prava import jedinice_obuhvata

    ids = jedinice_obuhvata(_obuhvat(user, PREDMETI))
    return queryset if ids is None else queryset.filter(pk__in=ids)


def fakture(queryset, user):
    """Fakture u obuhvatu korisnika."""
    if not na_registru() or not user.is_authenticated:
        return queryset
    from organizacija.services.prava import ogranici

    return ogranici(queryset, _obuhvat(user, FAKTURE), "org_node")
