"""Zvanični srednji kurs dinara sa sajta NBS (od 02.11.2026.).

Za svaki kalendarski dan čita se stranica „Na željeni dan” (latinica) i upisuje broj liste, datum
formiranja i srednji kurs svih valuta. Za vikend i praznik NBS prikazuje poslednju formiranu listu,
pa se dan vezuje za nju (`KursniDan`); prosek po radnim danima računa se iz lista formiranih u periodu.

Zakazano preuzimanje svakog jutra čita samo taj dan — jednu stranicu (od 04.11.2026.; više upita zaredom
NBS blokira). Istorija se unosi iz CSV izvoza NBS (`uvezi_csv`, komanda `kursna_lista_csv`); dopuna sa sajta,
dan po dan, ostaje komanda `kursna_lista_nbs`.
"""
import csv
import re
import time
from datetime import date, timedelta
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone

from finansije.models import KursnaLista, KursniDan, KursValute

ADRESA = "https://webappcenter.nbs.rs/ExchangeRateWebApp/ExchangeRate/IndexByDate"
SREDNJI_KURS = "3"  # ExchangeRateListTypeID
PRVI_DAN = date(2016, 1, 1)
AUTOMATSKI_DANA = 1  # samo današnji dan, jedan upit
RAZMAK = 3  # sekundi između stranica; na 0,5 s NBS je 03.11.2026. uključio zaštitu od botova


class NemaListe(Exception):
    pass


class NbsBlokira(Exception):
    """NBS umesto liste vraća stranicu zaštite od botova (F5 „TSPD”): dalje upite treba prekinuti."""


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
    if "/TSPD/" in html or 'window["bobcmn"]' in html:
        raise NbsBlokira("NBS je uključio zaštitu od botova; preuzimanje je prekinuto, pokušajte kasnije.")
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
    """Lista se upisuje jednom (NBS je ne menja); dan se vezuje za listu koju je NBS prikazala.

    Lista uneta iz CSV-a (bez broja, samo EUR) dobija broj i ostale valute kad se taj dan pročita sa sajta.
    """
    lista, nova = KursnaLista.objects.get_or_create(datum_formiranja=formirana,
                                                    defaults={"godina": formirana.year, "broj": broj})
    if lista.broj is None:
        lista.broj = broj
        lista.save(update_fields=["broj"])
    postoje = set(lista.kursevi.values_list("oznaka", flat=True))
    KursValute.objects.bulk_create([KursValute(lista=lista, **k) for k in kursevi if k["oznaka"] not in postoje])
    KursniDan.objects.update_or_create(datum=dan, defaults={"lista": lista})
    return lista, nova


def preuzmi(od=PRVI_DAN, do=None, svi=False, javi=None, s=None):
    """Dani bez liste (ili svi dani perioda, `svi`), najnoviji prvo. Greška jednog dana ne zaustavlja ostale,
    osim zaštite od botova NBS — tada se staje."""
    do = do or timezone.localdate()
    dani = [do - timedelta(days=i) for i in range((do - od).days + 1)]
    if not svi:
        imaju = set(KursniDan.objects.filter(datum__range=(od, do)).values_list("datum", flat=True))
        dani = [d for d in dani if d not in imaju]
    s = s or sesija()
    rezultat = {"dana": 0, "novih_lista": 0, "gresaka": 0, "poslednja_greska": ""}
    for i, dan in enumerate(dani):
        if i:
            time.sleep(RAZMAK)
        try:
            lista, nova = sacuvaj(dan, *preuzmi_dan(s, dan))
        except NbsBlokira as exc:  # svaki sledeći upit samo produžava blokadu
            rezultat["gresaka"] += 1
            rezultat["poslednja_greska"] = f"{dan:%d.%m.%Y.}: {exc}"
            break
        except Exception as exc:  # NBS ne radi, budući dan, neočekivana stranica — sledeći put ponovo
            rezultat["gresaka"] += 1
            rezultat["poslednja_greska"] = f"{dan:%d.%m.%Y.}: {type(exc).__name__}: {exc}"[:300]
            continue
        rezultat["dana"] += 1
        rezultat["novih_lista"] += nova
        if javi and (nova or i % 50 == 0):
            javi(f"{dan:%d.%m.%Y.} → lista {lista.broj_liste} od {lista.datum_formiranja:%d.%m.%Y.}"
                 + (", nova" if nova else ""))
    return rezultat


def preuzmi_poslednje(dana=AUTOMATSKI_DANA, s=None):
    danas = timezone.localdate()
    return preuzmi(danas - timedelta(days=dana - 1), danas, svi=True, s=s)


# --- Istorija iz CSV izvoza NBS -----------------------------------------------------------------------
# Izvoz sa sajta NBS (kursna lista za devize, jedna valuta, period): po kalendarskom danu „Datum formiranja,
# Datum primene, Valuta, Naziv zemlje, Oznaka, Važi za, Kupovni, Prodajni”. Srednjeg kursa i broja liste nema.

KUPOVNI, PRODAJNI = Decimal("0.997"), Decimal("1.003")  # NBS: kupovni i prodajni = srednji ∓ 0,3 %
CETIRI = Decimal("0.0001")


class LosCsv(Exception):
    pass


def srednji_iz_kupovnog_i_prodajnog(kupovni, prodajni):
    """Srednji kurs na 4 decimale za koji su kupovni i prodajni tačno srednji ∓ 0,3 % (zaokruženo).

    Obično je to (kupovni + prodajni) / 2; kad zbir nije paran u četvrtoj decimali (14.03.2022.), bira se onaj od
    dva susedna kursa koji daje oba objavljena kursa. Ako nijedan ili oba — greška, ne pogađa se.
    """
    pola = (kupovni + prodajni) / 2
    kandidati = {pola.quantize(CETIRI, rounding=r) for r in (ROUND_FLOOR, ROUND_CEILING)}
    dobri = [m for m in kandidati if (m * KUPOVNI).quantize(CETIRI, ROUND_HALF_UP) == kupovni
             and (m * PRODAJNI).quantize(CETIRI, ROUND_HALF_UP) == prodajni]
    if len(dobri) != 1:
        raise LosCsv(f"kupovni {kupovni} i prodajni {prodajni} ne daju jedan srednji kurs")
    return dobri[0]


def _csv_datum(tekst):
    d, m, g = (int(x) for x in tekst.strip().rstrip(".").split("."))
    return date(g, m, d)


def procitaj_csv(putanja):
    """[{datum, formirana, oznaka, sifra, zemlja, vazi_za, srednji_kurs}] — jedan red po kalendarskom danu."""
    redovi = []
    with open(putanja, encoding="utf-8-sig", newline="") as f:
        citac = csv.reader(f)
        zaglavlje = [x.strip().lower() for x in next(citac, [])]
        if len(zaglavlje) != 8 or not any(r in zaglavlje[6] for r in ("куповни", "kupovni")):
            raise LosCsv(f"{putanja}: nije CSV izvoz kursne liste NBS (kupovni/prodajni)")
        for i, red in enumerate(citac, start=2):
            if not any(x.strip() for x in red):
                continue
            try:
                formirana, primena, sifra, zemlja, oznaka, vazi_za, kupovni, prodajni = (x.strip() for x in red)
                redovi.append({"datum": _csv_datum(primena), "formirana": _csv_datum(formirana), "oznaka": oznaka,
                               "sifra": sifra, "zemlja": zemlja, "vazi_za": int(vazi_za),
                               "srednji_kurs": srednji_iz_kupovnog_i_prodajnog(Decimal(kupovni), Decimal(prodajni))})
            except (ValueError, ArithmeticError, LosCsv) as exc:
                raise LosCsv(f"{putanja}, red {i}: {exc}") from exc
    return redovi


@transaction.atomic
def uvezi_csv(putanje):
    """Unosi istoriju iz CSV izvoza NBS. Ne menja ništa što već postoji: dan koji već ima listu ostaje na njoj,
    a valuta koja je već na listi zadržava svoj kurs (razlika se samo prijavi). Ponovno pokretanje ne duplira."""
    redovi = {}
    for putanja in putanje:
        for r in procitaj_csv(putanja):
            kljuc = (r["datum"], r["oznaka"])
            if kljuc in redovi and redovi[kljuc] != r:
                raise LosCsv(f"{r['datum']:%d.%m.%Y.} {r['oznaka']}: fajlovi se ne slažu")
            redovi[kljuc] = r
    rezultat = {"redova": len(redovi), "novih_lista": 0, "novih_kurseva": 0, "novih_dana": 0, "razlika": []}
    liste = {}
    for r in sorted(redovi.values(), key=lambda r: (r["formirana"], r["datum"])):
        lista = liste.get(r["formirana"])
        if lista is None:
            lista, nova = KursnaLista.objects.get_or_create(datum_formiranja=r["formirana"],
                                                            defaults={"godina": r["formirana"].year, "broj": None})
            liste[r["formirana"]] = lista
            rezultat["novih_lista"] += nova
        kurs = {k: r[k] for k in ("oznaka", "sifra", "zemlja", "vazi_za", "srednji_kurs")}
        postojeci = KursValute.objects.filter(lista=lista, oznaka=r["oznaka"]).first()
        if postojeci is None:
            KursValute.objects.create(lista=lista, **kurs)
            rezultat["novih_kurseva"] += 1
        elif (postojeci.srednji_kurs, postojeci.vazi_za) != (r["srednji_kurs"], r["vazi_za"]):
            rezultat["razlika"].append(f"{r['formirana']:%d.%m.%Y.} {r['oznaka']}: u bazi {postojeci.srednji_kurs}, "
                                       f"u CSV-u {r['srednji_kurs']}")
        _, nov = KursniDan.objects.get_or_create(datum=r["datum"], defaults={"lista": lista})
        rezultat["novih_dana"] += nov
    return rezultat


def poruka(r):
    tekst = f"Kursna lista NBS: dana {r['dana']}, novih lista {r['novih_lista']}, grešaka {r['gresaka']}"
    if r["poslednja_greska"]:
        tekst += f". Poslednja greška: {r['poslednja_greska']}"
    return tekst + "."


# --- Ekran ---------------------------------------------------------------------------------------

def valute():
    """[(oznaka, naziv)] svih valuta koje su bile na listama, po oznaci."""
    poslednje = {}
    for oznaka, zemlja in KursValute.objects.order_by("lista__datum_formiranja").values_list("oznaka", "zemlja"):
        poslednje[oznaka] = zemlja
    return sorted(poslednje.items())


def proseci(od, do):
    """Po valuti: prosek, najniži i najviši srednji kurs na listama formiranim u periodu (radni dani)."""
    redovi = (KursValute.objects.filter(lista__datum_formiranja__range=(od, do))
              .values("oznaka", "vazi_za")
              .annotate(sifra=Max("sifra"), zemlja=Max("zemlja"), prosek=Avg("srednji_kurs"),
                        najnizi=Min("srednji_kurs"), najvisi=Max("srednji_kurs"), listi=Count("pk"),
                        prva=Min("lista__datum_formiranja"), poslednja=Max("lista__datum_formiranja"))
              .order_by("oznaka", "vazi_za"))
    return [dict(r, prosek=Decimal(r["prosek"]).quantize(Decimal("0.0001"))) for r in redovi]


def po_danima(od, do, oznaka):
    """Kalendarski dani perioda sa listom koja važi i kursom valute; radni dan = lista formirana tog dana."""
    kursevi = dict(KursValute.objects.filter(oznaka=oznaka, lista__dani__datum__range=(od, do))
                   .values_list("lista_id", "pk").distinct())
    stavke = KursValute.objects.in_bulk(list(kursevi.values()))
    redovi = []
    for dan in KursniDan.objects.filter(datum__range=(od, do)).select_related("lista").order_by("datum"):
        kurs = stavke.get(kursevi.get(dan.lista_id))
        redovi.append({"datum": dan.datum, "lista": dan.lista, "radni": dan.datum == dan.lista.datum_formiranja,
                       "vazi_za": kurs.vazi_za if kurs else None, "kurs": kurs.srednji_kurs if kurs else None})
    return redovi


def stanje():
    """Poslednja preuzeta lista i broj dana bez liste od `PRVI_DAN` do danas."""
    danas = timezone.localdate()
    ukupno = (danas - PRVI_DAN).days + 1
    return {"poslednja": KursnaLista.objects.order_by("-datum_formiranja").first(),
            "nedostaje": ukupno - KursniDan.objects.filter(datum__range=(PRVI_DAN, danas)).count()}


def tabela_proseka(redovi):
    from .izvoz import Kolona, Tabela

    kolone = [Kolona("Oznaka"), Kolona("Šifra"), Kolona("Zemlja"), Kolona("Važi za", "broj"),
              Kolona("Prosek srednjeg kursa", "kurs"), Kolona("Najniži", "kurs"), Kolona("Najviši", "kurs"),
              Kolona("Broj lista", "broj"), Kolona("Prva lista", "datum"), Kolona("Poslednja lista", "datum")]
    return Tabela("Prosek srednjeg kursa po valutama — radni dani", kolone, [
        [r["oznaka"], r["sifra"], r["zemlja"], r["vazi_za"], r["prosek"], r["najnizi"], r["najvisi"], r["listi"],
         r["prva"], r["poslednja"]] for r in redovi],
        opis="Prosek je aritmetička sredina srednjeg kursa sa svih kursnih lista formiranih u periodu (radni dani).")


def tabela_dana(redovi, oznaka):
    from .izvoz import Kolona, Tabela

    kolone = [Kolona("Datum", "datum"), Kolona("Radni dan"), Kolona("Broj liste"), Kolona("Lista formirana", "datum"),
              Kolona("Važi za", "broj"), Kolona(f"Srednji kurs {oznaka}", "kurs")]
    return Tabela(f"Srednji kurs {oznaka} po danima", kolone, [
        [r["datum"], "da" if r["radni"] else "ne", f"{r['lista'].broj}/{r['lista'].godina}", r["lista"].datum_formiranja,
         r["vazi_za"], r["kurs"]] for r in redovi],
        opis="Za vikend i praznik važi poslednja formirana lista; prosek se računa samo iz radnih dana.")


def sazetak_dana(redovi):
    """(prosek, najniži, najviši, broj radnih dana, različite jedinice „važi za”) iz radnih dana."""
    radni = [r for r in redovi if r["radni"] and r["kurs"] is not None]
    if not radni:
        return None
    kursevi = [r["kurs"] for r in radni]
    prosek = (sum(kursevi) / len(kursevi)).quantize(Decimal("0.0001"))
    return {"prosek": prosek, "najnizi": min(kursevi), "najvisi": max(kursevi), "dana": len(radni),
            "jedinice": sorted({r["vazi_za"] for r in radni})}
