"""Bruto bilans (od 29.10.2026.; od 30.10.2026. nad knjiženjima Finansija).

Pravila su ista kao u proceduri `SPFINizv12` iz Stankovog programa: početno stanje su nalozi POC,
promet u periodu su svi ostali nalozi, ukupno je zbir svih naloga u periodu (i POC), filteri po
OJ i rasponu konta; klasa 8 je vanbilansna evidencija (tip 2) i ne sabira se sa bilansnom.

Računa se nad `LedgerEntry` — istim knjiženjima kao ekran Konta, koja se iz izvora
(PUTGEO-SERVER.bazaims.dbo.nalog_z) preuzimaju svakog sata. Procedura radi nad lokalnom kopijom
`IMS_ERP.dbo.nalog_z`, a ona zadržava naloge obrisane u izvoru (npr. ON 300 od 30.04.2026: −75,4 mil.
na 52000) i kasni do osvežavanja u 10 i 11 h, pa je davala pogrešan bilans.

Saldo je za ovaj izveštaj dugovni ili potražni i uvek pozitivan: računa se za svaki konto posebno,
a na zbirnim nivoima (klasa, grupa, sintetika) dugovni i potražni salda se sabiraju odvojeno.
"""
from decimal import Decimal

from django.conf import settings
from django.db.models import Q, Sum

from finansije.models import LedgerEntry
from . import izvoz
from .kontni_plan import nazivi_konta

NIVOI = (("konto", "Konto"), ("k3", "Sintetika (3 cifre)"), ("k2", "Grupa (2 cifre)"), ("k1", "Klasa (1 cifra)"))
IZNOSI = ("dug0", "pot0", "dug1", "pot1", "dugu", "potu", "saldo_d", "saldo_p")
NULA = Decimal("0")
TIPOVI = {1: "BILANSNA AKTIVA I PASIVA", 2: "VANBILANSNA AKTIVA I PASIVA"}
KOLONE = [izvoz.Kolona("Konto"), izvoz.Kolona("Naziv"),
          izvoz.Kolona("Početno stanje – duguje", "iznos"), izvoz.Kolona("Početno stanje – potražuje", "iznos"),
          izvoz.Kolona("Promet u periodu – duguje", "iznos"), izvoz.Kolona("Promet u periodu – potražuje", "iznos"),
          izvoz.Kolona("Ukupno – duguje", "iznos"), izvoz.Kolona("Ukupno – potražuje", "iznos"),
          izvoz.Kolona("Saldo – duguje", "iznos"), izvoz.Kolona("Saldo – potražuje", "iznos")]


def tekst(vrednost):
    return " ".join(str(vrednost or "").split())


def izvrsi(godina, datum_od, datum_do, oj_od=None, oj_do=None, konto_od="", konto_do=""):
    """Redovi po kontu, u istom obliku kao rezultat procedure SPFINizv12; prazan OJ i konto znače „sve”."""
    knjizenja = LedgerEntry.objects.filter(company=getattr(settings, "FINANSIJE_COMPANY", 1), active=True, year=godina,
                                           booking_date__gte=datum_od, booking_date__lte=datum_do)
    if oj_od:
        knjizenja = knjizenja.filter(organizational_unit__gte=oj_od)
    if oj_do:
        knjizenja = knjizenja.filter(organizational_unit__lte=oj_do)
    if konto_od:
        knjizenja = knjizenja.filter(account__gte=konto_od)
    if konto_do:  # kao u proceduri: „5” znači do 599999, „52” do 529999
        knjizenja = knjizenja.filter(account__lte=konto_do.ljust(6, "9"))
    poc = Q(journal_type="POC")
    redovi = knjizenja.values("account").annotate(
        dug0=Sum("debit", filter=poc), pot0=Sum("credit", filter=poc),
        dug1=Sum("debit", filter=~poc), pot1=Sum("credit", filter=~poc),
        dugu=Sum("debit"), potu=Sum("credit")).order_by("account")
    plan = nazivi_konta()
    rezultat = []
    for red in redovi:
        knt = tekst(red["account"])
        iznosi = {k: red[k] or NULA for k in ("dug0", "pot0", "dug1", "pot1", "dugu", "potu")}
        if not any(iznosi.values()):
            continue
        tip = 2 if knt.startswith("8") else 1
        rezultat.append(dict(knt=knt, k1=knt[:1], k2=knt[:2], k3=knt[:3], naz_knt=plan.get(knt, ""),
                             naz_k1=plan.get(knt[:1], ""), naz_k2=plan.get(knt[:2], ""), naz_k3=plan.get(knt[:3], ""),
                             saldo=iznosi["dugu"] - iznosi["potu"], tip=tip, naz_tip=TIPOVI[tip], **iznosi))
    return rezultat


def agregiraj(redovi, nivo):
    """[{naziv, stavke, zbir}] po vrsti evidencije; stavke su konta sabrana na izabrani nivo.

    Saldo se deli na dugovni i potražni na nivou konta, pre sabiranja — dugovni saldo jednog konta
    ne prebija se sa potražnim saldom drugog konta iste grupe.
    """
    delovi = []
    for tip in sorted({red["tip"] for red in redovi}):
        grupe, naziv_dela = {}, ""
        for red in redovi:
            if red["tip"] != tip:
                continue
            naziv_dela = tekst(red["naz_tip"])
            sifra = tekst(red["knt" if nivo == "konto" else nivo])
            stavka = grupe.setdefault(sifra, {"konto": sifra, "naziv": tekst(red["naz_knt" if nivo == "konto" else f"naz_{nivo}"]),
                                              **{kljuc: NULA for kljuc in IZNOSI}})
            saldo = (red["dugu"] or NULA) - (red["potu"] or NULA)
            vrednosti = dict(red, saldo_d=max(saldo, NULA), saldo_p=max(-saldo, NULA))
            for kljuc in IZNOSI:
                stavka[kljuc] += vrednosti[kljuc] or NULA
        stavke = [grupe[sifra] for sifra in sorted(grupe)]
        delovi.append({"naziv": naziv_dela, "stavke": stavke,
                       "zbir": {kljuc: sum((s[kljuc] for s in stavke), NULA) for kljuc in IZNOSI}})
    return delovi


def opis_filtera(parametri):
    oj = (f"OJ {parametri['oj_od'] or 0}–{parametri['oj_do'] or 'poslednja'}"
          if parametri.get("oj_od") or parametri.get("oj_do") else "OJ: sve")
    konta = (f"konta {parametri['konto_od'] or 'od početka'}–{parametri['konto_do'] or 'do kraja'}"
             if parametri.get("konto_od") or parametri.get("konto_do") else "konta: sva")
    return f"Godina {parametri['godina']} · {oj} · {konta} · nivo: {dict(NIVOI)[parametri['nivo']]}"


def dokument(delovi, parametri):
    tabele = [izvoz.Tabela(deo["naziv"], KOLONE,
                           [[s["konto"], s["naziv"], *(s[k] for k in IZNOSI)] for s in deo["stavke"]],
                           zbir=["Svega", "", *(deo["zbir"][k] for k in IZNOSI)])
              for deo in delovi]
    return izvoz.Dokument(naslov="Bruto bilans", period=izvoz.period_tekst(parametri["datum_od"], parametri["datum_do"]),
                          filteri=opis_filtera(parametri),
                          napomena="Izvor: knjiženja Finansija (iz Stankovog programa, osvežavanje svakog sata), "
                                   "po pravilima procedure SPFINizv12.",
                          tabele=tabele)
