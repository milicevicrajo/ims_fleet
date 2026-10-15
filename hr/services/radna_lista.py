"""Pravila predaje radne liste (od 07.10.2026.; od 09.10.2026. stroža, zbog CSV-a za obračun zarada).

- Svaki red sa satima mora da ima **vrstu rada / odsustva i šifru posla** — i odsustva, jer obračun zarada
  (CSV, `obracun_csv`) traži šifru posla za svaki element.
- **Fond sati**: zbir sati vrsta koje ulaze u fond (`FOND_VRSTE`: redovan rad, rad na praznik, godišnji odmor,
  bolovanje, plaćeno odsustvo, državni i verski praznik) mora biti broj radnih dana meseca (pon–pet, i praznici)
  × 8; za zaposlenog primljenog u toku meseca — od dana zaposlenja. Prekovremeni i noćni rad su dodaci, van fonda.
- Topli obrok je obavezan pri predaji (broj dana, i 0 je odgovor); ako je veći od nule, traži šifru posla.
- Isto pravilo proverava i sačuvanu listu (`kontrola_liste`) — pregled radnih lista i odobravanje.
  Predlog je broj radnih dana sa kucanjem iz evidencije prolaza; zaposleni ga može promeniti.
- Datum na odštampanoj listi je prvi radni dan meseca u kome se lista predaje (mesec posle meseca liste).
- Godišnji odmor (od 15.10.2026.): uz listu se prikazuje pravo (ukupno), iskorišćeno i preostalo (`stanja_godisnjeg`).
  Upis više dana nego što je preostalo je **upozorenje**, ne sprečava predaju ni odobravanje.
"""
import calendar
from collections import defaultdict
from datetime import date, timedelta

from .praznici import neradni_praznici

# Vrste odsustva (prikaz i predlog popunjavanja; od 09.10.2026. i one traže šifru posla).
ODSUSTVA = {"bolovanje", "godisnji_odmor", "placeno_odsustvo", "drzavni_i_verski_praznik"}
# Vrste čiji sati čine mesečni fond (radni dani × 8); prekovremeni i noćni rad su dodaci.
FOND_VRSTE = {"redovan_rad", "redovan_rad_na_drzavne_praznike"} | ODSUSTVA
SATI_DNEVNO = 8
GODISNJI_ODMOR = "godisnji_odmor"
# Neiskorišćeni deo odmora iz prethodne godine koristi se najkasnije do 30. juna (Zakon o radu).
PRENOS_DO_MESECA = 6


def fond_sati(godina, mesec, od=None):
    """Radni dani meseca (pon–pet, praznici se računaju — plaćaju se kao praznik) × 8, od dana `od` ako je u mesecu."""
    poslednji = calendar.monthrange(godina, mesec)[1]
    prvi = od.day if od and (od.year, od.month) == (godina, mesec) else 1
    if od and (od.year, od.month) > (godina, mesec):
        return 0
    return sum(1 for dan in range(prvi, poslednji + 1) if date(godina, mesec, dan).weekday() < 5) * SATI_DNEVNO


def _greske(redovi, meal_days, meal_sifra, fond):
    """Zajednička provera. `redovi`: (broj reda, oznaka vrste ili None, ima šifru posla, sati). Vraća
    (greške po redu {broj: [poruke]}, opšte greške [poruke], zbir sati fonda)."""
    po_redu, opste, zbir = {}, [], 0
    for broj, vrsta, ima_sifru, sati in redovi:
        if not sati:
            continue
        if not vrsta:
            po_redu.setdefault(broj, []).append("izaberite vrstu rada ili odsustva")
        if not ima_sifru:
            po_redu.setdefault(broj, []).append("unesite šifru posla")
        if vrsta is None or vrsta in FOND_VRSTE:
            zbir += sati
    if zbir != fond:
        opste.append(f"zbir sati rada i odsustva je {zbir}, a fond meseca je {fond} ({fond // SATI_DNEVNO} radnih dana × "
                     f"{SATI_DNEVNO}); prekovremeni i noćni rad se upisuju posebno")
    if meal_days is None:
        opste.append("unesite broj dana za topli obrok (0 ako ga nema)")
    elif meal_days and not meal_sifra:
        opste.append("topli obrok nema šifru posla")
    return po_redu, opste, zbir


def kontrola_liste(lista):
    """Greške sačuvane radne liste (pregled, odobravanje): lista poruka, prazna ako je lista u redu."""
    dana = calendar.monthrange(lista.year, lista.month)[1]
    redovi = [(red.line_number, red.work_category.code if red.work_category_id else None, bool(red.organizational_unit_id),
               sum(getattr(red, f"day_{d}") or 0 for d in range(1, dana + 1))) for red in lista.lines.all()]
    po_redu, opste, _ = _greske(redovi, lista.meal_days, lista.meal_organizational_unit_id,
                                fond_sati(lista.year, lista.month, lista.employee.date_of_joining))
    return [f"red {broj}: {', '.join(poruke)}" for broj, poruke in sorted(po_redu.items())] + opste


def _dani(sati):
    """Sati godišnjeg odmora u danima (8 h = 1 dan); nepun dan na jednu decimalu."""
    return sati // SATI_DNEVNO if sati % SATI_DNEVNO == 0 else round(sati / SATI_DNEVNO, 1)


def dani_godisnjeg_u_listi(lista):
    """Dani godišnjeg odmora upisani u sačuvanu radnu listu."""
    return _dani(sum(red.total_hours for red in lista.lines.all()
                     if red.work_category_id and red.work_category.code == GODISNJI_ODMOR))


def stanja_godisnjeg(zaposleni_ids, godina, mesec):
    """Stanje godišnjeg odmora za mesec radne liste, po zaposlenom (bez dodele u kadrovskoj bazi — nema ga u rečniku).

    Izvor su dodele (`Godmor`) i rešenja (`GodmorKor`) iz kadrovske baze. Pravo je dodela za godinu liste i, do 30. juna,
    ostatak iz prethodne godine. Iskorišćeno su dani po rešenjima **bez rešenja koja padaju u mesec liste** — te dane
    zaposleni upisuje u listu, pa se broje iz liste (`dani_godisnjeg_u_listi`), da se ne saberu dvaput.
    """
    from hr.models import AnnualLeaveAllowance, AnnualLeaveDecision

    prethodna = godina - 1 if mesec <= PRENOS_DO_MESECA else None
    godine = [g for g in (prethodna, godina) if g]
    prvi, poslednji = date(godina, mesec, 1), date(godina, mesec, calendar.monthrange(godina, mesec)[1])
    dodele = defaultdict(dict)
    for zaposleni, god, dana in (AnnualLeaveAllowance.objects.filter(employee_id__in=zaposleni_ids, source_present=True,
                                                                     year__in=godine)
                                 .values_list("employee_id", "year", "allocated_days")):
        dodele[zaposleni][god] = dana
    resenja = defaultdict(int)
    for zaposleni, god, dana in (AnnualLeaveDecision.objects.filter(employee_id__in=list(dodele), source_present=True,
                                                                    year__in=godine)
                                 .exclude(start_date__lte=poslednji, end_date__gte=prvi)
                                 .values_list("employee_id", "year", "approved_days")):
        resenja[(zaposleni, god)] += dana
    stanja = {}
    for zaposleni, po_godini in dodele.items():
        if godina not in po_godini:
            continue
        prenos = max(po_godini.get(prethodna, 0) - resenja[(zaposleni, prethodna)], 0) if prethodna else 0
        stanja[zaposleni] = {"godina": godina, "dodeljeno": po_godini[godina], "prenos": prenos, "prethodna": prethodna,
                             "ukupno": po_godini[godina] + prenos, "po_resenjima": resenja[(zaposleni, godina)],
                             "dostupno": po_godini[godina] + prenos - resenja[(zaposleni, godina)]}
    return stanja


def godisnji_odmor_liste(lista, stanja=None):
    """Stanje godišnjeg odmora sa danima iz ove liste (`u_listi`, `iskorisceno`, `preostalo`) i upozorenjem (ili None).
    `stanja` — već učitana `stanja_godisnjeg` (pregled svih lista); bez njih se čita za ovog zaposlenog."""
    if stanja is None:
        stanja = stanja_godisnjeg([lista.employee_id], lista.year, lista.month)
    stanje = stanja.get(lista.employee_id)
    u_listi = dani_godisnjeg_u_listi(lista)
    if stanje is None:
        upozorenje = (f"upisano {u_listi} dana godišnjeg odmora, a u kadrovskoj bazi nema dodele odmora za {lista.year}"
                      if u_listi else None)
        return {"ima_dodelu": False, "upozorenje": upozorenje, "u_listi": u_listi}
    preostalo = stanje["dostupno"] - u_listi
    upozorenje = (f"upisano {u_listi} dana godišnjeg odmora, a preostalo je {max(stanje['dostupno'], 0)}"
                  if u_listi and preostalo < 0 else None)
    return {**stanje, "ima_dodelu": True, "u_listi": u_listi, "iskorisceno": stanje["po_resenjima"] + u_listi,
            "preostalo": preostalo, "upozorenje": upozorenje}


def ima_sate(cleaned_data, dana_u_mesecu):
    return any(cleaned_data.get(f"day_{dan}") for dan in range(1, dana_u_mesecu + 1))


def provera_predaje(header_form, line_formset, dana_u_mesecu, godina, mesec, zaposlen_od=None):
    """Upisuje greške u forme ako lista ne može da se preda. Forme moraju biti već validne. Vraća True ako je sve u redu."""
    forme = {}
    redovi = []
    for i, forma in enumerate(line_formset.forms, start=1):
        if forma.cleaned_data.get("DELETE"):
            continue
        cd = forma.cleaned_data
        broj = cd.get("line_number") or getattr(forma.instance, "line_number", None) or i
        forme[broj] = forma
        vrsta = cd.get("work_category")
        redovi.append((broj, vrsta.code if vrsta else None, bool(cd.get("organizational_unit")),
                       sum(cd.get(f"day_{d}") or 0 for d in range(1, dana_u_mesecu + 1))))
    meal_days = header_form.cleaned_data.get("meal_days")
    po_redu, opste, _ = _greske(redovi, meal_days, header_form.cleaned_data.get("meal_organizational_unit"),
                                fond_sati(godina, mesec, zaposlen_od))
    for broj, poruke in po_redu.items():
        for poruka in poruke:
            polje = "organizational_unit" if "šifru" in poruka else "work_category"
            forme[broj].add_error(polje, poruka[0].upper() + poruka[1:] + ".")
    poruke = []
    if po_redu:
        poruke.append("Lista nije predata: svaki red sa satima mora da ima vrstu i šifru posla.")
    poruke += ["Lista nije predata: " + p + "." for p in opste if "topli obrok" not in p]
    if poruke:
        line_formset._non_form_errors = line_formset.error_class(poruke)
    if meal_days is None:
        header_form.add_error("meal_days", "Unesite broj dana za topli obrok (0 ako ga nema).")
    elif meal_days and not header_form.cleaned_data.get("meal_organizational_unit"):
        header_form.add_error("meal_organizational_unit", "Unesite šifru posla za topli obrok.")
    return not po_redu and not opste


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
