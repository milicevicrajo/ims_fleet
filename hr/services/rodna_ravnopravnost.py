"""Statistika rodne ravnopravnosti — „Evidencija podataka o ostvarivanju rodne ravnopravnosti”, Obrazac 1
(od 07.10.2026.). Samo čitanje kadrovske baze starog programa.

Izvor je `radnik` (oba preduzeća: radni odnos i radno angažovani van radnog odnosa), jer samo on ima sve što
obrazac traži: pol, datum rođenja, datum dolaska i odlaska (`dat_odlaska` 01.01.1900. ili 3000. znači da ga nema),
razlog odlaska (`sif_odl` → `Odlazak`), stručnu spremu (`sif_spr` → `Sprema`) i rukovodeće mesto
(`sif_ruk` → `RukMesto`; rukovodeće mesto je „položaj”, ostali su na izvršilačkim radnim mestima).

Pravila:
- osoba se broji jednom (po JMBG-u), i kad ima zapis u oba preduzeća;
- zaposlen na dan D = došao do D i nije otišao do D; neaktivan radnik bez datuma odlaska se ne broji;
- D je 31.12. izabrane godine (za tekuću godinu — današnji dan); starost se računa na D;
- prijem u godini: dolazak u godini, a osoba nije radila 31.12. prethodne godine;
- prestanak u godini: odlazak u godini, a osoba ne radi 31.12. (nije samo prešla u drugo preduzeće);
- stručna sprema i rukovodeće mesto su današnji podaci iz kadrovske baze (stari program ne čuva istoriju).

Tačke obrasca kojih nema u bazi (plate, konkursi, pritužbe, sudski sporovi, obuke, organi upravljanja,
pravna pomoć, nasilje i obrazloženja) navode se kao „popunjava se ručno”.
"""
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import connections
from django.utils import timezone

IZVOR = "[putgeo-server].[BazaLDIMS].[dbo]"
RADNICI_SQL = (f"SELECT sif_pred, rasif, matbr, pol, dat_rodj, dat_dolaska, dat_odlaska, aktivan, sif_spr, sif_ruk, "
               f"sif_odl FROM {IZVOR}.[radnik]")
ODLAZAK_SQL = f"SELECT sif_odl, naz_odl FROM {IZVOR}.[Odlazak]"
RUKOVODECA_SQL = f"SELECT sif_pred, sif_ruk FROM {IZVOR}.[RukMesto]"

ZENE, MUSKI = "Z", "M"
STAROST = (("do 20 godina", 0, 20), ("Od 21–30 godina", 21, 30), ("Od 31–40 godina", 31, 40),
           ("Od 41–50 godina", 41, 50), ("Od 51–60 godina", 51, 60), ("Od 61–70 godina", 61, 70),
           ("preko 70 godina", 71, 200))
# Grupe iz obrasca (redni broj, naziv) i šifre stručne spreme iz šifarnika `Sprema`.
KVALIFIKACIJE = (
    ("1", "Nekvalifikovani i polukvalifikovani radnik", (10, 20)),
    ("2", "Kvalifikovani radnik", (30,)),
    ("3", "Srednja stručna sprema", (40,)),
    ("4", "Visokokvalifikovani radnik", (50,)),
    ("5", "Viša stručna sprema", (60,)),
    ("6", "Visoka stručna sprema", (71,)),
    ("7", "Master (magistar)", (72,)),
    ("8", "Doktor nauka", (80,)),
)
NEMA_ODLASKA = 3000
RUCNO = (
    ("5", "Plate i druge naknade (prosečan nominalni iznos) po polu, za izvršilačka mesta i položaje"),
    ("7, 8", "Razlozi zbog kojih na izvršilačka mesta, odnosno na položaje nisu raspoređena lica nedovoljno zastupljenog pola"),
    ("9", "Kandidati prijavljeni na konkurse, po polu i kvalifikacijama"),
    ("10, 11", "Pritužbe zbog uznemiravanja ili diskriminacije na osnovu pola i način postupanja"),
    ("12", "Sudski sporovi u vezi sa diskriminacijom na osnovu pola"),
    ("13", "Programi stručnog usavršavanja i obrazovanja, po polu"),
    ("14", "Organi upravljanja i nadzora, komisije i druga tela, po polu, kvalifikacijama i starosti"),
    ("15", "Korisnici besplatne pravne pomoći, po polu"),
    ("16", "Prijavljeni slučajevi nasilja, po polu žrtve i izvršioca"),
)


def _udeo(deo, ukupno):
    return (Decimal(deo) * 100 / ukupno).quantize(Decimal("0.1"), ROUND_HALF_UP) if ukupno else Decimal("0.0")


def _dan(vrednost):
    if isinstance(vrednost, datetime):
        return vrednost.date()
    return vrednost if isinstance(vrednost, date) else None


def _ceo(vrednost):
    try:
        return int(vrednost)
    except (TypeError, ValueError):
        return None


def procitaj_izvor(using="server_db"):
    """(radnici, razlozi odlaska, rukovodeća mesta) iz kadrovske baze."""
    with connections[using].cursor() as cursor:
        cursor.execute(RADNICI_SQL)
        redovi = cursor.fetchall()
        cursor.execute(ODLAZAK_SQL)
        razlozi = {str(s or "").strip(): " ".join(str(n or "").split()) for s, n in cursor.fetchall()}
        cursor.execute(RUKOVODECA_SQL)
        rukovodeca = {(_ceo(p), _ceo(s)) for p, s in cursor.fetchall()}
    radnici = []
    for pred, rasif, matbr, pol, rodj, dolazak, odlazak, aktivan, spr, ruk, odl in redovi:
        pol = str(pol or "").strip().upper()
        radnici.append({
            "preduzece": _ceo(pred), "broj": _ceo(rasif), "jmbg": str(matbr or "").strip(),
            "pol": ZENE if pol in ("Z", "Ž", "F") else MUSKI if pol == "M" else "",
            "rodjen": _dan(rodj), "dolazak": _dan(dolazak), "odlazak": _dan(odlazak),
            "aktivan": str(aktivan or "").strip().upper() == "D", "sprema": _ceo(spr),
            "polozaj": bool(_ceo(ruk)) and (_ceo(pred), _ceo(ruk)) in rukovodeca,
            "razlog": str(odl or "").strip(),
        })
    return radnici, razlozi


def _odlazak(r):
    """Datum odlaska ili None: 01.01.1900. i 3000. znače prazno, a odlazak pre dolaska je iz ranijeg perioda."""
    odlazak = r["odlazak"]
    if odlazak is None or odlazak.year <= 1900 or odlazak.year >= NEMA_ODLASKA:
        return None
    if r["dolazak"] and odlazak < r["dolazak"]:
        return None
    return odlazak


def _radi(r, dan):
    if not r["dolazak"] or r["dolazak"] > dan:
        return False
    odlazak = _odlazak(r)
    if odlazak is None:
        return r["aktivan"]  # neaktivan bez datuma odlaska: ne zna se kad je otišao
    return odlazak > dan


def _kljuc(r):
    return r["jmbg"] or f"{r['preduzece']}-{r['broj']}"


def _po_osobi(radnici):
    """Jedan zapis po osobi; prednost ima radni odnos (preduzeće 1)."""
    osobe = {}
    for r in sorted(radnici, key=lambda r: (r["preduzece"] or 9, r["broj"] or 0)):
        osobe.setdefault(_kljuc(r), r)
    return list(osobe.values())


def _starost(rodjen, dan):
    if not rodjen or rodjen.year < 1920 or rodjen > dan:
        return None
    return dan.year - rodjen.year - ((dan.month, dan.day) < (rodjen.month, rodjen.day))


def _grupa_starosti(r, dan):
    godine = _starost(r["rodjen"], dan)
    if godine is None:
        return "Bez datuma rođenja"
    return next(naziv for naziv, od, do in STAROST if od <= godine <= do)


def _pol(lista):
    zene = sum(1 for r in lista if r["pol"] == ZENE)
    return zene, sum(1 for r in lista if r["pol"] == MUSKI)


def _po_starosti(lista, dan, ukupno_za_udeo):
    """Redovi po starosti: ukupno (udeo u ukupnom), žene i muškarci (udeo u grupi) — kao u obrascu."""
    redovi = []
    for naziv in [s[0] for s in STAROST] + ["Bez datuma rođenja"]:
        clanovi = [r for r in lista if _grupa_starosti(r, dan) == naziv]
        if not clanovi and naziv in ("do 20 godina", "preko 70 godina", "Bez datuma rođenja"):
            continue
        zene, muski = _pol(clanovi)
        redovi.append({"naziv": naziv, "ukupno": len(clanovi), "udeo": _udeo(len(clanovi), ukupno_za_udeo),
                       "zene": zene, "udeo_zena": _udeo(zene, len(clanovi)),
                       "muski": muski, "udeo_muski": _udeo(muski, len(clanovi))})
    return redovi


def _pregled_promene(lista, dan, razlozi=None):
    zene, muski = _pol(lista)
    rezultat = {"ukupno": len(lista), "zene": zene, "muski": muski,
                "udeo_zena": _udeo(zene, len(lista)), "udeo_muski": _udeo(muski, len(lista)),
                "starost": _po_starosti(lista, dan, len(lista))}
    if razlozi is not None:
        po_razlogu = Counter(r["razlog"] for r in lista)
        rezultat["razlozi"] = []
        for sifra, broj in sorted(po_razlogu.items(), key=lambda x: (-x[1], x[0])):
            clanovi = [r for r in lista if r["razlog"] == sifra]
            z, m = _pol(clanovi)
            rezultat["razlozi"].append({"naziv": razlozi.get(sifra) or ("Razlog nije upisan" if not sifra else f"Šifra {sifra}"),
                                        "ukupno": broj, "zene": z, "muski": m, "udeo": _udeo(broj, len(lista))})
    return rezultat


def statistika(godina, radnici, razlozi, danas=None):
    danas = danas or timezone.localdate()
    na_dan = danas if godina >= danas.year else date(godina, 12, 31)
    kraj_prethodne = date(godina - 1, 12, 31)

    zaposleni = _po_osobi([r for r in radnici if _radi(r, na_dan)])
    ukupno = len(zaposleni)
    zene, muski = _pol(zaposleni)

    sprema = []
    poznate = {s for _, _, sifre in KVALIFIKACIJE for s in sifre}
    for rb, naziv, sifre in KVALIFIKACIJE + (("—", "Stručna sprema nije upisana", None),):
        clanovi = [r for r in zaposleni if (r["sprema"] in sifre if sifre else r["sprema"] not in poznate)]
        if sifre is None and not clanovi:
            continue
        z, m = _pol(clanovi)
        sprema.append({"rb": rb, "naziv": naziv, "ukupno": len(clanovi), "udeo": _udeo(len(clanovi), ukupno),
                       "zene": z, "udeo_zena": _udeo(z, ukupno), "muski": m, "udeo_muski": _udeo(m, ukupno)})

    polozaji = []
    for naziv, uslov in (("Lica na izvršilačkim radnim mestima", False), ("Lica na položajima", True)):
        clanovi = [r for r in zaposleni if r["polozaj"] is uslov]
        z, m = _pol(clanovi)
        polozaji.append({"naziv": naziv, "ukupno": len(clanovi), "udeo": _udeo(len(clanovi), ukupno),
                         "zene": z, "udeo_zena": _udeo(z, zene), "muski": m, "udeo_muski": _udeo(m, muski)})

    bili = {_kljuc(r) for r in radnici if _radi(r, kraj_prethodne)}
    ostali = {_kljuc(r) for r in zaposleni}
    primljeni = _po_osobi([r for r in radnici if r["dolazak"] and r["dolazak"].year == godina
                           and r["dolazak"] <= na_dan and _kljuc(r) not in bili])
    otisli = _po_osobi([r for r in radnici if _odlazak(r) and _odlazak(r).year == godina
                        and _odlazak(r) <= na_dan and _kljuc(r) not in ostali])

    return {
        "godina": godina, "na_dan": na_dan, "tekuca": na_dan == danas,
        "ukupno": {"ukupno": ukupno, "zene": zene, "muski": muski,
                   "udeo_zena": _udeo(zene, ukupno), "udeo_muski": _udeo(muski, ukupno)},
        "starost": _po_starosti(zaposleni, na_dan, ukupno),
        "sprema": sprema, "polozaji": polozaji,
        "prijem": _pregled_promene(primljeni, na_dan),
        "prestanak": _pregled_promene(otisli, na_dan, razlozi),
        "rucno": RUCNO,
    }


def broj_sa_udelom(broj, udeo):
    """„75 (24,1%)” kao u obrascu."""
    return f"{broj} ({str(udeo).replace('.', ',')}%)"
