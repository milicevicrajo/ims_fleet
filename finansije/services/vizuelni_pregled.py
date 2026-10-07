"""Vizuelni pregled poslovanja po centrima i šiframa posla (od 07.10.2026.).

Isti izvor i ista pravila kao Finansijski pregled: knjiženja u obuhvatu korisnika, za period, bez
završnog zatvaranja (ZAT, 59900/69900); prihodi su klasa 6, rashodi klasa 5, rezultat = prihodi − rashodi.
Učešća su udeo u zbiru prikazanog obuhvata. Struktura rashoda je po vrsti troška (`STRUKTURA`, po kontu:
zarade, porezi i doprinosi, ugovori, odbori, materijal, energija, održavanje, istraživanja, usluge,
amortizacija…), a uz direktne rashode i zajednički troškovi koje jedinica nosi, razdvojeni na zajedničke
službe (zarade) i ostalo (`zajednicki_troskovi`, ista raspodela kao ZT).

Bez izabranog centra ekran poredi centre; sa izabranim centrom poredi šifre posla tog centra.
Rezultat posle zajedničkih troškova (ZT) dolazi iz `pregled_centara`, kao na Finansijskom pregledu.
"""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Max
from django.db.models.functions import ExtractMonth, ExtractYear, Substr

from .reports import ZERO, expressions

# (ključ, naziv, početci konta) — prvo pogođeno pravilo određuje vrstu direktnog rashoda.
STRUKTURA = (
    ("zarade", "Zarade (bruto)", ("520",)),
    ("doprinosi", "Porezi i doprinosi na zarade", ("521",)),
    ("ugovori", "Ugovori o delu, autorski i privremeni poslovi", ("522", "523", "524")),
    ("odbori", "Upravni i nadzorni odbor", ("526",)),
    ("licni", "Ostali lični rashodi i naknade", ("52",)),
    ("energija", "Gorivo i energija", ("513",)),
    ("materijal", "Materijal i rezervni delovi", ("51",)),
    ("odrzavanje", "Održavanje", ("532",)),
    ("istrazivanja", "Istraživanja", ("536",)),
    ("usluge", "Transport, zakup i ostale usluge", ("53",)),
    ("amortizacija", "Amortizacija i rezervisanja", ("54",)),
    ("nematerijalni", "Nematerijalni (osiguranje, porezi, neproizvodne usluge…)", ("55",)),
    ("ostalo", "Finansijski i ostali rashodi", ("56", "57", "58", "59")),
)
ZT_DELOVI = (("zt_sluzbe", "Zajedničke službe (zarade) — ZT"), ("zt_ostalo", "Zajednički troškovi — ostalo (energija, održavanje…)"))
NAZIV_STRUKTURE = {k: n for k, n, _ in STRUKTURA} | dict(ZT_DELOVI)


def vrsta_rashoda(konto):
    konto = str(konto or "")
    return next((k for k, _, pocetci in STRUKTURA if konto.startswith(pocetci)), "ostalo")


MESECI = ("jan", "feb", "mar", "apr", "maj", "jun", "jul", "avg", "sep", "okt", "nov", "dec")
NAJVISE_SIFARA = 15
BEZ_MARZE = {"2"}  # centri koji se ne prikazuju na grafikonu marže (Poslovni blok)


def _p(deo, ukupno):
    """Procenat sa jednom decimalom ili None kad zbir nije definisan."""
    if not ukupno:
        return None
    return (Decimal(deo) * 100 / ukupno).quantize(Decimal("0.1"), ROUND_HALF_UP)


def _f(v):
    return float(v) if v is not None else None


def _red(code, label, name, revenue, expense, count, ukupno):
    revenue, expense = revenue or ZERO, expense or ZERO
    result = revenue - expense
    return {
        "code": code, "label": label, "name": name or "", "revenue": revenue, "expense": expense, "result": result,
        "count": count, "revenue_share": _p(revenue, ukupno["revenue"]), "expense_share": _p(expense, ukupno["expense"]),
        "result_share": _p(result, ukupno["dobit"]) if result > 0 else None,
        "margin": _p(result, revenue),
    }


def vizuelni_pregled(entries, centar=None, centri_zt=None, zt_po_jedinici=None):
    """Podaci za ekran i grafikone. `entries` su već filtrirana knjiženja (period, obuhvat, centar).
    `zt_po_jedinici`: {šifra centra ili posla: (zajedničke službe, ostali ZT)} iz `zajednicki_troskovi`."""
    from finansije.access import polje_centra
    from fleet.support.registar import Registar

    registar = Registar()
    ukupno = entries.aggregate(**expressions())
    ukupno["revenue"] = ukupno["revenue"] or ZERO
    ukupno["expense"] = ukupno["expense"] or ZERO
    ukupno["result"] = ukupno["revenue"] - ukupno["expense"]
    ukupno["margin"] = _p(ukupno["result"], ukupno["revenue"])

    # Jedinice poređenja: centri, a za izabrani centar njegove šifre posla.
    if centar is None:
        polje = polje_centra()
        grupe = list(entries.order_by().values(polje).annotate(**expressions()))
        sirovi = [(g[polje] or "", registar.oznaka_centra(g[polje]) if g[polje] else "Neraspoređeno", "", g) for g in grupe]
    else:
        polje = "job_code"
        grupe = list(entries.order_by().values("job_code").annotate(name=Max("job_name"), **expressions()))
        sirovi = [(g["job_code"] or "", g["job_code"] or "Bez šifre posla", g["name"], g) for g in grupe]
    ukupno["dobit"] = sum(((g["revenue"] or ZERO) - (g["expense"] or ZERO) for *_, g in sirovi
                           if (g["revenue"] or ZERO) > (g["expense"] or ZERO)), ZERO)
    jedinice = [_red(code, label, name, g["revenue"], g["expense"], g["count"], ukupno) for code, label, name, g in sirovi]
    jedinice.sort(key=lambda r: (-r["revenue"], -r["expense"], r["code"]))

    # Rezultat posle ZT (samo za centre, kad je raspodela dostupna).
    if centar is None and centri_zt and centri_zt.get("available"):
        po_centru = {r["code"]: r for g in centri_zt["groups"] for r in g["rows"]}
        for r in jedinice:
            zt = po_centru.get(r["code"])
            r["result_zt"] = zt["result_zt"] if zt else None

    # Struktura rashoda po vrsti troška, ukupno i po jedinici, uz zajedničke troškove koje jedinica nosi.
    po_grupi = list(entries.filter(account__startswith="5").annotate(grupa=Substr("account", 1, 3)).order_by()
                    .values(polje, "grupa").annotate(**expressions()))
    ukupno_vrste = defaultdict(lambda: ZERO)
    matrica = defaultdict(lambda: defaultdict(lambda: ZERO))
    for g in po_grupi:
        v = vrsta_rashoda(g["grupa"])
        ukupno_vrste[v] += g["expense"] or ZERO
        matrica[g[polje] or ""][v] += g["expense"] or ZERO
    vidljive = {r["code"] for r in jedinice}
    for code, (sluzbe, ostalo_zt) in (zt_po_jedinici or {}).items():
        if code in vidljive:
            for kljuc, iznos in (("zt_sluzbe", sluzbe), ("zt_ostalo", ostalo_zt)):
                matrica[code][kljuc] += iznos
                ukupno_vrste[kljuc] += iznos
    ukupno_sa_zt = sum(ukupno_vrste.values(), ZERO)
    redosled = [k for k, _, _ in STRUKTURA] + [k for k, _ in ZT_DELOVI]
    # Udeo u direktnim rashodima: ZT je raspodela troškova službi koji su već među direktnim rashodima službi.
    struktura = [{"code": k, "label": NAZIV_STRUKTURE[k], "expense": ukupno_vrste[k], "share": _p(ukupno_vrste[k], ukupno["expense"]),
                  "zt": k.startswith("zt_")} for k in redosled if ukupno_vrste[k]]
    for r in jedinice:
        r["struktura"] = {k: matrica[r["code"]].get(k, ZERO) for k in redosled}
        r["ukupno_sa_zt"] = sum(r["struktura"].values(), ZERO)

    # Mesečni tok.
    meseci = list(entries.annotate(g=ExtractYear("booking_date"), m=ExtractMonth("booking_date")).order_by()
                  .values("g", "m").annotate(**expressions()).order_by("g", "m"))
    vise_godina = len({m["g"] for m in meseci}) > 1
    tok = [{"label": f"{MESECI[m['m'] - 1]}{' ' + str(m['g']) if vise_godina else ''}",
            "revenue": m["revenue"] or ZERO, "expense": m["expense"] or ZERO,
            "result": (m["revenue"] or ZERO) - (m["expense"] or ZERO)} for m in meseci]
    kumulativ = ZERO
    for t in tok:
        kumulativ += t["result"]
        t["cumulative"] = kumulativ

    # Grafikoni: najviše 15 jedinica po prihodu (ostale u „Ostalo”), da ostanu čitljivi.
    prikaz = jedinice[:NAJVISE_SIFARA]
    ostalo = jedinice[NAJVISE_SIFARA:]
    def kolac(kljuc):
        stavke = [(r["label"], r[kljuc]) for r in prikaz if r[kljuc] > 0]
        ostatak = sum((r[kljuc] for r in ostalo if r[kljuc] > 0), ZERO)
        if ostatak:
            stavke.append((f"Ostalo ({len(ostalo)})", ostatak))
        return {"labels": [s[0] for s in stavke], "values": [_f(s[1]) for s in stavke]}

    po_rezultatu = sorted(jedinice, key=lambda r: r["result"], reverse=True)
    rang = po_rezultatu[:10] + [r for r in po_rezultatu[-10:] if r not in po_rezultatu[:10]] if len(jedinice) > 20 else po_rezultatu
    # Marža bez Poslovnog bloka (centar 2): to je uprava, ne posao koji donosi prihod.
    sa_maržom = [r for r in prikaz if r["revenue"] > 0 and not (centar is None and r["code"] in BEZ_MARZE)]
    # Struktura: najviše 15 jedinica po ukupnim rashodima (direktni + ZT).
    top_struktura = sorted((r for r in jedinice if r["ukupno_sa_zt"] > 0), key=lambda r: -r["ukupno_sa_zt"])[:NAJVISE_SIFARA]
    grafikoni = {
        "jedinice": {"labels": [r["label"] for r in prikaz], "revenue": [_f(r["revenue"]) for r in prikaz],
                     "expense": [_f(r["expense"]) for r in prikaz], "result": [_f(r["result"]) for r in prikaz],
                     "result_zt": [_f(r.get("result_zt")) for r in prikaz] if any(r.get("result_zt") is not None for r in prikaz) else None},
        "udeo_prihoda": kolac("revenue"), "udeo_rashoda": kolac("expense"), "udeo_dobiti": kolac("result"),
        "rezultat": {"labels": [r["label"] for r in rang], "values": [_f(r["result"]) for r in rang]},
        "marza": {"labels": [r["label"] for r in sa_maržom], "values": [_f(r["margin"]) for r in sa_maržom]},
        "struktura_po_jedinici": {
            "labels": [r["label"] for r in top_struktura],
            "datasets": [{"key": s["code"], "label": s["label"], "zt": s["zt"],
                          "values": [_f(r["struktura"][s["code"]]) for r in top_struktura]} for s in struktura],
        },
        "tok": {"labels": [t["label"] for t in tok], "revenue": [_f(t["revenue"]) for t in tok],
                "expense": [_f(t["expense"]) for t in tok], "result": [_f(t["result"]) for t in tok],
                "cumulative": [_f(t["cumulative"]) for t in tok]},
    }
    return {"ukupno": ukupno, "jedinice": jedinice, "struktura": struktura, "ukupno_sa_zt": ukupno_sa_zt,
            "struktura_jedinice": top_struktura, "tok": tok, "grafikoni": grafikoni,
            "ima_zt_strukturu": bool(zt_po_jedinici),
            "po_siframa": centar is not None, "ima_zt": grafikoni["jedinice"]["result_zt"] is not None}
