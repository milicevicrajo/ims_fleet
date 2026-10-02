"""Delovodnik: dodela delovodnog broja, podbroj, storno, zaključenje knjige.

Broj daje samo ovaj servis. Brojač knjige se zaključava (`select_for_update`, na SQL Serveru
UPDLOCK), pa dva istovremena zavođenja ne mogu dobiti isti broj; unique ograničenje na
(knjiga, osnovni broj) je druga linija zaštite. Ne koristi se `MAX()+1`.

Format broja dolazi iz podešavanja (`ARHIVA_FORMAT_BROJA`, `ARHIVA_FORMAT_PODBROJA`) jer je
to još otvorena odluka (plan, O-1). Podrazumevano `{centar}-{broj}` i `{osnovni}/{podbroj}`,
kao brojevi zahteva u Kadrovima (`43-15238`, `43-15238/2`).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from arhiva.models import Akt, BrojacKnjige, EvidencionaKnjiga, Predmet, Smer

FORMAT_BROJA = "{centar}-{broj}"
FORMAT_PODBROJA = "{osnovni}/{podbroj}"


def formatiraj_broj(centar, broj):
    sablon = getattr(settings, "ARHIVA_FORMAT_BROJA", FORMAT_BROJA)
    centar = str(centar or "").strip()
    if not centar:
        return str(broj)
    return sablon.format(centar=centar, broj=broj)


def formatiraj_podbroj(osnovni, podbroj):
    if podbroj <= 1:
        return osnovni
    return getattr(settings, "ARHIVA_FORMAT_PODBROJA", FORMAT_PODBROJA).format(osnovni=osnovni, podbroj=podbroj)


def oznaka_centra(cvor):
    """Oznaka centra za čvor registra: centar daje svoju šifru, OJ šifru nadređenog centra."""
    from organizacija.models import OrgNode, OrgNodeVersion

    verzija = OrgNodeVersion.objects.filter(node=cvor, valid_to__isnull=True).select_related("parent").first()
    if verzija is None:
        raise ValidationError("Organizaciona jedinica nema važeću verziju u registru.")
    if cvor.level == OrgNode.LEVEL_CENTER:
        return verzija.full_code
    if cvor.level == OrgNode.LEVEL_UNIT and verzija.parent_id:
        roditelj = OrgNodeVersion.objects.filter(node_id=verzija.parent_id, valid_to__isnull=True).first()
        if roditelj:
            return roditelj.full_code
    raise ValidationError("Predmet se zavodi na centar ili organizacionu jedinicu, ne na šifru posla.")


def knjiga_za(godina, vrsta=EvidencionaKnjiga.Vrsta.DELOVODNIK):
    knjiga, _ = EvidencionaKnjiga.objects.get_or_create(
        vrsta=vrsta, godina=godina, oznaka="",
        defaults={"naziv": f"{EvidencionaKnjiga.Vrsta(vrsta).label} {godina}"})
    return knjiga


@transaction.atomic
def zavedi(*, datum, naslov, glavna_oj, zaveo, smer=Smer.ULAZNI, **polja):
    """Zavodi novi predmet sa osnovnim aktom (podbroj 1) i vraća ga."""
    if not (naslov or "").strip():
        raise ValidationError("Unesite predmet (sadržaj akta).")
    knjiga = knjiga_za(datum.year)
    if knjiga.zakljucena:
        raise ValidationError(f"Delovodnik za {knjiga.godina}. je zaključen. Upis nije moguć.")
    if knjiga.istorijska:
        raise ValidationError(f"Delovodnik za {knjiga.godina}. je uvezen iz ranijeg programa i služi samo za čitanje.")
    centar = oznaka_centra(glavna_oj)
    BrojacKnjige.objects.get_or_create(knjiga=knjiga)
    brojac = BrojacKnjige.objects.select_for_update().get(knjiga=knjiga)
    brojac.poslednji_broj += 1
    brojac.save(update_fields=["poslednji_broj"])
    dodatne = polja.pop("dodatne_oj", None)
    predmet = Predmet.objects.create(
        knjiga=knjiga, osnovni_broj=brojac.poslednji_broj, delovodni_broj=formatiraj_broj(centar, brojac.poslednji_broj),
        datum_zavodjenja=datum, naslov=naslov.strip(), smer=smer, glavna_oj=glavna_oj, oznaka_centra=centar,
        zaveo=zaveo, **polja)
    if dodatne:
        predmet.dodatne_oj.set(dodatne)
    Akt.objects.create(predmet=predmet, podbroj=1, delovodni_broj=predmet.delovodni_broj, datum=datum,
                       opis=predmet.naslov, smer=smer, zaveo=zaveo)
    return predmet


@transaction.atomic
def dodaj_podbroj(predmet, *, datum, opis, zaveo, smer=None):
    """Novi akt u postojećem predmetu (odgovor, dopis). Predmet se zaključava dok se računa podbroj."""
    predmet = Predmet.objects.select_for_update().select_related("knjiga").get(pk=predmet.pk)
    if predmet.storniran:
        raise ValidationError("Predmet je storniran. U njega se ne upisuju novi akti.")
    if predmet.knjiga.zakljucena:
        raise ValidationError(f"Delovodnik za {predmet.knjiga.godina}. je zaključen.")
    if not (opis or "").strip():
        raise ValidationError("Unesite opis akta.")
    podbroj = (predmet.akti.aggregate(n=Max("podbroj"))["n"] or 0) + 1
    return Akt.objects.create(predmet=predmet, podbroj=podbroj,
                              delovodni_broj=formatiraj_podbroj(predmet.delovodni_broj, podbroj),
                              datum=datum, opis=opis.strip(), smer=smer or predmet.smer, zaveo=zaveo)


@transaction.atomic
def storniraj(predmet, *, razlog, ko):
    """Pogrešan upis se ne briše: broj ostaje, upisuje se razlog."""
    predmet = Predmet.objects.select_for_update().get(pk=predmet.pk)
    if predmet.storniran:
        raise ValidationError("Predmet je već storniran.")
    if not (razlog or "").strip():
        raise ValidationError("Unesite razlog storna.")
    predmet.status = Predmet.Status.STORNIRAN
    predmet.razlog_storna = razlog.strip()
    predmet.stornirao, predmet.stornirano_at = ko, timezone.now()
    predmet.save(update_fields=["status", "razlog_storna", "stornirao", "stornirano_at"])
    return predmet


@transaction.atomic
def zakljuci_knjigu(knjiga, *, ko, zabeleska=""):
    """Zaključenje službenom zabeleškom: upisuje broj akata; posle toga knjiga je samo za čitanje."""
    knjiga = EvidencionaKnjiga.objects.select_for_update().get(pk=knjiga.pk)
    if knjiga.zakljucena:
        raise ValidationError("Knjiga je već zaključena.")
    broj = knjiga.predmeti.count()
    knjiga.status = EvidencionaKnjiga.Status.ZAKLJUCENA
    knjiga.zakljucena_at, knjiga.zakljucio = timezone.now(), ko
    knjiga.broj_akata_pri_zakljucenju = broj
    knjiga.zabeleska = zabeleska.strip() or (
        f"Zaključeno sa {broj} upisa, poslednji osnovni broj {getattr(getattr(knjiga, 'brojac', None), 'poslednji_broj', 0)}.")
    knjiga.save(update_fields=["status", "zakljucena_at", "zakljucio", "broj_akata_pri_zakljucenju", "zabeleska"])
    return knjiga
