"""Bruto bilans (od 29.10.2026.).

Izveštaj daje procedura `IMS_ERP.dbo.SPFINizv12` iz starog ERP-a, ista kao u Stanovom programu.
Procedura samo čita `nalog_z`, `konto`, `ob_jedin` i `preduzece` u IMS_ERP, a piše isključivo u
svoje privremene tabele (`#TKartica`, `#TKartica1`). Čita **lokalnu kopiju** `nalog_z`, koju
osvežava `sp_AzurirajNalogZ` (10:00 i 11:00), a ne izvor na PUTGEO-SERVER-u kao ostale Finansije.

Procedura uvek vraća pun konto; klasa (k1), grupa (k2) i sintetika (k3) su ovde zbir konta.
Kolone: početno stanje (nalozi POC), promet u periodu (bez POC), ukupno i saldo = ukupno duguje
− ukupno potražuje. Bilansna (tip 1) i vanbilansna evidencija (tip 2, klasa 8) se ne sabiraju.
"""
from datetime import datetime, time
from decimal import Decimal

from django.conf import settings
from django.db import connections

from . import izvoz

NIVOI = (("konto", "Konto"), ("k3", "Sintetika (3 cifre)"), ("k2", "Grupa (2 cifre)"), ("k1", "Klasa (1 cifra)"))
IZNOSI = ("dug0", "pot0", "dug1", "pot1", "dugu", "potu", "saldo")
NULA = Decimal("0")
KOLONE = [izvoz.Kolona("Konto"), izvoz.Kolona("Naziv"),
          izvoz.Kolona("Početno stanje – duguje", "iznos"), izvoz.Kolona("Početno stanje – potražuje", "iznos"),
          izvoz.Kolona("Promet u periodu – duguje", "iznos"), izvoz.Kolona("Promet u periodu – potražuje", "iznos"),
          izvoz.Kolona("Ukupno – duguje", "iznos"), izvoz.Kolona("Ukupno – potražuje", "iznos"),
          izvoz.Kolona("Saldo", "iznos")]


def tekst(vrednost):
    return " ".join(str(vrednost or "").split())


def izvrsi(godina, datum_od, datum_do, oj_od=None, oj_do=None, konto_od="", konto_do=""):
    """Redovi procedure po kontu; prazan OJ i konto znače „sve” (0 i '' kao u starom programu)."""
    with connections["server_db"].cursor() as cursor:
        cursor.execute("SET NOCOUNT ON; EXEC dbo.SPFINizv12 %s, %s, %s, %s, %s, %s, %s, %s",
                       [getattr(settings, "FINANSIJE_COMPANY", 1), str(godina),
                        datetime.combine(datum_od, time()), datetime.combine(datum_do, time()),
                        oj_od or 0, oj_do or 0, konto_od or "", konto_do or ""])
        while cursor.description is None:
            if not cursor.nextset():
                return []
        kolone = [opis[0] for opis in cursor.description]
        return [dict(zip(kolone, red)) for red in cursor.fetchall()]


def agregiraj(redovi, nivo):
    """[{naziv, stavke, zbir}] po vrsti evidencije; stavke su konta sabrana na izabrani nivo."""
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
            for kljuc in IZNOSI:
                stavka[kljuc] += red[kljuc] or NULA
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
                          napomena="Izvor: procedura SPFINizv12 nad lokalnom kopijom nalog_z u IMS_ERP.",
                          tabele=tabele)
