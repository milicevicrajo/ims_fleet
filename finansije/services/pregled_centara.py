"""Finansijski pregled po centrima: rezultat bez i posle zajedničkih troškova (ZT).

Odluke 05.10.2026. (pisana potvrda korisnika):

- **ZT centra = zbir ZT njegovih šifara posla**, po istoj formuli kao ekran „Šifre posla”
  (`shared_costs.allocate`, procedure 52/53). Brojevi se zato poklapaju između ekrana.
- **Podela centara po raspodeli ZT**, iz podataka svake godine:
  profitni = centri sa koeficijentom > 0 u `blokraspodela`;
  zajedničke službe (neprofitni) = centri čije šifre čine osnovicu (kriterijum 1–3 u `posao_mes`);
  ostali = sve ostalo (npr. naučni blok, centri sa koeficijentom 0, neraspoređena knjiženja).

Raspodela **ne menja rezultat Instituta**: ZT profitnih centara je pokriće troškova zajedničkih
službi. Zbir „posle ZT” svih grupa jednak je zbiru „bez ZT” (vidi `uskladjenje`).
Šifra koja nema profitno pravilo ili čiji centar nema red u `blokraspodela` ne prima ZT (nula);
duplirana pravila ili nejednoznačna raspodela daju „nedostupno”, kao na ekranu Šifre posla.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import connections
from django.db.models.functions import ExtractMonth

from finansije.models import LedgerEntry
from .reports import ZERO, expressions
from .shared_costs import allocate, allocation_rules
from .source import SOURCE

GRUPE = (
    ("profitni", "Profitni centri", "Primaju raspodelu troškova zajedničkih službi (koeficijent centra u raspodeli)."),
    ("sluzbe", "Zajedničke službe (neprofitni centri)", "Njihove šifre posla čine osnovicu raspodele."),
    ("ostali", "Ostali centri", "Ne primaju raspodelu i nisu osnovica (npr. koeficijent 0) i neraspoređena knjiženja."),
)


def oznaka_centra(blok):
    """`posao.blok` → oznaka centra kakva je na knjiženju (20 → 2, 30 → 3)."""
    from organizacija.services.classification import OZNAKA_CENTRA_IZ_KNJIZENJA

    blok = str(blok or "").strip()
    return OZNAKA_CENTRA_IZ_KNJIZENJA.get(blok, blok)


def raspodela_centara(company, year):
    """Centri sa koeficijentima raspodele za godinu: {oznaka: (koef1, koef2, koef3)}."""
    with connections["server_db"].cursor() as cursor:
        cursor.execute(f"SELECT b.blok, b.koef1, b.koef2, b.koef3 FROM {SOURCE}.blokraspodela b "
                       "WHERE b.sif_pred=%s AND b.god=%s", [company, str(year)])
        return {oznaka_centra(r[0]): tuple(v or ZERO for v in r[1:]) for r in cursor.fetchall()}


def zt_sifara(company, codes, start, end, covered):
    """ZT po šifri za period (po godinama, kao Šifre posla) i podaci za podelu centara."""
    rezultat = {code: {"cost": ZERO, "prima": False, "available": True, "complete": True, "notes": []} for code in codes}
    profitni, osnovica = set(), set()
    for year in range(start.year, end.year + 1):
        lower, upper = max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        if year not in covered:
            for stavka in rezultat.values():
                stavka["available"] = False
                stavka["notes"].append(f"Nema potvrđenih sinhronizovanih podataka za {year}.")
            continue
        rules, centers = allocation_rules(company, year, lower.month, upper.month, None)
        profitni |= {centar for centar, koef in raspodela_centara(company, year).items() if any(k > 0 for k in koef)}
        osnovica |= {r["code"] for r in rules if r["criterion"] in ("1", "2", "3")}
        profitne_sifre = {r["code"] for r in rules if r["profit"] == "P"}
        balances = list(LedgerEntry.objects.filter(company=company, active=True, booking_date__range=(lower, upper))
                        .order_by().annotate(month=ExtractMonth("booking_date")).values("job_code", "month")
                        .annotate(**expressions()))
        months = upper.month - lower.month + 1
        for code, stavka in rezultat.items():
            if code not in profitne_sifre or code not in centers:
                continue  # nije profitni posao ili njegov centar nema raspodelu: ne prima ZT
            deo = allocate(rules, centers[code], balances, code, months)
            if not deo["available"]:
                stavka["available"] = False
                stavka["notes"].append(deo["note"])
                continue
            stavka["prima"] = True
            stavka["cost"] += deo["cost"]
            if not deo["complete"]:
                stavka["complete"] = False
                stavka["notes"].append(deo["note"])
    return rezultat, profitni, osnovica


def pregled_centara(entries, start, end, covered, *, cela_firma=True):
    """Centri u tri grupe, sa rezultatom bez i posle ZT, i usklađenje sa rezultatom Instituta."""
    from finansije.access import polje_centra
    from fleet.support.registar import Registar

    company = getattr(settings, "FINANSIJE_COMPANY", 1)
    polje = polje_centra()
    centri = defaultdict(lambda: {"revenue": ZERO, "expense": ZERO, "count": 0})
    sifre_centra = defaultdict(lambda: defaultdict(int))  # šifra → centar → broj knjiženja
    for red in entries.order_by().values(polje, "job_code").annotate(**expressions()):
        centar = red[polje] or ""
        stavka = centri[centar]
        stavka["revenue"] += red["revenue"] or ZERO
        stavka["expense"] += red["expense"] or ZERO
        stavka["count"] += red["count"]
        if red["job_code"]:
            sifre_centra[red["job_code"]][centar] += red["count"]
    # Šifra sa knjiženjima u više centara (promena centra u periodu) ide centru sa najviše knjiženja.
    centar_sifre = {code: max(po_centru, key=lambda c: (po_centru[c], c)) for code, po_centru in sifre_centra.items()}
    zt, profitni, osnovica = zt_sifara(company, set(centar_sifre), start, end, covered)
    sluzbe = {centar_sifre[code] for code in osnovica if code in centar_sifre}

    po_centru = defaultdict(lambda: {"cost": ZERO, "available": True, "complete": True, "notes": []})
    for code, centar in centar_sifre.items():
        stavka, cilj = zt[code], po_centru[centar]
        if not stavka["available"]:
            cilj["available"] = False
        cilj["cost"] += stavka["cost"]
        cilj["complete"] = cilj["complete"] and stavka["complete"]
        cilj["notes"].extend(n for n in stavka["notes"] if n not in cilj["notes"])

    registar = Registar()
    grupe = {kljuc: [] for kljuc, _, _ in GRUPE}
    for centar, iznosi in centri.items():
        raspodela = po_centru[centar]
        cost = raspodela["cost"] if raspodela["available"] else None
        result = iznosi["revenue"] - iznosi["expense"]
        red = {
            "code": centar, "label": registar.oznaka_centra(centar) if centar else "Neraspoređeno",
            "revenue": iznosi["revenue"], "expense": iznosi["expense"], "result": result, "count": iznosi["count"],
            "zt": -cost if cost is not None else None,
            "expense_zt": iznosi["expense"] + cost if cost is not None else None,
            "result_zt": result - cost if cost is not None else None,
            "complete": raspodela["available"] and raspodela["complete"], "note": " ".join(raspodela["notes"]),
        }
        kljuc = "profitni" if centar and centar in profitni else "sluzbe" if centar in sluzbe else "ostali"
        grupe[kljuc].append(red)

    def zbir(redovi):
        z = {k: sum((r[k] for r in redovi), ZERO) for k in ("revenue", "expense", "result")}
        z["count"] = sum(r["count"] for r in redovi)
        dostupno = all(r["zt"] is not None for r in redovi)
        for k in ("zt", "expense_zt", "result_zt"):
            z[k] = sum((r[k] for r in redovi), ZERO) if dostupno else None
        z["complete"] = dostupno and all(r["complete"] for r in redovi)
        return z

    rezultat = []
    for kljuc, naslov, opis in GRUPE:
        redovi = sorted(grupe[kljuc], key=lambda r: (not r["code"], len(r["code"]), r["code"]))
        if redovi:
            rezultat.append({"key": kljuc, "title": naslov, "description": opis, "rows": redovi, "total": zbir(redovi)})
    svi = [r for grupa in rezultat for r in grupa["rows"]]
    ukupno = zbir(svi)
    uskladjenje = None
    if cela_firma and ukupno["zt"] is not None:
        sluzbe_grupa = next((g for g in rezultat if g["key"] == "sluzbe"), None)
        pokrice = -ukupno["zt"]  # ukupno raspoređeni ZT, kao trošak centara (pozitivan)
        sluzbe_rezultat = sluzbe_grupa["total"]["result"] if sluzbe_grupa else ZERO
        sluzbe_posle_zt = sluzbe_grupa["total"]["result_zt"] if sluzbe_grupa else ZERO
        # Zbir „posle ZT” svih centara + pokriće službi = rezultat Instituta (raspodela ga ne menja).
        bez_minusa_nule = lambda v: v if v else ZERO  # -0.00 se ne prikazuje kao „−0”
        uskladjenje = {
            "pokrice": pokrice,
            "sluzbe_rezultat": sluzbe_rezultat,
            "sluzbe_posle": bez_minusa_nule(sluzbe_posle_zt + pokrice),
            "posle_zt_centri": ukupno["result_zt"],
            "institut": ukupno["result"],
        }
    return {"groups": rezultat, "total": ukupno, "uskladjenje": uskladjenje,
            "available": ukupno["zt"] is not None, "complete": ukupno["complete"]}
