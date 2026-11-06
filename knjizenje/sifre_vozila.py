"""Knjiženje → Promene šifre posla vozila (od 06.11.2026.).

Za izabrani mesec: svaka dodela vozila šifri posla (`fleet.JobCode`) sa datumom u tom mesecu koja **menja** šifru —
prethodna i nova šifra, centar, i koliko je dana meseca vozilo bilo na kojoj. Dodela iste šifre kao prethodna nije
promena i ne prikazuje se; prva dodela vozila (bez prethodne) jeste i označena je. Pravilo važenja je isto kao u
Floti (`fleet/support/assignments.py`): važi poslednja dodela do tog dana, dodele bez jedinice se preskaču.

Obuhvat je obuhvat Flote (kao izveštaji o gorivu u ovom meniju): red se vidi ako je prethodna ili nova šifra u
obuhvatu korisnika.
"""
import calendar
import datetime
from dataclasses import dataclass
from typing import Optional

from django.utils import timezone

from core.models import OrganizationalUnit
from fleet.models import JobCode, TrafficCard, Vehicle
from fleet.support import obuhvat


@dataclass
class Promena:
    datum: datetime.date
    vozilo: Vehicle
    registracija: str
    stara: Optional[OrganizationalUnit]
    nova: OrganizationalUnit
    dana_stara: int
    dana_nova: int

    @property
    def promena_centra(self):
        return self.stara is not None and (self.stara.center or "").strip() != (self.nova.center or "").strip()


def mesec(tekst):
    """Prvi i poslednji dan meseca iz `GGGG-MM`; bez ispravne vrednosti — tekući mesec."""
    try:
        godina, broj = (int(d) for d in (tekst or "").strip().split("-"))
        prvi = datetime.date(godina, broj, 1)
    except (TypeError, ValueError):
        prvi = timezone.localdate().replace(day=1)
    return prvi, prvi.replace(day=calendar.monthrange(prvi.year, prvi.month)[1])


def _registracije(vozila):
    po_vozilu = {}
    for vozilo, izdata, broj in (TrafficCard.objects.filter(vehicle_id__in=vozila)
                                 .order_by("vehicle_id", "issue_date", "pk")
                                 .values_list("vehicle_id", "issue_date", "registration_number")):
        po_vozilu.setdefault(vozilo, []).append((izdata, broj))
    return po_vozilu


def _registracija(kartice, na_dan):
    """Tablica saobraćajne važeće na dan; ako je prva izdata kasnije — ta prva."""
    if not kartice:
        return ""
    vazece = [broj for izdata, broj in kartice if izdata <= na_dan]
    return vazece[-1] if vazece else kartice[0][1]


def promene(prvi, poslednji, user=None):
    """Promene šifre posla vozila sa datumom dodele od `prvi` do `poslednji`, po datumu i vozilu."""
    vozila = set(JobCode.objects.filter(assigned_date__range=(prvi, poslednji), organizational_unit__isnull=False,
                                        vehicle__isnull=False).values_list("vehicle_id", flat=True))
    if not vozila:
        return []
    dodele = {}
    for d in (JobCode.objects.filter(vehicle_id__in=vozila, organizational_unit__isnull=False, assigned_date__lte=poslednji)
              .select_related("organizational_unit", "vehicle").order_by("vehicle_id", "assigned_date", "pk")):
        dodele.setdefault(d.vehicle_id, []).append(d)
    kartice = _registracije(vozila)
    posle_kraja = poslednji + datetime.timedelta(days=1)

    redovi = []
    for vozilo_id, spisak in dodele.items():
        # Samo stvarne promene: dodela iste jedinice kao prethodna nastavlja isto razdoblje.
        razdoblja = []  # (od, jedinica)
        for d in spisak:
            if not razdoblja or razdoblja[-1][1].pk != d.organizational_unit_id:
                razdoblja.append((d.assigned_date, d.organizational_unit, d.vehicle))
        for i, (od, jedinica, vozilo) in enumerate(razdoblja):
            if od < prvi:
                continue
            prethodno = razdoblja[i - 1] if i else None
            sledece_od = razdoblja[i + 1][0] if i + 1 < len(razdoblja) else posle_kraja
            redovi.append(Promena(
                datum=od, vozilo=vozilo, registracija=_registracija(kartice.get(vozilo_id), od),
                stara=prethodno[1] if prethodno else None, nova=jedinica,
                dana_stara=(od - max(prethodno[0], prvi)).days if prethodno else 0,
                dana_nova=(sledece_od - od).days,
            ))

    if user is not None and obuhvat.aktivno(user):
        sifre = obuhvat.sifre(user)
        if sifre is not None:
            redovi = [r for r in redovi if (r.nova.code or "").strip() in sifre
                      or (r.stara is not None and (r.stara.code or "").strip() in sifre)]
    return sorted(redovi, key=lambda r: (r.datum, r.registracija, r.vozilo.pk))
