"""Ucitavanje fiskalnog racuna citacem QR koda (Nabavka, od 28.09.2026.).

Tok: citac (radi kao tastatura) upise link sa QR koda → `ocitaj_link` popravi raspored tastature
i proveri kontrolni zbir (MD5 na kraju QR sadrzaja) → iz QR-a se cita zaglavlje (broj racuna,
iznos, vreme, kupac) → sa stranice za proveru Poreske uprave (`suf.purs.gov.rs/v/?vl=…`) prodavac,
tekst racuna i token → `POST /specifications` sa tim tokenom vraca stavke.

Ako stranica za proveru nije dostupna, racun se ipak upisuje iz QR-a u statusu „ceka proveru”, a
preuzimanje se ponavlja (dugme na detalju, nocni zadatak). Nista se ne upisuje ako kontrolni zbir
QR sadrzaja ne odgovara — pogresno ocitan link ne sme da napravi pogresan racun.
"""
import base64
import binascii
import hashlib
import html
import json
import re
import struct
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

SUF = "https://suf.purs.gov.rs"
IMS_PIB = "100223617"
TIMEOUT = 20

# Citac salje tastere americkog rasporeda; na srpskom latinicnom (QWERTZ) ili cirilicnom rasporedu
# isti tasteri daju druge znakove. Mape vracaju ono sto je stiglo u ono sto je citac poslao.
_US = "yzYZ;:/?-_=+'\"[]{}\\|"
_SR_LAT = "zyZYčČ-_'?+*ćĆšđŠĐžŽ"
_SR_CIR_SLOVA = dict(zip("qwertyuiop[]asdfghjkl;'\\zxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM",
                         "љњертзуиопшђасдфгхјклчћжѕџцвбнмЉЊЕРТЗУИОПАСДФГХЈКЛЅЏЦВБНМ"))
LATINICA = {sr: us for us, sr in zip(_US, _SR_LAT)}
CIRILICA = {**{sr: us for us, sr in _SR_CIR_SLOVA.items()}, ":": ":", "Ч": ":", "-": "/", "_": "?", "'": "-",
            "?": "_", "+": "=", "*": "+"}


class GreskaOcitavanja(ValueError):
    """Link nije ispravan racun (ne vrsi se nikakav upis)."""


@dataclass
class Zaglavlje:
    link: str
    broj_racuna: str
    zatrazio: str
    potpisao: str
    brojac_ukupno: int
    brojac_vrste: int
    iznos: Decimal
    pfr_vreme: datetime
    vrsta_racuna: int
    vrsta_transakcije: int
    id_kupca: str

    @property
    def pib_kupca(self):
        delovi = self.id_kupca.split(":")
        # 10 = PIB, 11 = JMBG, 12 = PIB i JBKJS (javni sektor), ostalo — dokumenti fizickih lica.
        return delovi[1] if len(delovi) > 1 and delovi[0] in ("10", "12") else ""


def _vl_iz_linka(tekst):
    tekst = (tekst or "").strip()
    upit = urllib.parse.urlparse(tekst).query
    vrednosti = urllib.parse.parse_qs(upit, keep_blank_values=True).get("vl")
    if vrednosti:
        return vrednosti[0].replace(" ", "+")  # `+` u upitu se cita kao razmak
    m = re.search(r"vl=([A-Za-z0-9+/=%]+)", tekst)
    return urllib.parse.unquote(m.group(1)) if m else ""


def _dekodiraj(vl):
    """Zaglavlje iz QR sadrzaja; None ako kontrolni zbir ne odgovara."""
    try:
        b = base64.b64decode(vl + "=" * (-len(vl) % 4), validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(b) < 60 or hashlib.md5(b[:-16]).digest() != b[-16:]:
        return None
    i = 1  # verzija
    zatrazio, potpisao = b[i:i + 8].decode("ascii", "replace"), b[i + 8:i + 16].decode("ascii", "replace")
    i += 16
    brojac_ukupno, brojac_vrste = struct.unpack("<II", b[i:i + 8])
    i += 8
    iznos, = struct.unpack("<Q", b[i:i + 8])
    i += 8
    ms, = struct.unpack(">Q", b[i:i + 8])
    i += 8
    vrsta_racuna, vrsta_transakcije = b[i], b[i + 1]
    i += 2
    duzina = b[i]
    id_kupca = b[i + 1:i + 1 + duzina].decode("utf-8", "replace")
    return dict(zatrazio=zatrazio, potpisao=potpisao, brojac_ukupno=brojac_ukupno, brojac_vrste=brojac_vrste,
                iznos=(Decimal(iznos) / Decimal(10000)).quantize(Decimal("0.01")),
                pfr_vreme=datetime.fromtimestamp(ms / 1000, tz=dt_timezone.utc),
                vrsta_racuna=vrsta_racuna, vrsta_transakcije=vrsta_transakcije, id_kupca=id_kupca)


def ocitaj_link(tekst):
    """Link sa citaca → `Zaglavlje`. Popravlja srpski latinicni i cirilicni raspored tastature."""
    sirov = (tekst or "").strip()
    if not sirov:
        raise GreskaOcitavanja("Link je prazan — očitajte QR kod računa.")
    for mapa in (None, LATINICA, CIRILICA):
        kandidat = sirov if mapa is None else "".join(mapa.get(z, z) for z in sirov)
        vl = _vl_iz_linka(kandidat)
        podaci = _dekodiraj(vl) if vl else None
        if podaci:
            link = f"{SUF}/v/?vl={urllib.parse.quote(vl, safe='')}" if mapa is not None else kandidat
            broj = f"{podaci['zatrazio']}-{podaci['potpisao']}-{podaci['brojac_ukupno']}"
            return Zaglavlje(link=link, broj_racuna=broj, **podaci)
    raise GreskaOcitavanja("QR kod nije ispravno očitan (kontrolni zbir ne odgovara). Podesite čitač na US "
                           "raspored tastature ili očitajte račun ponovo.")


# --------------------------------------------------------------------------- stranica za proveru


def _otvori(url, podaci=None):
    zahtev = urllib.request.Request(url, data=podaci, headers={"User-Agent": "IMS-ERP/1.0", "Accept-Language": "sr"})
    with urllib.request.urlopen(zahtev, timeout=getattr(settings, "FISKALNI_TIMEOUT", TIMEOUT)) as odgovor:
        return odgovor.read().decode("utf-8", "replace")


def _polje(stranica, id_):
    m = re.search(r'id="%s"[^>]*>(.*?)<' % re.escape(id_), stranica, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def _iznos(tekst):
    tekst = (tekst or "").strip().replace(".", "").replace(",", ".")
    try:
        return Decimal(tekst)
    except InvalidOperation:
        return None


def procitaj_stranicu(stranica):
    """Podaci sa stranice za proveru: zaglavlje prodavca, tekst racuna i token za stavke."""
    zurnal_m = re.search(r"<pre[^>]*>(.*?)</pre>", stranica, re.S)
    zurnal = html.unescape(re.sub(r"<[^>]+>", "", zurnal_m.group(1))).strip("\n") if zurnal_m else ""
    linije = [l.strip() for l in zurnal.splitlines()]
    token = re.search(r"viewModel\.Token\('([^']+)'\)", stranica)
    return {
        "pib_prodavca": _polje(stranica, "tinLabel"),
        "prodajno_mesto": _polje(stranica, "shopFullNameLabel"),
        "adresa": _polje(stranica, "addressLabel"),
        "grad": _polje(stranica, "cityLabel"),
        "opstina": _polje(stranica, "administrativeUnitLabel"),
        "oznaka_brojaca": _polje(stranica, "invoiceCounterExtensionLabel"),
        "naziv_prodavca": _naziv_prodavca(linije),
        "kasir": _vrednost_reda(linije, ("Касир:", "Kasir:")),
        "esir_broj": _vrednost_reda(linije, ("ЕСИР број:", "ESIR broj:")),
        "nacin_placanja": _nacin_placanja(linije),
        "pdv_ukupno": _iznos(_vrednost_reda(linije, ("Укупан износ пореза:", "Ukupan iznos poreza:"))),
        "zurnal": zurnal,
        "token": token.group(1) if token else "",
    }


def _vrednost_reda(linije, oznake):
    for linija in linije:
        for oznaka in oznake:
            if linija.startswith(oznaka):
                return linija[len(oznaka):].strip()
    return ""


def _naziv_prodavca(linije):
    """Prvi red posle PIB-a u zaglavlju teksta racuna (pravno lice)."""
    neprazne = [l for l in linije if l and not l.startswith("=")]
    for i, linija in enumerate(neprazne[:6]):
        if linija.isdigit() and i + 1 < len(neprazne):
            return neprazne[i + 1]
    return ""


def _nacin_placanja(linije):
    """Redovi izmedju „Ukupan iznos:” i sledece crte: nacini placanja sa iznosima."""
    nacini, unutra = [], False
    for linija in linije:
        if linija.startswith(("Укупан износ:", "Ukupan iznos:")):
            unutra = True
            continue
        if unutra:
            if not linija or linija.startswith("="):
                break
            nacini.append(re.sub(r"\s{2,}", " ", linija))
    return "; ".join(nacini)[:255]


def preuzmi_stavke(broj_racuna, token):
    podaci = urllib.parse.urlencode({"invoiceNumber": broj_racuna, "token": token}).encode()
    odgovor = json.loads(_otvori(f"{SUF}/specifications", podaci))
    if not odgovor.get("success"):
        raise ValueError("Stranica za proveru nije vratila stavke računa.")
    return odgovor.get("items") or []


def _decimal(vrednost):
    return None if vrednost is None else Decimal(str(vrednost))


# --------------------------------------------------------------------------- upis


def _upisi_sa_stranice(racun, stranica, stavke):
    from nabavka.models import FiskalniRacun, FiskalniRacunStavka

    podaci = procitaj_stranicu(stranica)
    podaci.pop("token")
    for polje, vrednost in podaci.items():
        if vrednost in ("", None) and polje != "zurnal":
            continue  # prazno na stranici ne brise ono sto je vec poznato
        duzina = FiskalniRacun._meta.get_field(polje).max_length
        setattr(racun, polje, vrednost[:duzina] if isinstance(vrednost, str) and duzina else vrednost)
    racun.stavke.all().delete()
    FiskalniRacunStavka.objects.bulk_create([
        FiskalniRacunStavka(racun=racun, redni_broj=i, gtin=(s.get("gtin") or "")[:40], naziv=(s.get("name") or "")[:500],
                            kolicina=_decimal(s.get("quantity")) or Decimal(0), jedinicna_cena=_decimal(s.get("unitPrice")) or Decimal(0),
                            ukupno=_decimal(s.get("total")) or Decimal(0), oznaka_pdv=(s.get("label") or "")[:5],
                            stopa_pdv=_decimal(s.get("labelRate")), osnovica=_decimal(s.get("taxBaseAmount")),
                            pdv=_decimal(s.get("vatAmount")))
        for i, s in enumerate(stavke, start=1)])
    if racun.pdv_ukupno is None and stavke:
        racun.pdv_ukupno = sum((_decimal(s.get("vatAmount")) or Decimal(0) for s in stavke), Decimal(0))
    racun.status, racun.greska, racun.preuzeto = FiskalniRacun.Status.POTVRDJEN, "", timezone.now()
    racun.save()


def preuzmi(racun):
    """(Ponovo) preuzima podatke sa stranice za proveru. Vraca True ako je uspelo."""
    try:
        stranica = _otvori(racun.link)
        token = procitaj_stranicu(stranica)["token"]
        stavke = preuzmi_stavke(racun.broj_racuna, token) if token else []
    except Exception as exc:  # mreza, stranica ili format odgovora — racun ostaje „ceka proveru”
        racun.greska = f"{type(exc).__name__}: {exc}"[:500]
        racun.save(update_fields=["greska"])
        return False
    with transaction.atomic():
        _upisi_sa_stranice(racun, stranica, stavke)
    return True


def upisi(tekst, job_code, korisnik, napomena="", dodatne=(), putni_nalog=None):
    """Novi racun iz ocitanog linka. Vraca (racun, upozorenja). Isti racun se ne upisuje dva puta.

    `job_code` je glavna sifra posla, `dodatne` ostale sifre na koje se racun vezuje.
    """
    from nabavka.models import FiskalniRacun, FiskalniRacunSifra

    zaglavlje = ocitaj_link(tekst)
    postojeci = FiskalniRacun.objects.filter(broj_racuna=zaglavlje.broj_racuna).first()
    if postojeci:
        raise GreskaOcitavanja(f"Račun {zaglavlje.broj_racuna} je već učitan ({postojeci.created_at:%d.%m.%Y. %H:%M}).")
    pib_ims = getattr(settings, "IMS_PIB", IMS_PIB)
    racun = FiskalniRacun.objects.create(
        link=zaglavlje.link, broj_racuna=zaglavlje.broj_racuna, zatrazio=zaglavlje.zatrazio, potpisao=zaglavlje.potpisao,
        brojac_ukupno=zaglavlje.brojac_ukupno, brojac_vrste=zaglavlje.brojac_vrste, iznos=zaglavlje.iznos,
        pfr_vreme=zaglavlje.pfr_vreme, vrsta_racuna=zaglavlje.vrsta_racuna, vrsta_transakcije=zaglavlje.vrsta_transakcije,
        id_kupca=zaglavlje.id_kupca, pib_kupca=zaglavlje.pib_kupca, na_ims=zaglavlje.pib_kupca == pib_ims,
        job_code=job_code, napomena=napomena, created_by=korisnik, putni_nalog=putni_nalog)
    racun.uskladi_glavnu_sifru(korisnik)
    for sifra in dodatne:
        if sifra.pk != job_code.pk:
            FiskalniRacunSifra.objects.get_or_create(racun=racun, job_code=sifra, defaults={"created_by": korisnik})
    preuzmi(racun)
    return racun, upozorenja(racun)


def upozorenja(racun):
    """Sta korisnik mora da vidi pri ucitavanju (racun je svakako upisan)."""
    poruke = []
    if not racun.na_ims:
        poruke.append("Račun NIJE izdat na IMS" + (f" (kupac: {racun.id_kupca})." if racun.id_kupca
                                                   else " — nema ID kupca, račun je na fizičko lice."))
    if racun.vrsta_racuna != 0:
        poruke.append(f"Vrsta računa je „{racun.vrsta_racuna_naziv}” — to nije račun prometa.")
    if racun.vrsta_transakcije == 1:
        poruke.append("Ovo je refundacija (umanjenje), ne kupovina.")
    if racun.status != racun.Status.POTVRDJEN:
        poruke.append("Stranica za proveru trenutno nije dostupna: upisano je zaglavlje iz QR koda, stavke će biti "
                      "preuzete kasnije.")
    else:
        zbir = sum((s.ukupno for s in racun.stavke.all()), Decimal(0))
        if zbir != racun.iznos:
            poruke.append(f"Zbir stavki ({zbir}) nije jednak iznosu računa ({racun.iznos}).")
    return poruke


# ---------------------------------------------------------------- putni nalozi i knjiženje (od 02.10.2026.)

def ucitaj_za_putni_nalog(tekst, putni_nalog, korisnik, napomena=""):
    """Račun sa putnog naloga. Vraća (račun, upozorenja, vezan_postojeći).

    Novi račun dobija šifru posla putnog naloga. Račun koji je već učitan (npr. u Nabavci) se samo
    veže za nalog i zadržava svoju šifru posla. Račun vezan za drugi nalog se ne prevezuje, a na
    storniran nalog se računi ne dodaju.
    """
    if putni_nalog.storniran:
        raise GreskaOcitavanja(f"Putni nalog {putni_nalog.order_number} je storniran. Računi se na njega ne dodaju.")
    from nabavka.models import FiskalniRacun

    zaglavlje = ocitaj_link(tekst)
    postojeci = FiskalniRacun.objects.select_related("putni_nalog").filter(broj_racuna=zaglavlje.broj_racuna).first()
    if postojeci is None:
        racun, poruke = upisi(tekst, putni_nalog.job_code, korisnik, napomena, putni_nalog=putni_nalog)
        return racun, poruke, False
    if postojeci.putni_nalog_id == putni_nalog.pk:
        raise GreskaOcitavanja(f"Račun {postojeci.broj_racuna} je već na ovom putnom nalogu.")
    if postojeci.putni_nalog_id:
        raise GreskaOcitavanja(f"Račun {postojeci.broj_racuna} je već vezan za putni nalog "
                               f"{postojeci.putni_nalog.order_number}.")
    postojeci.putni_nalog = putni_nalog
    postojeci.save(update_fields=["putni_nalog"])
    return postojeci, upozorenja(postojeci), True


def odvezi_od_putnog_naloga(racun):
    """Uklanja vezu sa putnim nalogom (pogrešno skeniran račun). Račun ostaje u Nabavci."""
    if racun.proknjizeno:
        raise GreskaOcitavanja(f"Račun {racun.broj_racuna} je proknjižen i ne može se skinuti sa putnog naloga.")
    racun.putni_nalog = None
    racun.save(update_fields=["putni_nalog"])
    return racun


def oznaci_proknjizeno(racun, korisnik, proknjizeno=True, request=None):
    """Oznaka knjigovodstva. Ne upisuje ništa u knjigovodstvo — samo beleži ko je i kada označio.
    Poništavanje oznake se posebno beleži u evidenciji rada."""
    from django.utils import timezone

    from core.activity import log_activity

    if racun.proknjizeno == proknjizeno:
        return racun
    racun.proknjizeno = proknjizeno
    racun.proknjizio, racun.proknjizeno_at = (korisnik, timezone.now()) if proknjizeno else (None, None)
    racun.save(update_fields=["proknjizeno", "proknjizio", "proknjizeno_at"])
    if not proknjizeno:
        log_activity(request=request, user=korisnik, object_instance=racun,
                     description=f"Poništena oznaka „proknjiženo” za fiskalni račun {racun.broj_racuna}.")
    return racun
