"""Povezivanje naucnih sifara sa ljudima iz Kadrova.

Naucna sifra je `3` + licni broj radnika (3 cifre) + broj projekta (odluka 25.09.2026.).
Veza se ne cuva, nego se izvodi iz pravila sifre, **samo po licnom broju**:

- `zaposlen` — radnik sa tim brojem je u Kadrovima i aktivan;
- `bivsi_u_kadrovima` — u Kadrovima je, ali neaktivan: vise nije zaposlen;
- `bivsi` — broja nema u Kadrovima: vise nije zaposlen (pravilo narucioca);
- `ne_poklapa` — broj postoji, ali se prezime iz Kadrova ne nalazi ni u jednoj sifri tog
  nosioca (npr. broj kasnije dat drugom radniku). Ostaje oznaceno; proveru radi Kadrovska;
- `zbirni` — nosioci 133, 233, 333 nisu radnici nego zbirne institutske teme.

Ime nosioca iz sifre uzima se iz korena (`3` + radnik + `00`), a bez njega iz naziva projekta
(„P190170-Vasic R." → „Vasic R.").
"""

import re
from collections import defaultdict

from organizacija.services import classification as klas

ZBIRNI = "Zbirne institutske teme"

# Oznake projekta i reci koje nisu ime: `P190170`, `P-42012`, `TD 7024`, `TR 6351B`, `ON 142041`,
# `Pr. DAAD`, `Projekat PROMIS`, „inst.finansiranje", „Ugovor o …".
_OZNAKA = re.compile(r"(?i)\b(?:projekat\s+[^\s-]+|pr\.\s*[^\s-]+|(?:p|td|tr|on)\s*-?\s*\d+[a-z]?)\b")
_NIJE_IME = re.compile(r"(?i)\b(?:dr|mr|projekat|ugovor|instit\w*|inst|finans\w*|o)\b\.?")
_KVACICE = str.maketrans("čćžšđČĆŽŠĐ", "cczsdCCZSD")


def bez_kvacica(tekst):
    return (tekst or "").translate(_KVACICE).lower()


def ime_iz_naziva(naziv):
    """„P190170-Vasic R." → „Vasic R."; „Ugovor o instit.finans. Susic Isidora" → „Susic Isidora"."""
    ostatak = _OZNAKA.sub(" ", naziv or "")
    ostatak = re.sub(r"\d+", " ", ostatak)
    ostatak = _NIJE_IME.sub(" ", ostatak)
    ime = " ".join(ostatak.replace("-", " ").split()).strip(" -").lstrip(".").strip()
    return ime if len(ime.replace(".", "")) > 1 else ""


def _ime_nosioca(sifre):
    koren = next((naziv for code, naziv in sifre if code[4:] == "00" and naziv), "")
    if koren:
        return ime_iz_naziva(koren) or koren
    return next((ime for ime in (ime_iz_naziva(naziv) for _, naziv in sifre) if ime), "")


def povezi(sifre_po_nazivu, kadrovi=None):
    """`{sifra: naziv}` → `{sifra: podaci o radniku}` za sve naucne sifre.

    `kadrovi` je lista radnika (za testove); bez nje se citaju iz Kadrova samo potrebni brojevi.
    """
    from hr.models import Employee

    po_nosiocu = defaultdict(list)
    for code, naziv in sifre_po_nazivu.items():
        if klas.je_nauka(code):
            po_nosiocu[code[1:4]].append((code, naziv or ""))
    if not po_nosiocu:
        return {}
    if kadrovi is None:
        brojevi = {int(b) for b in po_nosiocu if b not in klas.ZBIRNI_NOSIOCI_NAUKE}
        kadrovi = Employee.objects.filter(employee_code__in=brojevi)
    po_broju = {radnik.employee_code: radnik for radnik in kadrovi}

    rezultat = {}
    for broj, sifre in po_nosiocu.items():
        podaci = _nosilac(broj, sifre, po_broju)
        for code, _ in sifre:
            rezultat[code] = podaci
    return rezultat


def _nosilac(broj, sifre, po_broju):
    osnova = {"broj": int(broj), "pk": None, "ime": "", "u_sifri": _ime_nosioca(sifre)}
    if broj in klas.ZBIRNI_NOSIOCI_NAUKE:
        return dict(osnova, vrsta="zbirni", ime=ZBIRNI)
    radnik = po_broju.get(int(broj))
    if radnik is None:
        return dict(osnova, vrsta="bivsi", ime=osnova["u_sifri"])
    prezime = {d for d in re.split(r"[^a-z]+", bez_kvacica(radnik.last_name)) if len(d) > 1}
    potvrdjen = any(p in bez_kvacica(naziv) for p in prezime for _, naziv in sifre)
    if not potvrdjen:
        vrsta = "ne_poklapa"
    else:
        vrsta = "zaposlen" if radnik.is_active else "bivsi_u_kadrovima"
    return dict(osnova, vrsta=vrsta, pk=radnik.pk, ime=f"{radnik.last_name} {radnik.first_name}".strip())
