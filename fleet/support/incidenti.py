"""Incidenti (saobracajni prekrsaji i kazne): ko je vozio vozilo na dan prekrsaja.

Kazne stizu po tablici i datumu, pa forma incidenta predlaze vozaca iz zaduzenja vozila
(`VehicleTravelOrder`: otvoreno do tog dana, a nije zatvoreno pre njega) i putnih naloga
(`PutniNalog`: dan je u periodu putovanja, nalog nije storniran). Predlog je samo pomoc —
zaposlenog bira korisnik.
"""
import datetime

from fleet.models import PutniNalog, VehicleTravelOrder

# Putni nalog se trazi unazad najvise ovoliko dana (duzi nalozi su izuzetak).
NAJDUZI_NALOG_DANA = 60


def vozaci_na_dan(vozilo_id, dan):
    """Lista {id, ime, izvor} zaposlenih koji su imali vozilo tog dana, bez ponavljanja."""
    predlozi, vidjeni = [], set()

    def dodaj(zaposleni, izvor):
        if zaposleni is None or zaposleni.pk in vidjeni:
            return
        vidjeni.add(zaposleni.pk)
        predlozi.append({"id": zaposleni.pk, "ime": str(zaposleni), "izvor": izvor})

    zaduzenja = (VehicleTravelOrder.objects.select_related("employee")
                 .filter(vehicle_id=vozilo_id, created_at__lte=dan)
                 .exclude(closed_at__lt=dan).order_by("-created_at", "-pk"))
    for z in zaduzenja:
        dodaj(z.employee, f"zaduženje vozila od {z.created_at:%d.%m.%Y.}")

    nalozi = (PutniNalog.objects.select_related("employee")
              .filter(vehicle_id=vozilo_id, storniran=False, travel_date__lte=dan,
                      travel_date__gte=dan - datetime.timedelta(days=NAJDUZI_NALOG_DANA))
              .order_by("-travel_date", "-pk"))
    for n in nalozi:
        if dan < n.travel_date + datetime.timedelta(days=max(n.number_of_days or 1, 1)):
            dodaj(n.employee, f"putni nalog {n.travel_date:%d.%m.%Y.}")
    return predlozi
