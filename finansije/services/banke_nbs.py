"""Banke iz registra NBS i njihove grupe (od 29.10.2026.).

Spisak banaka i stranica „Detalji” svake banke čitaju se sa webappcenter.nbs.rs (samo čitanje).
Podaci su na sajtu ćirilicom, i kad je izabrana latinica (latinica menja samo natpise), pa se
ovde preslovljavaju. Preuzimanje se pokreće klikom na ekranu Banke i jednom mesečno (Celery).

Sve banke se preuzmu pre bilo kakvog upisa: ako jedna stranica ne uspe, ništa se ne menja.
Banka koja nestane sa spiska ostaje kao istorijska. Šifarnik partnera starog ERP-a se ne menja —
razlike prema NBS-u se samo prikazuju, a ispravljaju se u Stankovom programu.

Isti modul puni i lokalnu kopiju partnera grupe 11 (`BankaPartner`) iz Stankovog programa —
svake noći i istim dugmetom — i beleži šta se u šifarniku promenilo.
"""
import logging
import re
import time
from datetime import date

from django.conf import settings
from django.core.cache import cache
from django.db import connections, transaction
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone

from finansije.access import visible_scope
from finansije.models import BankaNbs, BankaPartner, BankePreuzimanje, LedgerEntry, PovezanoLiceBanke
from .source import SOURCE, clean

logger = logging.getLogger(__name__)

SAJT = "https://webappcenter.nbs.rs"
SPISAK = SAJT + "/WebApp/FinInstBank/LegalEntityFinInstitution/Index"
ZAGLAVLJA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/134.0.0.0 Safari/537.36", "Accept-Language": "sr-Latn-RS,sr;q=0.9"}
RAZMAK = 0.5  # sekundi između stranica; NBS je javni servis
ZAKLJUCAVANJE = "finansije:banke_nbs:preuzimanje"

# Polja koja se porede i prikazuju kao promena: (polje, naziv).
POLJA = [("naziv", "Naziv"), ("grad", "Grad"), ("adresa", "Adresa"), ("postanski_broj", "Poštanski broj"),
         ("maticni_broj", "Matični broj"), ("pib", "PIB"), ("telefon", "Telefon"), ("telefaks", "Telefaks"),
         ("web", "Veb sajt"), ("email", "E-mail"), ("swift", "SWIFT"), ("resenje", "Rešenje o dozvoli za rad"),
         ("datum_resenja", "Datum rešenja"), ("broj_zaposlenih", "Broj zaposlenih"), ("napomena", "Napomena NBS"),
         ("akcionari", "Akcionari preko 5%"), ("upravni_odbor", "Upravni odbor"), ("izvrsni_odbor", "Izvršni odbor"),
         ("prilozi", "Prilozi")]

_CIR = dict(zip("абвгдђежзијклљмњнопрстћуфхцчџшАБВГДЂЕЖЗИЈКЛЉМЊНОПРСТЋУФХЦЧЏШ",
                ["a", "b", "v", "g", "d", "đ", "e", "ž", "z", "i", "j", "k", "l", "lj", "m", "nj", "n", "o", "p", "r",
                 "s", "t", "ć", "u", "f", "h", "c", "č", "dž", "š",
                 "A", "B", "V", "G", "D", "Đ", "E", "Ž", "Z", "I", "J", "K", "L", "Lj", "M", "Nj", "N", "O", "P", "R",
                 "S", "T", "Ć", "U", "F", "H", "C", "Č", "Dž", "Š"]))


class PreuzimanjeUToku(Exception):
    pass


def latinica(tekst):
    """Srpska ćirilica u latinicu; Lj/Nj/Dž su velika slova i u rečima pisanim velikim slovima."""
    tekst = tekst or ""
    rezultat = []
    for i, znak in enumerate(tekst):
        slovo = _CIR.get(znak, znak)
        if len(slovo) == 2 and znak.isupper():
            susedi = (tekst[i + 1:i + 2] or " ") + (tekst[i - 1:i] if i else " ")
            if any(s.isupper() for s in susedi) and not any(s.islower() for s in susedi):
                slovo = slovo.upper()
        rezultat.append(slovo)
    return "".join(rezultat)


def normalizuj_mb(vrednost):
    return re.sub(r"\D", "", str(vrednost or "")).lstrip("0")


def normalizuj_pib(vrednost):
    return re.sub(r"\D", "", str(vrednost or ""))


def sesija():
    from .sef import _sesija  # ista provera sertifikata preko skladišta Windows-a

    s = _sesija()
    s.headers.update(ZAGLAVLJA)
    return s


def _tekst(cvor):
    return latinica(" ".join(cvor.get_text(" ", strip=True).split())) if cvor else ""


def _polje(stranica, oznaka):
    cvor = stranica.find(id=oznaka)
    if cvor is None:
        return ""
    if cvor.name == "input":  # NBS ponegde ima dupli razmak, a to nije promena podatka
        return latinica(" ".join((cvor.get("value") or "").split()))
    return latinica(cvor.get_text("\n", strip=True))


def _povezano(stranica, oznaka):
    """Veb sajt i e-mail nisu polja nego link u okviru ispod natpisa."""
    natpis = stranica.find("label", attrs={"for": oznaka})
    okvir = natpis.find_next_sibling() if natpis else None
    return _tekst(okvir)


def _datum(tekst):
    pogodak = re.match(r"\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", tekst or "")
    return date(int(pogodak[3]), int(pogodak[2]), int(pogodak[1])) if pogodak else None


def _tabele(stranica):
    """{naslov panela: [[ćelije reda], ...]} za akcionare, odbore i priloge."""
    paneli = {}
    for panel in stranica.select(".myColapsiblePanel"):
        naslov = _tekst(panel.select_one(".myColapsiblePanelCaptionContent")).lower()
        redovi = []
        for red in panel.select("tbody tr"):
            celije = red.find_all("td")
            link = red.find("a")
            redovi.append(([_tekst(c) for c in celije], link.get("href") if link else ""))
        paneli[naslov] = redovi
    return paneli


def procitaj_spisak(html):
    from bs4 import BeautifulSoup

    stranica = BeautifulSoup(html, "html.parser")
    ids = []
    for link in stranica.select("a[href*='LegalEntityFinInstitution/Details']"):
        pogodak = re.search(r"id=([0-9a-fA-F-]{36})", link["href"])
        if pogodak and pogodak[1] not in ids:
            ids.append(pogodak[1].lower())
    return ids


def procitaj_detalje(nbs_id, html):
    from bs4 import BeautifulSoup

    stranica = BeautifulSoup(html, "html.parser")
    naziv = _polje(stranica, "Name")
    if not naziv:
        raise ValueError(f"NBS stranica banke {nbs_id} nema naziv; izgled sajta se možda promenio.")
    paneli = _tabele(stranica)

    def panel(pocetak):
        return next((redovi for naslov, redovi in paneli.items() if naslov.startswith(pocetak)), [])

    napomena = re.sub(r"\*\s*Podaci se ažuriraju kvartalno\.?", "", _polje(stranica, "Description")).strip()
    zaposleni = re.sub(r"\D", "", _polje(stranica, "EmployeeNumber"))
    return {
        "nbs_id": nbs_id, "naziv": naziv, "grad": _polje(stranica, "City"), "adresa": _polje(stranica, "Address"),
        "postanski_broj": _polje(stranica, "PostalCode"), "maticni_broj": _polje(stranica, "NationalCode"),
        "pib": _polje(stranica, "TaxCode"), "telefon": _polje(stranica, "Phone"), "telefaks": _polje(stranica, "Fax"),
        "web": _povezano(stranica, "Url"), "email": _povezano(stranica, "Email"), "swift": _polje(stranica, "SwiftCode"),
        "resenje": _polje(stranica, "WorkLicence"), "datum_resenja": _datum(_polje(stranica, "WorkLicenceDate")),
        "broj_zaposlenih": int(zaposleni) if zaposleni else None, "napomena": napomena,
        "akcionari": [{"naziv": c[0], "procenat": c[1] if len(c) > 1 else ""} for c, _ in panel("najveći akcionari") if c],
        "upravni_odbor": [{"ime": c[0], "funkcija": c[1] if len(c) > 1 else ""} for c, _ in panel("članovi upravnog") if c],
        "izvrsni_odbor": [{"ime": c[0], "funkcija": c[1] if len(c) > 1 else ""} for c, _ in panel("članovi izvršnog") if c],
        "prilozi": [{"naziv": c[0], "url": SAJT + href if href.startswith("/") else href} for c, href in panel("prilozi") if c],
    }


def preuzmi_sa_sajta(http=None, pauza=RAZMAK):
    """Sve banke sa spiska NBS; izuzetak ako spisak ili bilo koja stranica ne uspe."""
    http = http or sesija()
    odgovor = http.get(SPISAK, timeout=60)
    odgovor.raise_for_status()
    ids = procitaj_spisak(odgovor.text)
    if not ids:
        raise ValueError("Na spisku banaka NBS nije pronađena nijedna banka; izgled sajta se možda promenio.")
    banke = []
    for nbs_id in ids:
        if pauza:
            time.sleep(pauza)
        odgovor = http.get(f"{SAJT}/WebApp/FinInstBank/LegalEntityFinInstitution/Details?id={nbs_id}", timeout=60)
        odgovor.raise_for_status()
        banke.append(procitaj_detalje(nbs_id, odgovor.text))
    return banke


def _opis(vrednost):
    if isinstance(vrednost, list):
        return "; ".join(" – ".join(str(v) for v in stavka.values() if v and not str(v).startswith("http"))
                         for stavka in vrednost)
    if isinstance(vrednost, date):
        return vrednost.strftime("%d.%m.%Y.")
    return "" if vrednost is None else str(vrednost)


def upisi(banke, sada=None):
    """Upisuje preuzeto stanje; vraća (novih, promenjenih, nestalih, promene)."""
    sada = sada or timezone.now()
    promene, novih, promenjenih = [], 0, 0
    postojece = {b.nbs_id: b for b in BankaNbs.objects.all()}
    for podaci in banke:
        banka = postojece.get(podaci["nbs_id"])
        if banka is None:
            BankaNbs.objects.create(preuzeto=sada, promenjeno=sada, **podaci)
            novih += 1
            promene.append({"banka": podaci["naziv"], "polje": "Banka", "staro": "", "novo": "Nova banka na spisku NBS"})
            continue
        izmene = []
        for polje, naziv in POLJA:
            if getattr(banka, polje) != podaci[polje]:
                izmene.append({"banka": podaci["naziv"], "polje": naziv, "staro": _opis(getattr(banka, polje)), "novo": _opis(podaci[polje])})
                setattr(banka, polje, podaci[polje])
        if not banka.aktivna:
            izmene.append({"banka": podaci["naziv"], "polje": "Banka", "staro": "Nije bila na spisku NBS", "novo": "Ponovo na spisku NBS"})
            banka.aktivna, banka.nestala = True, None
        banka.preuzeto = sada
        if izmene:
            banka.promenjeno = sada
            promenjenih += 1
            promene.extend(izmene)
        banka.save()
    nestale = BankaNbs.objects.filter(aktivna=True).exclude(nbs_id__in=[b["nbs_id"] for b in banke])
    for banka in nestale:
        promene.append({"banka": banka.naziv, "polje": "Banka", "staro": "Na spisku NBS", "novo": "Nije više na spisku NBS — istorijska"})
    nestalih = nestale.update(aktivna=False, nestala=sada, promenjeno=sada)
    return novih, promenjenih, nestalih, promene


def _pokreni(izvor, preuzmi, upis, pokretanje, korisnik):
    """Zajedničko za NBS i šifarnik: jedno preuzimanje istog izvora u isto vreme, zapis o ishodu."""
    kljuc = f"{ZAKLJUCAVANJE}:{izvor}"
    if not cache.add(kljuc, "1", 15 * 60):
        raise PreuzimanjeUToku(f"Preuzimanje banaka ({dict(BankePreuzimanje.IZVORI)[izvor]}) je već u toku.")
    run = BankePreuzimanje.objects.create(izvor=izvor, pokretanje=pokretanje, korisnik=korisnik)
    try:
        podaci = preuzmi()
        with transaction.atomic():
            run.novih, run.promenjenih, run.nestalih, run.promene = upis(podaci)
        run.banaka, run.status = len(podaci), "success"
    except Exception as exc:
        logger.exception("Preuzimanje banaka (%s) nije uspelo", izvor)
        run.status, run.greska = "failed", str(exc)[:2000]
    finally:
        run.kraj = timezone.now()
        run.save()
        cache.delete(kljuc)
    return run


def osvezi(pokretanje="manual", korisnik=None, http=None, pauza=RAZMAK):
    """Banke sa sajta NBS — za dugme i mesečni zakazani posao."""
    return _pokreni("nbs", lambda: preuzmi_sa_sajta(http, pauza), upisi, pokretanje, korisnik)


def upisi_sifarnik(redovi, company=None, sada=None):
    """Lokalna kopija partnera grupe 11; menjaju se samo preuzeta polja, naše oznake ostaju."""
    from .banks import PARTNER_FIELDS, PARTNER_LABELS

    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    sada = sada or timezone.now()
    nazivi = dict(zip(PARTNER_FIELDS, PARTNER_LABELS))
    postojece = {z.sifra: z for z in BankaPartner.objects.filter(company=company)}
    promene, novih, promenjenih, vidjene = [], 0, 0, set()
    for red in redovi:
        sifra = int(red["sif_par"])
        vidjene.add(sifra)
        polja = dict(naziv=red["naz_par"], pib=red["pib"], maticni_broj=red["mb"], podaci=red, preuzeto=sada)
        zapis = postojece.get(sifra)
        if zapis is None:
            BankaPartner.objects.create(company=company, sifra=sifra, promenjeno=sada, **polja)
            novih += 1
            promene.append({"banka": f"{sifra} {red['naz_par']}", "polje": "Šifra", "staro": "", "novo": "Nova šifra u šifarniku"})
            continue
        izmene = [{"banka": f"{sifra} {red['naz_par']}", "polje": nazivi.get(k, k), "staro": zapis.podaci.get(k, ""), "novo": v}
                  for k, v in red.items() if zapis.podaci.get(k, "") != v]
        if not zapis.u_izvoru:
            izmene.append({"banka": f"{sifra} {red['naz_par']}", "polje": "Šifra", "staro": "Obrisana u šifarniku", "novo": "Ponovo u šifarniku"})
            polja.update(u_izvoru=True, nestala=None)
        if izmene:
            polja["promenjeno"] = sada
            promenjenih += 1
            promene.extend(izmene)
        BankaPartner.objects.filter(pk=zapis.pk).update(**polja)
    nestale = BankaPartner.objects.filter(company=company, u_izvoru=True).exclude(sifra__in=vidjene)
    for zapis in nestale:
        promene.append({"banka": f"{zapis.sifra} {zapis.naziv}", "polje": "Šifra", "staro": "U šifarniku", "novo": "Obrisana u šifarniku — istorijska"})
    nestalih = nestale.update(u_izvoru=False, nestala=sada, promenjeno=sada)
    return novih, promenjenih, nestalih, promene


def sinhronizuj_sifarnik(pokretanje="manual", korisnik=None, company=None):
    """Partneri grupe 11 iz Stankovog programa u lokalnu kopiju — noću i dugmetom."""
    from .banks import source_banks

    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)

    def preuzmi():
        redovi = source_banks(company)
        if not redovi:  # prazan odgovor ne sme da „obriše” sve banke
            raise ValueError("Šifarnik partnera nije vratio nijednu banku (grupa 11).")
        return redovi

    return _pokreni("sifarnik", preuzmi, lambda redovi: upisi_sifarnik(redovi, company), pokretanje, korisnik)


def poruka(run):
    naziv = run.get_izvor_display()
    if run.status != "success":
        return f"{naziv}: preuzimanje nije uspelo — {run.greska}"
    nestale = "nije više na spisku" if run.izvor == "nbs" else "obrisanih"
    return (f"{naziv}: {run.banaka} banaka · novih {run.novih}, promenjenih {run.promenjenih}, "
            f"{nestale} {run.nestalih}.")


# --- razvrstavanje partnera grupe 11 --------------------------------------------------------------

def razvrstaj(banks):
    """Dopunjuje banke iz šifarnika partnera NBS podacima (`nbs`), grupom (`grupa`) i oznakom
    `van_nbs` — partner nije banka sa spiska NBS (stara banka, ugašen račun, Uprava za trezor).
    Više šifara partnera iste banke (npr. račun za bolovanja) vezuje se za istu NBS banku.
    """
    nbs = list(BankaNbs.objects.all())
    po_pib = {normalizuj_pib(b.pib): b for b in nbs if b.pib}
    po_mb = {normalizuj_mb(b.maticni_broj): b for b in nbs if b.maticni_broj}
    lica = {normalizuj_pib(l.pib): l for l in PovezanoLiceBanke.objects.select_related("grupa").filter(vrsta="Banka")}
    for bank in banks:
        pib, mb = normalizuj_pib(bank.get("pib")), normalizuj_mb(bank.get("mb"))
        banka = po_pib.get(pib) if pib else None
        banka = banka or (po_mb.get(mb) if mb else None)
        lice = lica.get(normalizuj_pib(banka.pib)) if banka else lica.get(pib)
        bank["nbs"] = banka
        bank["grupa"] = lice.grupa if lice else None
        bank["van_nbs"] = banka is None or not banka.aktivna
    return banks


def razlike(bank):
    """Polja šifarnika partnera (stari ERP) koja se razlikuju od NBS-a, za proveru."""
    banka = bank.get("nbs")
    if banka is None:
        return []

    def kljuc(tekst):  # stari ERP piše bez dijakritika („drustvo”, „Djordja”), NBS sa njima
        tekst = latinica(str(tekst or "")).lower().translate(str.maketrans({"č": "c", "ć": "c", "ž": "z", "š": "s", "đ": "dj"}))
        return re.sub(r"[^a-z0-9]", "", tekst)

    def isto(a, b):
        return kljuc(a) == kljuc(b)

    parovi = [("Naziv", bank.get("naz_par"), banka.naziv), ("Adresa", bank.get("ulica_par"), banka.adresa.split(",")[0]),
              ("Mesto", bank.get("mesto_par"), banka.grad), ("Poštanski broj", bank.get("p_b_par"), banka.postanski_broj),
              ("Matični broj", normalizuj_mb(bank.get("mb")), normalizuj_mb(banka.maticni_broj)),
              ("PIB", bank.get("pib"), banka.pib), ("Telefon", bank.get("telefon"), banka.telefon),
              ("Email", bank.get("email"), banka.email), ("Web", bank.get("web"), banka.web)]
    return [{"polje": naziv, "sifarnik": stari or "", "nbs": novi or "", "isto": isto(stari, novi)} for naziv, stari, novi in parovi]


def lica_grupe(user, grupa, start, end):
    """Članovi grupe sa našim partnerima (po PIB-u) i prometom u periodu, u obuhvatu korisnika."""
    lica = list(grupa.lica.all())
    pibovi = [normalizuj_pib(l.pib) for l in lica if l.pib]
    partneri = {}
    if pibovi:
        with connections[getattr(settings, "FINANSIJE_SOURCE_DB", "server_db")].cursor() as cursor:
            cursor.execute(f"SELECT grupa, sif_par, naz_par, pib FROM {SOURCE}.partner WHERE sif_pred=%s AND "
                           f"LTRIM(RTRIM(pib)) IN ({','.join(['%s'] * len(pibovi))})",
                           [getattr(settings, "FINANSIJE_COMPANY", 1), *pibovi])
            for grupa_par, sifra, naziv, pib in cursor.fetchall():
                partneri.setdefault(normalizuj_pib(pib), []).append({"grupa": grupa_par, "sifra": int(sifra), "naziv": clean(naziv)})
    knjizenja = visible_scope(LedgerEntry.objects.filter(active=True, booking_date__gte=start, booking_date__lte=end)
                              .exclude(journal_type__in=("POC", "ZAT")), user)
    rezultat = []
    for lice in lica:
        nasi = partneri.get(normalizuj_pib(lice.pib), [])
        uslov = Q(pk__in=[])
        for p in nasi:
            uslov |= Q(partner_group=p["grupa"], partner_code=p["sifra"])
        promet = knjizenja.filter(uslov).aggregate(stavki=Count("id"), duguje=Sum("debit"), potrazuje=Sum("credit"),
                                                     poslednje=Max("booking_date")) if nasi else {}
        rezultat.append({"lice": lice, "partneri": nasi, "promet": promet})
    return rezultat
