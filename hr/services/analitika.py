"""Analitika zaposlenih: pol, starost, stručna sprema, staž u Institutu, OJ i vrsta radnog odnosa (od 05.10.2026.).

Obuhvat su **aktivni** zaposleni koje korisnik vidi (`visible_employees`), na današnji dan.

Kadrovska baza nema stepen stručne spreme kao posebno polje — ima zanimanje (`naz_zan`) i školu
(`skola`). Stepen se zato **izvodi iz naziva zanimanja** (a kad ga nema, iz naziva škole) po pravilima
u `STEPENI`; šta se ne prepozna ide u „Nije razvrstano” i vidi se u Excelu (list „Razvrstavanje”), da
kadrovska služba može da proveri i dopuni pravila. Datum rođenja pre 1920. ili posle danas smatra se
neispravnim (izvor koristi 01.01.1900. kao prazno) i takav zaposleni nema starost.
"""
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .resenja import normalizuj_pol

POLOVI = (("F", "Žene"), ("M", "Muškarci"))
STAROSNI_RASPONI = ((0, 19, "do 19"), (20, 29, "20–29"), (30, 39, "30–39"), (40, 49, "40–49"),
                    (50, 59, "50–59"), (60, 64, "60–64"), (65, 200, "65 i više"))
STAZ_RASPONI = ((0, 0, "manje od 1"), (1, 4, "1–4"), (5, 9, "5–9"), (10, 19, "10–19"), (20, 29, "20–29"),
                (30, 200, "30 i više"))
NIJE_RAZVRSTANO = "Nije razvrstano"

# (oznaka, naziv, ključne reči) — proverava se redom, prva pogođena reč određuje stepen.
STEPENI = (
    ("I–II", "Bez stručne spreme / NK, PK", ("bez zanim", "bez str", "pomocni", "nekvalif", "polukvalif")),
    ("VIII", "Doktor nauka", ("doktor", "dok.", "dr ")),
    ("VII", "Master / diplomirani (VSS)", ("master", "dipl", "magist", "mr ", "fakultet", "univerzitet", "pmf",
                                           "akademij")),
    ("V", "Specijalista (VKV)", ("specijal", "spec.", "-spec")),
    ("VI", "Viša / strukovni (VŠS)", ("strukovn", "struk.", "inzenjer", "inz.", "inz ", "ekonomista", "informaticar",
                                      "dizajner", "menadzer", "visa ", "visoka ")),
    ("IV", "Srednja (SSS)", ("tehnicar", "tehn.", "tehn ", "gimn", "laborant", "administrator", "srednja", "skola",
                             "skolski centar", "obrazovni centar")),
    ("III", "Kvalifikovani (KV)", ("bravar", "mehanicar", "instalater", "vozac", "konobar", "pekar", "trgovac",
                                   "prodavac", "fotograf", "glodac", "strugar", "busac", "masinista", "dekorater",
                                   "proizv", "operater", "alatnicar", "zavarivac", "kv ")),
)
REDOSLED_STEPENA = ["VIII", "VII", "VI", "V", "IV", "III", "I–II", NIJE_RAZVRSTANO]
NAZIV_STEPENA = {oznaka: naziv for oznaka, naziv, _ in STEPENI} | {NIJE_RAZVRSTANO: NIJE_RAZVRSTANO}


def _ascii(tekst):
    """Mala slova bez dijakritika; popravlja i pogrešno kodirana slova iz izvora (è, æ, ð)."""
    tekst = str(tekst or "").lower().replace("ð", "dj").replace("đ", "dj").replace("è", "c").replace("æ", "c")
    tekst = unicodedata.normalize("NFKD", tekst).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", tekst).strip() + " "


def stepen_spreme(zanimanje, skola=""):
    """(oznaka, izvor) — stepen iz zanimanja, a kad ga nema ili se ne prepozna, iz škole."""
    for izvor, tekst in (("zanimanje", zanimanje), ("škola", skola)):
        tekst = _ascii(tekst)
        if not tekst.strip():
            continue
        for oznaka, _, reci in STEPENI:
            if any(rec in tekst for rec in reci):
                return oznaka, izvor
    return NIJE_RAZVRSTANO, ""


def godine(od, na_dan):
    return na_dan.year - od.year - ((na_dan.month, na_dan.day) < (od.month, od.day))


def starost(datum_rodjenja, na_dan):
    if not datum_rodjenja or datum_rodjenja.year < 1920 or datum_rodjenja > na_dan:
        return None
    return godine(datum_rodjenja, na_dan)


def staz(datum_zaposlenja, na_dan):
    if not datum_zaposlenja or datum_zaposlenja.year < 1950 or datum_zaposlenja > na_dan:
        return None
    return godine(datum_zaposlenja, na_dan)


def raspon(vrednost, rasponi):
    if vrednost is None:
        return None
    return next(naziv for od, do, naziv in rasponi if od <= vrednost <= do)


def prosek(vrednosti):
    vrednosti = [v for v in vrednosti if v is not None]
    if not vrednosti:
        return None
    return (Decimal(sum(vrednosti)) / len(vrednosti)).quantize(Decimal("0.1"), ROUND_HALF_UP)


def medijana(vrednosti):
    vrednosti = sorted(v for v in vrednosti if v is not None)
    if not vrednosti:
        return None
    sredina = len(vrednosti) // 2
    return Decimal(vrednosti[sredina]) if len(vrednosti) % 2 else (Decimal(vrednosti[sredina - 1] + vrednosti[sredina]) / 2)


def udeo(deo, ukupno):
    return (Decimal(deo) * 100 / ukupno).quantize(Decimal("0.1"), ROUND_HALF_UP) if ukupno else None


def osobe(employees, na_dan):
    from fleet.models import OrganizationalUnit

    lista = list(employees.select_related("org_node") if hasattr(employees, "select_related") else employees)
    # Šifre u izvoru mogu biti dopunjene razmacima; naziv OJ iz šifarnika, a kad ga nema, iz registra.
    nazivi = {str(k).strip(): " ".join(str(n or "").split()) for k, n in OrganizationalUnit.objects.values_list("code", "name")}
    rezultat = []
    for e in lista:
        oj = str(e.org_unit_code or e.department_code or "").strip()
        if oj not in nazivi and getattr(e, "org_node", None) is not None:
            nazivi[oj] = str(e.org_node).split(" — ", 1)[-1]
        oznaka, izvor = stepen_spreme(e.job_title, e.education)
        rezultat.append({
            "pol": normalizuj_pol(e.gender), "starost": starost(e.date_of_birth, na_dan),
            "staz": staz(e.date_of_joining, na_dan), "stepen": oznaka, "stepen_izvor": izvor,
            "zanimanje": e.job_title or "", "skola": e.education or "",
            "oj": oj, "oj_naziv": f"{oj} — {nazivi[oj]}" if nazivi.get(oj) else (f"OJ {oj}" if oj else "Bez OJ"),
            "odnos": e.status_name or "Nije upisano",
        })
    return rezultat


def _red(naziv, grupa, ukupno):
    zene = [o for o in grupa if o["pol"] == "F"]
    muski = [o for o in grupa if o["pol"] == "M"]
    return {
        "naziv": naziv, "ukupno": len(grupa), "udeo": udeo(len(grupa), ukupno),
        "zene": len(zene), "muski": len(muski),
        "udeo_zena": udeo(len(zene), len(grupa)),
        "prosek": prosek(o["starost"] for o in grupa),
        "prosek_zene": prosek(o["starost"] for o in zene), "prosek_muski": prosek(o["starost"] for o in muski),
    }


def _po(osobe_, kljuc, redosled=None, ukupno=None):
    grupe = defaultdict(list)
    for o in osobe_:
        grupe[kljuc(o)].append(o)
    nazivi = list(redosled) if redosled is not None else sorted(grupe, key=lambda k: (-len(grupe[k]), str(k)))
    ukupno = len(osobe_) if ukupno is None else ukupno
    return [_red(naziv, grupe.get(naziv, []), ukupno) for naziv in nazivi if redosled is None or grupe.get(naziv)]


def analitika(employees, na_dan=None):
    na_dan = na_dan or date.today()
    svi = osobe(employees, na_dan)
    ukupno = len(svi)
    sa_starosti = [o for o in svi if o["starost"] is not None]

    starosni = []
    najveci = 1
    for _, _, naziv in STAROSNI_RASPONI:
        grupa = [o for o in sa_starosti if raspon(o["starost"], STAROSNI_RASPONI) == naziv]
        red = _red(naziv, grupa, len(sa_starosti))
        starosni.append(red)
        najveci = max(najveci, red["zene"], red["muski"])
    for red in starosni:  # širine traka piramide, u odnosu na najveću grupu jednog pola
        red["sirina_zene"] = round(red["zene"] * 100 / najveci, 1)
        red["sirina_muski"] = round(red["muski"] * 100 / najveci, 1)
    najveci_ukupno = max((r["ukupno"] for r in starosni), default=0) or 1
    for red in starosni:
        red["sirina"] = round(red["ukupno"] * 100 / najveci_ukupno, 1)

    stepeni = _po(svi, lambda o: o["stepen"], REDOSLED_STEPENA)
    for red in stepeni:
        red["oznaka"], red["naziv"] = red["naziv"], NAZIV_STEPENA[red["naziv"]]
        red["prikaz"] = red["naziv"] if red["oznaka"] == NIJE_RAZVRSTANO else f'{red["oznaka"]} · {red["naziv"]}'
        red["sirina"] = round(red["ukupno"] * 100 / max(r["ukupno"] for r in stepeni), 1)

    # Starost × stručna sprema: broj zaposlenih u svakom rasponu za svaki stepen.
    ukrstanje = []
    for red in stepeni:
        grupa = [o for o in sa_starosti if o["stepen"] == red["oznaka"]]
        brojevi = Counter(raspon(o["starost"], STAROSNI_RASPONI) for o in grupa)
        ukrstanje.append({"oznaka": red["oznaka"], "naziv": red["naziv"], "prikaz": red["prikaz"],
                          "rasponi": [brojevi.get(n, 0) for _, _, n in STAROSNI_RASPONI], "ukupno": len(grupa),
                          "prosek": red["prosek"]})
    najvise = max((b for red in ukrstanje for b in red["rasponi"]), default=0) or 1
    for red in ukrstanje:  # jačina boje ćelije: udeo u najbrojnijoj ćeliji tabele
        red["celije"] = [{"broj": b, "jacina": round(0.08 + 0.72 * b / najvise, 2) if b else 0} for b in red["rasponi"]]

    sa_stazom = [o for o in svi if o["staz"] is not None]
    staz_rasponi = _po(sa_stazom, lambda o: raspon(o["staz"], STAZ_RASPONI), [n for _, _, n in STAZ_RASPONI])
    for red in staz_rasponi:
        grupa = [o for o in sa_stazom if raspon(o["staz"], STAZ_RASPONI) == red["naziv"]]
        red["prosek_staz"] = prosek(o["staz"] for o in grupa)

    zene = [o for o in svi if o["pol"] == "F"]
    muski = [o for o in svi if o["pol"] == "M"]
    starosti = [o["starost"] for o in sa_starosti]
    visoka = sum(1 for o in svi if o["stepen"] in ("VIII", "VII", "VI"))
    nerazvrstani = Counter((o["zanimanje"] or "—", o["skola"] or "—") for o in svi if o["stepen"] == NIJE_RAZVRSTANO)
    return {
        "na_dan": na_dan, "ukupno": ukupno, "sa_starosti": len(sa_starosti),
        "sazetak": {
            "zene": len(zene), "muski": len(muski), "udeo_zena": udeo(len(zene), ukupno),
            "udeo_muski": udeo(len(muski), ukupno), "bez_pola": ukupno - len(zene) - len(muski),
            "prosek": prosek(starosti), "medijana": medijana(starosti),
            "prosek_zene": prosek(o["starost"] for o in zene), "prosek_muski": prosek(o["starost"] for o in muski),
            "najmladji": min(starosti, default=None), "najstariji": max(starosti, default=None),
            "bez_starosti": ukupno - len(sa_starosti),
            "prosek_staz": prosek(o["staz"] for o in sa_stazom),
            "visoka": visoka, "udeo_visoka": udeo(visoka, ukupno),
            "pred_penzijom": sum(1 for s in starosti if s >= 60),
        },
        "pol": [_red(naziv, [o for o in svi if o["pol"] == kod], ukupno) for kod, naziv in POLOVI],
        "starosni": starosni, "rasponi_nazivi": [n for _, _, n in STAROSNI_RASPONI],
        "stepeni": stepeni, "ukrstanje": ukrstanje,
        "staz": staz_rasponi,
        "oj": _po(svi, lambda o: o["oj_naziv"]),
        "odnos": _po(svi, lambda o: o["odnos"]),
        "nerazvrstani": [{"zanimanje": z, "skola": s, "broj": b} for (z, s), b in nerazvrstani.most_common()],
        "razvrstavanje": sorted(Counter((o["stepen"], o["stepen_izvor"], o["zanimanje"] or "—", o["skola"] or "—")
                                        for o in svi).items(),
                                key=lambda x: (REDOSLED_STEPENA.index(x[0][0]), x[0][2], x[0][3])),
    }
