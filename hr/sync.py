import logging
import re
from datetime import date, datetime

from django.conf import settings
from django.db import connections

from .models import Employee

logger = logging.getLogger(__name__)

TITLE_TOKENS = {"dr", "mr", "prof", "ing", "msc", "phd"}
LOCKED_HR_IDENTITY_FIELDS = ("title", "original_full_name", "first_name", "last_name", "gender")


def _preserve_locked_identity_fields(employee, defaults):
    if not employee or not employee.skip_hr_identity_update:
        return defaults
    for field_name in LOCKED_HR_IDENTITY_FIELDS:
        defaults[field_name] = getattr(employee, field_name)
    return defaults


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

    title = None
    title_match = re.match(r"^(dr|mr|prof|ing|msc|phd)\.?\s*", cleaned, flags=re.IGNORECASE)
    if title_match:
        title = title_match.group(1)
        cleaned = cleaned[title_match.end():].strip()

    raw_tokens = [t for t in cleaned.split(" ") if t]
    if title is None:
        for raw in raw_tokens:
            token_key = raw.rstrip(".").lower()
            if token_key in TITLE_TOKENS:
                title = token_key
                break

    tokens = [t for t in raw_tokens if t and t.rstrip(".").lower() not in TITLE_TOKENS]

    if not tokens:
        return title, "", ""

    if len(tokens) == 1:
        last_name = tokens[0]
        first_name = ""
    else:
        first_name = tokens[-1]
        last_name = " ".join(tokens[:-1])

    first_name = " ".join(_normalize_part(p) for p in first_name.split())
    last_name = " ".join(_normalize_part(p) for p in last_name.replace("-", " ").split())
    title = title.lower() if title else None

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


def _normalize_residence_municipality(value):
    value = _as_str(value)
    if value is None:
        return None
    return " ".join(value.split()).upper()


def _resolve_hr_db_alias(preferred=None):
    if preferred:
        return preferred
    configured = set(getattr(settings, "DATABASES", {}).keys())
    if "default" in configured:
        return "default"
    if "server_db" in configured:
        return "server_db"
    return next(iter(configured))


def _hr_employee_columns(cursor):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = 'hr_employee'
        """
    )
    return {str(row[0]).lower(): str(row[0]) for row in cursor.fetchall()}


def _optional_column(columns, candidates, alias):
    for candidate in candidates:
        column = columns.get(candidate.lower())
        if column:
            return f"[{column}] AS {alias}", True
    return f"CAST(NULL AS nvarchar(255)) AS {alias}", False


def sync_employees_from_hr_view(using=None):
    using = _resolve_hr_db_alias(using)

    with connections[using].cursor() as cursor:
        columns = _hr_employee_columns(cursor)

    residence_municipality_expr, has_residence_municipality_source = _optional_column(
        columns,
        [
            "naz_ops",
            "opstina_boravka",
            "opstina",
            "opstina_stanovanja",
            "opstina_prebivalista",
            "municipality",
            "residence_municipality",
        ],
        "opstina_boravka",
    )

    query = f"""
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
            {residence_municipality_expr},
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
    skipped_invalid_code = 0

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
            opstina_boravka,
            skola,
            sif_zan,
            naz_zan,
            sif_stat,
            naz_stat,
            slava,
        ) = row

        employee_code = _as_int(rasif)
        if employee_code is None:
            skipped_invalid_code += 1
            logger.debug("Preskacem zapis bez validne sifre zaposlenog: %s", rasif)
            continue

        title, first_name, last_name = _normalize_full_name(ranaz)
        is_active = str(aktivan).strip().upper() == "D"

        defaults = {
            "title": title,
            "original_full_name": _as_str(ranaz) or "",
            "first_name": first_name,
            "last_name": last_name,
            "display_first_name_override": "",
            "display_last_name_override": "",
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
        if has_residence_municipality_source:
            defaults["residence_municipality"] = _normalize_residence_municipality(opstina_boravka)

        existing = Employee.objects.filter(employee_code=employee_code).first()
        if existing:
            defaults["display_first_name_override"] = existing.display_first_name_override or ""
            defaults["display_last_name_override"] = existing.display_last_name_override or ""
        _preserve_locked_identity_fields(existing, defaults)

        if not is_active:
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
        "skipped_invalid_code": skipped_invalid_code,
        "total": len(rows),
    }
