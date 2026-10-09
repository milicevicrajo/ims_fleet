"""CSV za učitavanje obračuna zarada iz radne liste (od 09.10.2026.).

Kolone kao u bazi zarada (knjigovodstvo ih učitava u `bazaldims`; aplikacija tamo ništa ne upisuje):
`sif_pred, god, mesec, br_obr, rasif, elsif, sati, sif_pos` — jedan red po elementu zarade i šifri posla.

Pravila:
- red radne liste: element = element vrste rada za vrstu primaoca radnika (`Elementi radne liste`, aktivan);
  red sa satima bez izabrane vrste računa se kao redovan rad (stare liste, pre obaveznog izbora vrste);
- topli obrok: broj dana × 8 sati na šifri toplog obroka (bez nje — podrazumevana šifra radnika);
- sati istog elementa i iste šifre posla se sabiraju; regres, minuli rad i terenski dodatak nisu u radnoj listi;
- red bez elementa (radnik bez vrste primaoca ili vrsta bez veze u šifrarniku) ne ulazi u CSV, nego u upozorenja.
"""
import csv
from collections import defaultdict

from hr.models import WorkTimeElement, WorkTimeSheet

ZAGLAVLJE = ["sif_pred", "god", "mesec", "br_obr", "rasif", "elsif", "sati", "sif_pos"]
SATI_TOPLOG_OBROKA = 8
REDOVAN_RAD = "redovan_rad"
TOPLI_OBROK = "topli_obrok"


def elementi():
    """(vrsta primaoca, oznaka vrste rada) → šifra elementa; više aktivnih — najniža šifra."""
    mapa = {}
    for primalac, vrsta, sifra in (WorkTimeElement.objects.filter(is_active=True, recipient_type__is_active=True)
                                   .order_by("payroll_code").values_list("recipient_type__code", "category__code", "payroll_code")):
        mapa.setdefault((primalac, vrsta), sifra)
    return mapa


def stavke(listove, br_obr, katalog=None):
    """Redovi CSV-a i upozorenja za radne liste (`WorkTimeSheet`); `katalog` — već učitani `elementi()` (za spisak)."""
    from hr.services.work_time_prefill import podrazumevana_sifra

    katalog = katalog if katalog is not None else elementi()
    redovi, upozorenja = [], []
    for lista in listove:
        radnik = lista.employee
        primalac = radnik.recipient_code or ""
        sati = defaultdict(int)

        def dodaj(vrsta, broj, sifra_posla, opis):
            element = katalog.get((primalac, vrsta))
            if element is None:
                upozorenja.append(f"{radnik.employee_code} {radnik}: {opis} ({broj} h) — nema elementa za vrstu primaoca "
                                  f"„{primalac or 'nije upisana'}”; nije u CSV-u.")
                return
            sati[(element, sifra_posla)] += broj

        for red in lista.lines.all():
            if not red.total_hours:
                continue
            vrsta = red.work_category.code if red.work_category_id else REDOVAN_RAD
            sifra = red.organizational_unit.code.strip() if red.organizational_unit_id else ""
            if not sifra:
                upozorenja.append(f"{radnik.employee_code} {radnik}: red {red.line_number} ({red.total_hours} h) nema šifru posla.")
            dodaj(vrsta, red.total_hours, sifra, f"red {red.line_number}")
        if lista.meal_days:
            jedinica = lista.meal_organizational_unit or podrazumevana_sifra(radnik)
            dodaj(TOPLI_OBROK, lista.meal_days * SATI_TOPLOG_OBROKA, jedinica.code.strip() if jedinica else "", "topli obrok")
        for (element, sifra_posla), broj in sorted(sati.items(), key=lambda s: (s[0][0], s[0][1])):
            redovi.append([radnik.preduzece, lista.year, lista.month, br_obr, radnik.employee_code, element, broj, sifra_posla])
    return redovi, upozorenja


def listovi(zaposleni):
    """Radne liste datih zaposlenih, sa svim što CSV čita."""
    return (WorkTimeSheet.objects.filter(employee__in=zaposleni)
            .select_related("employee", "meal_organizational_unit")
            .prefetch_related("lines__organizational_unit", "lines__work_category")
            .order_by("employee__employee_code"))


def listovi_meseca(zaposleni, godina, mesec):
    return listovi(zaposleni).filter(year=godina, month=mesec)


def upisi(response, redovi):
    """Isti oblik kao CSV obustava za obračun: UTF-8 sa BOM, `;`, CRLF."""
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";", lineterminator="\r\n")
    writer.writerow(ZAGLAVLJE)
    writer.writerows(redovi)
    return response
