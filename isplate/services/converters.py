import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError


RECORD_LENGTH = 180
HEADER_LINE_COUNT = 2


@dataclass(frozen=True)
class TxtJsonConversion:
    records: list
    source_filename: str

    @property
    def json_text(self):
        return json.dumps(self.records, ensure_ascii=False, indent=4)

    @property
    def output_filename(self):
        base_name = (self.source_filename or "virman").rsplit(".", 1)[0]
        return f"{base_name}.json"


def _decode_text_file(uploaded_file):
    content = uploaded_file.read()
    for encoding in ("cp1250", "utf-8-sig", "utf-16"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError("TXT fajl nije u podrzanom encoding-u.")


def _line_value(line, start, end):
    return line[start - 1:end].strip()


def _line_digits(line, start, end):
    return "".join(character for character in _line_value(line, start, end) if character.isdigit())


def _parse_int(value, default=0):
    value = (value or "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(f"Neispravna numericka vrednost: {value}") from exc


def _parse_amount(value):
    value = (value or "").strip()
    if not value.isdigit():
        raise ValidationError(f"Neispravan iznos u pozivu na broj: {value}")
    amount = Decimal(value) / Decimal("100")
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)


def _parse_payment_date(value):
    value = (value or "").strip()
    if len(value) < 6 or not value[:6].isdigit():
        raise ValidationError(f"Neispravan datum placanja: {value}")
    day = int(value[0:2])
    month = int(value[2:4])
    year = 2000 + int(value[4:6])
    try:
        return date(year, month, day).isoformat()
    except ValueError as exc:
        raise ValidationError(f"Neispravan datum placanja: {value}") from exc


def _normalize_lines(text):
    lines = [line.rstrip("\r\n") for line in text.splitlines() if line.strip()]
    if len(lines) <= HEADER_LINE_COUNT:
        raise ValidationError("TXT mora imati dva header reda i bar jedan detaljni red.")

    invalid_lengths = [
        f"{index + 1}: {len(line)}"
        for index, line in enumerate(lines)
        if len(line) != RECORD_LENGTH
    ]
    if invalid_lengths:
        raise ValidationError(
            "Svi redovi moraju imati 180 karaktera. Neispravni redovi: "
            + ", ".join(invalid_lengths[:10])
        )
    return lines


def _convert_detail_line(line, debtor_bank_account):
    reference = _line_value(line, 136, 169)
    if len(reference) < 15:
        raise ValidationError("Poziv na broj je prekratak.")

    return {
        "PaymentBasis": _line_value(line, 89, 123),
        "PaymentCode": _parse_int(_line_value(line, 131, 133)),
        "Amount": _parse_amount(reference[:13]),
        "DebtorBankAccount": debtor_bank_account,
        "DebtorCodeModel": _parse_int(_line_value(line, 64, 66)),
        "DebtorCode": _line_value(line, 67, 88),
        "CreditorName": _line_value(line, 19, 53),
        "CreditorAddress": _line_value(line, 54, 63),
        "CreditorBankAccount": _line_digits(line, 1, 18),
        "CreditorCodeModel": _parse_int(reference[13:15]),
        "CreditorCode": reference[15:],
        "UrgentPayment": True,
        "ExpectedPaymentDate": _parse_payment_date(_line_value(line, 173, 180)),
        "ExternalId": None,
        "UserGroupName": None,
        "UserTags": "",
        "Comment": "",
    }


def convert_virman_txt_to_internal_json(uploaded_file):
    text = _decode_text_file(uploaded_file)
    lines = _normalize_lines(text)
    debtor_bank_account = _line_digits(lines[0], 1, 18)
    if len(debtor_bank_account) != 18:
        raise ValidationError("Header ne sadrzi ispravan racun duznika.")

    records = [
        _convert_detail_line(line, debtor_bank_account)
        for line in lines[HEADER_LINE_COUNT:]
    ]
    return TxtJsonConversion(records=records, source_filename=getattr(uploaded_file, "name", "virman.txt"))
