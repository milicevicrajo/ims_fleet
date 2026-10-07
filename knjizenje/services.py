"""Tok knjiženja fiskalnih računa Isplata: pošalji → (vrati na doradu → pošalji) → proknjiži (→ poništi).

Isplate samo šalju; poslat račun se u Isplatama ne menja dok ga knjiženje ne vrati na doradu.
Račun proknjižen pre modula Knjiženje (oznaka iz Isplata, do 07.10.2026.) nema zapis — smatra se proknjiženim.
"""
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from nabavka.models import FiskalniRacun
from nabavka.services import fiskalni

from .models import DogadjajKnjizenja, KnjizenjeRacuna

Status = KnjizenjeRacuna.Status


class GreskaKnjizenja(Exception):
    pass


def racuni_isplata():
    """Računi koje Isplate šalju na knjiženje: sa putnih naloga i ostali (gotovinski obračun)."""
    return FiskalniRacun.objects.filter(Q(putni_nalog__isnull=False) | Q(evidencija=FiskalniRacun.Evidencija.GOTOVINA))


def racuni_knjizenja():
    """Računi koje modul Knjiženje vidi: poslati (i vraćeni, proknjiženi) i ranije proknjiženi."""
    return racuni_isplata().filter(Q(knjizenje__isnull=False) | Q(proknjizeno=True))


def zapis(racun):
    try:
        return racun.knjizenje
    except KnjizenjeRacuna.DoesNotExist:
        return None


def stanje(racun):
    """None (nije poslat), „poslato”, „vraceno” ili „proknjizeno”."""
    if racun.proknjizeno:
        return Status.PROKNJIZENO
    z = zapis(racun)
    return z.status if z else None


def zakljucan_u_isplatama(racun):
    """Poslat ili proknjižen račun Isplate ne menjaju (ni šifru, ni interni broj, ni putni nalog)."""
    return stanje(racun) in (Status.POSLATO, Status.PROKNJIZENO)


def moze_se_poslati(racun):
    return stanje(racun) in (None, Status.VRACENO)


def _dogadjaj(z, vrsta, korisnik, napomena=""):
    DogadjajKnjizenja.objects.create(knjizenje=z, vrsta=vrsta, korisnik=korisnik, napomena=napomena or "")


@transaction.atomic
def posalji(racun, korisnik):
    st = stanje(racun)
    if st == Status.PROKNJIZENO:
        raise GreskaKnjizenja(f"Račun {racun.broj_racuna} je već proknjižen.")
    if st == Status.POSLATO:
        raise GreskaKnjizenja(f"Račun {racun.broj_racuna} je već poslat na knjiženje.")
    z = zapis(racun) or KnjizenjeRacuna(racun=racun)
    z.status, z.poslao, z.poslato_at = Status.POSLATO, korisnik, timezone.now()
    z.save()
    racun.knjizenje = z
    _dogadjaj(z, DogadjajKnjizenja.Vrsta.POSLATO, korisnik)
    return z


@transaction.atomic
def vrati_na_doradu(racun, korisnik, razlog, request=None):
    from core.activity import log_activity

    razlog = (razlog or "").strip()
    if not razlog:
        raise GreskaKnjizenja("Upišite razlog vraćanja — Isplate ga vide na računu.")
    z = zapis(racun)
    if stanje(racun) != Status.POSLATO:
        raise GreskaKnjizenja(f"Na doradu se vraća samo račun koji čeka knjiženje ({racun.broj_racuna}).")
    z.status, z.razlog_vracanja, z.vratio, z.vraceno_at = Status.VRACENO, razlog[:500], korisnik, timezone.now()
    z.save(update_fields=["status", "razlog_vracanja", "vratio", "vraceno_at"])
    _dogadjaj(z, DogadjajKnjizenja.Vrsta.VRACENO, korisnik, razlog)
    log_activity(request=request, user=korisnik, object_instance=racun,
                 description=f"Fiskalni račun {racun.broj_racuna} je vraćen Isplatama na doradu: {razlog}")
    return z


@transaction.atomic
def proknjizi(racuni, korisnik, datum, broj_naloga="", napomena=""):
    """Knjiži jedan ili više računa pod istim datumom i nalogom za knjiženje. Svi moraju da čekaju knjiženje."""
    racuni = list(racuni)
    if not racuni:
        raise GreskaKnjizenja("Izaberite račune za knjiženje.")
    if not datum:
        raise GreskaKnjizenja("Upišite datum knjiženja.")
    neispravni = [r.broj_racuna for r in racuni if stanje(r) != Status.POSLATO]
    if neispravni:
        raise GreskaKnjizenja("Ne čekaju knjiženje: " + ", ".join(neispravni[:5]) + (" …" if len(neispravni) > 5 else ""))
    sada = timezone.now()
    for racun in racuni:
        z = zapis(racun)
        z.status, z.datum_knjizenja, z.broj_naloga, z.napomena = Status.PROKNJIZENO, datum, (broj_naloga or "").strip(), (napomena or "").strip()
        z.knjizio, z.proknjizeno_at = korisnik, sada
        z.save()
        _dogadjaj(z, DogadjajKnjizenja.Vrsta.PROKNJIZENO, korisnik,
                  " · ".join(d for d in (f"datum {datum:%d.%m.%Y.}", f"nalog {z.broj_naloga}" if z.broj_naloga else "", z.napomena) if d))
        fiskalni.oznaci_proknjizeno(racun, korisnik, True)
    return len(racuni)


@transaction.atomic
def ponisti(racun, korisnik, razlog, request=None):
    """Poništava knjiženje: račun ponovo čeka knjiženje (ne vraća se Isplatama). Beleži se u evidenciji rada."""
    razlog = (razlog or "").strip()
    if not razlog:
        raise GreskaKnjizenja("Upišite razlog poništavanja knjiženja.")
    if stanje(racun) != Status.PROKNJIZENO:
        raise GreskaKnjizenja(f"Račun {racun.broj_racuna} nije proknjižen.")
    z = zapis(racun) or KnjizenjeRacuna(racun=racun)  # proknjižen pre modula Knjiženje
    z.status = Status.POSLATO
    z.datum_knjizenja, z.broj_naloga, z.napomena, z.knjizio, z.proknjizeno_at = None, "", "", None, None
    z.save()
    racun.knjizenje = z
    _dogadjaj(z, DogadjajKnjizenja.Vrsta.PONISTENO, korisnik, razlog)
    fiskalni.oznaci_proknjizeno(racun, korisnik, False, request=request)
    return z
