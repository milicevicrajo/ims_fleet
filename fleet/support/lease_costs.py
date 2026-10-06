"""Contract amounts are stored on Lease, with an explicit monthly/total basis."""
import calendar
from datetime import date, timedelta
from decimal import Decimal


def lease_daily_amount(lease, day):
    if not lease.start_date <= day <= lease.end_date:
        return Decimal(0)
    amount = lease.current_payment_amount
    if amount is None or amount < 0:
        return None
    if lease.payment_basis == 'monthly':
        return amount / Decimal(calendar.monthrange(day.year, day.month)[1])
    if lease.payment_basis == 'total':
        return amount / Decimal((lease.end_date - lease.start_date).days + 1)
    return None


def lease_amount_between(lease, start, end):
    start, end = max(start, lease.start_date), min(end, lease.end_date)
    if end < start:
        return Decimal(0)
    if lease_daily_amount(lease, start) is None:
        return None
    if lease.payment_basis == 'total':
        return lease.current_payment_amount * ((end - start).days + 1) / Decimal((lease.end_date - lease.start_date).days + 1)
    # Sum month segments, preserving actual calendar lengths, including leap years.
    result = Decimal(0)
    day = start
    while day <= end:
        last = min(end, day.replace(day=calendar.monthrange(day.year, day.month)[1]))
        result += lease.current_payment_amount * ((last - day).days + 1) / Decimal(calendar.monthrange(day.year, day.month)[1])
        day = last + timedelta(days=1)
    return result


def lease_days_in_year(lease, year):
    """Broj dana ugovora u kalendarskoj godini (oba kraja uključena)."""
    start, end = max(lease.start_date, date(year, 1, 1)), min(lease.end_date, date(year, 12, 31))
    return max((end - start).days + 1, 0)


def interest_daily_amount(lease, amount, day):
    """Dnevni deo kamate finansijskog lizinga (od 05.10.2026.).

    Upisuje se stvarna kamata za kalendarsku godinu; deli se na dane ugovora **u toj godini**, pa
    delimična prva i poslednja godina ulaze u celosti (ranije: deljenje sa 365/366 dana godine).
    """
    if amount is None:
        return None
    days = lease_days_in_year(lease, day.year)
    return amount / Decimal(days) if days else Decimal(0)
