"""Zajednički troškovi (ZT) po vrsti, po OJ gde nastaju i po centrima/OJ koji ih primaju (od 07.10.2026.).

Ista raspodela kao ekran Šifre posla i Finansijski pregled (`shared_costs.allocate`, procedure 52/53):
osnovica kriterijuma j = zbir (P − R) šifara sa mesečnim kriterijumom j; profitna šifra prima
`−osnovica_j × koef. centra_j × prosečan koef. šifre_j / 10000`. Raspodela je linearna po osnovici, pa se
deo svake vrste troška računa **tačno** istom formulom, primenjenom na deo osnovice te vrste
(zbir vrsta = ZT šifre). Vrsta troška je po kontu (`VRSTE`); prihodi službi umanjuju osnovicu.

Šifra prima ZT u centru u kome ima najviše knjiženja u periodu (kao Finansijski pregled), a OJ primaoca je
jedinica šifre u registru organizacije.
Samo za obuhvat cele firme — osnovica su troškovi zajedničkih službi cele firme.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db.models import Max
from django.db.models.functions import ExtractMonth

from finansije.models import LedgerEntry
from .reports import CLOSING_POSTINGS, ZERO, expressions
from .shared_costs import allocate, allocation_rules

SLUZBE = "sluzbe"
# (ključ, naziv, početci konta) — prvo pogođeno pravilo određuje vrstu; 52 su zarade zaposlenih u službama.
VRSTE = (
    (SLUZBE, "Zajedničke službe — zarade i lični rashodi", ("52",)),
    ("energija", "Energija i grejanje (struja, ugalj, gorivo)", ("513",)),
    ("komunalije", "Komunalne usluge (voda, gradska čistoća)", ("5392",)),
    ("odrzavanje", "Održavanje, čišćenje i obezbeđenje", ("532", "55080", "55040")),
    ("amortizacija", "Amortizacija i rezervisanja", ("54",)),
    ("osiguranje", "Osiguranje, porezi i članarine", ("552", "554", "555")),
    ("materijal", "Materijal", ("51",)),
    ("usluge", "Ostale usluge (prevoz, PTT, zakup…)", ("53",)),
    ("nematerijalni", "Ostali nematerijalni troškovi", ("55",)),
    ("ostalo", "Finansijski i ostali rashodi", ("56", "57", "58", "59")),
    ("prihodi", "Prihodi službi (umanjuju osnovicu)", ("6",)),
)
NAZIV = {k: n for k, n, _ in VRSTE}
REDOSLED = [k for k, _, _ in VRSTE]


def oj_sifara():
    """Šifra posla → (šifra OJ, naziv OJ) iz registra organizacije (nadređena jedinica šifre)."""
    from organizacija.models import OrgNode, OrgNodeVersion

    verzije = {v.node_id: v for v in OrgNodeVersion.objects.filter(valid_to__isnull=True).select_related("node")}
    mapa = {}
    for v in verzije.values():
        if v.node.level == OrgNode.LEVEL_JOB and v.parent_id in verzije:
            jedinica = verzije[v.parent_id]
            mapa[v.full_code.strip()] = (jedinica.full_code.strip(), " ".join((jedinica.name or "").split()))
    if any(not naziv for _, naziv in mapa.values()):
        # Jedinica bez naziva u registru: naziv iz šifarnika organizacionih jedinica.
        from core.models import OrganizationalUnit

        nazivi = {str(k).strip(): " ".join(str(n or "").split()) for k, n in OrganizationalUnit.objects.values_list("code", "name")}
        mapa = {sifra: (oj, naziv or nazivi.get(oj, "")) for sifra, (oj, naziv) in mapa.items()}
    return mapa


def vrsta(konto):
    konto = str(konto or "")
    return next((k for k, _, pocetci in VRSTE if konto.startswith(pocetci)), "ostalo")


def _p(deo, ukupno):
    return (Decimal(deo) * 100 / ukupno).quantize(Decimal("0.1"), ROUND_HALF_UP) if ukupno else None


def _q(v):
    return v.quantize(Decimal("0.01"), ROUND_HALF_UP)


def _godina(company, lower, upper, rezultat, napomene):
    rules, centers = allocation_rules(company, lower.year, lower.month, upper.month, None)
    meseci = upper.month - lower.month + 1
    kriterijum = {}
    for r in rules:
        kljuc = (r["code"], r["month"])
        if kljuc in kriterijum:
            napomene.add("Postoje duplirani mesečni kriterijumi raspodele; raspodela nije dostupna.")
            return False
        kriterijum[kljuc] = r
    osnovica_sifre = {r["code"] for r in rules if r["criterion"] in ("1", "2", "3")}
    upit = (LedgerEntry.objects.filter(company=company, active=True, booking_date__range=(lower, upper))
            .exclude(CLOSING_POSTINGS))
    # Osnovica po kriterijumu i vrsti troška, i po OJ gde nastaje (samo meseci u kojima šifra ima kriterijum).
    po_kriterijumu = [defaultdict(lambda: ZERO) for _ in range(3)]  # vrsta → (P − R)
    for red in (upit.filter(job_code__in=osnovica_sifre).annotate(m=ExtractMonth("booking_date")).order_by()
                .values("job_code", "m", "account", "organizational_unit").annotate(oj_naziv=Max("organizational_unit_name"), **expressions())):
        pravilo = kriterijum.get((red["job_code"], red["m"]))
        if not pravilo or pravilo["criterion"] not in ("1", "2", "3"):
            continue
        neto = (red["revenue"] or ZERO) - (red["expense"] or ZERO)
        v = vrsta(red["account"])
        po_kriterijumu[int(pravilo["criterion"]) - 1][v] += neto
        oj = rezultat["izvor_oj"][red["organizational_unit"]]
        oj["naziv"] = oj["naziv"] or " ".join(str(red["oj_naziv"] or "").split())
        oj["vrste"][v] += -neto
        oj["sifre"].add(red["job_code"])
        rezultat["osnovica"][v] += -neto

    # Raspodela po profitnoj šifri: isti obračun kao `allocate`, razložen po vrsti troška.
    balansi = list(upit.order_by().annotate(month=ExtractMonth("booking_date")).values("job_code", "month")
                   .annotate(**expressions()))
    for code in {r["code"] for r in rules if r["profit"] == "P"}:
        if code not in centers:
            continue
        ukupno = allocate(rules, centers[code], balansi, code, meseci)
        if not ukupno["available"]:
            napomene.add(ukupno["note"])
            continue
        if not ukupno["complete"]:
            napomene.add("Neke šifre nemaju aktivne koeficijente za sve mesece perioda; raspodela je nepotpuna.")
        sopstvena = [r for r in rules if r["code"] == code and r["profit"] == "P"]
        prosek = [sum((r["coefficients"][i] for r in sopstvena), ZERO) / meseci for i in range(3)]
        faktor = [centers[code][i] * prosek[i] / Decimal("10000") for i in range(3)]
        po_vrsti = defaultdict(lambda: ZERO)
        for i in range(3):
            for v, neto in po_kriterijumu[i].items():
                po_vrsti[v] += -neto * faktor[i]
        stavka = rezultat["sifre"][code]
        for v, iznos in po_vrsti.items():
            stavka[v] += iznos
        stavka["__ukupno"] += ukupno["cost"]
    return True


def zajednicki_troskovi(start, end, covered, company=None):
    company = company or getattr(settings, "FINANSIJE_COMPANY", 1)
    from finansije.access import polje_centra
    from fleet.support.registar import Registar

    rezultat = {"osnovica": defaultdict(lambda: ZERO),
                "izvor_oj": defaultdict(lambda: {"naziv": "", "vrste": defaultdict(lambda: ZERO), "sifre": set()}),
                "sifre": defaultdict(lambda: defaultdict(lambda: ZERO))}
    napomene, dostupno = set(), True
    for godina in range(start.year, end.year + 1):
        lower, upper = max(start, date(godina, 1, 1)), min(end, date(godina, 12, 31))
        if godina not in covered:
            napomene.add(f"Nema potvrđenih sinhronizovanih podataka za {godina}.")
            dostupno = False
            continue
        dostupno = _godina(company, lower, upper, rezultat, napomene) and dostupno

    # Centar i OJ primaoca: gde šifra ima najviše knjiženja u periodu.
    polje = polje_centra()
    po_sifri = defaultdict(lambda: {"centar": defaultdict(int), "oj": defaultdict(int), "naziv": "", "oj_naziv": {}})
    for red in (LedgerEntry.objects.filter(company=company, active=True, booking_date__range=(start, end),
                                           job_code__in=list(rezultat["sifre"])).order_by()
                .values("job_code", polje, "organizational_unit")
                .annotate(naziv=Max("job_name"), oj_naziv=Max("organizational_unit_name"), **expressions())):
        s = po_sifri[red["job_code"]]
        s["centar"][red[polje] or ""] += red["count"]
        s["oj"][red["organizational_unit"]] += red["count"]
        s["naziv"] = s["naziv"] or red["naziv"] or ""
        s["oj_naziv"][red["organizational_unit"]] = " ".join(str(red["oj_naziv"] or "").split())

    registar = Registar()
    oj_registra = oj_sifara()
    centri = defaultdict(lambda: defaultdict(lambda: ZERO))
    oj_primaoca = defaultdict(lambda: {"naziv": "", "centar": "", "vrste": defaultdict(lambda: ZERO)})
    sifre = []
    for code, vrste in rezultat["sifre"].items():
        s = po_sifri.get(code)
        centar = max(s["centar"], key=lambda c: (s["centar"][c], c)) if s and s["centar"] else ""
        # OJ primaoca: jedinica šifre u registru; bez registra — OJ sa knjiženja.
        if code.strip() in oj_registra:
            oj, oj_naziv = oj_registra[code.strip()]
        else:
            oj = max(s["oj"], key=lambda o: (s["oj"][o], str(o))) if s and s["oj"] else None
            oj_naziv = s["oj_naziv"].get(oj, "") if s else ""
        iznosi = {v: vrste.get(v, ZERO) for v in REDOSLED}
        ukupno = vrste["__ukupno"]
        if not ukupno and not any(iznosi.values()):
            continue
        for v, iznos in iznosi.items():
            centri[centar][v] += iznos
            oj_primaoca[oj]["vrste"][v] += iznos
        centri[centar]["__ukupno"] += ukupno
        oj_primaoca[oj]["vrste"]["__ukupno"] += ukupno
        oj_primaoca[oj]["naziv"] = oj_naziv
        oj_primaoca[oj]["centar"] = centar
        sifre.append(_red(code, (s or {}).get("naziv", ""), iznosi, ukupno, centar=centar))

    osnovica = {v: rezultat["osnovica"].get(v, ZERO) for v in REDOSLED}
    ukupno_osnovica = sum(osnovica.values(), ZERO)
    raspodeljeno = sum((c["__ukupno"] for c in centri.values()), ZERO)
    return {
        "dostupno": dostupno and bool(rezultat["sifre"] or ukupno_osnovica),
        "napomene": sorted(napomene),
        "vrste": [{"key": v, "naziv": NAZIV[v], "iznos": _q(osnovica[v]), "udeo": _p(osnovica[v], ukupno_osnovica)}
                  for v in REDOSLED if osnovica[v]],
        "osnovica": _q(ukupno_osnovica),
        "sluzbe": _q(osnovica[SLUZBE]), "sluzbe_udeo": _p(osnovica[SLUZBE], ukupno_osnovica),
        "ostalo": _q(ukupno_osnovica - osnovica[SLUZBE]), "ostalo_udeo": _p(ukupno_osnovica - osnovica[SLUZBE], ukupno_osnovica),
        "raspodeljeno": _q(raspodeljeno), "neraspodeljeno": _q(ukupno_osnovica - raspodeljeno),
        "izvor_oj": sorted((_red(str(oj), d["naziv"], {v: d["vrste"].get(v, ZERO) for v in REDOSLED},
                                 sum(d["vrste"].values(), ZERO), broj_sifara=len(d["sifre"]))
                            for oj, d in rezultat["izvor_oj"].items() if any(d["vrste"].values())),
                           key=lambda r: -r["ukupno"]),
        "centri": sorted((_red(c, registar.oznaka_centra(c) if c else "Neraspoređeno",
                               {v: d.get(v, ZERO) for v in REDOSLED}, d["__ukupno"], udeo_u=raspodeljeno)
                          for c, d in centri.items()), key=lambda r: -r["ukupno"]),
        "oj_primaoca": sorted((_red(str(oj) if oj is not None else "", d["naziv"] or (f"OJ {oj}" if oj else "Bez OJ"),
                                    {v: d["vrste"].get(v, ZERO) for v in REDOSLED}, d["vrste"]["__ukupno"],
                                    centar=d["centar"], udeo_u=raspodeljeno)
                               for oj, d in oj_primaoca.items()), key=lambda r: -r["ukupno"]),
        "sifre": sorted(sifre, key=lambda r: -r["ukupno"]),
        "kolone": [(v, NAZIV[v]) for v in REDOSLED if osnovica[v]],
    }


def _red(code, naziv, iznosi, ukupno, *, centar="", broj_sifara=None, udeo_u=None):
    sluzbe = iznosi.get(SLUZBE, ZERO)
    return {"code": code, "naziv": naziv, "centar": centar, "ukupno": _q(ukupno), "sluzbe": _q(sluzbe),
            "ostalo": _q(ukupno - sluzbe), "sluzbe_udeo": _p(sluzbe, ukupno),
            "vrste": {v: _q(i) for v, i in iznosi.items()}, "broj_sifara": broj_sifara,
            "udeo": _p(ukupno, udeo_u) if udeo_u is not None else None}
