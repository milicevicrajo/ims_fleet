"""Contract amounts are stored on Lease, with an explicit monthly/total basis."""
import calendar
from datetime import timedelta
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
