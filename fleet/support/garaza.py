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
            {"name": "SveÄ‡ice", "quantity": "4", "uom": "kom"},
            {"name": "WD sprej", "quantity": "1", "uom": "kom"},
        ],
        Kvar.WorkType.VELIKI_SERVIS: [
            {"name": "Motorno ulje", "quantity": "6.0", "uom": "l"},
            {"name": "Filter ulja", "quantity": "1", "uom": "kom"},
            {"name": "Filter vazduha", "quantity": "1", "uom": "kom"},
            {"name": "Filter klime", "quantity": "1", "uom": "kom"},
            {"name": "Vodena pumpa", "quantity": "1", "uom": "kom"},
            {"name": "PK kaiÅ¡ komplet", "quantity": "1", "uom": "kom"},
            {"name": "PK kaiÅ¡ i set zupÄastog kaiÅ¡a", "quantity": "1", "uom": "kom"},
            {"name": "G-12", "quantity": "2.0", "uom": "l"},
            {"name": "Diht masa", "quantity": "1", "uom": "kom"},
            {"name": "WD sprej", "quantity": "1", "uom": "kom"},
            {"name": "SveÄ‡ice", "quantity": "4", "uom": "kom"},
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
