"""Kupci sa računima u Alta banci (od 02.11.2026.): poseban slučaj naplate.

1. Iz izvoda Stankovog programa (samo čitanje) uzimaju se kupci (grupa 1) koji su nam uplatili od 2024:
   uplata je preko Alta banke kada račun uplatioca počinje sa 190.
2. U NBS registru tekućih računa rezidenata (webappcenter.nbs.rs, javna pretraga po matičnom broju ili PIB-u)
   traže se računi: za kupce koji su plaćali preko Alta banke **svi računi u svim bankama** (gde još može da se
   naplati), a za ostale kupce samo računi u Alta banci (šifra 190).
3. Čuvaju se kupci sa uplatama preko Alta banke i kupci kojima je NBS našao račun u Alta banci, sa snimkom
   računa na dan preuzimanja — NBS će račune Alta banke ukloniti, pa snimak ostaje dokaz.

Upiti ka NBS idu jedan po jedan sa pauzom (`RAZMAK`); prekinuto preuzimanje nastavlja se od kupaca bez snimka.
"""
import json
import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.db import connections, transaction
from django.utils import timezone

from finansije.services.source import SOURCE
from potrazivanja.models import KupacAltaBanka, RacunKupcaNbs

logger = logging.getLogger(__name__)

ALTA = "190"
OD_GODINE = 2024
NBS = "https://webappcenter.nbs.rs/PnWebApp"
ZAGLAVLJA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/134.0.0.0 Safari/537.36", "Accept-Language": "sr-Latn-RS,sr;q=0.9"}
RAZMAK = 0.8  # sekundi između upita; NBS je javni servis
STRANA = 50
KOLONE_NBS = ["naziv", "mb", "pib", "adresa", "mesto", "opstina", "delatnost", "banka", "_1", "racun", "_2", "status",
              "blokada", "datum_otvaranja"]
TIPOVI = {1: "dinarski", 2: "devizni"}


# --- izvod ---------------------------------------------------------------------------------------

def kupci_iz_izvoda(company=1):
    """[{sif_par, naziv, mb, pib, broj_uplata, iznos_uplata, prva_uplata, poslednja_uplata, racuni_uplata}] —
    svi kupci sa uplatom od 2024; polja uplata se odnose samo na uplate sa računa Alta banke."""
    with connections["server_db"].cursor() as cursor:
        cursor.execute(f"""
            SELECT i.Sif_par, MAX(p.naz_par), MAX(p.mb), MAX(p.pib),
                   SUM(CASE WHEN LEFT(i.Ziro_rac, 3) = %s THEN 1 ELSE 0 END),
                   SUM(CASE WHEN LEFT(i.Ziro_rac, 3) = %s THEN i.iznos_pot ELSE 0 END),
                   MIN(CASE WHEN LEFT(i.Ziro_rac, 3) = %s THEN i.Datum END),
                   MAX(CASE WHEN LEFT(i.Ziro_rac, 3) = %s THEN i.Datum END)
            FROM {SOURCE}.izvod i
            LEFT JOIN {SOURCE}.partner p ON p.sif_pred = i.Sif_pred AND p.grupa = i.grupa AND p.sif_par = i.Sif_par
            WHERE i.Sif_pred = %s AND i.grupa = 1 AND i.god >= %s AND i.iznos_pot > 0 AND i.Sif_par > 0
            GROUP BY i.Sif_par""", [ALTA, ALTA, ALTA, ALTA, company, OD_GODINE])
        redovi = cursor.fetchall()
        cursor.execute(f"""
            SELECT i.Sif_par, i.Ziro_rac FROM {SOURCE}.izvod i
            WHERE i.Sif_pred = %s AND i.grupa = 1 AND i.god >= %s AND i.iznos_pot > 0 AND i.Sif_par > 0
              AND LEFT(i.Ziro_rac, 3) = %s
            GROUP BY i.Sif_par, i.Ziro_rac""", [company, OD_GODINE, ALTA])
        racuni = {}
        for sif_par, racun in cursor.fetchall():
            racuni.setdefault(int(sif_par), []).append(str(racun or "").strip())
    return [{"sif_par": int(r[0]), "naziv": (r[1] or "").strip(), "mb": (r[2] or "").strip(), "pib": (r[3] or "").strip(),
             "broj_uplata": int(r[4] or 0), "iznos_uplata": r[5] or 0, "prva_uplata": _dan(r[6]), "poslednja_uplata": _dan(r[7]),
             "racuni_uplata": ", ".join(sorted(racuni.get(int(r[0]), [])))} for r in redovi]


def _dan(vrednost):
    return vrednost.date() if isinstance(vrednost, datetime) else vrednost


# --- NBS -----------------------------------------------------------------------------------------

def nbs_sesija():
    """Sesija sa latiničnim prikazom (NBS inače vraća ćirilicu)."""
    sesija = requests.Session()
    sesija.headers.update(ZAGLAVLJA)
    odgovor = sesija.get(NBS + "/CompanyAccount/CompanyAccountResident/Index", timeout=60)
    odgovor.raise_for_status()
    token = BeautifulSoup(odgovor.text, "html.parser").find("input", attrs={"name": "__RequestVerificationToken"})
    if token is not None:
        sesija.post(NBS + "/CultureInfo/SetLanguage?returnUrl=~%2FCompanyAccount%2FCompanyAccountResident%2FIndex",
                    data={"language": "sr-Latn", "__RequestVerificationToken": token["value"]}, timeout=60)
    return sesija


def citaj_stranu(html):
    """Redovi tabele rezultata NBS pretrage."""
    soup = BeautifulSoup(html, "html.parser")
    redovi = []
    for tr in soup.select("table tr"):
        celije = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
        if len(celije) == len(KOLONE_NBS):
            redovi.append({k: v for k, v in zip(KOLONE_NBS, celije) if not k.startswith("_")})
    return redovi


def racuni_iz_nbs(sesija, mb, pib, banka=""):
    """Svi računi (dinarski i devizni, sve strane) za matični broj, a bez njega za PIB; `banka` sužava na šifru banke."""
    racuni = []
    for tip, naziv_tipa in TIPOVI.items():
        strana = 1
        while True:
            parametri = {"isSearchExecuted": "true", "BankCode": banka, "AccountNumber": "", "ControlNumber": "",
                         "CompanyNationalCode": mb, "CompanyTaxCode": "" if mb else pib, "CompanyName": "", "City": "",
                         "TypeID": str(tip), "OrderBy": "", "Pagging.CurrentPage": str(strana),
                         "Pagging.PageSize": str(STRANA)}
            odgovor = None
            for pokusaj in range(4):
                try:
                    odgovor = sesija.get(NBS + "/CompanyAccount/CompanyAccountResident", params=parametri, timeout=60)
                    if odgovor.status_code == 200:
                        break
                except requests.RequestException:
                    odgovor = None
                time.sleep(5 * (pokusaj + 1))
            if odgovor is None or odgovor.status_code != 200:
                raise RuntimeError("NBS ne odgovara.")
            if "Неочекивана грешка" in odgovor.text or "Neočekivana greška" in odgovor.text:
                raise RuntimeError("NBS je vratio grešku za pretragu.")
            redovi = citaj_stranu(odgovor.text)
            for red in redovi:
                red["tip"] = naziv_tipa
            racuni += redovi
            time.sleep(RAZMAK)
            if len(redovi) < STRANA:
                break
            strana += 1
    return racuni


def _datum_nbs(tekst):
    try:
        return datetime.strptime((tekst or "").strip().rstrip("."), "%d.%m.%Y").date()
    except ValueError:
        return None


# --- čuvanje -------------------------------------------------------------------------------------

@transaction.atomic
def sacuvaj(kupac, racuni, obuhvat, greska="", preuzeto=None, company=1):
    """Upisuje kupca (ako je plaćao preko Alta banke ili ima račun u njoj) i zamenjuje snimak njegovih računa.

    Vraća sačuvanog kupca ili None kada kupac nema veze sa Alta bankom.
    """
    preuzeto = preuzeto or timezone.now()
    ima_alta = any(r["racun"].startswith(ALTA) for r in racuni)
    postojeci = KupacAltaBanka.objects.filter(company=company, partner_code=kupac["sif_par"]).first()
    if not (kupac["broj_uplata"] or ima_alta or postojeci):
        return None
    zapis, _ = KupacAltaBanka.objects.update_or_create(company=company, partner_code=kupac["sif_par"], defaults={
        "naziv": kupac["naziv"][:255], "maticni_broj": kupac["mb"], "pib": kupac["pib"],
        "broj_uplata": kupac["broj_uplata"], "iznos_uplata": kupac["iznos_uplata"],
        "prva_uplata": kupac["prva_uplata"], "poslednja_uplata": kupac["poslednja_uplata"],
        "racuni_uplata": kupac["racuni_uplata"], "nbs_obuhvat": obuhvat, "nbs_greska": greska[:300],
        **({} if greska else {"nbs_preuzeto": preuzeto})})
    if greska:
        return zapis  # prethodni snimak računa ostaje — NBS ga možda više nema
    zapis.racuni.all().delete()
    jedinstveni = {r["racun"]: r for r in racuni}
    RacunKupcaNbs.objects.bulk_create([RacunKupcaNbs(
        kupac=zapis, racun=r["racun"], banka_sifra=r["racun"][:3], banka=r.get("banka", "")[:255],
        tip=r.get("tip", ""), status=r.get("status", "")[:50], blokada=r.get("blokada", "")[:50],
        datum_otvaranja=_datum_nbs(r.get("datum_otvaranja")), naziv_nbs=r.get("naziv", "")[:255],
        mesto=r.get("mesto", "")[:100], preuzeto=preuzeto) for r in jedinstveni.values()])
    return zapis


def preuzmi(*, fajl=None, nastavi=True, javi=print, company=1):
    """Kupci iz izvoda + računi iz NBS (ili iz ranije snimljenog JSONL fajla, red po kupcu: sif_par, obuhvat, racuni)."""
    kupci = kupci_iz_izvoda(company)
    if fajl:
        snimak = {}
        with open(fajl, encoding="utf-8") as f:
            for linija in f:
                if linija.strip():
                    zapis = json.loads(linija)
                    snimak[zapis["sif_par"]] = zapis
        preuzeto = timezone.now()
        sacuvano = 0
        for kupac in kupci:
            if kupac["sif_par"] in snimak:
                zapis = snimak[kupac["sif_par"]]
                sacuvano += bool(sacuvaj(kupac, zapis["racuni"], zapis["obuhvat"], zapis.get("greska", ""), preuzeto, company))
            elif kupac["broj_uplata"]:
                sacuvaj(kupac, [], "", "Nije pretražen u NBS.", preuzeto, company)
                sacuvano += 1
        javi(f"Iz fajla: {len(snimak)} pretraga, sačuvano kupaca: {sacuvano}.")
        return sacuvano
    gotovi = set(KupacAltaBanka.objects.filter(company=company, nbs_preuzeto__isnull=False)
                 .values_list("partner_code", flat=True)) if nastavi else set()
    # prvo platioci preko Alta banke (najveće uplate), pa ostali kupci
    kupci.sort(key=lambda k: (k["broj_uplata"] == 0, -float(k["iznos_uplata"])))
    sesija, sacuvano = nbs_sesija(), 0
    for broj, kupac in enumerate(kupci, 1):
        if kupac["sif_par"] in gotovi:
            continue
        mb = kupac["mb"] if kupac["mb"].isdigit() and len(kupac["mb"]) >= 4 else ""
        pib = kupac["pib"] if kupac["pib"].isdigit() and len(kupac["pib"]) == 9 else ""
        obuhvat = "sve_banke" if kupac["broj_uplata"] else "alta"
        racuni, greska = [], ""
        if not mb and not pib:
            greska = "Partner nema ispravan matični broj ni PIB."
        else:
            try:
                racuni = racuni_iz_nbs(sesija, mb, pib, "" if kupac["broj_uplata"] else ALTA)
            except Exception as e:  # kupac ostaje bez snimka, nastavlja se sa sledećim
                logger.warning("NBS računi za partnera %s: %s", kupac["sif_par"], e)
                greska = str(e)
                time.sleep(10)
                sesija = nbs_sesija()
        sacuvano += bool(sacuvaj(kupac, racuni, obuhvat, greska, company=company))
        if broj % 50 == 0:
            javi(f"{broj}/{len(kupci)} kupaca, sačuvano {sacuvano}.")
    javi(f"Završeno: {len(kupci)} kupaca, sačuvano {sacuvano}.")
    return sacuvano
