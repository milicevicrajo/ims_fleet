"""SEF (Sistem elektronskih faktura) — preuzimanje ulaznih i izlaznih faktura, samo citanje.

Po „Okvirnoj specifikaciji aplikativnog interfejsa” (API dokumentacija SEF, 31.07.2026.):

- ulazne: `GET purchase-invoice/overview` (period slanja) daje sve podatke u jednom pozivu;
- izlazne: `POST sales-invoice/ids` (po statusu i periodu) daje samo ID-jeve, a broj, kupca i
  iznose citamo iz UBL-a (`GET sales-invoice/xml`) — samo za fakture koje jos nemamo;
- promene statusa: `POST {purchase|sales}-invoice/changes?date=` za protekle dane (SEF ih cuva
  mesec dana), sa istorijom u `SefPromena`.

Aplikacija nista ne salje na SEF: nema slanja, prihvatanja, odbijanja ni storniranja.
API kljuc je `settings.SEF_API_KEY` (iz `.env`). SEF ima nocnu pauzu, pa se nocni posao
pokrece ujutru.
"""
import datetime
import logging
import re
import time
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from finansije.models import LedgerEntry
from finansije.sef_models import SefFaktura, SefPromena, SefSinhronizacija, broj_u_knjizenju, kljuc_broja

logger = logging.getLogger(__name__)

API = "/api/publicApi"
# Statusi izlaznih faktura (SalesInvoiceStatus) koji se traze po ID-jevima; nacrti i obrisane se ne preuzimaju.
IZLAZNI_STATUSI = ("Sent", "Sending", "Seen", "Approved", "Rejected", "Cancelled", "Storno", "Paid", "Mistake",
                   "OverDue", "Archived")
STATUSI = {
    "New": "Nova", "Seen": "Pregledana", "ReNotified": "Ponovo obaveštena", "Approved": "Prihvaćena",
    "Rejected": "Odbijena", "Storno": "Stornirana", "Sent": "Poslata", "Sending": "U slanju", "Draft": "Nacrt",
    "Paid": "Plaćena", "Mistake": "Greška", "OverDue": "Istekao rok", "Archived": "Arhivirana",
    "Deleted": "Obrisana", "Cancelled": "Otkazana", "Unknown": "Nepoznat",
}
VRSTE = {"Invoice": "Faktura", "CreditNote": "Knjižno odobrenje", "DebitNote": "Knjižno zaduženje",
         "Prepayment": "Avansna faktura"}
DANA_UNAZAD = 45        # nocni posao: fakture poslate u poslednjih 45 dana
DANA_PROMENA = 30       # SEF cuva promene statusa mesec dana
PERIOD_DANA = 31        # jedan poziv za pregled pokriva najvise mesec dana
# SEF prima najvise 3 zahteva u sekundi (odgovor 429 „Rate of max 3 requests per second exceeded”).
RAZMAK_POZIVA = 0.4     # sekundi izmedju dva poziva
PONAVLJANJA_429 = 4


class SefNijePodesen(Exception):
    """Nema API kljuca u okruzenju."""


class SefGreska(Exception):
    """SEF je vratio gresku ili nije odgovorio."""


# --------------------------------------------------------------------------- klijent


def _sesija():
    """`requests` sesija koja sertifikat SEF-a proverava preko skladista sertifikata Windows-a.

    Izdavac sertifikata `efaktura.mfin.gov.rs` nije u spisku `certifi`, pa podrazumevana provera
    pada („unable to get local issuer certificate”), iako mu Windows veruje. `truststore` koristi
    skladiste operativnog sistema — provera sertifikata ostaje ukljucena.
    """
    import ssl

    import requests
    from requests.adapters import HTTPAdapter

    sesija = requests.Session()
    try:
        import truststore
    except ImportError:  # bez biblioteke ostaje certifi
        return sesija

    class _SistemskiSertifikati(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs["ssl_context"] = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            return super().init_poolmanager(*args, **kwargs)

    sesija.mount("https://", _SistemskiSertifikati())
    return sesija


class Klijent:
    def __init__(self, url=None, kljuc=None, timeout=None, session=None):
        self.url = (url or settings.SEF_API_URL).rstrip("/")
        self.kljuc = kljuc if kljuc is not None else settings.SEF_API_KEY
        if not self.kljuc:
            raise SefNijePodesen("SEF nije podešen: u .env nedostaje SEF_API_KEY.")
        self.timeout = timeout or settings.SEF_TIMEOUT
        self.session = session if session is not None else _sesija()
        self._poslednji = 0.0
        self.razmak = RAZMAK_POZIVA if session is None else 0.0  # lazna sesija u testovima ne ceka

    def _sacekaj(self, sekundi):
        time.sleep(sekundi)

    def _poziv(self, metoda, putanja, params=None):
        for pokusaj in range(PONAVLJANJA_429 + 1):
            ceka = self._poslednji + self.razmak - time.monotonic()
            if ceka > 0:
                self._sacekaj(ceka)
            try:
                odgovor = self.session.request(metoda, f"{self.url}{API}/{putanja}", params=params,
                                               headers={"ApiKey": self.kljuc, "accept": "*/*"}, timeout=self.timeout)
            except Exception as exc:  # mreza, DNS, istek vremena — bez kljuca u poruci
                raise SefGreska(f"SEF nije odgovorio ({type(exc).__name__}).") from exc
            finally:
                self._poslednji = time.monotonic()
            if odgovor.status_code != 429 or pokusaj == PONAVLJANJA_429:
                break
            self._sacekaj(1.0 + pokusaj)  # previse zahteva — kratka pauza pa ponovo
        if odgovor.status_code == 401:
            raise SefGreska("SEF je odbio API ključ (401). Proverite SEF_API_KEY i SEF_API_URL.")
        if odgovor.status_code >= 400:
            raise SefGreska(f"SEF je vratio grešku {odgovor.status_code} za {putanja}: {odgovor.text[:300]}")
        return odgovor

    def _json(self, metoda, putanja, params=None):
        return self._poziv(metoda, putanja, params).json()

    def verzija(self):
        return self._json("GET", "getEfakturaVersion").get("Version", "")

    def ulazne_pregled(self, od, do):
        return self._json("GET", "purchase-invoice/overview", {"dateFrom": od.isoformat(), "dateTo": do.isoformat()}) or []

    def izlazne_ids(self, status, od, do):
        podaci = self._json("POST", "sales-invoice/ids", {"status": status, "dateFrom": od.isoformat(),
                                                          "dateTo": do.isoformat()}) or {}
        return podaci.get("SalesInvoiceIds") or []

    def promene(self, smer, dan):
        putanja = "purchase-invoice/changes" if smer == SefFaktura.Smer.ULAZNA else "sales-invoice/changes"
        return self._json("POST", putanja, {"date": dan.isoformat()}) or []

    def ubl(self, smer, sef_id):
        putanja = "purchase-invoice/xml" if smer == SefFaktura.Smer.ULAZNA else "sales-invoice/xml"
        return self._poziv("GET", putanja, {"invoiceId": sef_id}).content

    def pdf(self, smer, sef_id):
        """(sadrzaj, poruka): SEF prvi put samo pokrene izradu PDF-a i vrati poruku u JSON-u."""
        putanja = "purchase-invoice/pdf" if smer == SefFaktura.Smer.ULAZNA else "sales-invoice/pdf"
        odgovor = self._poziv("GET", putanja, {"invoiceId": sef_id})
        vrsta = odgovor.headers.get("Content-Type", "")
        if "json" in vrsta or odgovor.content[:1] in (b"{", b"["):
            try:
                return None, odgovor.json().get("message") or "SEF priprema PDF. Pokušajte ponovo za minut."
            except ValueError:
                return None, "SEF priprema PDF. Pokušajte ponovo za minut."
        return odgovor.content, ""


# --------------------------------------------------------------------------- pomocne


def _dt(vrednost):
    """ISO datum-vreme sa SEF-a (do 7 decimala sekunde) → aware datetime."""
    if not vrednost:
        return None
    tekst = re.sub(r"(\.\d{6})\d+", r"\1", str(vrednost).strip()).replace("Z", "+00:00")
    try:
        dt = datetime.datetime.fromisoformat(tekst)
    except ValueError:
        return None
    return dt if timezone.is_aware(dt) else timezone.make_aware(dt, datetime.timezone.utc)


def _dan(vrednost):
    dt = _dt(vrednost)
    if dt is None:
        try:
            return datetime.date.fromisoformat(str(vrednost)[:10]) if vrednost else None
        except ValueError:
            return None
    return timezone.localtime(dt).date()


def _iznos(vrednost):
    if vrednost in (None, ""):
        return None
    try:
        return Decimal(str(vrednost)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def _pib(vrednost):
    tekst = (vrednost or "").strip()
    return tekst[2:] if tekst.upper().startswith("RS") else tekst


def periodi(od, do, dana=PERIOD_DANA):
    """[od, do] podeljen na delove od najvise `dana` dana."""
    pocetak = od
    while pocetak <= do:
        kraj = min(do, pocetak + datetime.timedelta(days=dana - 1))
        yield pocetak, kraj
        pocetak = kraj + datetime.timedelta(days=1)


# --------------------------------------------------------------------------- UBL


def _ime(el):
    return el.tag.rsplit("}", 1)[-1]


def _deca(el, ime):
    return [d for d in el if _ime(d) == ime]


def _putanja(el, *imena):
    """Prvi element po putanji lokalnih imena (bez obzira na namespace)."""
    trenutni = [el]
    for ime in imena:
        trenutni = [d for t in trenutni for d in _deca(t, ime)]
        if not trenutni:
            return None
    return trenutni[0]


def _tekst(el, *imena):
    cvor = _putanja(el, *imena) if imena else el
    return (cvor.text or "").strip() if cvor is not None and cvor.text else ""


def iz_ubl(sadrzaj):
    """Podaci izlazne fakture iz UBL-a (i kada je u omotu `DocumentEnvelope`)."""
    koren = ET.fromstring(sadrzaj)
    dokument = next((el for el in koren.iter() if _ime(el) in ("Invoice", "CreditNote")), None)
    if dokument is None:
        raise SefGreska("UBL ne sadrži fakturu (Invoice ili CreditNote).")
    kupac = _putanja(dokument, "AccountingCustomerParty", "Party")
    tip = _tekst(dokument, "InvoiceTypeCode")
    vrsta = "CreditNote" if _ime(dokument) == "CreditNote" or tip == "381" else (
        "Prepayment" if tip == "386" else "DebitNote" if tip == "383" else "Invoice")
    naziv = ""
    if kupac is not None:
        naziv = _tekst(kupac, "PartyLegalEntity", "RegistrationName") or _tekst(kupac, "PartyName", "Name")
    return {
        "broj": _tekst(dokument, "ID"),
        "vrsta": vrsta,
        "datum_izdavanja": _dan(_tekst(dokument, "IssueDate")),
        "datum_dospeca": _dan(_tekst(dokument, "DueDate")),
        "datum_prometa": _dan(_tekst(dokument, "Delivery", "ActualDeliveryDate")),
        "valuta": _tekst(dokument, "DocumentCurrencyCode"),
        "partner_naziv": naziv,
        "partner_pib": _pib(_tekst(kupac, "PartyTaxScheme", "CompanyID")) if kupac is not None else "",
        "partner_mb": _tekst(kupac, "PartyLegalEntity", "CompanyID") if kupac is not None else "",
        "iznos": _iznos(_tekst(dokument, "LegalMonetaryTotal", "PayableAmount")),
        "osnovica": _iznos(_tekst(dokument, "LegalMonetaryTotal", "TaxExclusiveAmount")),
        "pdv": _iznos(_tekst(dokument, "TaxTotal", "TaxAmount")),
    }


# --------------------------------------------------------------------------- sinhronizacija


def _ulazna_iz_pregleda(red):
    return {
        "glob_uniq_id": red.get("GlobUniqId") or "",
        "broj": (red.get("DocumentNumber") or "").strip(),
        "vrsta": red.get("DocumentType") or "",
        "status": red.get("Status") or "",
        "cir_id": red.get("CirInvoiceId") or "",
        "partner_naziv": (red.get("SupplierName") or "").strip(),
        "partner_pib": _pib(red.get("SupplierVatRegistrationNumber")),
        "partner_mb": (red.get("SupplierRegistrationNumber") or "").strip(),
        "iznos": _iznos(red.get("Amount")),
        "osnovica": _iznos(red.get("SumWithoutVat")),
        "pdv": _iznos(red.get("VatAmount")),
        "valuta": red.get("Currency") or "",
        "datum_prometa": _dan(red.get("DeliveryDate") or red.get("PrepaymentDate") or red.get("DateOfReduction")),
        "datum_dospeca": _dan(red.get("DueDate")),
        "datum_slanja": _dt(red.get("SentDate")),
    }


def _upisi(smer, sef_id, vrednosti, sada, brojaci):
    postojeca = SefFaktura.objects.filter(smer=smer, sef_id=sef_id).first()
    if postojeca is None:
        SefFaktura.objects.create(smer=smer, sef_id=sef_id, sinhronizovano=sada, **vrednosti)
        brojaci["novih"] += 1
        return
    promena = False
    for polje, vrednost in vrednosti.items():
        if getattr(postojeca, polje) != vrednost:
            setattr(postojeca, polje, vrednost)
            promena = True
    if promena:
        postojeca.sinhronizovano = sada
        postojeca.save()
        brojaci["azurirano"] += 1


def _ulazne(klijent, od, do, sada, brojaci):
    for pocetak, kraj in periodi(od, do):
        for red in klijent.ulazne_pregled(pocetak, kraj):
            if red.get("InvoiceId") is None:
                continue
            brojaci["ulaznih"] += 1
            _upisi(SefFaktura.Smer.ULAZNA, int(red["InvoiceId"]), _ulazna_iz_pregleda(red), sada, brojaci)


def _izlazne(klijent, od, do, sada, brojaci):
    postojece = dict(SefFaktura.objects.filter(smer=SefFaktura.Smer.IZLAZNA).values_list("sef_id", "status"))
    # Faktura „u slanju” ponekad jos nema UBL; bez broja se UBL trazi ponovo.
    bez_broja = set(SefFaktura.objects.filter(smer=SefFaktura.Smer.IZLAZNA, broj="").values_list("sef_id", flat=True))
    for status in IZLAZNI_STATUSI:
        for pocetak, kraj in periodi(od, do):
            for sef_id in klijent.izlazne_ids(status, pocetak, kraj):
                sef_id = int(sef_id)
                brojaci["izlaznih"] += 1
                if sef_id in postojece and sef_id not in bez_broja:
                    if postojece[sef_id] != status:
                        SefFaktura.objects.filter(smer=SefFaktura.Smer.IZLAZNA, sef_id=sef_id).update(
                            status=status, sinhronizovano=sada)
                        postojece[sef_id] = status
                        brojaci["azurirano"] += 1
                    continue
                try:
                    vrednosti = iz_ubl(klijent.ubl(SefFaktura.Smer.IZLAZNA, sef_id))
                except (SefGreska, ET.ParseError) as exc:
                    logger.warning("SEF izlazna %s: UBL nije procitan (%s)", sef_id, exc)
                    brojaci["bez_ubl"] += 1
                    vrednosti = {}
                _upisi(SefFaktura.Smer.IZLAZNA, sef_id, {**vrednosti, "status": status}, sada, brojaci)
                postojece[sef_id] = status
                if vrednosti.get("broj"):
                    bez_broja.discard(sef_id)


def _promene(klijent, od, do, brojaci):
    for smer in (SefFaktura.Smer.ULAZNA, SefFaktura.Smer.IZLAZNA):
        kljuc_id = "PurchaseInvoiceId" if smer == SefFaktura.Smer.ULAZNA else "SalesInvoiceId"
        dan = od
        while dan <= do:
            for red in klijent.promene(smer, dan):
                if red.get("EventId") is None or red.get(kljuc_id) is None:
                    continue
                sef_id, status, datum = int(red[kljuc_id]), red.get("NewInvoiceStatus") or "", _dt(red.get("Date"))
                _, nova = SefPromena.objects.get_or_create(
                    smer=smer, event_id=int(red["EventId"]),
                    defaults={"sef_id": sef_id, "datum": datum, "status": status, "komentar": red.get("Comment") or ""})
                if not nova:
                    continue
                brojaci["promena"] += 1
                faktura = SefFaktura.objects.filter(smer=smer, sef_id=sef_id).first()
                if faktura is None:
                    brojaci["promena_bez_fakture"] += 1
                elif status and (faktura.izmenjeno_na_sefu is None or (datum and datum >= faktura.izmenjeno_na_sefu)):
                    # novija promena od poslednje upisane menja status (promene ne stizu uvek po redu)
                    faktura.status, faktura.izmenjeno_na_sefu = status, datum
                    faktura.save(update_fields=["status", "izmenjeno_na_sefu"])
            dan += datetime.timedelta(days=1)


def sinhronizuj(od=None, do=None, *, klijent=None, korisnik=None, danas=None):
    """Preuzima fakture poslate u [od, do] i promene statusa za protekle dane. Vraca `SefSinhronizacija`."""
    danas = danas or timezone.localdate()
    do = do or danas
    od = od or (do - datetime.timedelta(days=DANA_UNAZAD))
    if od > do:
        raise ValueError("Datum od je posle datuma do.")
    klijent = klijent or Klijent()
    run = SefSinhronizacija.objects.create(od=od, do=do, korisnik=korisnik)
    brojaci = {"ulaznih": 0, "izlaznih": 0, "novih": 0, "azurirano": 0, "bez_ubl": 0, "promena": 0,
               "promena_bez_fakture": 0}
    sada = timezone.now()
    # Bez jedne velike transakcije oko mreznih poziva: upis po fakturi je ponovljiv, pa prekinuta
    # sinhronizacija zadrzava ono sto je preuzela, a ponovljena nastavlja bez duplikata.
    try:
        _ulazne(klijent, od, do, sada, brojaci)
        _izlazne(klijent, od, do, sada, brojaci)
        # Promene samo za protekle dane (SEF ne daje tekuci dan), najvise mesec unazad.
        juce = danas - datetime.timedelta(days=1)
        _promene(klijent, max(od, danas - datetime.timedelta(days=DANA_PROMENA)), min(do, juce), brojaci)
    except Exception as exc:
        run.status, run.error, run.counts, run.finished_at = "error", str(exc)[:2000], brojaci, timezone.now()
        run.save(update_fields=["status", "error", "counts", "finished_at"])
        raise
    run.status, run.counts, run.finished_at = "success", brojaci, timezone.now()
    run.save(update_fields=["status", "counts", "finished_at"])
    return run


def preuzmi_pdf(faktura, klijent=None):
    """Cuva PDF fakture sa SEF-a u aplikaciji (jednom). Vraca (True, "") ili (False, poruka) dok ga SEF priprema."""
    if faktura.pdf:
        return True, ""
    sadrzaj, poruka_sefa = (klijent or Klijent()).pdf(faktura.smer, faktura.sef_id)
    if sadrzaj is None:
        return False, poruka_sefa
    if not sadrzaj.lstrip().startswith(b"%PDF"):
        raise SefGreska("SEF nije vratio PDF dokument.")
    faktura.pdf.save(f"SEF_{faktura.smer}_{faktura.sef_id}.pdf", ContentFile(sadrzaj), save=False)
    faktura.pdf_preuzet = timezone.now()
    faktura.save(update_fields=["pdf", "pdf_preuzet"])
    return True, ""


PDF_KRUGOVA = 4          # SEF prvi poziv samo pokrene izradu PDF-a; ostali krugovi ga preuzimaju
PDF_CEKANJE = 15         # sekundi izmedju krugova


def preuzmi_pdfove(fakture, *, klijent=None, krugova=PDF_KRUGOVA, cekanje=PDF_CEKANJE, spavaj=time.sleep):
    """PDF-ovi za fakture koje ga jos nemaju. Prvi krug pokrece izradu na SEF-u, sledeci krugovi
    preuzimaju gotove. Ogranicenje od 3 zahteva u sekundi postuje klijent. Vraca brojeve."""
    klijent = klijent or Klijent()
    cekaju = [f for f in fakture if not f.pdf]
    brojaci = {"bez_pdf": len(cekaju), "preuzeto": 0, "u_pripremi": 0, "gresaka": 0}
    for krug in range(krugova):
        ostali = []
        for faktura in cekaju:
            try:
                spreman, _ = preuzmi_pdf(faktura, klijent)
            except SefGreska as exc:
                logger.warning("SEF PDF %s %s: %s", faktura.smer, faktura.sef_id, exc)
                brojaci["gresaka"] += 1
                continue
            if spreman:
                brojaci["preuzeto"] += 1
            else:
                ostali.append(faktura)
        cekaju = ostali
        if not cekaju:
            break
        if krug < krugova - 1:
            spavaj(cekanje)
    brojaci["u_pripremi"] = len(cekaju)
    return brojaci


def _bezbedno_ime(tekst, duzina=60):
    ime = "".join(z if z.isalnum() or z in "-_" else "_" for z in (tekst or "").strip())
    return re.sub(r"_+", "_", ime).strip("_")[:duzina] or "bez_naziva"


def izvoz_zip(fakture, izlaz):
    """ZIP u otvoren binarni fajl `izlaz`: PDF-ovi po `Ulazne|Izlazne/GGGG-MM/` i `spisak.csv` svih faktura.

    `fakture` imaju `datum_dok` (datum izdavanja, za ulazne promet ili dan slanja). Fakture bez PDF-a
    ostaju samo u spisku, sa oznakom. Vraca (broj_faktura, broj_pdf).
    """
    import csv
    import io
    import zipfile

    spisak = io.StringIO()
    upis = csv.writer(spisak, delimiter=";")
    upis.writerow(["Smer", "Broj", "Datum", "Vrsta", "Partner", "PIB", "Osnovica", "PDV", "Iznos", "Valuta",
                   "Status", "SEF ID", "PDF"])
    imena, broj, sa_pdf = set(), 0, 0
    with zipfile.ZipFile(izlaz, "w", compression=zipfile.ZIP_DEFLATED) as arhiva:
        for f in fakture:
            broj += 1
            datum = f.datum_dok
            fajl = ""
            if f.pdf:
                fascikla = f"{'Ulazne' if f.smer == SefFaktura.Smer.ULAZNA else 'Izlazne'}/{datum:%Y-%m}" if datum else "Bez_datuma"
                osnova = f"{fascikla}/{datum:%Y-%m-%d}_" if datum else f"{fascikla}/"
                ime = f"{osnova}{_bezbedno_ime(f.broj or str(f.sef_id))}_{_bezbedno_ime(f.partner_naziv, 40)}"
                if ime in imena:
                    ime = f"{ime}_{f.sef_id}"
                imena.add(ime)
                try:
                    with f.pdf.open("rb") as pdf:
                        arhiva.writestr(zipfile.ZipInfo(f"{ime}.pdf", date_time=timezone.localtime(
                            f.pdf_preuzet or timezone.now()).timetuple()[:6]), pdf.read(), zipfile.ZIP_STORED)
                    fajl, sa_pdf = f"{ime}.pdf", sa_pdf + 1
                except FileNotFoundError:
                    fajl = "PDF nedostaje na disku"
            upis.writerow([f.get_smer_display(), f.broj, f"{datum:%d.%m.%Y}" if datum else "", VRSTE.get(f.vrsta, f.vrsta),
                           f.partner_naziv, f.partner_pib, f.osnovica or "", f.pdv or "", f.iznos or "", f.valuta,
                           STATUSI.get(f.status, f.status), f.sef_id, fajl or "nije preuzet"])
        arhiva.writestr("spisak.csv", "\ufeff" + spisak.getvalue())
    return broj, sa_pdf


def poruka_pdf(brojaci):
    return (f"SEF PDF: bez PDF-a {brojaci['bez_pdf']}, preuzeto {brojaci['preuzeto']}, "
            f"SEF još priprema {brojaci['u_pripremi']}, grešaka {brojaci['gresaka']}")


def poruka(run):
    c = run.counts
    return (f"SEF {run.od:%d.%m.%Y.}–{run.do:%d.%m.%Y.}: ulaznih {c.get('ulaznih', 0)}, izlaznih {c.get('izlaznih', 0)}, "
            f"novih {c.get('novih', 0)}, ažurirano {c.get('azurirano', 0)}, promena statusa {c.get('promena', 0)}"
            + (f", bez UBL-a {c['bez_ubl']}" if c.get("bez_ubl") else ""))


# --------------------------------------------------------------------------- meka veza sa knjizenjima


def sa_datumom(qs):
    """`datum_dok`: datum izdavanja (izlazne), inace datum prometa, inace dan slanja na SEF (ulazne nemaju datum izdavanja)."""
    from django.db.models import DateField
    from django.db.models.functions import Cast, Coalesce

    return qs.annotate(datum_dok=Coalesce("datum_izdavanja", "datum_prometa", Cast("datum_slanja", DateField())))


def _oblici(broj):
    """Broj kako moze da stoji u knjizenju: ceo i oblik iz `broj_u_knjizenju` (skracen na 20 znakova,
    a za izlaznu fakturu bez cetiri cifre ispred sifre posla)."""
    kljuc = kljuc_broja(broj)
    return {kljuc, broj_u_knjizenju(kljuc)} if kljuc else set()


def q_proknjizena(company=None):
    """`Exists` uslov: postoji knjizenje sa istim brojem (ceo broj ili oblik u knjizenju)."""
    from django.db.models import Exists, OuterRef, Q

    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    knjizenja = LedgerEntry.objects.filter(company=company, active=True)
    return (Exists(knjizenja.filter(document_reference=OuterRef("broj_kljuc")))
            | Exists(knjizenja.filter(document_reference=OuterRef("broj_knjizenja")))) & ~Q(broj_kljuc="")


def knjizenja(faktura, company=None):
    """Knjizenja sa istim brojem dokumenta (meka veza, bez stranog kljuca).

    Poredjenje je `IN` nad `document_reference` (koristi indeks); na SQL Serveru je kolacija
    neosetljiva na velicinu slova i prateće razmake, pa „mf3814/25 ” odgovara „MF3814/25”.
    """
    oblici = _oblici(faktura.broj)
    if not oblici:
        return LedgerEntry.objects.none()
    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    return (LedgerEntry.objects.filter(company=company, active=True, document_reference__in=oblici)
            .order_by("booking_date", "journal_type", "journal_number", "line_number"))


def proknjizeni_brojevi(fakture, company=None):
    """Skup `broj_kljuc` faktura sa strane koje imaju bar jedno knjizenje (jedan upit za celu stranu)."""
    oblici = {}
    for f in fakture:
        for oblik in _oblici(f.broj):
            oblici.setdefault(oblik, set()).add(f.broj_kljuc)
    if not oblici:
        return set()
    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    nadjeni = (LedgerEntry.objects.filter(company=company, active=True, document_reference__in=list(oblici))
               .values_list("document_reference", flat=True).distinct())
    return {kljuc for ref in nadjeni for kljuc in oblici.get(kljuc_broja(ref), ())}
