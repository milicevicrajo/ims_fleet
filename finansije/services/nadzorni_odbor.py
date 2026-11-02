"""Izveštaj za nadzorni odbor (od 02.11.2026.): prihodi i rashodi po pozicijama, za celu firmu i po profitnim centrima.

Izgled i mapiranje konta: „Izgled izvestaja i mapiranja.xlsx” (Finansije, 30.10.2026.). Odluke 02.11.2026.:

* Pozicija konta je po prve tri cifre (`MAPIRANJE`). Prihod je potražuje − duguje, rashod duguje − potražuje,
  pa 631 (smanjenje zaliha, znak −1 u mapiranju) sam umanjuje Ostale prihode — znak se ne primenjuje dvaput.
  Konta bez pozicije se ne raspoređuju i prikazuju se u kontrolama.
* Knjiženja bez početnog stanja i zatvaranja (POC, ZAT, 59900/69900), kao Bilans uspeha.
* Centar je centar iz registra na datum knjiženja (`LedgerEntry.org_centar`, centar `3` je naučni blok —
  „30” u Excelu). Profitni centri godine su upisani u `NadzorniCentar`, a sva knjiženja ostalih centara
  (službe, centar 11, knjiženja bez centra) su zajednička. Zajednički prihodi i troškovi dele se centrima po
  fiksnom koeficijentu godine (%).
* Provereno na 2025 (Excel, list „izvestaj oj”, i 1–6/2025 list „izvestaj IMS”): cela firma, zajednički
  troškovi, rashodi centara 42, 43, 44 i 70 i prihodi na ino tržištu i iz budžeta slažu se do dinara.
  Razlike su u Excelu: „Ostali prihodi” centra tamo sadrže samo konto 631, pa ostali prihodi profitnih centara
  (kamate, kursne razlike, 676, 685…, oko 7,4 mil. din. u 2025) nisu ni kod centra ni u zajedničkim prihodima;
  ovde jesu, kao u izveštaju za celu firmu. Stavka konta 614 od 1.321.100 din. (centar 11) je u Excelu kod
  centra 41, i 4.192,57 din. rashoda je u Excelu kod centra 3 umesto 41 (centri su se u registru menjali).
* Plan je godišnji, u hiljadama dinara; plan za period = godišnji × broj meseci perioda / 12.
* Broj zaposlenih: upisan za godinu, a za tekuću godinu bez upisa — aktivni zaposleni iz Kadrova danas
  (centar zaposlenog iz registra organizacije).
"""
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.db.models import Q, Sum
from django.db.models.functions import Substr
from django.utils import timezone

from finansije.models import LedgerEntry, NadzorniCentar, NadzorniGodina, NadzorniPlan
from . import izvoz
from .reports import CLOSING_POSTINGS

NULA = Decimal("0")
STO = Decimal("100")
HILJADA = Decimal("1000")
POLJE_CENTRA = "org_centar"
UKUPAN_PRIHOD, UKUPAN_RASHOD = "UP", "UR"


@dataclass(frozen=True)
class Pozicija:
    kod: str
    broj: int
    naziv: str

    @property
    def prihod(self):
        return self.kod.startswith("P")


PRIHODI = [Pozicija(f"P{i}", i, naziv) for i, naziv in enumerate((
    "Prihodi od prodaje na domaćem tržištu", "Prihodi od prodaje na ino tržištu", "Prihodi iz budžeta",
    "Ostali prihodi"), start=1)]
RASHODI = [Pozicija(f"R{i}", i, naziv) for i, naziv in enumerate((
    "Troškovi materijala", "Režijski troškovi", "Troškovi goriva i energije", "Zarade sa doprinosima poslodavca",
    "Naknada za ugovore o delu i autorske ugovore", "Troškovi članova upravnog odbora i povremenih poslova",
    "Dnevnice i ostala lična primanja", "Usluge i dorade", "Transportne usluge", "Usluge održavanja",
    "Troškovi reklame i propagande", "Troškovi podizvođača", "Ostale usluge",
    "Neproizvodne usluge (čišćenje, obezbeđenje, advokati)", "Reprezentacija", "Premije osiguranja",
    "Platni promet", "Drugi porezi i članarine", "Ostali nematerijalni troškovi (takse, oglasi, tenderi)",
    "Zatezne kamate", "Kursne razlike", "Ostali nepomenuti rashodi i kazne", "Amortizacija"), start=1)]
POZICIJE = PRIHODI + RASHODI
NAZIV = {p.kod: p.naziv for p in POZICIJE}

# Konto (prve tri cifre) → pozicija, iz lista „mapiranje konto”.
MAPIRANJE = {
    "501": "R22", "511": "R1", "512": "R2", "513": "R3", "514": "R2", "515": "R2", "520": "R4", "521": "R4",
    "522": "R5", "523": "R5", "524": "R6", "525": "R22", "526": "R6", "529": "R7", "530": "R8", "531": "R9",
    "532": "R10", "533": "R22", "534": "R11", "535": "R11", "536": "R12", "539": "R13", "540": "R23",
    "545": "R22", "549": "R22", "550": "R14", "551": "R15", "552": "R16", "553": "R17", "554": "R18",
    "555": "R18", "556": "R18", "559": "R19", "562": "R20", "563": "R21", "564": "R22", "570": "R22",
    "574": "R22", "576": "R22", "579": "R22", "582": "R22", "585": "R22", "591": "R22",
    "614": "P1", "615": "P2", "630": "P4", "631": "P4", "640": "P3", "650": "P4", "659": "P4", "662": "P4",
    "663": "P4", "664": "P4", "669": "P4", "670": "P4", "674": "P4", "675": "P4", "676": "P4", "677": "P4",
    "678": "P4", "679": "P4", "685": "P4", "691": "P4",
}


# --- obračun -----------------------------------------------------------------------------------------

def _knjizenja():
    return LedgerEntry.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1), active=True)


def isti_period(od, do, godina):
    """Isti period u drugoj godini (29.02. → 28.02.)."""
    def pomeri(dan):
        try:
            return dan.replace(year=godina)
        except ValueError:
            return dan.replace(year=godina, day=28)
    return pomeri(od), pomeri(do)


def salda_po_centru(od, do):
    """{centar: {konto (3 cifre): iznos na strani konta}} za period jedne godine; None ako godina nema knjiženja."""
    if not _knjizenja().filter(year=od.year).exists():
        return None
    redovi = (_knjizenja().filter(year=od.year, booking_date__range=(od, do)).exclude(journal_type="POC")
              .exclude(CLOSING_POSTINGS).filter(Q(account__startswith="5") | Q(account__startswith="6"))
              .order_by().annotate(konto=Substr("account", 1, 3)).values(POLJE_CENTRA, "konto")
              .annotate(d=Sum("debit"), p=Sum("credit")))
    salda = defaultdict(lambda: defaultdict(lambda: NULA))
    for red in redovi:
        d, p = red["d"] or NULA, red["p"] or NULA
        salda[(red[POLJE_CENTRA] or "").strip()][red["konto"]] += (p - d) if red["konto"].startswith("6") else (d - p)
    return salda


def pozicije(konta):
    """Iznosi pozicija sa zbirovima iz {konto: iznos}; drugi rezultat su konta bez pozicije."""
    iznosi = {p.kod: NULA for p in POZICIJE}
    nerasporedjeno = {}
    for konto, iznos in konta.items():
        if konto in MAPIRANJE:
            iznosi[MAPIRANJE[konto]] += iznos
        elif iznos:
            nerasporedjeno[konto] = iznos
    iznosi[UKUPAN_PRIHOD] = sum((iznosi[p.kod] for p in PRIHODI), NULA)
    iznosi[UKUPAN_RASHOD] = sum((iznosi[p.kod] for p in RASHODI), NULA)
    return iznosi, nerasporedjeno


def _zbir(*recnici):
    ukupno = defaultdict(lambda: NULA)
    for recnik in recnici:
        for kljuc, iznos in recnik.items():
            ukupno[kljuc] += iznos
    return ukupno


def centri_godine(godina):
    """{centar: koeficijent (%)} profitnih centara godine."""
    return {c.centar: c.koeficijent for c in NadzorniCentar.objects.filter(godina=godina)}


def zaposleni_iz_kadrova():
    """(ukupno, {centar: broj}) aktivnih zaposlenih danas, centar iz registra organizacije."""
    from hr.models import Employee
    from organizacija.services.zaposleni import mape_registra

    centri, jedinice = mape_registra()
    oznaka = {cvor: kod for kod, cvor in centri.items()}
    oznaka.update({cvor: oznaka.get(roditelj) for cvor, roditelj in jedinice.values()})
    po_centru = defaultdict(int)
    ukupno = 0
    for cvor in Employee.objects.filter(is_active=True).values_list("org_node_id", flat=True):
        ukupno += 1
        if oznaka.get(cvor):
            po_centru[oznaka[cvor]] += 1
    return ukupno, dict(po_centru)


def zaposleni(godine):
    """{godina: (ukupno ili None, {centar: broj}, izvor)} — upis za godinu, a za tekuću bez upisa Kadrovi."""
    upisano = {g.godina: g.broj_zaposlenih for g in NadzorniGodina.objects.filter(godina__in=godine)}
    po_centru = defaultdict(dict)
    for c in NadzorniCentar.objects.filter(godina__in=godine, broj_zaposlenih__isnull=False):
        po_centru[c.godina][c.centar] = c.broj_zaposlenih
    tekuca = timezone.localdate().year
    rezultat = {}
    for godina in godine:
        ukupno, centri, izvor = upisano.get(godina), dict(po_centru[godina]), "upis"
        if godina == tekuca and (ukupno is None or not centri):
            iz_kadrova, centri_kadrova = zaposleni_iz_kadrova()
            ukupno = iz_kadrova if ukupno is None else ukupno
            centri = centri or centri_kadrova
            izvor = "kadrovi"
        rezultat[godina] = (ukupno, centri, izvor)
    return rezultat


def broj_meseci(od, do):
    return do.month - od.month + 1


def godine_izvestaja(do, broj_godina):
    return list(range(do.year - broj_godina + 1, do.year + 1))


def izradi_firmu(od, do, broj_godina=4):
    """Cela firma: za svaku godinu isti period — plan, ostvarenje, učešće u ukupnom prihodu i indeksi."""
    godine = godine_izvestaja(do, broj_godina)
    meseci = broj_meseci(od, do)
    planovi = defaultdict(dict)
    for plan in NadzorniPlan.objects.filter(godina__in=godine):
        planovi[plan.godina][plan.pozicija] = plan.iznos * HILJADA
    godisnji = {g.godina: g.plan_zaposlenih for g in NadzorniGodina.objects.filter(godina__in=godine)}
    broj_zaposlenih = zaposleni(godine)
    kolone, kontrole = [], []
    for godina in godine:
        g_od, g_do = isti_period(od, do, godina)
        salda = salda_po_centru(g_od, g_do)
        if salda is None:
            kolone.append({"godina": godina, "od": g_od, "do": g_do, "iznosi": None, "plan": None, "plan_period": None})
            kontrole.append((str(godina), "Nema preuzetih knjiženja za ovu godinu.", None))
            continue
        iznosi, nerasporedjeno = pozicije(_zbir(*salda.values()))
        plan = planovi.get(godina)
        if plan:
            plan = dict(plan)
            plan[UKUPAN_PRIHOD] = sum((plan.get(p.kod, NULA) for p in PRIHODI), NULA)
            plan[UKUPAN_RASHOD] = sum((plan.get(p.kod, NULA) for p in RASHODI), NULA)
        kolone.append({"godina": godina, "od": g_od, "do": g_do, "iznosi": iznosi, "plan": plan,
                       "plan_period": {k: v * meseci / 12 for k, v in plan.items()} if plan else None,
                       "zaposleni": broj_zaposlenih[godina], "plan_zaposlenih": godisnji.get(godina)})
        kontrole.append((str(godina), _opis_nerasporedjenih(nerasporedjeno), not nerasporedjeno))
    return {"godine": godine, "kolone": kolone, "kontrole": kontrole, "meseci": meseci}


def izradi_centre(od, do, broj_godina=4):
    """Po profitnim centrima: za svaku godinu pozicije centra, deo zajedničkih prihoda i troškova i rezultat."""
    godine = godine_izvestaja(do, broj_godina)
    broj_zaposlenih = zaposleni(godine)
    centri = sorted({c for g in godine for c in centri_godine(g)}, key=lambda c: (len(c), c))
    po_godini, kontrole = {}, []
    for godina in godine:
        koeficijenti = centri_godine(godina)
        g_od, g_do = isti_period(od, do, godina)
        salda = salda_po_centru(g_od, g_do) if koeficijenti else None
        if not koeficijenti:
            kontrole.append((str(godina), "Za godinu nisu upisani profitni centri i koeficijenti (Podešavanja).", None))
            continue
        if salda is None:
            kontrole.append((str(godina), "Nema preuzetih knjiženja za ovu godinu.", None))
            continue
        zajednicko, nerasporedjeno_zajednicko = pozicije(_zbir(*(k for c, k in salda.items() if c not in koeficijenti)))
        zp, zt = zajednicko[UKUPAN_PRIHOD], zajednicko[UKUPAN_RASHOD]
        stavke = {}
        for centar, koef in koeficijenti.items():
            iznosi, nerasporedjeno = pozicije(salda.get(centar, {}))
            udeo = koef / STO
            stavka = dict(iznosi)
            stavka.update(koef=koef, zp=zp * udeo, zt=zt * udeo, nerasporedjeno=nerasporedjeno,
                          zaposleni=broj_zaposlenih[godina][1].get(centar))
            stavka[UKUPAN_PRIHOD] += stavka["zp"]
            stavka["rezultat"] = stavka[UKUPAN_PRIHOD] - stavka[UKUPAN_RASHOD]
            stavka["ukupni_troskovi"] = stavka[UKUPAN_RASHOD] + stavka["zt"]
            stavka["dobit"] = stavka[UKUPAN_PRIHOD] - stavka["ukupni_troskovi"]
            stavke[centar] = stavka
        ukupno = {k: sum((s[k] for s in stavke.values()), NULA) for k in
                  [p.kod for p in POZICIJE] + [UKUPAN_PRIHOD, UKUPAN_RASHOD, "koef", "zp", "zt", "rezultat",
                                               "ukupni_troskovi", "dobit"]}
        ukupno["zaposleni"] = sum(s["zaposleni"] or 0 for s in stavke.values()) or None
        po_godini[godina] = {"centri": stavke, "ukupno": ukupno, "zp": zp, "zt": zt}
        zbir_koef = sum(koeficijenti.values(), NULA)
        if zbir_koef != STO:
            kontrole.append((str(godina), f"Zbir koeficijenata je {izvoz.prikaz(zbir_koef, 'procenat')}, a mora biti 100% — "
                                          "deo zajedničkih prihoda i troškova nije raspoređen.", False))
        else:
            firma, _ = pozicije(_zbir(*salda.values()))
            razlika = ukupno["dobit"] - (firma[UKUPAN_PRIHOD] - firma[UKUPAN_RASHOD])
            kontrole.append((str(godina), "Zbir centara posle raspodele − rezultat firme = "
                                          f"{izvoz.prikaz(razlika, 'iznos')}", abs(razlika) < Decimal("0.01")))
        svi = _zbir(nerasporedjeno_zajednicko, *(s["nerasporedjeno"] for s in stavke.values()))
        if svi:
            kontrole.append((str(godina), _opis_nerasporedjenih(svi), False))
    return {"godine": godine, "centri": centri, "po_godini": po_godini, "kontrole": kontrole}


def _opis_nerasporedjenih(konta):
    if not konta:
        return "Sva konta klasa 5 i 6 imaju poziciju."
    from .kontni_plan import nazivi_konta

    plan = nazivi_konta()
    return "Konta bez pozicije (nisu u izveštaju): " + ", ".join(
        f"{k} {plan.get(k, '')} ({izvoz.prikaz(v, 'iznos')})".replace("  ", " ") for k, v in sorted(konta.items()))


# --- tabele za ekran i izvoz -------------------------------------------------------------------------

JEDINICE = {"hiljade": (HILJADA, "u hiljadama dinara"), "dinari": (Decimal("1"), "u dinarima")}


@dataclass
class Kolona:
    grupa: str
    naslov: str
    vrsta: str = "iznos"  # iznos ili procenat

    @property
    def puni_naziv(self):
        return f"{self.grupa} · {self.naslov}"


def _red(rb, naziv, vrednosti, vrsta="stavka", format_=""):
    """Red tabele; `format_` („procenat”, „broj”) važi za ceo red i zamenjuje vrstu kolone."""
    return {"rb": rb, "naziv": naziv, "vrednosti": vrednosti, "vrsta": vrsta, "format": format_}


def _deli(iznos, delilac):
    return None if iznos is None else iznos / delilac


def _procenat(iznos, osnovica):
    return iznos / osnovica * STO if iznos is not None and osnovica else None


def _vrednost(iznosi, kod):
    if kod == "rezultat":
        return iznosi[UKUPAN_PRIHOD] - iznosi[UKUPAN_RASHOD]
    return iznosi.get(kod)


def _plan(plan, kod):
    if kod == "rezultat":
        return plan.get(UKUPAN_PRIHOD, NULA) - plan.get(UKUPAN_RASHOD, NULA)
    return plan.get(kod)


def tabela_firme(rezultat, jedinica):
    """Kolone i redovi izveštaja za celu firmu (kao list „izvestaj IMS”): po godini plan, ostvarenje, učešće, indeksi."""
    delilac = JEDINICE[jedinica][0]
    kolone, citaci, zaposleni_red = [], [], []
    prethodna = None
    for kol in rezultat["kolone"]:
        godina, iznosi = kol["godina"], kol["iznosi"]
        if iznosi is None:
            kolone.append(Kolona(str(godina), "Ostvareno"))
            citaci.append(lambda kod: None)
            zaposleni_red.append(None)
            prethodna = None
            continue
        plan, plan_period = kol["plan"], kol["plan_period"]
        if plan:
            kolone += [Kolona(f"Plan {godina}", "Godišnji"), Kolona(f"Plan {godina}", f"Za {rezultat['meseci']} mes.")]
            citaci += [lambda kod, p=plan: _deli(_plan(p, kod), delilac),
                       lambda kod, p=plan_period: _deli(_plan(p, kod), delilac)]
            zaposleni_red += [kol["plan_zaposlenih"], kol["plan_zaposlenih"]]
        kolone += [Kolona(str(godina), "Ostvareno"), Kolona(str(godina), "% učešća", "procenat")]
        citaci += [lambda kod, i=iznosi: _deli(_vrednost(i, kod), delilac),
                   lambda kod, i=iznosi: _procenat(_vrednost(i, kod), i[UKUPAN_PRIHOD])]
        zaposleni_red += [kol["zaposleni"][0], None]
        if plan:
            kolone.append(Kolona(str(godina), "Indeks / plan", "procenat"))
            citaci.append(lambda kod, i=iznosi, p=plan_period: _procenat(_vrednost(i, kod), _plan(p, kod)))
            zaposleni_red.append(None)
        if prethodna:
            kolone.append(Kolona(str(godina), f"Indeks / {godina - 1}", "procenat"))
            citaci.append(lambda kod, i=iznosi, r=prethodna: _procenat(_vrednost(i, kod), _vrednost(r, kod)))
            zaposleni_red.append(None)
        prethodna = iznosi
    redovi = [_red(p.broj, p.naziv, [c(p.kod) for c in citaci]) for p in PRIHODI]
    redovi.append(_red("I", "UKUPAN PRIHOD", [c(UKUPAN_PRIHOD) for c in citaci], "zbir"))
    redovi += [_red(p.broj, p.naziv, [c(p.kod) for c in citaci]) for p in RASHODI]
    redovi.append(_red("II", "UKUPAN RASHOD", [c(UKUPAN_RASHOD) for c in citaci], "zbir"))
    redovi.append(_red("III", "DOBITAK − GUBITAK (I − II)", [c("rezultat") for c in citaci], "zbir-glavni"))
    redovi.append(_red("IV", "BROJ ZAPOSLENIH", zaposleni_red, format_="broj"))
    return {"kolone": kolone, "redovi": redovi, "jedinica": JEDINICE[jedinica][1]}


NAZIV_IMS = "IMS – PC"


def tabela_centara(rezultat, jedinica):
    """Kolone i redovi izveštaja po profitnim centrima (kao list „izvestaj oj”): centar × godina, pa ukupno."""
    delilac = JEDINICE[jedinica][0]
    kolone, stavke = [], []
    for centar in rezultat["centri"] + [NAZIV_IMS]:
        for godina in rezultat["godine"]:
            podaci = rezultat["po_godini"].get(godina)
            stavka = None
            if podaci:
                stavka = podaci["ukupno"] if centar == NAZIV_IMS else podaci["centri"].get(centar)
            kolone.append(Kolona(NAZIV_IMS if centar == NAZIV_IMS else f"Centar {centar}", str(godina)))
            stavke.append(stavka)

    def red(rb, naziv, kljuc, vrsta="stavka", format_=""):
        deli = not format_
        return _red(rb, naziv, [None if s is None or s[kljuc] is None else (s[kljuc] / delilac if deli else s[kljuc])
                                for s in stavke], vrsta, format_)

    redovi = [red("", "Koeficijent raspodele (%)", "koef", format_="procenat"),
              red("", "Broj zaposlenih", "zaposleni", format_="broj"),
              _red("I", "PRIHODI", [], "zaglavlje"), red(0, "Zajednički prihodi (deo centra)", "zp")]
    redovi += [red(p.broj, p.naziv, p.kod) for p in PRIHODI]
    redovi.append(red("", "Ukupan prihod", UKUPAN_PRIHOD, "zbir"))
    redovi.append(_red("II", "TROŠKOVI CENTARA", [], "zaglavlje"))
    redovi += [red(p.broj, p.naziv, p.kod) for p in RASHODI]
    redovi += [red("", "Ukupan rashod", UKUPAN_RASHOD, "zbir"),
               red("", "Rezultat centra (prihod − rashod)", "rezultat", "zbir"),
               red("III", "ZAJEDNIČKI TROŠKOVI (deo centra)", "zt", "zbir"),
               red("IV", "UKUPNI TROŠKOVI (II + III)", "ukupni_troskovi", "zbir"),
               red("V", "DOBIT − GUBITAK (I − IV)", "dobit", "zbir-glavni")]
    return {"kolone": kolone, "redovi": redovi, "jedinica": JEDINICE[jedinica][1]}


def za_ekran(tabela):
    """Dodaje redovima ćelije za ekran: (tekst, negativan), formatirane kao u izvozu."""
    for red in tabela["redovi"]:
        red["celije"] = [(izvoz.prikaz(v, red["format"] or k.vrsta), v is not None and v < 0)
                         for k, v in zip(tabela["kolone"], red["vrednosti"])]
    return tabela


def zajednicko_tekst(rezultat, jedinica):
    delilac, _ = JEDINICE[jedinica]
    return [f"{godina}: zajednički prihodi {izvoz.prikaz(p['zp'] / delilac, 'iznos')}, zajednički troškovi "
            f"{izvoz.prikaz(p['zt'] / delilac, 'iznos')}" for godina, p in sorted(rezultat["po_godini"].items())]


NASLOVI = {"firma": "Prihodi i rashodi — Institut", "centri": "Prihodi i rashodi po profitnim centrima"}


def dokument(prikaz, tabela, opis_perioda, kontrole, dodatak=()):
    """Excel/PDF: ista tabela kao na ekranu (broj zaposlenih i koeficijent ostaju brojevi u koloni iznosa)."""
    kolone = [izvoz.Kolona("R.br."), izvoz.Kolona("Opis")] + [izvoz.Kolona(k.puni_naziv, k.vrsta) for k in tabela["kolone"]]
    redovi = [[str(red["rb"]), red["naziv"], *(red["vrednosti"] or [None] * len(tabela["kolone"]))]
              for red in tabela["redovi"]]
    napomena = (f"Iznosi {tabela['jedinica']}. Izvor: knjiženja Finansija (klase 5 i 6, bez početnog stanja i "
                "zatvaranja); pozicije po mapiranju konta za izveštaj nadzornom odboru.")
    filteri = " · ".join([*dodatak, *(f"{naslov}: {poruka}" for naslov, poruka, _ in kontrole)])
    return izvoz.Dokument(naslov=NASLOVI[prikaz], period=opis_perioda, napomena=napomena, filteri=filteri,
                          tabele=[izvoz.Tabela(NASLOVI[prikaz], kolone, redovi)])
