import logging
import re
from datetime import date, datetime

from django.db import connections

from fleet.models import Employee

logger = logging.getLogger(__name__)

TITLE_TOKENS = {"dr", "mr", "prof", "ing", "msc", "phd"}


def _normalize_part(part: str) -> str:
    part = part.strip()
    if not part:
        return ""
    lowered = part.lower()
    if lowered.endswith("ic"):
        lowered = lowered[:-2] + "ić"
    return lowered.capitalize()


def _normalize_full_name(full_name: str):
    if not full_name:
        return None, "", ""
    cleaned = " ".join(str(full_name).split())
    tokens = cleaned.split(" ")

    title = None
    if tokens:
        first_token = tokens[0].rstrip(".").lower()
        if first_token in TITLE_TOKENS:
            title = tokens.pop(0).rstrip(".")

    if not tokens:
        return title, "", ""

    if len(tokens) == 1:
        last_name = tokens[0]
        first_name = ""
    else:
        first_name = tokens[-1]
        last_name = " ".join(tokens[:-1])

    first_name = " ".join(_normalize_part(p) for p in first_name.split())
    last_name = " ".join(_normalize_part(p) for p in last_name.split())
    title = _normalize_part(title) if title else None

    return title, first_name, last_name


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return value


def _as_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def sync_employees_from_hr_view(using="test_db"):
    query = """
        SELECT
            rasif,
            ranaz,
            sif_sis,
            naz_sis,
            oj,
            pol,
            dat_rodj,
            dat_dolaska,
            mob_br,
            aktivan,
            matbr,
            partija,
            adresa,
            skola,
            sif_zan,
            naz_zan,
            sif_stat,
            naz_stat,
            slava
        FROM dbo.hr_employee
    """

    with connections[using].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    created = 0
    updated = 0
    updated_inactive = 0
    skipped_inactive = 0

    for row in rows:
        (
            rasif,
            ranaz,
            sif_sis,
            naz_sis,
            oj,
            pol,
            dat_rodj,
            dat_dolaska,
            mob_br,
            aktivan,
            matbr,
            partija,
            adresa,
            skola,
            sif_zan,
            naz_zan,
            sif_stat,
            naz_stat,
            slava,
        ) = row

        employee_code = _as_int(rasif)
        if employee_code is None:
            logger.warning("Preskačem zapis bez validne šifre zaposlenog: %s", rasif)
            continue

        title, first_name, last_name = _normalize_full_name(ranaz)
        is_active = str(aktivan).strip().upper() == "D"

        defaults = {
            "title": title,
            "first_name": first_name,
            "last_name": last_name,
            "position": _as_str(naz_sis) or "",
            "department_code": _as_int(oj) or 0,
            "org_unit_code": _as_str(oj),
            "system_code": _as_str(sif_sis),
            "system_name": _as_str(naz_sis),
            "gender": _as_str(pol) or "",
            "date_of_birth": _as_date(dat_rodj),
            "date_of_joining": _as_date(dat_dolaska),
            "phone_number": _as_str(mob_br),
            "mobile_phone": _as_str(mob_br),
            "is_active": is_active,
            "personal_number": _as_str(matbr),
            "account_number": _as_str(partija),
            "address": _as_str(adresa),
            "education": _as_str(skola),
            "job_code": _as_str(sif_zan),
            "job_title": _as_str(naz_zan),
            "status_code": _as_str(sif_stat),
            "status_name": _as_str(naz_stat),
            "slava": _as_str(slava),
        }

        if not is_active:
            existing = Employee.objects.filter(employee_code=employee_code).first()
            if existing:
                for key, value in defaults.items():
                    setattr(existing, key, value)
                existing.save()
                updated_inactive += 1
            else:
                skipped_inactive += 1
            continue

        employee, was_created = Employee.objects.update_or_create(
            employee_code=employee_code,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {
        "created": created,
        "updated": updated,
        "updated_inactive": updated_inactive,
        "skipped_inactive": skipped_inactive,
        "total": len(rows),
    }
