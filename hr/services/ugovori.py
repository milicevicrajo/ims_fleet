"""Sinhronizacija ugovora zaposlenih iz kadrovske baze (samo citanje izvora).

Izvor perioda je `dbo.v_hr_RadStaz` (IMS_ERP, cita `RadStaz` na PUTGEO-SERVER.bazaldims, samo
`u_firmi = 'DA'`). Trenutna OJ i radno mesto radnika citaju se iz `radnik`, nazivi iz `ob_jedin`
(po godini — uzima se tekuca, inace poslednja pre nje) i `Sistemat` (po preduzecu).

Pravila:
- menjaju se samo polja iz izvora; broj ugovora, aneks, dokument i napomenu sinhronizacija ne dira;
- OJ i radno mesto upisuju se kad se red prvi put pojavi (ili dok su prazni) i posle se ne menjaju;
- red koji nestane iz izvora se ne brise, nego dobija `u_izvoru = False`;
- ako se posle unosa promeni datum pocetka, stari datum se cuva u `prethodni_datum_od` (za proveru);
- prazan izvor zaustavlja sinhronizaciju (ne oznacava sve redove kao nestale).
"""
import datetime
import decimal

from django.db import connections, transaction
from django.utils import timezone

from hr.models import Employee, UgovoriSinhronizacija, UgovorZaposlenog
from hr.sync import _resolve_hr_db_alias

IZVOR = "[putgeo-server].[BazaLDIMS].[dbo]"
PERIODI_SQL = ("SELECT Kategorija, rasif, rb, datum1, datum2, opis, staz_gg, staz_mm, staz_dd "
               "FROM dbo.v_hr_RadStaz")
RADNICI_SQL = f"SELECT rasif, sif_pred, ranaz, aktivan, oj, sif_sis FROM {IZVOR}.[radnik]"
OJ_SQL = f"SELECT sif_pred, god, oj, naz_oj FROM {IZVOR}.[ob_jedin]"
SISTEMATIZACIJA_SQL = f"SELECT sif_pred, sif_sis, naz_sis FROM {IZVOR}.[Sistemat]"

KATEGORIJE = {"radni odnos": UgovorZaposlenog.Kategorija.RADNI_ODNOS,
              "van radnog odnosa": UgovorZaposlenog.Kategorija.VAN_RADNOG_ODNOSA}
# Kategorija u pogledu dolazi iz preduzeca (sif_pred 1 = radni odnos).
PREDUZECE_KATEGORIJE = {UgovorZaposlenog.Kategorija.RADNI_ODNOS: 1, UgovorZaposlenog.Kategorija.VAN_RADNOG_ODNOSA: 2}

POLJA_IZVORA = ["employee", "ime_prezime", "kategorija", "datum_od", "datum_do", "na_neodredjeno", "opis",
                "staz_godina", "staz_meseci", "staz_dana", "u_izvoru", "radnik_aktivan", "prethodni_datum_od"]
POLJA_OJ = ["oj", "naziv_oj", "sifra_sistematizacije", "naziv_radnog_mesta", "podaci_poreklo", "podaci_zabelezeni"]


class PrazanIzvor(Exception):
    """Izvor nije vratio nijedan period — verovatno greska izvora, ne stvarno stanje."""


def _tekst(vrednost):
    if vrednost is None:
        return ""
    # Numeric kolone stizu kao Decimal('1100') ili Decimal('1100.00') — sifra je ceo broj.
    if isinstance(vrednost, (float, decimal.Decimal)) and vrednost == int(vrednost):
        vrednost = int(vrednost)
    return str(vrednost).strip()


def _ceo(vrednost):
    if vrednost in (None, ""):
        return None
    try:
        return int(vrednost)
    except (TypeError, ValueError):
        return None


def _datum(vrednost):
    if isinstance(vrednost, datetime.datetime):
        return vrednost.date()
    return vrednost


def procitaj_izvor(using=None):
    """(periodi, radnici, oj, sistematizacija) kao liste torki, kako ih vraca izvor."""
    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        rezultat = []
        for sql in (PERIODI_SQL, RADNICI_SQL, OJ_SQL, SISTEMATIZACIJA_SQL):
            cursor.execute(sql)
            rezultat.append(cursor.fetchall())
    return tuple(rezultat)


def _nazivi_oj(redovi, godina):
    """(sif_pred, oj) -> naziv za tekucu godinu, inace poslednju pre nje, inace bilo koju."""
    izbor = {}
    for sif_pred, god, oj, naziv in redovi:
        kljuc = (_ceo(sif_pred), _tekst(oj))
        g = _ceo(god) or 0
        rang = (0 if g <= godina else 1, -g if g <= godina else g)  # prvo <= tekuca (najnovija), pa ostale
        if kljuc not in izbor or rang < izbor[kljuc][0]:
            izbor[kljuc] = (rang, _tekst(naziv))
    return {k: v[1] for k, v in izbor.items()}


def trenutno_stanje(radnici, oj_redovi, sistematizacija, danas=None):
    """sifra radnika -> dict trenutne OJ i radnog mesta (sa nazivima), imena i aktivnosti."""
    danas = danas or timezone.localdate()
    nazivi_oj = _nazivi_oj(oj_redovi, danas.year)
    nazivi_rm = {(_ceo(p), _tekst(s)): _tekst(n) for p, s, n in sistematizacija}
    stanje = {}
    for rasif, sif_pred, ranaz, aktivan, oj, sif_sis in radnici:
        sifra, preduzece = _ceo(rasif), _ceo(sif_pred)
        if sifra is None:
            continue
        oj, sif_sis = _tekst(oj), _tekst(sif_sis)
        stanje[(sifra, preduzece)] = {
            "ime_prezime": " ".join(_tekst(ranaz).split()),
            "aktivan": _tekst(aktivan).upper() == "D",
            "oj": oj, "naziv_oj": nazivi_oj.get((preduzece, oj), ""),
            "sifra_sistematizacije": sif_sis, "naziv_radnog_mesta": nazivi_rm.get((preduzece, sif_sis), ""),
        }
        stanje.setdefault((sifra, None), stanje[(sifra, preduzece)])
    return stanje


def sinhronizuj(*, using=None, izvor=None, danas=None, korisnik=None):
    """Osvezava ugovore zaposlenih iz kadrovske baze. Vraca brojeve za poruku (i belezi zapis)."""
    danas = danas or timezone.localdate()
    periodi, radnici, oj_redovi, sistematizacija = izvor or procitaj_izvor(using)
    if not periodi:
        raise PrazanIzvor("Kadrovska baza nije vratila nijedan period rada (dbo.v_hr_RadStaz).")
    stanje = trenutno_stanje(radnici, oj_redovi, sistematizacija, danas)
    sada = timezone.now()
    zaposleni = dict(Employee.objects.values_list("employee_code", "pk"))
    postojeci = {(u.employee_code, u.redni_broj): u for u in UgovorZaposlenog.objects.all()}

    novi, izmenjeni, vidjeni = [], [], set()
    for kategorija, rasif, rb, datum1, datum2, opis, staz_gg, staz_mm, staz_dd in periodi:
        sifra, redni = _ceo(rasif), _ceo(rb)
        datum_od = _datum(datum1)
        if sifra is None or redni is None or datum_od is None:
            continue
        kljuc = (sifra, redni)
        vidjeni.add(kljuc)
        kat = KATEGORIJE.get(_tekst(kategorija).lower(), UgovorZaposlenog.Kategorija.RADNI_ODNOS)
        radnik = stanje.get((sifra, PREDUZECE_KATEGORIJE[kat])) or stanje.get((sifra, None)) or {}
        datum_do, neodredjeno = UgovorZaposlenog.datum_do_iz_izvora(_datum(datum2))
        vrednosti = {
            "employee_id": zaposleni.get(sifra), "ime_prezime": radnik.get("ime_prezime", ""), "kategorija": kat,
            "datum_od": datum_od, "datum_do": datum_do, "na_neodredjeno": neodredjeno, "opis": _tekst(opis),
            "staz_godina": _ceo(staz_gg), "staz_meseci": _ceo(staz_mm), "staz_dana": _ceo(staz_dd),
            "u_izvoru": True, "radnik_aktivan": radnik.get("aktivan", False),
        }
        red = postojeci.get(kljuc)
        if red is None:
            red = UgovorZaposlenog(employee_code=sifra, redni_broj=redni, sinhronizovano=sada, **vrednosti)
            _zabelezi_oj(red, radnik, danas)
            novi.append(red)
            continue
        promena = False
        if red.datum_od != datum_od and red.unet and red.prethodni_datum_od is None:
            red.prethodni_datum_od = red.datum_od
            promena = True
        for polje, vrednost in vrednosti.items():
            if getattr(red, polje) != vrednost:
                setattr(red, polje, vrednost)
                promena = True
        if not red.podaci_poreklo and _zabelezi_oj(red, radnik, danas):
            promena = True
        if promena:
            red.sinhronizovano = sada
            izmenjeni.append(red)

    nestali = [red for kljuc, red in postojeci.items() if kljuc not in vidjeni and red.u_izvoru]
    for red in nestali:
        red.u_izvoru = False
        red.sinhronizovano = sada

    with transaction.atomic(using=None):
        UgovorZaposlenog.objects.bulk_create(novi, batch_size=500)
        UgovorZaposlenog.objects.bulk_update(izmenjeni, POLJA_IZVORA + POLJA_OJ + ["sinhronizovano"], batch_size=500)
        UgovorZaposlenog.objects.bulk_update(nestali, ["u_izvoru", "sinhronizovano"], batch_size=500)

        rezultat = {"ukupno": len(vidjeni), "novih": len(novi), "azurirano": len(izmenjeni),
                    "nema_u_izvoru": len(nestali), "bez_zaposlenog": sum(1 for k in vidjeni if k[0] not in zaposleni)}
        UgovoriSinhronizacija.objects.create(created_by=korisnik, counts=rezultat)
    return rezultat


def _zabelezi_oj(red, radnik, danas):
    """Upisuje trenutnu OJ i radno mesto radnika (samo ako ih kadrovska baza ima)."""
    if not (radnik.get("oj") or radnik.get("sifra_sistematizacije")):
        return False
    red.oj = radnik["oj"]
    red.naziv_oj = radnik["naziv_oj"]
    red.sifra_sistematizacije = radnik["sifra_sistematizacije"]
    red.naziv_radnog_mesta = radnik["naziv_radnog_mesta"]
    red.podaci_poreklo = UgovorZaposlenog.Poreklo.SINHRONIZACIJA
    red.podaci_zabelezeni = danas
    return True


def poruka(rezultat):
    return (f"Ugovori zaposlenih: ukupno {rezultat['ukupno']}, novih {rezultat['novih']}, "
            f"azurirano {rezultat['azurirano']}, nema u izvoru {rezultat['nema_u_izvoru']}, "
            f"bez kartice zaposlenog {rezultat['bez_zaposlenog']}")


def trenutno_za_radnika(sifra, *, kategorija=None, using=None):
    """Trenutna OJ i radno mesto jednog radnika iz kadrovske baze (za dugme „Preuzmi trenutno”)."""
    with connections[_resolve_hr_db_alias(using)].cursor() as cursor:
        cursor.execute(RADNICI_SQL + " WHERE rasif = %s", [sifra])
        radnici = cursor.fetchall()
        cursor.execute(OJ_SQL + " WHERE oj IN (SELECT oj FROM " + IZVOR + ".[radnik] WHERE rasif = %s)", [sifra])
        oj_redovi = cursor.fetchall()
        cursor.execute(SISTEMATIZACIJA_SQL + " WHERE sif_sis IN (SELECT sif_sis FROM " + IZVOR + ".[radnik] WHERE rasif = %s)", [sifra])
        sistematizacija = cursor.fetchall()
    stanje = trenutno_stanje(radnici, oj_redovi, sistematizacija)
    return stanje.get((int(sifra), PREDUZECE_KATEGORIJE.get(kategorija))) or stanje.get((int(sifra), None)) or {}
