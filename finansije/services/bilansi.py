"""Bilans stanja i Bilans uspeha (od 30.10.2026.) nad knjiženjima Finansija, po obrascu iz `bilansi_obrazac`.

Pravila (potvrdile finansije 30.10.2026., provereno na probnom bilansu programa SMS za 2022: sve pozicije
bez „deo” konta slažu se do dinara):

* Bilans stanja na dan: sva knjiženja godine do tog dana, uključujući POC, ZAT i zaključni nalog. Dok godina
  nije zaključena, saldo klasa 5–7 je rezultat tekuće godine i ide na 0410 (dobitak) ili 0414 (gubitak).
* Bilans uspeha za period: klase 5 i 6 bez početnog stanja i bez zatvaranja (ZAT i prenosi 59900/69900, kao u
  ostalim izveštajima Finansija). Porez na dobit knjiži se u zaključnom nalogu zajedno sa zatvaranjem klase 7,
  pa se ne čita iz salda: 1051 je dugovni promet 721, 1054 dugovni promet 723, a odloženi porez (1052/1053) je
  promet konta 498 i 288 u nalozima koji knjiže 722.
* Iznos stavke je saldo konta na strani pozicije; parovi dobitak/gubitak i kapital (0401/0455) nikad nisu
  negativni (negativan iznos je 0, a razlika se vidi na drugoj poziciji para). Stavka sa saldom na suprotnoj
  strani ostaje negativna, zajedno sa zbirom iznad nje, i prikazuje se kao upozorenje — u zvaničnom bilansu
  takav saldo se prekvalifikuje (npr. preplaćen porez na dobit na 0046), a ovde se ne prepravlja.
"""
import re
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db.models import Q, Sum

from finansije.models import LedgerEntry
from . import izvoz
from .bilansi_obrazac import NAPOMENE, NENEGATIVNE, POZICIJE
from .kontni_plan import nazivi_konta
from .reports import CLOSING_POSTINGS

NULA = Decimal("0")
NAZIVI = {"BS": "Bilans stanja", "BU": "Bilans uspeha"}
# Konta koja ulaze u izveštaj; ostala se ne raspoređuju (klasa 9 je obračun troškova).
KLASE = {"BS": "012348", "BU": "56"}
# Rezultat nezaključene godine i porez iz zaključnog naloga ulaze kao konta sa posebnom oznakom.
DOBITAK_TEKUCE, GUBITAK_TEKUCE = "341-R", "351-R"
POSEBNA_KONTA = {DOBITAK_TEKUCE: "Rezultat tekuće godine (klase 5–7, godina nije zaključena)",
                 GUBITAK_TEKUCE: "Rezultat tekuće godine (klase 5–7, godina nije zaključena)",
                 "721": "Porez na dobit – dugovni promet 721", "722": "Odloženi porez – promet 498 i 288 uz 722",
                 "723": "Lična primanja poslodavcu – dugovni promet 723"}


def _pozicije(izvestaj):
    return [p for p in POZICIJE if p.izvestaj == izvestaj]


def pravila(izvestaj):
    """[(početak konta, uslov, pozicija)]: uslov je "" (uvek), "d" (dugovni saldo) ili "p" (potražni saldo)."""
    rezultat = []
    for p in _pozicije(izvestaj):
        for oznaka in p.konta.split():
            uslov = oznaka[-1] if oznaka[-1] in "dp" else ""
            rezultat.append((oznaka.rstrip("dp"), uslov, p))
    return rezultat


def rasporedi(konto, saldo, pravila_izvestaja):
    """Pozicije na koje ide konto: najduži početak konta koji odgovara (par dobitak/gubitak dobija obe)."""
    moguce = [(pocetak, p) for pocetak, uslov, p in pravila_izvestaja if konto.startswith(pocetak)
              and (not uslov or (uslov == "d" and saldo > 0) or (uslov == "p" and saldo < 0))]
    if not moguce:
        return []
    najduzi = max(len(pocetak) for pocetak, _ in moguce)
    return [p for pocetak, p in moguce if len(pocetak) == najduzi]


def izracunaj(izvestaj, salda):
    """Iznosi pozicija iz salda konta ({konto: duguje − potražuje}).

    Vraća {"iznosi": {aop: iznos}, "konta": {aop: [(konto, iznos)]}, "nerasporedjeno": {konto: saldo}}.
    """
    pozicije = {p.aop: p for p in _pozicije(izvestaj)}
    pravila_izvestaja = pravila(izvestaj)
    iznosi = {aop: NULA for aop, p in pozicije.items() if not p.formula}
    po_kontima = {aop: [] for aop in pozicije}
    nerasporedjeno = {}
    for konto, saldo in sorted(salda.items()):
        if not saldo:
            continue
        cilj = rasporedi(konto, saldo, pravila_izvestaja)
        if not cilj:
            nerasporedjeno[konto] = saldo
        for p in cilj:
            iznos = saldo if p.strana == "D" else -saldo
            iznosi[p.aop] += iznos
            po_kontima[p.aop].append((konto, iznos))
    for aop in NENEGATIVNE & set(iznosi):
        iznosi[aop] = max(iznosi[aop], NULA)

    def vrednost(aop):
        if aop not in iznosi:
            ukupno = sum((vrednost(ref) if znak == "+" else -vrednost(ref)
                          for znak, ref in re.findall(r"([+-])(\d{4})", pozicije[aop].formula)), NULA)
            iznosi[aop] = max(ukupno, NULA) if aop in NENEGATIVNE else ukupno
        return iznosi[aop]

    for aop in pozicije:
        vrednost(aop)
    return {"iznosi": iznosi, "konta": po_kontima, "nerasporedjeno": nerasporedjeno}


# --- salda iz knjiženja --------------------------------------------------------------------------

def _knjizenja():
    return LedgerEntry.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1), active=True)


def _salda(knjizenja):
    salda = {}
    for red in knjizenja.values("account").annotate(d=Sum("debit"), p=Sum("credit")):
        konto = red["account"].strip()
        salda[konto] = salda.get(konto, NULA) + (red["d"] or NULA) - (red["p"] or NULA)
    return salda


def ima_godinu(godina):
    return _knjizenja().filter(year=godina).exists()


def salda_stanja(na_dan):
    """{konto: saldo} za Bilans stanja na dan; None ako za tu godinu nema knjiženja.

    Za 31.12. godine koja nije preuzeta koristi se početno stanje naredne godine (isti saldo posle zaključka).
    """
    if ima_godinu(na_dan.year):
        sva = _salda(_knjizenja().filter(year=na_dan.year, booking_date__lte=na_dan))
    elif (na_dan.month, na_dan.day) == (12, 31) and _knjizenja().filter(year=na_dan.year + 1, journal_type="POC").exists():
        sva = _salda(_knjizenja().filter(year=na_dan.year + 1, journal_type="POC"))
    else:
        return None
    salda = {k: v for k, v in sva.items() if k[:1] in KLASE["BS"]}
    rezultat = sum((v for k, v in sva.items() if k[:1] in "567"), NULA)
    if rezultat < 0:
        salda[DOBITAK_TEKUCE] = rezultat
    elif rezultat > 0:
        salda[GUBITAK_TEKUCE] = rezultat
    return salda


def salda_uspeha(datum_od, datum_do):
    """{konto: saldo} za Bilans uspeha u periodu (jedna godina); None ako za godinu nema knjiženja."""
    if not ima_godinu(datum_od.year):
        return None
    period = _knjizenja().filter(year=datum_od.year, booking_date__gte=datum_od, booking_date__lte=datum_do) \
                         .exclude(journal_type="POC")
    salda = _salda(period.exclude(CLOSING_POSTINGS).filter(Q(account__startswith="5") | Q(account__startswith="6")))
    for konto in ("721", "723"):
        salda[konto] = period.filter(account__startswith=konto).aggregate(s=Sum("debit"))["s"] or NULA
    nalozi = set(period.filter(account__startswith="722").values_list("journal_type", "journal_number"))
    if nalozi:
        u_nalozima = Q()
        for vrsta, broj in nalozi:
            u_nalozima |= Q(journal_type=vrsta, journal_number=broj)
        odlozeni = period.filter(u_nalozima).filter(Q(account__startswith="498") | Q(account__startswith="288")) \
                         .aggregate(d=Sum("debit"), p=Sum("credit"))
        # Rashod (D 722) je potražna strana 498/288, prihod (P 722) dugovna.
        salda["722"] = (odlozeni["p"] or NULA) - (odlozeni["d"] or NULA)
    return salda


# --- izveštaj -------------------------------------------------------------------------------------

def opis_konta(konta):
    """„330, 331 (P)”: početak konta, a uslov salda u zagradi."""
    return ", ".join(f"{k[:-1]} ({k[-1].upper()})" if k[-1] in "dp" else k for k in konta.split())


def kolone(izvestaj, parametri):
    """[(naslov kolone, salda ili None)] — tekuća i uporedna kolona."""
    if izvestaj == "BS":
        na_dan = parametri["na_dan"]
        prethodni = date(na_dan.year - 1, 12, 31)
        return [(f"Na dan {na_dan:%d.%m.%Y.}", salda_stanja(na_dan)), (f"Na dan {prethodni:%d.%m.%Y.}", salda_stanja(prethodni))]
    od, do = parametri["datum_od"], parametri["datum_do"]
    try:
        od_ranije, do_ranije = od.replace(year=od.year - 1), do.replace(year=do.year - 1)
    except ValueError:  # 29.02.
        od_ranije, do_ranije = od.replace(year=od.year - 1, day=28), do.replace(year=do.year - 1, day=28)
    return [(f"{od:%d.%m.%Y.} – {do:%d.%m.%Y.}", salda_uspeha(od, do)),
            (f"{od_ranije:%d.%m.%Y.} – {do_ranije:%d.%m.%Y.}", salda_uspeha(od_ranije, do_ranije))]


def izradi(izvestaj, parametri):
    """Redovi obrasca sa iznosima po kolonama i kontrole."""
    plan = nazivi_konta()
    zaglavlja, rezultati = [], []
    for naslov, salda in kolone(izvestaj, parametri):
        zaglavlja.append(naslov)
        rezultati.append(izracunaj(izvestaj, salda) if salda is not None else None)
    redovi = []
    for p in _pozicije(izvestaj):
        iznosi = [r["iznosi"][p.aop] if r else None for r in rezultati]
        konta = [(k, POSEBNA_KONTA.get(k) or plan.get(k, ""), iznos) for k, iznos in rezultati[0]["konta"][p.aop]] if rezultati[0] else []
        redovi.append({"aop": p.aop, "naziv": p.naziv, "nivo": p.nivo, "zbir": bool(p.formula), "zaglavlje": p.zaglavlje,
                       "grupa_racuna": opis_konta(p.konta), "iznosi": iznosi, "konta": konta,
                       "negativan": any(i is not None and i < 0 for i in iznosi)})
    return {"izvestaj": izvestaj, "naslov": NAZIVI[izvestaj], "kolone": zaglavlja, "redovi": redovi,
            "kontrole": kontrole(izvestaj, zaglavlja, rezultati, plan)}


def _delovi(izvestaj, aop):
    """AOP pozicije iz formule zbira (za zbir koji je negativan samo zbog svoje stavke)."""
    p = next(p for p in _pozicije(izvestaj) if p.aop == aop)
    return re.findall(r"\d{4}", p.formula)


def kontrole(izvestaj, zaglavlja, rezultati, plan):
    """[(naslov, poruka, u_redu)] po koloni."""
    stavke = []
    for naslov, r in zip(zaglavlja, rezultati):
        if r is None:
            stavke.append((naslov, "Nema preuzetih knjiženja za ovaj period.", None))
            continue
        i = r["iznosi"]
        if izvestaj == "BS":
            razlika = i["0059"] - i["0456"]
            stavke.append((naslov, f"Aktiva (0059) − pasiva (0456) = {izvoz.prikaz(razlika, 'iznos')}", not razlika))
            razlika = i["0060"] - i["0457"]
            stavke.append((naslov, f"Vanbilansna aktiva (0060) − pasiva (0457) = {izvoz.prikaz(razlika, 'iznos')}", not razlika))
        else:
            neto = i["1055"] - i["1056"]
            stavke.append((naslov, f"Neto rezultat (1055 − 1056) = {izvoz.prikaz(neto, 'iznos')}", True))
        negativne = [aop for aop, iznos in i.items() if iznos < 0 and not any(i[d] < 0 for d in _delovi(izvestaj, aop))]
        if negativne:
            stavke.append((naslov, "Saldo na suprotnoj strani (za prekvalifikaciju): " + ", ".join(
                f"{aop} ({izvoz.prikaz(i[aop], 'iznos')})" for aop in sorted(negativne)), False))
        if r["nerasporedjeno"]:
            spisak = ", ".join(f"{k} {plan.get(k, '')} ({izvoz.prikaz(v, 'iznos')})".replace("  ", " ")
                               for k, v in r["nerasporedjeno"].items())
            stavke.append((naslov, f"Konta bez pozicije u obrascu: {spisak}", False))
    return stavke


STRANE = {"D": "duguje − potražuje", "P": "potražuje − duguje"}
USLOVI = {"d": "samo dugovni saldo", "p": "samo potražni saldo"}


def metodologija(izvestaj):
    """Pozicije obrasca za ekran Metodologija: konta, strana salda, formula i napomena."""
    redovi = []
    for p in _pozicije(izvestaj):
        redovi.append({
            "aop": p.aop, "naziv": p.naziv, "nivo": p.nivo, "zaglavlje": p.zaglavlje,
            "konta": [(k.rstrip("dp"), USLOVI.get(k[-1], "")) for k in p.konta.split()],
            "strana": STRANE[p.strana] if p.konta else "",
            "formula": [("+" if znak == "+" else "−", ref) for znak, ref in re.findall(r"([+-])(\d{4})", p.formula)],
            "nenegativna": p.aop in NENEGATIVNE, "napomena": NAPOMENE.get(p.aop, ""),
        })
    return redovi


KOLONE_IZVOZA = [izvoz.Kolona("Grupa računa, račun"), izvoz.Kolona("Pozicija"), izvoz.Kolona("AOP")]


def dokument(rezultat, opis_perioda):
    kolone_izvoza = KOLONE_IZVOZA + [izvoz.Kolona(naslov, "iznos") for naslov in rezultat["kolone"]]
    redovi = []
    for red in rezultat["redovi"]:
        if red["zaglavlje"]:
            redovi.append(["", red["zaglavlje"], "", *[None] * len(rezultat["kolone"])])
        redovi.append([red["grupa_racuna"], red["naziv"], red["aop"], *red["iznosi"]])
    napomena = "Izvor: knjiženja Finansija (iz Stankovog programa, osvežavanje svakog sata), obrazac za privredna društva."
    kontrole_tekst = " · ".join(f"{naslov}: {poruka}" for naslov, poruka, _ in rezultat["kontrole"])
    return izvoz.Dokument(naslov=rezultat["naslov"], period=opis_perioda, napomena=napomena, filteri=kontrole_tekst,
                          tabele=[izvoz.Tabela(rezultat["naslov"], kolone_izvoza, redovi)])
