from decimal import Decimal

from ..models import JobCode, Kvar, KvarPart


def ensure_auto_parts(kvar: Kvar):
    """Autofill parts for mali/veliki servis ako nisu uneti."""
    if kvar.van_ims or kvar.parts.exists():
        return list(kvar.parts.all())

    parts_map = {
        Kvar.WorkType.MALI_SERVIS: [
            {"name": "Motorno ulje", "quantity": "5.0", "uom": "l"},
            {"name": "Filter ulja", "quantity": "1", "uom": "kom"},
            {"name": "Filter vazduha", "quantity": "1", "uom": "kom"},
            {"name": "Filter klime", "quantity": "1", "uom": "kom"},
            {"name": "Filter goriva", "quantity": "1", "uom": "kom"},
            {"name": "Svećice", "quantity": "4", "uom": "kom"},
            {"name": "WD sprej", "quantity": "1", "uom": "kom"},
        ],
        Kvar.WorkType.VELIKI_SERVIS: [
            {"name": "Motorno ulje", "quantity": "6.0", "uom": "l"},
            {"name": "Filter ulja", "quantity": "1", "uom": "kom"},
            {"name": "Filter vazduha", "quantity": "1", "uom": "kom"},
            {"name": "Filter klime", "quantity": "1", "uom": "kom"},
            {"name": "Vodena pumpa", "quantity": "1", "uom": "kom"},
            {"name": "PK kaiš komplet", "quantity": "1", "uom": "kom"},
            {"name": "PK kaiš i set zupčastog kaiša", "quantity": "1", "uom": "kom"},
            {"name": "G-12", "quantity": "2.0", "uom": "l"},
            {"name": "Diht masa", "quantity": "1", "uom": "kom"},
            {"name": "WD sprej", "quantity": "1", "uom": "kom"},
            {"name": "Svećice", "quantity": "4", "uom": "kom"},
            {"name": "Antifriz", "quantity": "2.0", "uom": "l"},
        ],
    }
    defaults = parts_map.get(kvar.work_type)
    if not defaults:
        return list(kvar.parts.all())

    objs = [
        KvarPart(
            kvar=kvar,
            name=item["name"],
            quantity=Decimal(str(item["quantity"])),
            uom=item["uom"],
        )
        for item in defaults
    ]
    KvarPart.objects.bulk_create(objs)
    return list(kvar.parts.all())


def get_vehicle_latest_organizational_unit(vehicle):
    latest_jobcode = (
        JobCode.objects.select_related("organizational_unit")
        .filter(vehicle=vehicle)
        .order_by("-assigned_date", "-id")
        .first()
    )
    return getattr(latest_jobcode, "organizational_unit", None)


def get_vehicle_center_code(vehicle):
    organizational_unit = get_vehicle_latest_organizational_unit(vehicle)
    if organizational_unit:
        return (getattr(organizational_unit, "center", "") or "").strip()
    return ""


def sifra_posla_vozila(vehicle):
    """Dodela sifre posla vozila za garazu: danasnja, a ako je nema — poslednja dodeljena.

    Na zahtevu u Nabavci sifra posla je automatski ova; Nabavka je po potrebi menja.
    """
    from django.utils import timezone

    dodele = (JobCode.objects.select_related("organizational_unit")
              .filter(vehicle=vehicle, organizational_unit__isnull=False).order_by("-assigned_date", "-id"))
    return dodele.filter(assigned_date__lte=timezone.localdate()).first() or dodele.first()


# --- Kilometraza na prijavi kvara (od 29.09.2026.) ---------------------------------------------
# Najveci realan dnevni predjeni put; veci skok od poslednjeg ocitavanja trazi potvrdu.
NAJVISE_KM_DNEVNO = 1000
NAJMANJI_DOZVOLJEN_SKOK_KM = 2000
NAJVECA_KILOMETRAZA = 3_000_000


def poslednja_kilometraza(vehicle, *, iskljuci_kvar=None, dan=None):
    """Poslednje poznato ocitavanje brojila vozila do `dan` (ukljucivo), ili None.

    Izvori su tocenja (NIS, OMV, ranija evidencija goriva), nalozi vozila (`vehicle_mileage`) i
    ranije prijave kvara istog vozila. Za isti dan uzima se najveca vrednost.
    Vraca dict: value (int), date, source.
    """
    from django.utils import timezone

    from .vehicle_mileage import mileage_readings

    dan = dan or timezone.localdate()
    po_vozilu, _ = mileage_readings([vehicle.pk], today=dan)
    ocitavanja = [dict(date=r["date"], value=int(r["value"]), source=r["source"]) for r in po_vozilu[vehicle.pk]]
    kvarovi = Kvar.objects.filter(vehicle=vehicle).exclude(pk=getattr(iskljuci_kvar, "pk", None))
    for k in kvarovi.only("kilometraza", "created_at", "rbz"):
        datum = timezone.localtime(k.created_at).date() if k.created_at else None
        if datum and datum <= dan and k.kilometraza:
            ocitavanja.append(dict(date=datum, value=int(k.kilometraza), source=f"prijava kvara {k.rbz or ''}".strip()))
    if not ocitavanja:
        return None
    return max(ocitavanja, key=lambda r: (r["date"], r["value"]))


def proveri_kilometrazu(vehicle, km, *, iskljuci_kvar=None, dan=None):
    """Lista upozorenja za unetu kilometrazu (prazna = u redu). Upozorenje se moze potvrditi."""
    from django.utils import timezone

    dan = dan or timezone.localdate()
    poslednja = poslednja_kilometraza(vehicle, iskljuci_kvar=iskljuci_kvar, dan=dan)
    if poslednja is None or km is None:
        return []
    opis = f"{poslednja['value']:,} km ({poslednja['date']:%d.%m.%Y.}, {poslednja['source']})".replace(",", ".")
    if km < poslednja["value"]:
        return [f"Kilometraža je manja od poslednjeg poznatog očitavanja: {opis}."]
    dana = max((dan - poslednja["date"]).days, 1)
    dozvoljeno = max(NAJMANJI_DOZVOLJEN_SKOK_KM, dana * NAJVISE_KM_DNEVNO)
    if km - poslednja["value"] > dozvoljeno:
        razlika = f"{km - poslednja['value']:,}".replace(",", ".")
        return [f"Kilometraža je za {razlika} km veća od poslednjeg poznatog očitavanja {opis} — to je više od "
                f"{NAJVISE_KM_DNEVNO} km dnevno."]
    return []


# --- Zahtev u Nabavci iz prijave kvara (od 29.09.2026.) ------------------------------------------
def aktivni_zahtevi(kvar):
    """Predmeti Nabavke formirani iz ove prijave koji nisu otkazani (najnoviji prvi)."""
    from nabavka.models import ProcurementCase

    return (ProcurementCase.objects.filter(garage_order=kvar).exclude(status=ProcurementCase.Status.CANCELLED)
            .order_by("-created_at", "-pk"))


def formiraj_zahtev(kvar, user):
    """Nacrt predmeta Nabavke iz prijave kvara, sa vozilom, nalogom garaze i delovima.

    Popravka u IMS garazi → Zahtev za nabavku (ZNG-…), van IMS-a → Zahtev za uslugu (ZUG-…).
    Sifra posla je automatski ona sa vozila (`sifra_posla_vozila`); Nabavka je po potrebi menja.
    Broj predmeta dodeljuje Nabavka pri cuvanju.
    Nabavka (Helena) nacrt potvrdjuje i dopunjuje. Vraca (predmet, nov) — postojeci aktivni
    predmet se ne pravi ponovo.
    """
    from django.core.exceptions import ValidationError
    from django.db import transaction
    from django.utils import timezone

    from nabavka.models import ProcurementCase, ProcurementItem, ProcurementStatusLog

    postojeci = aktivni_zahtevi(kvar).first()
    if postojeci:
        return postojeci, False
    vehicle = kvar.vehicle
    dodela = sifra_posla_vozila(vehicle)
    if dodela is None:
        raise ValidationError("Vozilo nema šifru posla, pa zahtev ne može dobiti broj. Dodelite vozilu šifru posla.")
    tip = ProcurementCase.CaseType.SERVICE if kvar.van_ims else ProcurementCase.CaseType.PROCUREMENT
    tablica = vehicle.traffic_cards.order_by("-issue_date", "-id").values_list("registration_number", flat=True).first()
    naslov = f"{kvar.get_work_type_display()} — {tablica or vehicle.chassis_number} {vehicle.brand} {vehicle.model}".strip()
    delovi = ensure_auto_parts(kvar) if not kvar.van_ims else list(kvar.parts.all())
    with transaction.atomic():
        predmet = ProcurementCase(
            case_type=tip, status=ProcurementCase.Status.DRAFT, title=naslov[:255],
            description=kvar.opis, note=kvar.napomena or None, is_garage=True, work_type=kvar.work_type,
            garage_order=kvar, vehicle=vehicle, job_code=dodela.organizational_unit,
            needed_by=timezone.localdate(), created_by=user, responsible=user,
        )
        predmet.save()
        ProcurementItem.objects.bulk_create([
            ProcurementItem(procurement_case=predmet, name=d.name, uom=d.uom or "kom", quantity=d.quantity)
            for d in delovi if d.name
        ])
        ProcurementStatusLog.objects.create(
            procurement_case=predmet, old_status=None, new_status=predmet.status, created_by=user,
            comment=f"Formiran iz Garaže, prijava kvara {kvar.rbz} ({kvar.kilometraza} km). Čeka potvrdu Nabavke.",
        )
    return predmet, True
