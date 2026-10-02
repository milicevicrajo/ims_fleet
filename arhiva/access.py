"""Obuhvat Arhive: koje predmete korisnik vidi (od prvog dana na registru organizacije).

Predmet pripada centru ili organizacionoj jedinici (`Predmet.glavna_oj`, `dodatne_oj`), a ne
šifri posla, pa se ne koristi `q_obuhvata` (on ide preko putanja šifara posla). Predmet se vidi
kada mu je glavna ili dodatna OJ u obuhvatu dodele: dodeljen centar obuhvata i sve njegove OJ.
Zaduženi referent i onaj ko je predmet zaveo uvek ga vide. Pisarnica i arhivista imaju dodelu
cele firme. `allowed_center_codes` / `allowed_centers` se ne čitaju (AGENTS.md, zamka 12).
"""
from django.db.models import Q

DOZVOLE = "arhiva:"


def na_registru():
    from organizacija.services.prava import modul_na_registru

    return modul_na_registru("arhiva")


def cvorovi_obuhvata(obuhvat_):
    """Čvorovi (centri i OJ) čije predmete korisnik vidi; None znači cela firma."""
    from organizacija.models import OrgNodeVersion

    if obuhvat_.cela_firma:
        return None
    cvorovi = set(obuhvat_.centri) | set(obuhvat_.jedinice)
    if obuhvat_.centri:
        cvorovi.update(OrgNodeVersion.objects.filter(valid_to__isnull=True, parent_id__in=obuhvat_.centri)
                       .values_list("node_id", flat=True))
    return cvorovi


def predmeti(queryset, user):
    """Predmeti u obuhvatu korisnika. Van registra (testovi, prelazak) ne ograničava."""
    if not na_registru() or not user.is_authenticated:
        return queryset
    from organizacija.services.prava import obuhvat_zahteva

    cvorovi = cvorovi_obuhvata(obuhvat_zahteva(user, DOZVOLE))
    if cvorovi is None:
        return queryset
    uslov = Q(referent=user) | Q(zaveo=user)
    if cvorovi:
        uslov |= Q(glavna_oj__in=cvorovi) | Q(pk__in=queryset.model.objects.filter(dodatne_oj__in=cvorovi).values("pk"))
    return queryset.filter(uslov)
