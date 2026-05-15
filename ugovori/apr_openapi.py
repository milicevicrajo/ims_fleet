import json
import re
from dataclasses import dataclass

import requests
from django.utils import timezone
from requests.exceptions import SSLError
from urllib3.exceptions import InsecureRequestWarning
import urllib3

from .models import Partner


APR_COMPANIES_URL = "https://openapi.apr.gov.rs/api/opendata/companies"
APR_OPENAPI_SOURCE = "apr_openapi"


@dataclass
class AprPartnerUpdateResult:
    checked: int = 0
    updated: int = 0
    unchanged: int = 0
    missing_maticni_broj: int = 0
    not_found: int = 0


def normalize_maticni_broj(value):
    digits = re.sub(r"\D+", "", str(value or ""))
    if not digits:
        return ""
    return digits.zfill(8) if len(digits) < 8 else digits


def is_active_apr_status(status):
    return str(status or "").strip().casefold() == "активан".casefold()


def fetch_apr_companies(url=APR_COMPANIES_URL, timeout=60):
    try:
        response = requests.get(url, timeout=timeout)
    except SSLError:
        urllib3.disable_warnings(InsecureRequestWarning)
        response = requests.get(url, timeout=timeout, verify=False)
    response.raise_for_status()
    payload = json.loads(response.content.decode("utf-8-sig"))
    return payload.get("Podaci") or {}


def get_apr_company(maticni_broj, companies=None):
    companies = companies if companies is not None else fetch_apr_companies()
    return companies.get(normalize_maticni_broj(maticni_broj))


def update_partner_from_apr(partner, company, commit=True):
    now = timezone.now()
    status = str(company.get("NazivStatus") or "").strip()
    defaults = {
        "name": str(company.get("PoslovnoIme") or "").strip() or partner.name,
        "is_active": is_active_apr_status(status),
        "apr_status": status or None,
        "apr_checked_at": now,
        "data_source": APR_OPENAPI_SOURCE,
        "data_validated": True,
        "data_validated_at": now,
    }

    changed_fields = []
    for field, value in defaults.items():
        if getattr(partner, field) != value:
            setattr(partner, field, value)
            changed_fields.append(field)

    if commit and changed_fields:
        partner.save(update_fields=[*changed_fields, "updated_at"])
    return changed_fields


def update_partners_from_apr(partners, *, companies=None, commit=True):
    companies = companies if companies is not None else fetch_apr_companies()
    result = AprPartnerUpdateResult()

    for partner in partners:
        result.checked += 1
        maticni_broj = normalize_maticni_broj(partner.maticni_broj)
        if not maticni_broj:
            result.missing_maticni_broj += 1
            continue

        company = companies.get(maticni_broj)
        if not company:
            result.not_found += 1
            continue

        changed_fields = update_partner_from_apr(partner, company, commit=commit)
        if changed_fields:
            result.updated += 1
        else:
            result.unchanged += 1

    return result
