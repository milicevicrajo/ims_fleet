import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError


RECORD_LENGTH = 180

PAYER_ACCOUNT = "205000000001445485"
PAYER_NAME = "Institut IMS a.d."
PAYER_CITY = "Beograd"
HEADER_DATE_FORMAT = "%d%m%y"
DETAIL_DATE_FORMAT = "%d%m%y01"
HEADER_SUFFIX = "Multi E_BANK0"

DETAIL_MODEL = "000"
DETAIL_PURPOSE = "NEOPOREZIVA PRIMANJA ZAPOSLENIH"
DETAIL_CONTROL = "00000"
DETAIL_PAYMENT_CODE = "241"
DETAIL_REFERENCE_SUFFIX_WIDTH = 21


SERBIAN_TRANSLITERATION = str.maketrans(
    {
        "č": "c",
        "ć": "c",
        "š": "s",
        "ž": "z",
        "đ": "dj",
        "Č": "C",
        "Ć": "C",
        "Š": "S",
        "Ž": "Z",
        "Đ": "DJ",
    }
)


@dataclass(frozen=True)
class VirmanFile:
    filename: str
    content: str

    @property
    def bytes(self):
        return self.content.encode("cp1250", errors="replace")


def _blank_record():
    return [" "] * RECORD_LENGTH


def _write(record, start, width, value, align="left"):
    text = "" if value is None else str(value)
    text = text[:width]
    padded = text.rjust(width) if align == "right" else text.ljust(width)
    record[start - 1:start - 1 + width] = padded


def _record_to_string(record):
    line = "".join(record)
    if len(line) != RECORD_LENGTH:
        raise AssertionError(f"Virman red mora imati {RECORD_LENGTH} karaktera, ima {len(line)}.")
    return line


def _safe_text(value):
    value = "" if value is None else str(value)
    value = " ".join(value.split())
    value = value.translate(SERBIAN_TRANSLITERATION)
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", errors="ignore").decode("ascii")
    return value


def _account_digits(value):
    return re.sub(r"\D", "", value or "")


def _amount_cents(value):
    amount = Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise ValidationError("Iznos mora biti veci od nule.")
    return int(amount * 100)


def _amount_cents_for_header(value):
    amount = Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount < 0:
        raise ValidationError("Ukupan iznos ne moze biti negativan.")
    return int(amount * 100)


def _detail_reference(amount, order):
    amount_part = str(_amount_cents(amount)).zfill(13)
    return f"{amount_part}{_order_number_reference(order)}"


def _order_number_reference(order):
    reference = _safe_text(order.order_number or "")
    if not reference:
        raise ValidationError(f"{order.order_number}: nedostaje broj putnog naloga.")
    if len(reference) > DETAIL_REFERENCE_SUFFIX_WIDTH:
        raise ValidationError(
            f"{order.order_number}: broj putnog naloga je duzi od {DETAIL_REFERENCE_SUFFIX_WIDTH} karaktera."
        )
    return reference.rjust(DETAIL_REFERENCE_SUFFIX_WIDTH)


def _recipient_name(order):
    if order.employee:
        return order.employee.original_full_name or str(order.employee)
    return order.other_employee_name or ""


def _recipient_city(order):
    if order.employee:
        return (order.employee.residence_municipality or PAYER_CITY).upper()
    return PAYER_CITY


def validate_order_for_virman(order, allow_regenerate=False):
    errors = []

    if order.storniran:
        errors.append(f"{order.order_number}: nalog je storniran.")
    if order.virman_generated and not allow_regenerate:
        errors.append(f"{order.order_number}: virman je vec odradjen.")
    if order.advance_payment_currency != "RSD":
        errors.append(f"{order.order_number}: valuta mora biti RSD.")
    if not order.employee:
        errors.append(f"{order.order_number}: nalog nema IMS zaposlenog.")
    elif not _account_digits(order.employee.account_number):
        errors.append(f"{order.order_number}: zaposlenom nedostaje racun.")
    elif len(_account_digits(order.employee.account_number)) != 18:
        errors.append(f"{order.order_number}: racun mora imati 18 cifara.")

    try:
        _amount_cents(order.advance_payment)
    except ValidationError as exc:
        errors.append(f"{order.order_number}: {exc.messages[0]}")

    if errors:
        raise ValidationError(errors)


def build_header_lines(payment_date, total_amount=0, order_count=0):
    date_text = payment_date.strftime(HEADER_DATE_FORMAT)

    first = _blank_record()
    _write(first, 1, 18, PAYER_ACCOUNT)
    _write(first, 19, 35, PAYER_NAME)
    _write(first, 54, 10, PAYER_CITY)
    _write(first, 64, 6, date_text)
    _write(first, 168, 13, HEADER_SUFFIX)

    second = _blank_record()
    _write(second, 1, 18, PAYER_ACCOUNT)
    _write(second, 19, 35, PAYER_NAME)
    _write(second, 54, 10, PAYER_CITY)
    _write(second, 64, 15, f"{_amount_cents_for_header(total_amount):015d}")
    _write(second, 79, 5, f"{order_count:05d}")
    _write(second, 180, 1, "9")

    return [_record_to_string(first), _record_to_string(second)]


def build_detail_line(order, payment_date, allow_regenerate=False):
    validate_order_for_virman(order, allow_regenerate=allow_regenerate)

    record = _blank_record()
    _write(record, 1, 18, _account_digits(order.employee.account_number))
    _write(record, 19, 35, _safe_text(_recipient_name(order)).upper())
    _write(record, 54, 10, _safe_text(_recipient_city(order)))
    _write(record, 64, 25, DETAIL_MODEL)
    _write(record, 89, 35, DETAIL_PURPOSE)
    _write(record, 125, 5, DETAIL_CONTROL)
    _write(record, 131, 3, DETAIL_PAYMENT_CODE)
    _write(record, 136, 34, _detail_reference(order.advance_payment, order))
    _write(record, 173, 8, payment_date.strftime(DETAIL_DATE_FORMAT))
    return _record_to_string(record)


def build_virman_file(orders, payment_date, generated_at, allow_regenerate=False):
    orders = list(orders)
    if not orders:
        raise ValidationError("Izaberi bar jedan putni nalog.")

    for order in orders:
        validate_order_for_virman(order, allow_regenerate=allow_regenerate)

    total_amount = sum(Decimal(order.advance_payment or 0) for order in orders)
    lines = build_header_lines(payment_date, total_amount=total_amount, order_count=len(orders))
    lines.extend(
        build_detail_line(order, payment_date, allow_regenerate=allow_regenerate)
        for order in orders
    )
    content = "\r\n".join(lines) + "\r\n"
    filename = f"Virman-putni-nalozi-{generated_at.strftime('%Y%m%d-%H%M%S')}.txt"
    return VirmanFile(filename=filename, content=content)
