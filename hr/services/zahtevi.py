"""Zahtevi za kadrovska rešenja: broj, dokument, podnošenje i rešenje iz zahteva.

Zahtev dobija broj `{centar}-{redni broj u godini}`, npr. `43-17`. Rešenje napravljeno
iz zahteva dobija podbroj tog zahteva, npr. `43-17/1`. Brojevi se ne koriste ponovo:
ni storniran zahtev ni obrisan nacrt rešenja ne vraćaju svoj broj.
"""
from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from hr.models import BrojacZahteva, Pismo, Potpisnik, Resenje, ResenjeDan, Zahtev

from .resenja import (ADRESA, INSTITUT, MESTO, _neprazni, _redovi, datum_teksta, dodatne_vrednosti, ime_osobe,
    ime_zaposlenog, naziv_jedinice, normalizuj_pol, opis_vremena, organizaciona_jedinica, pripremi_resenje,
    razresi, to_cyrillic, u_obuhvatu, u_pismu, vrednosti_perioda)


def formatiraj_broj(centar, redni_broj):
    centar = str(centar or '').strip()
    return f'{centar}-{redni_broj}' if centar else str(redni_broj)


@transaction.atomic
def dodeli_broj(zahtev):
    """Sledeći redni broj u godini zahteva. Red brojača ostaje zaključan do kraja transakcije."""
    godina = zahtev.datum_zahteva.year
    BrojacZahteva.objects.get_or_create(godina=godina)
    brojac = BrojacZahteva.objects.select_for_update().get(godina=godina)
    brojac.poslednji_broj += 1
    brojac.save(update_fields=['poslednji_broj'])
    zahtev.godina, zahtev.redni_broj = godina, brojac.poslednji_broj
    zahtev.broj = formatiraj_broj(zahtev.centar, zahtev.redni_broj)
    return zahtev


def pripremi_zahtev(zahtev):
    """Popunjava podatke koji se izvode iz zaposlenog i potpisnika, pre snimanja."""
    employee = zahtev.zaposleni
    kod = zahtev.oj_kod or organizaciona_jedinica(employee)[0]
    from core.models import OrganizationalUnit
    from fleet.services.employee_user_profiles import infer_center
    jedinica = OrganizationalUnit.objects.filter(code=kod).first()
    zahtev.pol = normalizuj_pol(zahtev.pol or employee.gender)
    if not zahtev.zaposleni_tekst:
        zahtev.zaposleni_tekst = ime_zaposlenog(employee, zahtev.pismo)
    if not zahtev.oj_naziv:
        zahtev.oj_naziv = naziv_jedinice(kod, zahtev.pismo)
    if not zahtev.radno_mesto:
        radno = (employee.position or employee.job_title or '').upper()
        zahtev.radno_mesto = radno if zahtev.pismo == Pismo.LATINICA else to_cyrillic(radno)
    zahtev.oj_kod = kod
    zahtev.centar = str((jedinica.center if jedinica else '') or '').strip() or infer_center(kod)[0]
    if not zahtev.odobrava_id:
        potpisnik = Potpisnik.za_datum(zahtev.datum_zahteva or date.today())
        if potpisnik:
            zahtev.odobrava = potpisnik.zaposleni
            zahtev.odobrava_funkcija = zahtev.odobrava_funkcija or potpisnik.funkcija
    if zahtev.redni_broj:
        # Nacrt može da promeni zaposlenog; redni broj ostaje, menja se samo oznaka centra.
        zahtev.broj = formatiraj_broj(zahtev.centar, zahtev.redni_broj)
    return zahtev


def build_zahtev_document(zahtev, *, dani=None):
    """Potpuno razrešen tekst zahteva. Isti ulaz uvek daje isti izlaz."""
    pismo = zahtev.pismo
    employee = zahtev.zaposleni
    dani = list(dani if dani is not None else zahtev.dani.all())
    podnosilac = ime_osobe(zahtev.podnosilac, pismo)
    odobrava = ime_osobe(zahtev.odobrava, pismo)
    vrednosti = {
        'zaposleni': zahtev.zaposleni_tekst,
        'oj': zahtev.oj_naziv,
        'radno_mesto': zahtev.radno_mesto,
        'centar': zahtev.centar,
        **vrednosti_perioda(zahtev, dani, pismo),
        'razlog': zahtev.razlog,
        'podnosilac': podnosilac,
        'podnosilac_funkcija': u_pismu(zahtev.podnosilac_funkcija, pismo),
        'odobrava': odobrava,
        'odobrava_funkcija': u_pismu(zahtev.odobrava_funkcija, pismo),
        'broj': zahtev.broj,
        'datum': datum_teksta(zahtev.datum_zahteva),
    }
    vrednosti.update({kljuc: vrednost for kljuc, vrednost in
                      dodatne_vrednosti(zahtev.vrsta, zahtev.dodatni_podaci).items() if kljuc not in vrednosti})
    pol = normalizuj_pol(zahtev.pol or employee.gender)
    tekst = lambda value: razresi(u_pismu(value, pismo), vrednosti, pol)
    pasusi = _neprazni(tekst(red) for red in _redovi(zahtev.vrsta.tekst))
    vreme = opis_vremena(zahtev, pismo)
    if vreme:
        pasusi.append(vreme)
    return {
        'schema': 1,
        'tip': 'zahtev',
        'pismo': pismo,
        'vrsta': {'kod': zahtev.vrsta.kod, 'naziv': zahtev.vrsta.naziv},
        'broj': zahtev.broj,
        'datum': datum_teksta(zahtev.datum_zahteva),
        'zaglavlje': {'institut': u_pismu(INSTITUT, pismo), 'mesto': u_pismu(MESTO, pismo),
                      'adresa': u_pismu(ADRESA, pismo)},
        'oznake': {kljuc: u_pismu(vrednost, pismo) for kljuc, vrednost in
                   (('broj', 'Наш знак:'), ('datum', 'Датум:'), ('predmet', 'Предмет:'),
                    ('primalac', 'Упућено:'), ('odobrava', 'Одобрава:'), ('podnosilac', 'Подносилац захтева'))},
        'primalac': {'funkcija': vrednosti['odobrava_funkcija'], 'ime': odobrava},
        'predmet': tekst(zahtev.vrsta.predmet),
        'pasusi': pasusi,
        'potpis': {'funkcija': vrednosti['podnosilac_funkcija'], 'ime': podnosilac},
        'odobrenje': {'funkcija': vrednosti['odobrava_funkcija'], 'ime': odobrava},
        'zaposleni': {'id': employee.pk, 'sifra': employee.employee_code, 'ime': zahtev.zaposleni_tekst,
                      'oj': zahtev.oj_naziv, 'oj_kod': zahtev.oj_kod, 'centar': zahtev.centar, 'pol': pol},
    }


def dokument_zahteva_za_prikaz(zahtev):
    """Podnet zahtev se prikazuje iz snimka, nacrt iz trenutnih podataka."""
    return zahtev.dokument or build_zahtev_document(zahtev)


@transaction.atomic
def podnesi_zahtev(zahtev, user):
    """Zaključava tekst zahteva. Posle ovoga se zahtev ne menja, samo stornira."""
    if zahtev.status != Zahtev.Status.NACRT:
        raise ValidationError('Zahtev je već podnet ili storniran.')
    if not normalizuj_pol(zahtev.pol or zahtev.zaposleni.gender):
        raise ValidationError('Izaberite pol za tekst zahteva u izmeni nacrta.')
    zahtev.dokument = build_zahtev_document(zahtev)
    zahtev.status = Zahtev.Status.PODNET
    zahtev.podneto_at = timezone.now()
    zahtev.save(update_fields=['dokument', 'status', 'podneto_at', 'updated_at'])
    return zahtev


def aktivna_resenja(zahtev):
    return zahtev.resenja.exclude(status=Resenje.Status.STORNIRANO)


@transaction.atomic
def storniraj_zahtev(zahtev, user):
    if zahtev.status == Zahtev.Status.STORNIRAN:
        raise ValidationError('Zahtev je već storniran.')
    postojeca = list(aktivna_resenja(zahtev).values_list('broj', flat=True))
    if postojeca:
        raise ValidationError('Zahtev ima rešenja koja nisu stornirana (' + ', '.join(postojeca) +
                              '). Prvo stornirajte rešenja ili obrišite nacrte.')
    zahtev.status = Zahtev.Status.STORNIRAN
    zahtev.save(update_fields=['status', 'updated_at'])
    return zahtev


@transaction.atomic
def napravi_resenje(zahtev, user, *, vrsta=None, datum_resenja=None, potpisnik=None):
    """Nacrt rešenja iz zahteva: isti zaposleni, period, dani i dodatni podaci, broj je podbroj zahteva."""
    zahtev = Zahtev.objects.select_for_update().select_related('vrsta__vrsta_resenja', 'zaposleni').get(pk=zahtev.pk)
    if zahtev.resenja.exists():
        raise ValidationError('Zahtev već ima rešenje. Jedan zahtev može imati samo jedno rešenje, uključujući stornirano.')
    if zahtev.status == Zahtev.Status.STORNIRAN:
        raise ValidationError('Iz storniranog zahteva se ne pravi rešenje.')
    vrsta = vrsta or zahtev.vrsta.vrsta_resenja
    if vrsta is None:
        raise ValidationError('Za ovu vrstu zahteva nije određeno rešenje. Izaberite vrstu rešenja.')
    zahtev.poslednji_podbroj += 1
    zahtev.save(update_fields=['poslednji_podbroj', 'updated_at'])
    podbroj = zahtev.poslednji_podbroj
    polja = dodatne_vrednosti(vrsta, zahtev.dodatni_podaci)
    resenje = Resenje(
        zahtev=zahtev, podbroj=podbroj, broj=f'{zahtev.broj}/{podbroj}', vrsta=vrsta, zaposleni=zahtev.zaposleni,
        datum_resenja=datum_resenja or timezone.localdate(), pismo=zahtev.pismo, pol=zahtev.pol,
        oj_kod=zahtev.oj_kod, oj_naziv=zahtev.oj_naziv, radno_mesto=zahtev.radno_mesto,
        datum_od=zahtev.datum_od, datum_do=zahtev.datum_do, vreme_od=zahtev.vreme_od, vreme_do=zahtev.vreme_do,
        do_zavrsetka_posla=zahtev.do_zavrsetka_posla, broj_radnih_dana=zahtev.broj_radnih_dana,
        datum_povratka=zahtev.datum_povratka, zahtev_broj=zahtev.broj, zahtev_datum=zahtev.datum_zahteva,
        potpisnik=potpisnik, dodatni_podaci=polja, created_by=user)
    pripremi_resenje(resenje)
    try:
        with transaction.atomic():
            resenje.save()
    except IntegrityError:
        if zahtev.resenja.exists():
            raise ValidationError('Zahtev već ima rešenje. Otvorite postojeće rešenje.')
        raise
    ResenjeDan.objects.bulk_create([ResenjeDan(resenje=resenje, datum=dan.datum, vrsta_dana=dan.vrsta_dana)
                                    for dan in zahtev.dani.all()])
    return resenje


def visible_zahtevi(user):
    return u_obuhvatu(Zahtev.objects.select_related('zaposleni', 'vrsta', 'podnosilac', 'odobrava', 'created_by'), user)
