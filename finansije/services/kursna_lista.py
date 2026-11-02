"""Zvanični srednji kurs dinara sa sajta NBS (od 02.11.2026.).

Za svaki kalendarski dan čita se stranica „Na željeni dan” (latinica) i upisuje broj liste, datum
formiranja i srednji kurs svih valuta. Za vikend i praznik NBS prikazuje poslednju formiranu listu,
pa se dan vezuje za nju (`KursniDan`); prosek po radnim danima računa se iz dana kada je lista formirana.

Preuzimanje dopunjuje dane koji nedostaju od `PRVI_DAN` (deset godina unazad) — zakazano svakog jutra,
najviše `NAJVISE_DANA` stranica po pokretanju, dok se istorija ne popuni — i ponovo proverava poslednjih
`PROVERA_DANA` dana vezanih za raniju listu (preuzeti pre nego što je NBS formirala listu tog dana).
"""
import re
import time
from datetime import date, timedelta
from decimal import Decimal

from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from finansije.models import KursnaLista, KursniDan, KursValute

ADRESA = "https://webappcenter.nbs.rs/ExchangeRateWebApp/ExchangeRate/IndexByDate"
SREDNJI_KURS = "3"  # ExchangeRateListTypeID
PRVI_DAN = date(2016, 1, 1)
NAJVISE_DANA = 500  # po zakazanom pokretanju (~7 min); cela istorija preko komande `kursna_lista_nbs`
PROVERA_DANA = 7
RAZMAK = 0.5  # sekundi između stranica; NBS je javni servis


class NemaListe(Exception):
    pass


def sesija():
    from .banke_nbs import sesija as nbs_sesija

    s = nbs_sesija()
    s.cookies.set(".AspNetCore.Culture", "c=sr-Latn-RS|uic=sr-Latn-RS", domain="webappcenter.nbs.rs")  # latinica
    return s


def _datum(tekst):
    d, m, g = (int(x) for x in re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", tekst).groups())
    return date(g, m, d)


def procitaj(html):
    """Stranica „Na željeni dan” → (broj liste, datum formiranja, [kursevi])."""
    stranica = BeautifulSoup(html, "html.parser")
    naslovi = [" ".join(h.get_text(" ", strip=True).split()) for h in stranica.find_all(["h5", "h6"])]
    broj = next((re.search(r"LISTA BR\.\s*(\d+)", n) for n in naslovi if "LISTA BR" in n), None)
    formirana = next((n for n in naslovi if n.startswith("FORMIRANA NA DAN")), None)
    tabela = stranica.find("table")
    if not (broj and formirana and tabela):
        poruka = " ".join(x.get_text(" ", strip=True) for x in stranica.select(".alert") if x.get_text(strip=True))
        raise NemaListe(poruka or "Na stranici NBS nema kursne liste.")
    kursevi = []
    for red in tabela.select("tbody tr"):
        celije = [" ".join(td.get_text(" ", strip=True).split()) for td in red.find_all("td")]
        if len(celije) != 5:
            continue
        oznaka, sifra, zemlja, vazi_za, kurs = celije
        kursevi.append({"oznaka": oznaka, "sifra": sifra, "zemlja": zemlja, "vazi_za": int(vazi_za),
                        "srednji_kurs": Decimal(kurs.replace(".", "").replace(",", "."))})
    if not kursevi:
        raise NemaListe("Kursna lista NBS je bez valuta.")
    return int(broj.group(1)), _datum(formirana), kursevi


def preuzmi_dan(s, dan):
    odgovor = s.get(ADRESA, params={"isSearchExecuted": "true", "Date": f"{dan:%d.%m.%Y}.",
                                    "ExchangeRateListTypeID": SREDNJI_KURS}, timeout=60)
    odgovor.raise_for_status()
    return procitaj(odgovor.text)


@transaction.atomic
def sacuvaj(dan, broj, formirana, kursevi):
    """Lista se upisuje jednom (NBS je ne menja); dan se vezuje za listu koju je NBS prikazala."""
    lista, nova = KursnaLista.objects.get_or_create(godina=formirana.year, broj=broj,
                                                    defaults={"datum_formiranja": formirana})
    if nova:
        KursValute.objects.bulk_create([KursValute(lista=lista, **k) for k in kursevi])
    KursniDan.objects.update_or_create(datum=dan, defaults={"lista": lista})
    return lista, nova


def dani_za_preuzimanje(od=PRVI_DAN, do=None):
    """Dani bez liste (najnoviji prvo) i poslednjih dana vezanih za listu formiranu ranije."""
    do = do or timezone.localdate()
    imaju = set(KursniDan.objects.filter(datum__range=(od, do)).values_list("datum", flat=True))
    sumnjivi = set(KursniDan.objects.filter(datum__gt=do - timedelta(days=PROVERA_DANA), datum__lte=do,
                                            lista__datum_formiranja__lt=F("datum")).values_list("datum", flat=True))
    dani = [od + timedelta(days=i) for i in range((do - od).days + 1)]
    return sorted((d for d in dani if d not in imaju or d in sumnjivi), reverse=True)


def preuzmi(od=PRVI_DAN, do=None, najvise=None, javi=None, s=None):
    """Dopunjuje kursne liste; vraća rečnik sa brojevima za poruku. Greška jednog dana ne zaustavlja ostale."""
    dani = dani_za_preuzimanje(od, do)
    preostalo = max(len(dani) - najvise, 0) if najvise else 0
    dani = dani[:najvise] if najvise else dani
    s = s or sesija()
    rezultat = {"dana": 0, "novih_lista": 0, "gresaka": 0, "preostalo": preostalo, "poslednja_greska": ""}
    for i, dan in enumerate(dani):
        if i:
            time.sleep(RAZMAK)
        try:
            lista, nova = sacuvaj(dan, *preuzmi_dan(s, dan))
        except Exception as exc:  # NBS ne radi, budući dan, neočekivana stranica — sledeći put ponovo
            rezultat["gresaka"] += 1
            rezultat["poslednja_greska"] = f"{dan:%d.%m.%Y.}: {type(exc).__name__}: {exc}"[:300]
            continue
        rezultat["dana"] += 1
        rezultat["novih_lista"] += nova
        if javi and (nova or i % 50 == 0):
            javi(f"{dan:%d.%m.%Y.} → lista {lista.broj}/{lista.godina} od {lista.datum_formiranja:%d.%m.%Y.}"
                 + (", nova" if nova else ""))
    return rezultat


def poruka(r):
    tekst = f"Kursna lista NBS: dana {r['dana']}, novih lista {r['novih_lista']}, grešaka {r['gresaka']}"
    if r["preostalo"]:
        tekst += f", preostalo za sledeće pokretanje {r['preostalo']}"
    if r["poslednja_greska"]:
        tekst += f". Poslednja greška: {r['poslednja_greska']}"
    return tekst + "."
