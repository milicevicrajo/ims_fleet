"""Stanje u magacinu (od 09.10.2026.): pregled pogleda `dbo.nbv_magacin` (IMS_ERP, alias `server_db`; samo čitanje).

Pogled je napravilo knjigovodstvo: jedan red po artiklu u magacinu i godini — ulaz i izlaz (količina i nabavna
vrednost) i magacinska cena. Stanje je ulaz − izlaz, i za količinu i za vrednost; ništa drugo se ne računa.
Kolone `popkol`, `revalzal`, `razliz`, `kolpon`, `cenapon` su u pogledu prazne, a vrednosti po VP ceni iste kao
nabavne (09.10.2026.), pa se ne prikazuju.
"""
from decimal import Decimal

from django.db import connections

NULA = Decimal("0.00")

SQL = """
    SELECT god, sif_mag, naz_mag, mesto, oj, sif_art, naz_art, sif_vrsart, naz_vrsart,
           kolul, koliz, vrulnab, vriznab, mag_cena
    FROM dbo.nbv_magacin
"""


def _tekst(v):
    return str(v).strip() if v is not None else ""


def _broj(v):
    return v if v is not None else NULA


def procitaj():
    """Svi redovi pogleda, sa stanjem (ulaz − izlaz)."""
    with connections["server_db"].cursor() as cursor:
        cursor.execute(SQL)
        redovi = cursor.fetchall()
    rezultat = []
    for god, sif_mag, naz_mag, mesto, oj, sif_art, naz_art, sif_vrsart, naz_vrsart, kolul, koliz, vrul, vriz, cena in redovi:
        kolul, koliz, vrul, vriz = _broj(kolul), _broj(koliz), _broj(vrul), _broj(vriz)
        rezultat.append({
            "godina": _tekst(god), "sif_mag": sif_mag, "magacin": _tekst(naz_mag), "mesto": _tekst(mesto), "oj": oj,
            "sifra": _tekst(sif_art), "naziv": _tekst(naz_art), "vrsta": _tekst(sif_vrsart), "naziv_vrste": _tekst(naz_vrsart),
            "ulaz": kolul, "izlaz": koliz, "stanje": kolul - koliz,
            "vrednost_ulaz": vrul, "vrednost_izlaz": vriz, "vrednost": vrul - vriz, "cena": _broj(cena),
        })
    return rezultat


def pregled(godina="", magacin="", vrsta="", stanje="sa_stanjem"):
    """Redovi po filterima i izbori za filtere. `stanje`: sa_stanjem (podrazumevano), nula ili sve."""
    svi = procitaj()
    godine = sorted({r["godina"] for r in svi}, reverse=True)
    godina = godina if godina in godine else (godine[0] if godine else "")
    u_godini = [r for r in svi if r["godina"] == godina]
    magacini = sorted({(r["sif_mag"], r["magacin"], r["mesto"]) for r in u_godini})
    vrste = sorted({(r["vrsta"], r["naziv_vrste"]) for r in u_godini})
    redovi = [r for r in u_godini
              if (not magacin or str(r["sif_mag"]) == magacin) and (not vrsta or r["vrsta"] == vrsta)
              and (stanje == "sve" or (stanje == "nula") == (r["stanje"] == 0))]
    redovi.sort(key=lambda r: (r["magacin"], r["naziv"], r["sifra"]))
    return {
        "redovi": redovi, "godine": godine, "magacini": magacini, "vrste": vrste,
        "filteri": {"godina": godina, "magacin": magacin, "vrsta": vrsta, "stanje": stanje},
        "ukupno": {"artikala": len(redovi), "vrednost": sum((r["vrednost"] for r in redovi), NULA),
                   "magacina": len({r["sif_mag"] for r in redovi})},
    }
