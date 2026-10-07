"""Pravila predaje radne liste (od 07.10.2026.).

- Red sa satima rada (redovan, prekovremeni, noćni, rad na praznik ili red bez izabrane vrste) mora da
  ima šifru posla — bez nje se lista ne može predati. Odsustva (bolovanje, godišnji, plaćeno odsustvo,
  državni i verski praznik) ne traže šifru.
- Topli obrok je obavezan pri predaji (broj dana, i 0 je odgovor); ako je veći od nule, traži šifru posla.
  Predlog je broj radnih dana sa kucanjem iz evidencije prolaza; zaposleni ga može promeniti.
- Datum na odštampanoj listi je prvi radni dan meseca u kome se lista predaje (mesec posle meseca liste).
"""
from datetime import date, timedelta

from .praznici import neradni_praznici

# Vrste odsustva: sati se ne vezuju za šifru posla.
ODSUSTVA = {"bolovanje", "godisnji_odmor", "placeno_odsustvo", "drzavni_i_verski_praznik"}


def ima_sate(cleaned_data, dana_u_mesecu):
    return any(cleaned_data.get(f"day_{dan}") for dan in range(1, dana_u_mesecu + 1))


def trazi_sifru(cleaned_data, dana_u_mesecu):
    """Red sa satima rada (ne odsustva) bez šifre posla."""
    vrsta = cleaned_data.get("work_category")
    if vrsta is not None and vrsta.code in ODSUSTVA:
        return False
    return ima_sate(cleaned_data, dana_u_mesecu) and not cleaned_data.get("organizational_unit")


def provera_predaje(header_form, line_formset, dana_u_mesecu):
    """Upisuje greške u forme ako lista ne može da se preda. Forme moraju biti već validne. Vraća True ako je sve u redu."""
    u_redu = True
    for forma in line_formset.forms:
        if trazi_sifru(forma.cleaned_data, dana_u_mesecu):
            forma.add_error("organizational_unit", "Unesite šifru posla za sate rada.")
            u_redu = False
    if not u_redu:
        line_formset._non_form_errors = line_formset.error_class(
            ["Lista nije predata: red sa satima rada mora da ima šifru posla."])
    if header_form.cleaned_data.get("meal_days") is None:
        header_form.add_error("meal_days", "Unesite broj dana za topli obrok (0 ako ga nema).")
        u_redu = False
    return u_redu


def dani_sa_kucanjem(redovi_prolaza):
    """Broj radnih dana (pon–pet, bez praznika) sa bar jednim prolazom — predlog za topli obrok."""
    return sum(1 for red in redovi_prolaza if red["passes"] and not red["is_weekend"] and not red["holiday"])


def prvi_radni_dan_predaje(godina, mesec):
    """Prvi radni dan meseca posle meseca radne liste (bez vikenda i neradnih praznika)."""
    dan = date(godina + (mesec == 12), mesec % 12 + 1, 1)
    praznici = neradni_praznici(dan.year)
    while dan.weekday() >= 5 or dan in praznici:
        dan += timedelta(days=1)
    return dan
