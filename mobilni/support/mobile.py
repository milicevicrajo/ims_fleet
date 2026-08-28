from dataclasses import dataclass, field
import calendar
import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
import math
import re
import unicodedata

import pandas as pd
from django.db import transaction
from django.utils import timezone

from fleet.models import Employee

from ..models import MobileAssignment, MobilePackage, MobileUsage, MobileUser


USAGE_FIELD_MAP = {
    "onnet": "onnet",
    "umtsmrezi": "mts_network",
    "vanmtsmreze": "outside_mts",
    "kakim": "kim",
    "kaspecijalnim": "special",
    "internacionalni": "international",
    "roaming": "roaming",
    "gprs": "gprs",
    "sms": "sms",
    "smsinternac": "sms_international",
    "smsuroamingu": "sms_roaming",
    "mms": "mms",
    "vassms": "vas_sms",
    "saobracajzapopust": "discount_traffic",
    "fiksnipopust": "fixed_discount",
    "varijabilnipopust": "variable_discount",
    "varjabilnipopust": "variable_discount",
    "usluge": "services",
    "otpremnice": "dispatch_notes",
    "parking": "parking",
    "nzrd": "nzrd",
    "osnovicazapdv": "vat_base",
    "pdv": "vat",
    "placanjenarate": "installments",
    "ukupnozanaplatu": "total",
}


@dataclass
class ImportResult:
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class SqlServerSyncResult:
    packages: ImportResult = field(default_factory=ImportResult)
    users: ImportResult = field(default_factory=ImportResult)
    assignments: ImportResult = field(default_factory=ImportResult)
    usages: ImportResult = field(default_factory=ImportResult)
    employee_links: dict = field(default_factory=dict)


def add_import_error(result, message, limit=50):
    if len(result.errors) < limit:
        result.errors.append(message)


def normalize_column(value):
    value = "" if value is None else str(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalize_dataframe(df):
    df = df.dropna(how="all")
    df = df.loc[:, [not str(column).lower().startswith("unnamed") for column in df.columns]]
    df.columns = [normalize_column(column) for column in df.columns]
    return df


def read_table(uploaded_file, matcher):
    name = uploaded_file.name.lower()
    content = uploaded_file.read()
    uploaded_file.seek(0)

    if name.endswith((".xlsx", ".xls")):
        sheets = pd.read_excel(BytesIO(content), sheet_name=None, dtype=object)
        for df in sheets.values():
            normalized = normalize_dataframe(df)
            if matcher(normalized):
                return normalized
        raise ValueError("Fajl nema očekivane kolone.")

    text = decode_bytes(content)
    lines = text.splitlines()
    header_index = find_header_index(lines)
    relevant = "\n".join(lines[header_index:])
    header = lines[header_index] if lines else ""
    separator = ";" if header.count(";") > header.count(",") else ","
    df = pd.read_csv(StringIO(relevant), sep=separator, dtype=str, engine="python")
    normalized = normalize_dataframe(df)
    if not matcher(normalized):
        raise ValueError("CSV nema očekivane kolone.")
    return normalized


def decode_bytes(content):
    for encoding in ("utf-8-sig", "cp1250", "latin1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def find_header_index(lines):
    for index, line in enumerate(lines):
        normalized = normalize_column(line)
        if "rednibroj" in normalized and "pretplbroj" in normalized:
            return index
        if "rasif" in normalized and "matbr" in normalized:
            return index
        if "broj" in normalized and "paket" in normalized:
            return index
        if "sifpar" in normalized and "partner" in normalized and "paket" in normalized:
            return index
    return 0


def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def clean_int(value):
    value = clean_text(value)
    if not value:
        return None
    match = re.search(r"-?\d+", value)
    return int(match.group(0)) if match else None


def clean_decimal(value):
    value = clean_text(value)
    if not value:
        return Decimal("0")
    value = value.replace(" ", "")
    match = re.search(r"-?\d+(?:[.,]\d+)?", value)
    if not match:
        return Decimal("0")
    try:
        return Decimal(match.group(0).replace(",", "."))
    except InvalidOperation:
        return Decimal("0")


def clean_date(value):
    if value is None or pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    date_value = parsed.date()
    if date_value.year == 1900 and date_value.month == 1 and date_value.day == 1:
        return None
    return date_value


def clean_phone_number(value):
    value = clean_text(value)
    if not value:
        return ""
    if re.fullmatch(r"\d+\.0+", value):
        value = value.split(".", 1)[0]
    if "e" in value.lower():
        try:
            decimal_value = Decimal(value)
            if decimal_value == decimal_value.to_integral_value():
                value = str(decimal_value.quantize(Decimal("1")))
        except InvalidOperation:
            pass
    return "".join(ch for ch in value if ch.isdigit()) or value


def clean_bool(value, default=True):
    value = clean_text(value).strip().lower()
    if value in {"", "nan"}:
        return default
    if value in {"1", "d", "da", "true", "yes", "y", "aktivan"}:
        return True
    if value in {"0", "n", "ne", "false", "no"}:
        return False
    return default


def get_value(row, *names):
    for name in names:
        normalized = normalize_column(name)
        if normalized in row and not pd.isna(row[normalized]):
            return row[normalized]
    return None


def import_packages(uploaded_file):
    df = read_table(
        uploaded_file,
        lambda table: {"sifpar", "partner", "paket"}.issubset(set(table.columns)),
    )
    result = ImportResult()

    with transaction.atomic():
        for _, row in df.iterrows():
            name = clean_text(get_value(row, "paket"))
            if not name:
                result.skipped += 1
                continue

            defaults = {
                "partner_name": clean_text(get_value(row, "partner")),
                "valid_to": clean_date(get_value(row, "datum_do")),
                "net_amount": clean_decimal(get_value(row, "iznos_neto")),
                "gross_amount": clean_decimal(get_value(row, "iznos_bruto")),
                "description": clean_text(get_value(row, "opis")),
            }
            _, created = MobilePackage.objects.update_or_create(
                partner_code=clean_text(get_value(row, "sif_par")),
                name=name,
                valid_from=clean_date(get_value(row, "datum_od")),
                defaults=defaults,
            )
            result.imported += int(created)
            result.updated += int(not created)

    return result


def import_users(uploaded_file):
    df = read_table(
        uploaded_file,
        lambda table: {"oj", "rasif", "ime"}.issubset(set(table.columns)),
    )
    result = ImportResult()
    employees_by_code = employee_map()

    with transaction.atomic():
        for _, row in df.iterrows():
            employee_code = clean_int(get_value(row, "rasif"))
            full_name = clean_text(get_value(row, "ime"))
            if not employee_code or not full_name:
                result.skipped += 1
                continue

            defaults = {
                "organizational_unit": clean_text(get_value(row, "oj")),
                "full_name": full_name,
                "personal_number": clean_text(get_value(row, "matbr")),
                "is_active": clean_bool(get_value(row, "aktivan"), default=True),
                "departure_date": clean_date(get_value(row, "dat_odlaska")),
                "employee": employees_by_code.get(employee_code),
            }
            _, created = MobileUser.objects.update_or_create(
                employee_code=employee_code,
                defaults=defaults,
            )
            result.imported += int(created)
            result.updated += int(not created)

    return result


def import_assignments(uploaded_file, year=None, month=None):
    df = read_table(uploaded_file, lambda table: {"broj", "paket"}.issubset(set(table.columns)))
    result = ImportResult()
    employees_by_code = employee_map()
    packages_by_name = package_candidates_by_name()

    with transaction.atomic():
        for _, row in df.iterrows():
            target_year = year or clean_int(get_value(row, "god", "godina"))
            target_month = month or clean_int(get_value(row, "mesec", "mjesec"))
            if not target_year or not target_month:
                result.skipped += 1
                continue

            phone_number = clean_phone_number(get_value(row, "broj"))
            if not phone_number:
                result.skipped += 1
                continue

            employee_code = clean_int(get_value(row, "rasif"))
            package_name = clean_text(get_value(row, "paket"))
            package = find_package_from_candidates(
                package_name,
                packages_by_name,
                valid_from=clean_date(get_value(row, "datum_od")),
                year=target_year,
                month=target_month,
            )
            mobile_user = find_mobile_user(employee_code)
            employee = find_employee(employee_code, employees_by_code, mobile_user)
            if not package:
                result.skipped += 1
                add_import_error(
                    result,
                    f"Dodela {phone_number} {target_month:02d}/{target_year}: paket '{package_name}' nije pronadjen.",
                )
                continue
            if not employee:
                result.skipped += 1
                add_import_error(
                    result,
                    f"Dodela {phone_number} {target_month:02d}/{target_year}: radnik '{employee_code or ''}' nije pronadjen.",
                )
                continue

            defaults = {
                "number_active": clean_bool(
                    get_value(row, "aktivan_broj", "broj_aktivan"),
                    default=True,
                ),
                "package": package,
                "employee": employee,
            }
            _, created = MobileAssignment.objects.update_or_create(
                year=target_year,
                month=target_month,
                phone_number=phone_number,
                defaults=defaults,
            )
            result.imported += int(created)
            result.updated += int(not created)

    return result


def import_usages(uploaded_file, year=None, month=None):
    df = read_table(
        uploaded_file,
        lambda table: (
            ("pretplbroj" in table.columns or "broj" in table.columns)
            and "ukupnozanaplatu" in table.columns
        ),
    )
    result = ImportResult()

    with transaction.atomic():
        for _, row in df.iterrows():
            target_year = year or clean_int(get_value(row, "god", "godina"))
            target_month = month or clean_int(get_value(row, "mesec", "mjesec"))
            if not target_year or not target_month:
                result.skipped += 1
                continue

            phone_number = clean_phone_number(get_value(row, "pretpl.broj", "pretpl_broj", "broj"))
            if not phone_number:
                result.skipped += 1
                continue

            assignment = find_assignment(phone_number, target_year, target_month)
            defaults = {
                "assignment": assignment,
                "employee": employee_from_assignment(assignment),
            }
            for source_column, model_field in USAGE_FIELD_MAP.items():
                defaults[model_field] = clean_decimal(get_value(row, source_column))

            _, created = MobileUsage.objects.update_or_create(
                year=target_year,
                month=target_month,
                phone_number=phone_number,
                defaults=defaults,
            )
            result.imported += int(created)
            result.updated += int(not created)

    return result


def package_candidates_by_name():
    packages = {}
    for package in MobilePackage.objects.order_by("name", "-valid_from", "-id"):
        packages.setdefault(clean_text(package.name).lower(), []).append(package)
    return packages


def package_matches_period(package, year, month):
    if not year or not month:
        return False
    period_start = datetime.date(year, month, 1)
    period_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
    if package.valid_from and package.valid_from > period_end:
        return False
    if package.valid_to and package.valid_to < period_start:
        return False
    return True


def find_package_from_candidates(package_name, packages_by_name, *, valid_from=None, year=None, month=None):
    candidates = packages_by_name.get(clean_text(package_name).lower(), [])
    if not candidates:
        return None
    if valid_from:
        for package in candidates:
            if package.valid_from == valid_from:
                return package
    for package in candidates:
        if package_matches_period(package, year, month):
            return package
    return candidates[0]


def find_package(package_name, valid_from=None, year=None, month=None):
    return find_package_from_candidates(
        package_name,
        package_candidates_by_name(),
        valid_from=valid_from,
        year=year,
        month=month,
    )


def find_mobile_user(employee_code):
    if not employee_code:
        return None
    return MobileUser.objects.filter(employee_code=employee_code).first()


def find_assignment(phone_number, year, month):
    exact = MobileAssignment.objects.filter(
        year=year,
        month=month,
        phone_number=phone_number,
    ).first()
    if exact:
        return exact

    before_or_same = MobileAssignment.objects.filter(
        phone_number=phone_number,
    ).filter(
        year__lt=year,
    ) | MobileAssignment.objects.filter(
        phone_number=phone_number,
        year=year,
        month__lte=month,
    )
    assignment = before_or_same.order_by("-year", "-month", "-id").first()
    if assignment:
        return assignment

    return MobileAssignment.objects.filter(phone_number=phone_number).order_by("-year", "-month", "-id").first()


def employee_map():
    return {employee.employee_code: employee for employee in Employee.objects.all()}


def find_employee(employee_code, employees_by_code=None, mobile_user=None):
    if mobile_user and mobile_user.employee_id:
        return mobile_user.employee
    if not employee_code:
        return None
    employees_by_code = employees_by_code or employee_map()
    return employees_by_code.get(employee_code)


def employee_from_assignment(assignment):
    if not assignment:
        return None
    return assignment.employee if assignment.employee_id else None


def sync_employee_links():
    result = {
        "mobile_users_linked": 0,
        "usages_assignment_linked": 0,
        "usages_employee_linked": 0,
    }
    employees_by_code = employee_map()

    with transaction.atomic():
        for mobile_user in MobileUser.objects.all():
            employee = employees_by_code.get(mobile_user.employee_code)
            if employee and mobile_user.employee_id != employee.id:
                mobile_user.employee = employee
                mobile_user.save(update_fields=["employee", "updated_at"])
                result["mobile_users_linked"] += 1

        for usage in MobileUsage.objects.select_related("assignment", "employee"):
            update_fields = []
            assignment = usage.assignment or find_assignment(usage.phone_number, usage.year, usage.month)
            if assignment and usage.assignment_id != assignment.id:
                usage.assignment = assignment
                update_fields.append("assignment")
                result["usages_assignment_linked"] += 1

            employee = employee_from_assignment(assignment)
            if employee and usage.employee_id != employee.id:
                usage.employee = employee
                update_fields.append("employee")
                result["usages_employee_linked"] += 1

            if update_fields:
                usage.save(update_fields=[*update_fields, "updated_at"])

    return result


def sync_from_sqlserver(server, database, username, password, driver="ODBC Driver 17 for SQL Server"):
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc nije instaliran u virtuelnom okruženju.") from exc

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )
    conn = pyodbc.connect(connection_string, timeout=30)
    try:
        result = SqlServerSyncResult()
        with transaction.atomic():
            result.packages = sync_sqlserver_packages(conn)
            result.users = sync_sqlserver_users(conn)
            result.assignments = sync_sqlserver_assignments(conn)
            result.usages = sync_sqlserver_usages(conn)
        result.employee_links = sync_employee_links()
        return result
    finally:
        conn.close()


def sync_sqlserver_packages(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sif_par, partner, paket, datum_od, datum_do, iznos_neto, iznos_bruto, opis
        FROM paketi
        """
    )
    result = ImportResult()
    source = {}
    for row in cursor.fetchall():
        name = clean_text(row.paket)
        if not name:
            result.skipped += 1
            continue
        key = (clean_text(row.sif_par), name, clean_date(row.datum_od))
        source[key] = {
            "partner_name": clean_text(row.partner),
            "valid_to": clean_date(row.datum_do),
            "net_amount": clean_decimal(row.iznos_neto),
            "gross_amount": clean_decimal(row.iznos_bruto),
            "description": clean_text(row.opis),
        }

    existing = {
        (item.partner_code, item.name, item.valid_from): item
        for item in MobilePackage.objects.all()
    }
    now = timezone.now()
    to_create = []
    to_update = []
    update_fields = ["partner_name", "valid_to", "net_amount", "gross_amount", "description", "updated_at"]
    for (partner_code, name, valid_from), defaults in source.items():
        item = existing.get((partner_code, name, valid_from))
        if item:
            for field, value in defaults.items():
                setattr(item, field, value)
            item.updated_at = now
            to_update.append(item)
        else:
            to_create.append(
                MobilePackage(
                    partner_code=partner_code,
                    name=name,
                    valid_from=valid_from,
                    created_at=now,
                    updated_at=now,
                    **defaults,
                )
            )

    MobilePackage.objects.bulk_create(to_create, batch_size=500)
    MobilePackage.objects.bulk_update(to_update, update_fields, batch_size=500)
    result.imported = len(to_create)
    result.updated = len(to_update)

    return result


def sync_sqlserver_users(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT rasif, MAX(ranaz) AS ranaz, MAX(aktivan_radnik) AS aktivan_radnik
        FROM dodeljeno
        WHERE rasif IS NOT NULL
        GROUP BY rasif
        """
    )
    result = ImportResult()
    employees_by_code = employee_map()
    source = {}

    for row in cursor.fetchall():
        employee_code = clean_int(row.rasif)
        full_name = clean_text(row.ranaz)
        if not employee_code or not full_name:
            result.skipped += 1
            continue
        source[employee_code] = {
            "full_name": full_name,
            "is_active": clean_bool(row.aktivan_radnik, default=True),
            "employee": employees_by_code.get(employee_code),
        }

    existing = {item.employee_code: item for item in MobileUser.objects.all()}
    now = timezone.now()
    to_create = []
    to_update = []
    update_fields = ["full_name", "is_active", "employee", "updated_at"]
    for employee_code, defaults in source.items():
        item = existing.get(employee_code)
        if item:
            for field, value in defaults.items():
                setattr(item, field, value)
            item.updated_at = now
            to_update.append(item)
        else:
            to_create.append(
                MobileUser(
                    employee_code=employee_code,
                    organizational_unit="",
                    personal_number="",
                    departure_date=None,
                    created_at=now,
                    updated_at=now,
                    **defaults,
                )
            )

    MobileUser.objects.bulk_create(to_create, batch_size=500)
    MobileUser.objects.bulk_update(to_update, update_fields, batch_size=500)
    result.imported = len(to_create)
    result.updated = len(to_update)

    return result


def sync_sqlserver_assignments(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT god, mesec, broj, aktivan_broj, paket, rasif
        FROM dodeljeno
        """
    )
    result = ImportResult()
    employees_by_code = employee_map()
    mobile_users_by_code = {item.employee_code: item for item in MobileUser.objects.select_related("employee")}
    packages_by_name = package_candidates_by_name()
    source = {}

    for row in cursor.fetchall():
        year = clean_int(row.god)
        month = clean_int(row.mesec)
        phone_number = clean_phone_number(row.broj)
        if not year or not month or not phone_number:
            result.skipped += 1
            continue

        employee_code = clean_int(row.rasif)
        package_name = clean_text(row.paket)
        mobile_user = mobile_users_by_code.get(employee_code)
        employee = find_employee(employee_code, employees_by_code, mobile_user)
        package = find_package_from_candidates(package_name, packages_by_name, year=year, month=month)
        if not package:
            result.skipped += 1
            add_import_error(
                result,
                f"Dodela {phone_number} {month:02d}/{year}: paket '{package_name}' nije pronadjen.",
            )
            continue
        if not employee:
            result.skipped += 1
            add_import_error(
                result,
                f"Dodela {phone_number} {month:02d}/{year}: radnik '{employee_code or ''}' nije pronadjen.",
            )
            continue
        source[(year, month, phone_number)] = {
            "number_active": clean_bool(row.aktivan_broj, default=True),
            "package": package,
            "employee": employee,
        }

    existing = {
        (item.year, item.month, item.phone_number): item
        for item in MobileAssignment.objects.all()
    }
    now = timezone.now()
    to_create = []
    to_update = []
    update_fields = [
        "number_active",
        "package",
        "employee",
        "updated_at",
    ]
    for (year, month, phone_number), defaults in source.items():
        item = existing.get((year, month, phone_number))
        if item:
            for field, value in defaults.items():
                setattr(item, field, value)
            item.updated_at = now
            to_update.append(item)
        else:
            to_create.append(
                MobileAssignment(
                    year=year,
                    month=month,
                    phone_number=phone_number,
                    created_at=now,
                    updated_at=now,
                    **defaults,
                )
            )

    MobileAssignment.objects.bulk_create(to_create, batch_size=500)
    MobileAssignment.objects.bulk_update(to_update, update_fields, batch_size=500)
    result.imported = len(to_create)
    result.updated = len(to_update)

    return result


def sync_sqlserver_usages(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT god, mesec, broj, Onnet, UMTSmrezi, VanMTSmreze, KaKIM, Kaspecijalnim,
               Internacionalni, Roaming, GPRS, SMS, SMSInternac, SMSuRoamingu, MMS,
               VASSMS, Saobracajzapopust, Fiksnipopust, Varjabilnipopust, Usluge,
               Otpremnice, Parking, NZRD, OsnovicazaPDV, PDV, Placanjenarate,
               Ukupnozanaplatu
        FROM potrosnja
        """
    )
    result = ImportResult()

    field_map = {
        "Onnet": "onnet",
        "UMTSmrezi": "mts_network",
        "VanMTSmreze": "outside_mts",
        "KaKIM": "kim",
        "Kaspecijalnim": "special",
        "Internacionalni": "international",
        "Roaming": "roaming",
        "GPRS": "gprs",
        "SMS": "sms",
        "SMSInternac": "sms_international",
        "SMSuRoamingu": "sms_roaming",
        "MMS": "mms",
        "VASSMS": "vas_sms",
        "Saobracajzapopust": "discount_traffic",
        "Fiksnipopust": "fixed_discount",
        "Varjabilnipopust": "variable_discount",
        "Usluge": "services",
        "Otpremnice": "dispatch_notes",
        "Parking": "parking",
        "NZRD": "nzrd",
        "OsnovicazaPDV": "vat_base",
        "PDV": "vat",
        "Placanjenarate": "installments",
        "Ukupnozanaplatu": "total",
    }
    exact_assignments, assignments_by_phone = assignment_lookup_maps()
    source = {}

    for row in cursor.fetchall():
        year = clean_int(row.god)
        month = clean_int(row.mesec)
        phone_number = clean_phone_number(row.broj)
        if not year or not month or not phone_number:
            result.skipped += 1
            continue

        assignment = find_assignment_from_maps(phone_number, year, month, exact_assignments, assignments_by_phone)
        defaults = {
            "assignment": assignment,
            "employee": employee_from_assignment(assignment),
        }
        for source_field, model_field in field_map.items():
            defaults[model_field] = clean_decimal(getattr(row, source_field))
        source[(year, month, phone_number)] = defaults

    existing = {
        (item.year, item.month, item.phone_number): item
        for item in MobileUsage.objects.all()
    }
    now = timezone.now()
    to_create = []
    to_update = []
    update_fields = [
        "assignment",
        "employee",
        "onnet",
        "mts_network",
        "outside_mts",
        "kim",
        "special",
        "international",
        "roaming",
        "gprs",
        "sms",
        "sms_international",
        "sms_roaming",
        "mms",
        "vas_sms",
        "discount_traffic",
        "fixed_discount",
        "variable_discount",
        "services",
        "dispatch_notes",
        "parking",
        "nzrd",
        "vat_base",
        "vat",
        "installments",
        "total",
        "updated_at",
    ]
    for (year, month, phone_number), defaults in source.items():
        item = existing.get((year, month, phone_number))
        if item:
            for field, value in defaults.items():
                setattr(item, field, value)
            item.updated_at = now
            to_update.append(item)
        else:
            to_create.append(
                MobileUsage(
                    year=year,
                    month=month,
                    phone_number=phone_number,
                    created_at=now,
                    updated_at=now,
                    **defaults,
                )
            )

    MobileUsage.objects.bulk_create(to_create, batch_size=500)
    MobileUsage.objects.bulk_update(to_update, update_fields, batch_size=500)
    result.imported = len(to_create)
    result.updated = len(to_update)

    return result


def assignment_lookup_maps():
    exact = {}
    by_phone = {}
    qs = MobileAssignment.objects.select_related("employee", "package").order_by(
        "phone_number",
        "-year",
        "-month",
        "-id",
    )
    for assignment in qs:
        exact[(assignment.year, assignment.month, assignment.phone_number)] = assignment
        by_phone.setdefault(assignment.phone_number, []).append(assignment)
    return exact, by_phone


def find_assignment_from_maps(phone_number, year, month, exact_assignments, assignments_by_phone):
    exact = exact_assignments.get((year, month, phone_number))
    if exact:
        return exact

    assignments = assignments_by_phone.get(phone_number, [])
    for assignment in assignments:
        if assignment.year < year or (assignment.year == year and assignment.month <= month):
            return assignment

    return assignments[0] if assignments else None
