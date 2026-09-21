"""Bank statements from the existing ledger snapshot; never writes accounting data."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
import re
import unicodedata

from django.conf import settings
from django.db import connections
from django.db.models import Q
from django.utils import timezone

from finansije.access import visible_scope
from finansije.models import BankAccountRule, LedgerEntry
from .source import SOURCE, clean

ZERO = Decimal("0.00")
PARTNER_FIELDS = "sif_par naz_par ulica_par p_b_par mesto_par zr mb telefon fax email lice web proc_rabata br_dana vlasnik pib zemlja pdv_obveznik".split()
PARTNER_LABELS = ["Šifra partnera", "Naziv", "Ulica", "Poštanski broj", "Mesto", "Račun iz šifarnika partnera",
                  "Matični broj", "Telefon", "Fax", "Email", "Kontakt osoba", "Web", "Procenat rabata",
                  "Broj dana plaćanja", "Vlasnik", "PIB", "Zemlja", "PDV obveznik"]
SEGMENTS = dict(BankAccountRule.SEGMENTS)


def company_id():
    return getattr(settings, "FINANSIJE_COMPANY", 1)


def fetch_banks(company):
    alias = getattr(settings, "FINANSIJE_SOURCE_DB", "server_db")
    with connections[alias].cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(PARTNER_FIELDS)} FROM {SOURCE}.partner WHERE sif_pred=%s AND grupa=%s ORDER BY naz_par,sif_par", [company, 11])
        banks = [dict(zip(PARTNER_FIELDS, (clean(value) for value in row))) for row in cursor.fetchall()]
    for bank in banks:
        bank["code"] = int(bank["sif_par"])
        bank["name"] = bank["naz_par"]
        bank["fields"] = [(label, bank[field]) for field, label in zip(PARTNER_FIELDS, PARTNER_LABELS)]
    if len({bank["code"] for bank in banks}) != len(banks):
        raise ValueError("Šifarnik banaka ima duplirane šifre.")
    return banks


def normalized(value):
    value = unicodedata.normalize("NFKD", value.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def suggested_segment(account, name):
    name = normalized(name)
    if account.startswith(("243", "246", "239")) or "prelazni" in name or account == "23230":
        return "excluded"
    if "garan" in name and account.startswith(("23", "24", "038", "048")):
        return "guarantee"
    if account.startswith(("238", "038", "048")) and ("oroc" in name or "depoz" in name):
        return "deposit"
    if account.startswith("241"):
        return "dinar"
    if account.startswith("244"):
        return "foreign"
    return "other"


def suggested_bank(name, banks):
    """A suggestion for approval, never an automatic posting assignment."""
    text = normalized(name)
    brands = ("raiff", "intesa", "aik", "erste", "halk", "otp", "alta", "addiko", "adriatic", "nlb")
    matches = [bank for bank in banks if any(brand in text and brand in normalized(bank["name"]) for brand in brands)]
    if len(matches) > 1:
        primary = [bank for bank in matches if bank.get("zr", "").startswith("908-")]
        if len(primary) == 1:
            matches = primary
    return matches[0]["code"] if len(matches) == 1 else None


def bank_entries(user, year, through):
    return visible_scope(LedgerEntry.objects.filter(company=company_id(), active=True, year=year,
        booking_date__gte=date(year, 1, 1), booking_date__lte=through).exclude(journal_type="ZAT"), user).filter(
        Q(account__startswith="23") | Q(account__startswith="24"))


def empty_amounts():
    return dict(opening=ZERO, inflow=ZERO, outflow=ZERO, turnover=ZERO, balance=ZERO,
                ytd_inflow=ZERO, ytd_outflow=ZERO, count=0)


def add_amounts(target, debit, credit, row, start, end, ytd_end):
    day = row["booking_date"]
    initial = row["journal_type"].upper() == "POC"
    if day <= end:
        target["balance"] += debit - credit
        if initial or day < start:
            target["opening"] += debit - credit
        else:
            target["inflow"] += debit
            target["outflow"] += credit
            target["turnover"] += debit + credit
            target["count"] += 1
    if day <= ytd_end and not initial:
        target["ytd_inflow"] += debit
        target["ytd_outflow"] += credit


def foreign_sides(row):
    amount = row["foreign_amount"]
    if amount is None:
        return None
    flag = row["debit_credit_flag"].strip().lower()
    if flag not in ("d", "p"):
        return None
    # Storno may have a positive deviza with a negative domestic posting.
    side = row["debit"] if flag == "d" else row["credit"]
    if side < ZERO and amount > ZERO:
        amount = -amount
    return (amount, ZERO) if flag == "d" else (ZERO, amount)


def build_report(entries, banks, rules, start, end, today=None):
    """Each posting belongs to exactly one bank/account/currency bucket or control bucket."""
    today = today or timezone.localdate()
    ytd_end = min(today, date(start.year, 12, 31))
    bank_index = {bank["code"]: bank for bank in banks}
    rules = {rule.account: rule for rule in rules}
    grouped, unmapped, excluded = {}, {}, {}
    for row in entries:
        account = row["account"].strip()
        rule = rules.get(account)
        segment = rule.segment if rule else suggested_segment(account, row["account_name"])
        code = row["partner_code"] if row["partner_group"] == 11 else None
        # An explicit external partner always takes precedence over a local account rule.
        if not code and row["partner_group"] in (None, 0) and row["partner_code"] in (None, 0):
            code = rule.bank_code if rule else None
        currency = row["currency"].strip().upper()
        currency = "RSD" if currency in ("DIN", "RSD") else currency or "Nepoznata"
        is_excluded = segment == "excluded" and row["partner_group"] != 11
        destination = excluded if is_excluded else grouped if code in bank_index else unmapped
        key = (code, account, currency)
        item = destination.setdefault(key, dict(code=code, account=account, name=row["account_name"], currency=currency,
            segment=segment, segment_label=SEGMENTS[segment], rsd=empty_amounts(), fx=empty_amounts(), fx_missing=False,
            mapped_by="Partner" if row["partner_group"] == 11 else "Potvrđena veza konta", documents=[]))
        add_amounts(item["rsd"], row["debit"], row["credit"], row, start, end, ytd_end)
        if currency != "RSD":
            sides = foreign_sides(row)
            if sides is None:
                item["fx_missing"] = True
            else:
                add_amounts(item["fx"], *sides, row, start, end, ytd_end)
        if start <= row["booking_date"] <= end:
            item["documents"].append(row)
    summaries = []
    for bank in banks:
        accounts = sorted([item for item in grouped.values() if item["code"] == bank["code"]], key=lambda x: (x["account"], x["currency"]))
        totals = empty_amounts()
        for item in accounts:
            for field in totals:
                totals[field] += item["rsd"][field]
        summaries.append(dict(bank, accounts=accounts, totals=totals))
    return dict(banks=summaries, unmapped=list(unmapped.values()), excluded=list(excluded.values()), ytd_end=ytd_end)


def report_for(user, banks, start, end):
    today = timezone.localdate()
    through = max(end, min(today, date(start.year, 12, 31)))
    entries = bank_entries(user, start.year, through).values("account", "account_name", "partner_group", "partner_code",
        "currency", "debit_credit_flag", "debit", "credit", "foreign_amount", "booking_date", "journal_type",
        "journal_number", "document_reference", "description", "pk").order_by("booking_date", "pk")
    return build_report(entries.iterator(), banks, BankAccountRule.objects.filter(company=company_id()), start, end, today)


def account_catalog():
    return list(LedgerEntry.objects.filter(company=company_id(), active=True).filter(
        Q(account__startswith="23") | Q(account__startswith="24")).order_by("account", "account_name").values_list("account", "account_name").distinct())
