"""Osoba (JMBG) i zaposlenja (preduzece + broj radnika) — pregled pre razdvajanja (od 06.10.2026.).

Broj radnika (`rasif`) jedinstven je samo unutar preduzeca (`sif_pred`: 1 = radni odnos, 2 = van
radnog odnosa), a ista osoba posle ponovnog prijema dobija novi broj. Osobu odredjuje JMBG (`matbr`).
Ovde se samo cita: izvor `radnik` na PUTGEO-SERVER.bazaldims i lokalna tabela zaposlenih.
"""
from collections import defaultdict

from django.db import connections

from hr.models import Employee, Osoba
from hr.services.ugovori import IZVOR
from hr.sync import _resolve_hr_db_alias

PRIKAZ_POLJA = {"display_first_name_override": "ime_za_prikaz", "display_last_name_override": "prezime_za_prikaz",
                "full_name_cyrillic": "ime_cirilica"}

RADNICI_OSOBE_SQL = f"SELECT sif_pred, rasif, matbr, ranaz, aktivan, dat_dolaska FROM {IZVOR}.[radnik]"
POGLED_SQL = "SELECT COUNT(*), COUNT(DISTINCT rasif) FROM dbo.hr_employee"


def jmbg(vrednost):
    """JMBG iz izvora ili tabele: samo cifre; prazno ako nije upisan."""
    return "".join(z for z in str(vrednost or "") if z.isdigit())


def _ceo(vrednost):
    try:
        return int(vrednost)
    except (TypeError, ValueError):
        return None


def _redosled(e):
    """Glavno zaposlenje ide prvo: aktivno, radni odnos, poslednji prijem."""
    return (not e.is_active, e.preduzece != Employee.Preduzece.RADNI_ODNOS,
            -(e.date_of_joining.toordinal() if e.date_of_joining else 0), -e.employee_code)


def glavno_zaposlenje(osoba):
    """Zaposlenje koje daje lične podatke osobe: aktivno, radni odnos, poslednji prijem."""
    return min(osoba.zaposlenja.all(), default=None, key=_redosled)


def jedan_po_osobi(zaposlenja):
    """Spisak zaposlenja svedeni na jedan red po osobi: glavno među datim zaposlenjima.

    Svaki red dobija `druge_sifre` — ostala zaposlenja iste osobe (sva, ne samo filtrirana), za prikaz uz broj.
    Zaposlenje bez osobe ostaje svoj red. Redosled ulaza se čuva.
    """
    izabrana = {}
    for e in zaposlenja:
        kljuc = e.osoba_id or f"z{e.pk}"
        if kljuc not in izabrana or _redosled(e) < _redosled(izabrana[kljuc]):
            izabrana[kljuc] = e
    po_osobi = defaultdict(list)
    osobe = [e.osoba_id for e in izabrana.values() if e.osoba_id]
    for e in Employee.objects.filter(osoba_id__in=osobe).only("pk", "osoba_id", "employee_code", "preduzece",
                                                               "is_active", "date_of_joining"):
        po_osobi[e.osoba_id].append(e)
    redovi = []
    for e in zaposlenja:
        if izabrana.get(e.osoba_id or f"z{e.pk}") is e:
            e.druge_sifre = sorted((d for d in po_osobi.get(e.osoba_id, []) if d.pk != e.pk), key=_redosled)
            redovi.append(e)
    return redovi


def osvezi_osobu(osoba):
    """Ime, prezime, titula, pol i datum rođenja iz glavnog zaposlenja (HR podaci)."""
    glavno = glavno_zaposlenje(osoba)
    if glavno is None:
        return osoba
    vrednosti = dict(titula=glavno.title or "", ime=glavno.first_name or "", prezime=glavno.last_name or "",
                     pol=glavno.gender or "", datum_rodjenja=glavno.date_of_birth)
    if any(getattr(osoba, k) != v for k, v in vrednosti.items()):
        for k, v in vrednosti.items():
            setattr(osoba, k, v)
        osoba.save(update_fields=[*vrednosti, "updated_at"])
    return osoba


def prenesi_prikaz(osoba):
    """Ime za prikaz i ćirilični oblik važe za osobu: prepisuju se na sva njena zaposlenja."""
    osoba.zaposlenja.update(**{polje: getattr(osoba, izvor) for polje, izvor in PRIKAZ_POLJA.items()})


def povezi_osobu(employee):
    """Veže zaposlenje za osobu po JMBG-u (pravi je ako ne postoji). Bez JMBG-a zaposlenje zadržava svoju
    osobu ili dobija novu. Nova veza preuzima ime za prikaz i ćirilicu osobe. Vraća osobu."""
    broj = jmbg(employee.personal_number)
    if broj:
        osoba = Osoba.objects.filter(jmbg=broj).first()
    else:
        osoba = employee.osoba if employee.osoba_id and not employee.osoba.jmbg else None
    if osoba is None:
        osoba = Osoba.objects.create(jmbg=broj, **{izvor: getattr(employee, polje) or ""
                                                   for polje, izvor in PRIKAZ_POLJA.items()})
    if employee.osoba_id != osoba.pk:
        employee.osoba = osoba
        for polje, izvor in PRIKAZ_POLJA.items():
            setattr(employee, polje, getattr(osoba, izvor))
        employee.save(update_fields=["osoba", *PRIKAZ_POLJA])
    return osoba


def sacuvaj_prikaz_zaposlenja(employee):
    """Posle izmene imena za prikaz ili ćirilice na zaposlenju: upisuje ih na osobu i ostala zaposlenja."""
    osoba = employee.osoba if employee.osoba_id else povezi_osobu(employee)
    for polje, izvor in PRIKAZ_POLJA.items():
        setattr(osoba, izvor, getattr(employee, polje) or "")
    osoba.save(update_fields=[*PRIKAZ_POLJA.values(), "updated_at"])
    prenesi_prikaz(osoba)


STAZ_SQL = (f"SELECT sif_pred, rasif, CONVERT(date, datum1), CONVERT(date, datum2), u_firmi, staz_gg, staz_mm, staz_dd "
            f"FROM {IZVOR}.[RadStaz]")
BEZ_KRAJA = 2999  # kadrovska baza upisuje 01.01.3000. kad kraj perioda nije poznat


def periodi_staza(using=None):
    """Svi periodi staža iz `RadStaz`: u IMS (`DA`) i kod drugih poslodavaca (`NE`, `ME`)."""
    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        cursor.execute(STAZ_SQL)
        redovi = cursor.fetchall()
    return [dict(preduzece=_ceo(r[0]), broj=_ceo(r[1]), od=r[2], do=r[3], u_ims=str(r[4] or "").strip().upper() == "DA",
                 staz=(_ceo(r[5]) or 0, _ceo(r[6]) or 0, _ceo(r[7]) or 0)) for r in redovi]


def _normalizuj(godina, meseci, dana):
    # Kao kadrovska baza: 30 dana = 1 mesec, 12 meseci = 1 godina.
    meseci += dana // 30
    return godina + meseci // 12, meseci % 12, dana % 30


def obracunaj_staz(periodi, redosled_sifara):
    """Ukupan staž osobe iz perioda svih njenih šifara: ((g, m, d) ukupno, (g, m, d) u IMS).

    Staž perioda je izvorni (efektivni) staž, ne razlika datuma. Pod novom šifrom kadrovska baza ponekad ponovi
    periode stare šifre, pa: period bez staža otpada; isti period (iste datume) računa se jednom — vrednost
    novije šifre; period ceo unutar dužeg perioda druge šifre ne računa se, osim kad duži period nema upisan
    kraj (3000), jer se tada ne zna šta obuhvata. `redosled_sifara`: broj radnika -> rang (manji je noviji).
    """
    periodi = [p for p in periodi if any(p["staz"])]
    periodi.sort(key=lambda p: (-(p["do"] - p["od"]).days if p["od"] and p["do"] else 0,
                                redosled_sifara.get(p["broj"], 99)))
    uzeti = []
    for p in periodi:
        if not (p["od"] and p["do"]):
            uzeti.append(p)
            continue
        ponovljen = any(u["broj"] != p["broj"] and u["od"] and u["do"] and u["do"].year < BEZ_KRAJA
                        and u["od"] <= p["od"] and p["do"] <= u["do"] for u in uzeti)
        if not ponovljen:
            uzeti.append(p)
    ukupno = _normalizuj(*(sum(p["staz"][i] for p in uzeti) for i in range(3)))
    u_ims = _normalizuj(*(sum(p["staz"][i] for p in uzeti if p["u_ims"]) for i in range(3)))
    return ukupno, u_ims


def osvezi_staz(periodi):
    """Upisuje ukupan staž i staž u IMS na osobe. `periodi` iz `periodi_staza`. Vraća broj osoba."""
    from django.utils import timezone

    zaposlenja = list(Employee.objects.filter(osoba__isnull=False).only(
        "osoba_id", "employee_code", "preduzece", "is_active", "date_of_joining"))
    osoba_sifre = {(e.preduzece, e.employee_code): e.osoba_id for e in zaposlenja}
    rang = defaultdict(dict)
    for e in zaposlenja:
        rang[e.osoba_id][e.employee_code] = _redosled(e)
    po_osobi = defaultdict(list)
    for p in periodi:
        osoba_id = osoba_sifre.get((p["preduzece"], p["broj"]))
        if osoba_id:
            po_osobi[osoba_id].append(p)
    sada = timezone.now()
    for osoba_id, njegovi in po_osobi.items():
        redosled = {broj: i for i, broj in enumerate(sorted(rang[osoba_id], key=lambda b: rang[osoba_id][b]))}
        (g, m, d), (ig, im, idn) = obracunaj_staz(njegovi, redosled)
        Osoba.objects.filter(pk=osoba_id).update(staz_godina=g, staz_meseci=m, staz_dana=d, staz_ims_godina=ig,
                                                 staz_ims_meseci=im, staz_ims_dana=idn, staz_preuzet=sada)
    return len(po_osobi)


def radnici_izvora(using=None):
    """Svi brojevi radnika iz izvora, oba preduzeca, aktivni i neaktivni."""
    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        cursor.execute(RADNICI_OSOBE_SQL)
        redovi = cursor.fetchall()
    return [dict(preduzece=_ceo(r[0]), broj=_ceo(r[1]), jmbg=jmbg(r[2]), ime=(r[3] or "").strip(),
                 aktivan=str(r[4] or "").strip().upper() == "D", prijem=r[5]) for r in redovi]


def pregled_identiteta(using=None):
    """Sta bi razdvajanje osobe od broja radnika zateklo. Nista ne upisuje."""
    izvor = radnici_izvora(using)
    lokalni = {e.employee_code: e for e in Employee.objects.all()}

    po_jmbg = defaultdict(list)
    bez_jmbg = []
    po_broju = defaultdict(list)
    for r in izvor:
        r["lokalni"] = lokalni.get(r["broj"])
        po_broju[r["broj"]].append(r)
        (po_jmbg[r["jmbg"]] if r["jmbg"] else bez_jmbg).append(r)
    for redovi in po_jmbg.values():
        redovi.sort(key=lambda r: (r["preduzece"] or 0, r["broj"] or 0))

    # Isti broj radnika u oba preduzeca: kod nas je broj jedinstven, pa bi jedan prepisao drugog.
    sukobi_broja = {broj: redovi for broj, redovi in po_broju.items()
                    if len({r["preduzece"] for r in redovi}) > 1}
    brojevi_izvora = set(po_broju)

    lokalni_po_jmbg = defaultdict(list)
    for e in lokalni.values():
        lokalni_po_jmbg[jmbg(e.personal_number)].append(e)

    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        cursor.execute(POGLED_SQL)
        redova_pogleda, brojeva_pogleda = cursor.fetchone()

    return {
        "izvor_redova": len(izvor),
        "izvor_osoba": len(po_jmbg),
        "vise_brojeva": {k: v for k, v in po_jmbg.items() if len(v) > 1},
        "izvor_bez_jmbg": bez_jmbg,
        "sukobi_broja": sukobi_broja,
        "lokalno_duplikati": {k: sorted(v, key=lambda e: e.employee_code)
                              for k, v in lokalni_po_jmbg.items() if k and len(v) > 1},
        "lokalno_bez_jmbg": sorted(lokalni_po_jmbg.get("", []), key=lambda e: e.employee_code),
        "lokalno_nema_u_izvoru": sorted((e for broj, e in lokalni.items() if broj not in brojevi_izvora),
                                        key=lambda e: e.employee_code),
        "pogled_redova": redova_pogleda,
        "pogled_brojeva": brojeva_pogleda,
    }
