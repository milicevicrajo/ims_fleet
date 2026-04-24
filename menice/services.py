from argparse import Namespace
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import Menica


FIELD_MAP = {
    "Naziv duznika": "naziv_duznika",
    "Maticni broj duznika": "maticni_broj_duznika",
    "Poreski broj duznika": "poreski_broj_duznika",
    "Strana rezultata": "strana_rezultata",
    "Serijski broj menice": "serijski_broj_menice",
    "Datum izdavanja": "datum_izdavanja",
    "Iznos menice": "iznos_menice",
    "Valuta menice": "valuta_menice",
    "Datum dospeca": "datum_dospeca",
    "Izdavalac menice": "izdavalac_menice",
    "Vrsta menice": "vrsta_menice",
    "Redni broj": "redni_broj",
    "Osnov izdavanja": "osnov_izdavanja",
    "Iznos iz osnova": "iznos_iz_osnova",
    "Valuta osnova": "valuta_osnova",
    "Datum registracije": "datum_registracije",
    "Naziv banke": "naziv_banke",
    "Status": "status",
    "Avalisti detalji": "avalisti_detalji",
    "Avalisti broj zapisa": "avalisti_broj_zapisa",
}

DATE_FIELDS = {"datum_izdavanja", "datum_dospeca", "datum_registracije"}
DECIMAL_FIELDS = {"iznos_menice", "iznos_iz_osnova"}
INTEGER_FIELDS = {"strana_rezultata", "redni_broj", "avalisti_broj_zapisa"}


def parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith(".") and text.count(".") >= 3:
        text = text.rstrip(".")
    for date_format in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def parse_decimal(value):
    if value in (None, ""):
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_integer(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def normalize_record(record):
    values = {"tip": Menica.TIP_IZLAZNA}
    for source_name, field_name in FIELD_MAP.items():
        raw_value = record.get(source_name, "")
        if field_name in DATE_FIELDS:
            values[field_name] = parse_date(raw_value)
        elif field_name in DECIMAL_FIELDS:
            values[field_name] = parse_decimal(raw_value)
        elif field_name in INTEGER_FIELDS:
            values[field_name] = parse_integer(raw_value)
        else:
            values[field_name] = str(raw_value).strip() or None
    return values


def sync_izlazne_menice(
    *,
    tax_code="100223617",
    national_code="",
    serial_number="",
    registration_date="",
    page_size=100,
    include_avalists=True,
    max_pages=None,
    timeout=30,
):
    from .scraper import scrape

    args = Namespace(
        tax_code=tax_code,
        national_code=national_code,
        serial_number=serial_number,
        registration_date=registration_date,
        page_size=page_size,
        include_avalists=include_avalists,
        max_pages=max_pages,
        timeout=timeout,
    )
    records = scrape(args)
    created_count = 0
    skipped_count = 0

    for record in records:
        values = normalize_record(record)
        serial = values.get("serijski_broj_menice")
        registration = values.get("datum_registracije")
        if not serial or not registration:
            skipped_count += 1
            continue

        exists = Menica.objects.filter(
            tip=Menica.TIP_IZLAZNA,
            serijski_broj_menice=serial,
            datum_registracije=registration,
        ).exists()
        if exists:
            skipped_count += 1
            continue

        Menica.objects.create(**values)
        created_count += 1

    return {
        "fetched": len(records),
        "created": created_count,
        "skipped": skipped_count,
    }
