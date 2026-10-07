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
    recipient_code_expr, has_recipient_code = _optional_column(columns, ["sif_prim"], "recipient_code")
    recipient_name_expr, has_recipient_name = _optional_column(columns, ["naz_prim"], "recipient_name")

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
            slava,
            {recipient_code_expr},
            {recipient_name_expr}
        FROM dbo.hr_employee
    """

    with connections[using].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    from hr.models import Osoba
    from hr.services.osobe import PRIKAZ_POLJA, jmbg, osvezi_osobu, osvezi_staz, povezi_osobu

    counts = dict(created=0, updated=0, updated_inactive=0, skipped_inactive=0, skipped_invalid_code=0,
                  created_inactive=0, duplicate_rows=0, conflicting_rows=0, company_conflicts=0, missing_in_source=0)

    # Pogled `dbo.hr_employee` (od 06.10.2026.) vraća svaki red dvaput: identični redovi se računaju jednom.
    # Različiti redovi za isti broj radnika su sukob — taj broj se preskače, ništa se ne prepisuje.
    po_broju = {}
    for row in rows:
        employee_code = _as_int(row[0])
        if employee_code is None:
            counts["skipped_invalid_code"] += 1
            logger.debug("Preskacem zapis bez validne sifre zaposlenog: %s", row[0])
            continue
        po_broju.setdefault(employee_code, []).append(tuple(row))

    # Pogled nema preduzeće; broj radnika je jedinstven samo unutar preduzeća (izvor `radnik`).
    preduzeca = preduzeca_radnika(using)
    za_obradu = []
    for employee_code, grupa in po_broju.items():
        jedinstveni = list(dict.fromkeys(grupa))
        counts["duplicate_rows"] += len(grupa) - len(jedinstveni)
        if len(jedinstveni) > 1:
            counts["conflicting_rows"] += 1
            logger.warning("HR sync: broj radnika %s ima razlicite redove u pogledu, preskacem", employee_code)
            continue
        preduzece = {p for p, _ in preduzeca.get(employee_code, ())}
        if len(preduzece) > 1:
            counts["company_conflicts"] += 1
            logger.warning("HR sync: broj radnika %s postoji u oba preduzeca, preskacem", employee_code)
            continue
        za_obradu.append((employee_code, next(iter(preduzece), None), jedinstveni[0]))
    # Aktivni prvo: neaktivan broj se uvozi samo za osobu koja već postoji (da se vide sve njene šifre).
    za_obradu.sort(key=lambda r: str(r[2][9]).strip().upper() != "D")

    osobe = set()
    for employee_code, preduzece, row in za_obradu:
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
            recipient_code,
            recipient_name,
        ) = row

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
            "u_izvoru": True,
        }
        if preduzece:
            defaults["preduzece"] = preduzece
        if has_residence_municipality_source:
            defaults["residence_municipality"] = _normalize_residence_municipality(opstina_boravka)
        if has_recipient_code:
            defaults["recipient_code"] = _as_str(recipient_code) or ""
        if has_recipient_name:
            defaults["recipient_name"] = _as_str(recipient_name) or ""

        existing = Employee.objects.filter(employee_code=employee_code).select_related("osoba").first()
        broj_jmbg = jmbg(matbr)
        osoba = (Osoba.objects.filter(jmbg=broj_jmbg).first() if broj_jmbg
                 else existing.osoba if existing and existing.osoba_id else None)
        # Ime za prikaz i ćirilica pripadaju osobi; bez osobe ostaje ono što je upisano na zaposlenju.
        if osoba:
            defaults.update({polje: getattr(osoba, izvor) for polje, izvor in PRIKAZ_POLJA.items()})
        elif existing:
            defaults["display_first_name_override"] = existing.display_first_name_override or ""
            defaults["display_last_name_override"] = existing.display_last_name_override or ""
        _preserve_locked_identity_fields(existing, defaults)

        if existing:
            for key, value in defaults.items():
                setattr(existing, key, value)
            existing.save()
            employee = existing
            counts["updated" if is_active else "updated_inactive"] += 1
        elif is_active or osoba:
            employee = Employee.objects.create(employee_code=employee_code, **defaults)
            counts["created" if is_active else "created_inactive"] += 1
        else:
            counts["skipped_inactive"] += 1
            continue
        osobe.add(povezi_osobu(employee).pk)

    for osoba in Osoba.objects.filter(pk__in=osobe):
        osvezi_osobu(osoba)
    # Broj koji nestane iz izvora se ne briše i aktivnost mu se ne menja — samo dobija oznaku.
    if po_broju:
        counts["missing_in_source"] = (Employee.objects.exclude(employee_code__in=list(po_broju))
                                       .filter(u_izvoru=True).update(u_izvoru=False))
    # Ukupan staž osobe (sve šifre, `RadStaz`) — posle vezivanja osoba i upisa preduzeća.
    counts["staz_osoba"] = osvezi_staz(staz_periodi(using))

    return {**counts, "total": len(rows)}


def staz_periodi(using=None):
    """Periodi staža iz kadrovske baze (`RadStaz`), svi poslodavci."""
    from hr.services.osobe import periodi_staza

    return periodi_staza(using)


def opis_osoba(result):
    """Dopuna poruke o sinhronizaciji: osobe, preduzeća i stanje pogleda (od 06.10.2026.)."""
    return (f"Neaktivne šifre postojećih osoba: {result.get('created_inactive', 0)}, "
            f"nema u izvoru: {result.get('missing_in_source', 0)}, "
            f"sukob preduzeća: {result.get('company_conflicts', 0)}, "
            f"različiti redovi istog broja: {result.get('conflicting_rows', 0)}, "
            f"duplirani redovi pogleda: {result.get('duplicate_rows', 0)}, "
            f"staž osoba: {result.get('staz_osoba', 0)}")


def preduzeca_radnika(using=None):
    """Broj radnika -> {(preduzeće, JMBG)} iz izvora `radnik` (pogled `hr_employee` nema preduzeće)."""
    from collections import defaultdict

    from hr.services.osobe import radnici_izvora

    mapa = defaultdict(set)
    for r in radnici_izvora(using):
        mapa[r["broj"]].add((r["preduzece"], r["jmbg"]))
    return mapa
