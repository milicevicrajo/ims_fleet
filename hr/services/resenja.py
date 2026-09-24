"""Izrada kadrovskih rešenja iz šifrarnika vrsta i podataka o zaposlenom.

Tekstovi šifrarnika se čuvaju ćirilicom i preslovljavaju u latinicu kada rešenje to
traži. Obrnut smer (latinica → ćirilica) koristi se samo za predlog vrednosti u formi,
nikada za sam dokument, jer je zbog digrafa lj, nj i dž dvosmislen.
"""
import re
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.mixins import user_has_role_permission
from core.models import OrganizationalUnit
from hr.models import Pismo, Potpisnik, Resenje, ResenjeDan

from .evaluations import latin

INSTITUT = 'Институт за испитивање материјала а.д.'
MESTO = 'Б е о г р а д'
ADRESA = 'Бул.војводе Мишића 43'

_DIGRAFI = [('LJ', 'Љ'), ('Lj', 'Љ'), ('lj', 'љ'), ('NJ', 'Њ'), ('Nj', 'Њ'), ('nj', 'њ'),
            ('DŽ', 'Џ'), ('Dž', 'Џ'), ('dž', 'џ')]
_SLOVA = dict([
    ('A', 'А'), ('B', 'Б'), ('V', 'В'), ('G', 'Г'), ('D', 'Д'), ('Đ', 'Ђ'), ('E', 'Е'), ('Ž', 'Ж'), ('Z', 'З'),
    ('I', 'И'), ('J', 'Ј'), ('K', 'К'), ('L', 'Л'), ('M', 'М'), ('N', 'Н'), ('O', 'О'), ('P', 'П'), ('R', 'Р'),
    ('S', 'С'), ('T', 'Т'), ('Ć', 'Ћ'), ('U', 'У'), ('F', 'Ф'), ('H', 'Х'), ('C', 'Ц'), ('Č', 'Ч'), ('Š', 'Ш'),
    ('a', 'а'), ('b', 'б'), ('v', 'в'), ('g', 'г'), ('d', 'д'), ('đ', 'ђ'), ('e', 'е'), ('ž', 'ж'), ('z', 'з'),
    ('i', 'и'), ('j', 'ј'), ('k', 'к'), ('l', 'л'), ('m', 'м'), ('n', 'н'), ('o', 'о'), ('p', 'п'), ('r', 'р'),
    ('s', 'с'), ('t', 'т'), ('ć', 'ћ'), ('u', 'у'), ('f', 'ф'), ('h', 'х'), ('c', 'ц'), ('č', 'ч'), ('š', 'ш'),
])


def to_cyrillic(value):
    """Predlog ćirilične verzije latiničnog teksta. Digrafi se rešavaju prvi.

    Nije pouzdano za reči u kojima se l+j ili n+j izgovaraju odvojeno (npr. „injekcija“),
    zato je svuda gde se koristi ostavljeno polje za ručnu ispravku.
    """
    text = str(value or '')
    for latinica, cirilica in _DIGRAFI:
        text = text.replace(latinica, cirilica)
    return ''.join(_SLOVA.get(character, character) for character in text)


_VELIKO = 'A-ZŠĐČĆŽ'
_MALO = 'a-zšđčćž'
_DIGRAF_U_VERZALU = re.compile(
    rf'(?<=[{_VELIKO}])(Lj|Nj|Dž)(?![{_MALO}])|(?<![{_VELIKO}{_MALO}])(Lj|Nj|Dž)(?=[{_VELIKO}])')


def uskladi_digrafe(text):
    """`РЕШЕЊЕ` preslovljeno daje `REŠENjE`; u verzalu treba `REŠENJE`.

    Zajednička funkcija `latin()` uvek daje `Nj`, jer ne gleda okolinu. Ovde se
    drugo slovo digrafa podiže samo kada je reč očigledno pisana verzalom, pa
    `Njegoš` i `Ljubomir` ostaju netaknuti.
    """
    return _DIGRAF_U_VERZALU.sub(lambda match: (match.group(1) or match.group(2)).upper(), str(text or ''))


def u_pismu(value, pismo):
    """Tekst iz šifarnika (ćirilica) u traženom pismu."""
    text = str(value or '')
    return uskladi_digrafe(latin(text)) if pismo == Pismo.LATINICA else text


def ime_zaposlenog(employee, pismo):
    """Ime i prezime za tekst rešenja, verzalom, u traženom pismu."""
    latinica = f'{employee.display_first_name} {employee.display_last_name}'.strip()
    if pismo != Pismo.LATINICA:
        return (getattr(employee, 'full_name_cyrillic', '') or to_cyrillic(latinica)).upper()
    return latin(latinica).upper()


def ime_potpisnika(potpisnik, pismo):
    if potpisnik is None:
        return ''
    latinica = str(potpisnik.zaposleni)
    if pismo != Pismo.LATINICA:
        return potpisnik.ime_cirilica or getattr(potpisnik.zaposleni, 'full_name_cyrillic', '') or to_cyrillic(latinica)
    return latin(potpisnik.ime_cirilica) if potpisnik.ime_cirilica else latin(latinica)


def organizaciona_jedinica(employee):
    kod = str(employee.org_unit_code or employee.department_code or '').strip()
    return kod, OrganizationalUnit.objects.filter(code=kod).first()


def normalizuj_pol(value):
    value = str(value or '').strip().upper()
    return {'M': 'M', 'М': 'M', 'F': 'F', 'Z': 'F', 'Ž': 'F', 'Ж': 'F'}.get(value, '')


def naziv_jedinice(kod, pismo):
    jedinica = OrganizationalUnit.objects.filter(code=kod).first()
    naziv = jedinica.name.upper() if jedinica else f'OJ {kod}' if kod else ''
    return u_pismu(naziv, pismo) if pismo == Pismo.LATINICA else to_cyrillic(naziv)


def datum_teksta(value):
    return f'{value:%d.%m.%Y}.' if value else ''


def _nabrajanje(stavke, veznik='и'):
    stavke = [stavka for stavka in stavke if stavka]
    if not stavke:
        return ''
    if len(stavke) == 1:
        return stavke[0]
    return ', '.join(stavke[:-1]) + f' {veznik} ' + stavke[-1]


def spisak_dana(dani):
    return _nabrajanje([datum_teksta(dan.datum) for dan in dani])


def opis_perioda(resenje, dani):
    """Opis vremena na koje se rešenje odnosi, uvek ćirilicom."""
    if resenje.datum_od and resenje.do_zavrsetka_posla:
        return f'почев од {datum_teksta(resenje.datum_od)} до завршетка посла'
    if resenje.datum_od and resenje.datum_do:
        return f'у периоду од {datum_teksta(resenje.datum_od)} до {datum_teksta(resenje.datum_do)} године'
    if resenje.datum_od:
        return f'{datum_teksta(resenje.datum_od)} године'
    if dani:
        return f'{spisak_dana(dani)} године'
    return ''


_CUVAR = re.compile(r'\{([a-z_]+)(?::([^}]*))?\}')
_USLOV = re.compile(r'\[\[([a-z_]+)\|([^\]]*)\]\]')


def razresi(text, vrednosti, pol):
    """Zamena čuvara mesta. Nepoznat čuvar ostaje u tekstu da greška bude vidljiva.

    Segment `[[ime|tekst]]` opstaje samo kada vrednost `ime` nije prazna. Tako isti
    obrazac pokriva i rešenje samo za državni praznik i ono za državni i verski.
    """
    text = _USLOV.sub(lambda match: match.group(2) if str(vrednosti.get(match.group(1)) or '').strip() else '',
                      str(text or ''))

    def zameni(match):
        ime, opcije = match.group(1), match.group(2)
        if ime == 'rod':
            oblici = (opcije or '').split('|')
            if len(oblici) != 2:
                return match.group(0)
            if pol == 'M':
                return oblici[0]
            if pol == 'F':
                return oblici[1]
            return f'{oblici[0]}/{oblici[1]}'
        if ime in vrednosti:
            return str(vrednosti[ime] or '')
        return match.group(0)
    return _CUVAR.sub(zameni, str(text or ''))


def _redovi(text):
    return [red.strip() for red in str(text or '').splitlines() if red.strip()]


def _neprazni(redovi):
    """Red koji se posle razrešavanja isprazni ne sme da ostavi praznu tačku."""
    return [red.strip() for red in redovi if red.strip()]


def build_document(resenje, *, dani=None):
    """Potpuno razrešen dokument. Isti ulaz uvek daje isti izlaz."""
    pismo = resenje.pismo
    employee = resenje.zaposleni
    dani = list(dani if dani is not None else resenje.dani.all())
    po_vrsti = {vrsta: [dan for dan in dani if dan.vrsta_dana == vrsta] for vrsta, _ in ResenjeDan.VrstaDana.choices}
    period_dana = ''
    if resenje.datum_od:
        period_dana = datum_teksta(resenje.datum_od)
        if resenje.datum_do and resenje.datum_do != resenje.datum_od:
            period_dana = f'од {period_dana} до {datum_teksta(resenje.datum_do)}'
    vrednosti = {
        'zaposleni': resenje.zaposleni_tekst,
        'oj': resenje.oj_naziv,
        'radno_mesto': resenje.radno_mesto,
        'centar': resenje.centar,
        'period': opis_perioda(resenje, dani),
        'dani': spisak_dana(dani) or period_dana,
        'dani_prekovremeni': spisak_dana(po_vrsti['prekovremeni']),
        'dani_nocni': spisak_dana(po_vrsti['nocni']),
        'dani_vikend': spisak_dana(po_vrsti['vikend']),
        'dani_drzavni': spisak_dana(po_vrsti['drzavni']),
        'dani_verski': spisak_dana(po_vrsti['verski']),
        'radni_dani': resenje.broj_radnih_dana or '',
        'datum_povratka': datum_teksta(resenje.datum_povratka),
        'zahtev_broj': resenje.zahtev_broj,
        'zahtev_datum': datum_teksta(resenje.zahtev_datum),
        'napomena': resenje.napomena,
        'broj': resenje.broj,
        'datum': datum_teksta(resenje.datum_resenja),
    }
    # Ime, naziv OJ i napomena unose se u pismu koje je izabrano, pa se ne preslovljavaju.
    # Tekstovi šifrarnika i izvedeni opisi jesu ćirilični i prolaze kroz preslovljavanje.
    for kljuc in ('period', 'dani', 'dani_prekovremeni', 'dani_nocni', 'dani_vikend', 'dani_drzavni', 'dani_verski'):
        vrednosti[kljuc] = u_pismu(vrednosti[kljuc], pismo)
    vrsta = resenje.vrsta
    pol = normalizuj_pol(resenje.pol or employee.gender)
    tekst = lambda value: razresi(u_pismu(value, pismo), vrednosti, pol)
    potpisnik = resenje.potpisnik
    funkcija = u_pismu(potpisnik.funkcija, pismo) if potpisnik else ''
    tacke = _neprazni(tekst(red) for red in _redovi(vrsta.dispozitiv))
    if resenje.vreme_od and resenje.vreme_do and tacke:
        vreme = f'Време рада: од {resenje.vreme_od:%H:%M} до {resenje.vreme_do:%H:%M} часова'
        if resenje.vreme_do < resenje.vreme_od:
            vreme += ' наредног дана'
        tacke[0] += ' ' + u_pismu(vreme + '.', pismo)
    return {
        'schema': 1,
        'pismo': pismo,
        'vrsta': {'kod': vrsta.kod, 'naziv': vrsta.naziv},
        'broj': resenje.broj,
        'datum': datum_teksta(resenje.datum_resenja),
        'zaglavlje': {'institut': u_pismu(INSTITUT, pismo), 'funkcija': funkcija,
                      'mesto': u_pismu(MESTO, pismo), 'adresa': u_pismu(ADRESA, pismo)},
        'oznake': {kljuc: u_pismu(vrednost, pismo) for kljuc, vrednost in
                   (('broj', 'Бр.'), ('datum', 'Датум:'), ('obrazlozenje', 'Образложење'),
                    ('dostavljeno', 'Достављено:'))},
        'pravni_osnov': tekst(vrsta.pravni_osnov),
        'naslov': u_pismu(vrsta.naslov, pismo),
        'podnaslov': tekst(vrsta.podnaslov).replace('запосленог (е)', 'запослене' if pol == 'F' else 'запосленог').replace('zaposlenog (e)', 'zaposlene' if pol == 'F' else 'zaposlenog'),
        'tacke': tacke,
        'obrazlozenje': _neprazni(tekst(red) for red in _redovi(vrsta.obrazlozenje)),
        'pravna_pouka': tekst(vrsta.pravna_pouka),
        'dostavljeno': _neprazni(tekst(red) for red in _redovi(vrsta.dostavljeno)),
        'potpis': {'funkcija': funkcija, 'institut': u_pismu(INSTITUT, pismo),
                   'ime': ime_potpisnika(potpisnik, pismo)},
        'zaposleni': {'id': employee.pk, 'sifra': employee.employee_code, 'ime': resenje.zaposleni_tekst,
                      'oj': resenje.oj_naziv, 'oj_kod': resenje.oj_kod, 'centar': resenje.centar, 'pol': pol},
    }


def pripremi_resenje(resenje):
    """Popunjava podatke koji se izvode iz zaposlenog, pre prvog snimanja."""
    employee = resenje.zaposleni
    kod = resenje.oj_kod or organizaciona_jedinica(employee)[0]
    jedinica = OrganizationalUnit.objects.filter(code=kod).first()
    resenje.pol = normalizuj_pol(resenje.pol or employee.gender)
    if not resenje.zaposleni_tekst:
        resenje.zaposleni_tekst = ime_zaposlenog(employee, resenje.pismo)
    if not resenje.oj_naziv:
        resenje.oj_naziv = naziv_jedinice(kod, resenje.pismo)
    if not resenje.radno_mesto:
        radno = (employee.position or employee.job_title or '').upper()
        resenje.radno_mesto = radno if resenje.pismo == Pismo.LATINICA else to_cyrillic(radno)
    resenje.oj_kod = kod
    from fleet.services.employee_user_profiles import infer_center
    resenje.centar = str((jedinica.center if jedinica else '') or '').strip() or infer_center(kod)[0]
    if resenje.potpisnik_id is None:
        resenje.potpisnik = Potpisnik.za_datum(resenje.datum_resenja or date.today())
    return resenje


@transaction.atomic
def izdaj_resenje(resenje, user):
    """Zaključava rešenje i pamti razrešen dokument. Posle ovoga se tekst ne menja."""
    if resenje.status != Resenje.Status.NACRT:
        raise ValidationError('Rešenje je već izdato ili stornirano.')
    if not resenje.potpisnik_id:
        raise ValidationError('Nije određen potpisnik za datum rešenja. Dopuni šifrarnik potpisnika.')
    signer = resenje.potpisnik
    if resenje.datum_resenja < signer.vazi_od or (signer.vazi_do and resenje.datum_resenja >= signer.vazi_do):
        raise ValidationError('Potpisnik ne važi na datum rešenja. Izaberite važećeg potpisnika u izmeni nacrta.')
    if not normalizuj_pol(resenje.pol or resenje.zaposleni.gender):
        raise ValidationError('Izaberite pol za tekst rešenja u izmeni nacrta.')
    resenje.dokument = build_document(resenje)
    resenje.status = Resenje.Status.IZDATO
    resenje.izdato_at = timezone.now()
    resenje.save(update_fields=['dokument', 'status', 'izdato_at', 'updated_at'])
    return resenje


@transaction.atomic
def storniraj_resenje(resenje, user):
    if resenje.status == Resenje.Status.STORNIRANO:
        raise ValidationError('Rešenje je već stornirano.')
    resenje.status = Resenje.Status.STORNIRANO
    resenje.save(update_fields=['status', 'updated_at'])
    return resenje


def dokument_za_prikaz(resenje):
    """Izdato rešenje se prikazuje iz snimka, nacrt iz trenutnih podataka."""
    if resenje.dokument:
        return resenje.dokument
    return build_document(resenje)


def can_view_all(user):
    return user_has_role_permission(user, 'hr:resenje_view_all')


def dozvoljeni_centri(user):
    raw = (getattr(user, 'allowed_center_codes', '') or '').replace(';', ',')
    kodovi = [deo.strip() for deo in raw.split(',') if deo.strip()]
    jedinice = list(user.allowed_centers.values_list('center', flat=True)) if user.pk else []
    return sorted({*kodovi, *(centar for centar in jedinice if centar)})


def visible_resenja(user):
    qs = Resenje.objects.select_related('zaposleni', 'vrsta', 'potpisnik__zaposleni', 'created_by')
    if not user.is_authenticated:
        return qs.none()
    if user.is_superuser or can_view_all(user):
        return qs
    from hr.access import allowed_unit_codes, scope_values, has_restricted_scope
    from django.db.models import Q
    from django.db.models.functions import Trim
    centri, _ = scope_values(user)
    if not has_restricted_scope(user):
        return qs.filter(created_by=user)
    return qs.annotate(access_center=Trim('centar'), access_unit=Trim('oj_kod')).filter(
        Q(access_center__in=centri) | Q(access_unit__in=allowed_unit_codes(user)))
