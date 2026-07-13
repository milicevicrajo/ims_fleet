from dataclasses import dataclass
from decimal import Decimal

from django.db import connection

from fleet.models import PutniNalog


@dataclass
class PutniNaloziPaymentSyncResult:
    view_rows: int = 0
    matched_orders: int = 0
    updated_orders: int = 0
    skipped_unchanged: int = 0

    def summary(self):
        return (
            f"view_redova={self.view_rows}, "
            f"pronadjeno_naloga={self.matched_orders}, "
            f"azurirano={self.updated_orders}, "
            f"preskoceno_bez_promene={self.skipped_unchanged}"
        )


def _chunks(items, size=500):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def fetch_paid_amounts_from_view(order_number=None):
    params = []
    where = ""
    if order_number:
        where = "WHERE LTRIM(RTRIM(order_number)) = %s"
        params.append(str(order_number).strip())

    query = f"""
        SELECT LTRIM(RTRIM(order_number)) AS order_number,
               SUM(CAST(iznos AS decimal(18, 2))) AS isplaceno
        FROM [dbo].[fleet_zatvoren_putni]
        {where}
        GROUP BY LTRIM(RTRIM(order_number))
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return {
            str(row[0]).strip(): row[1] or Decimal("0.00")
            for row in cursor.fetchall()
            if row[0]
        }


def sync_putni_nalozi_paid_amounts(order_number=None, dry_run=False):
    paid_amounts = fetch_paid_amounts_from_view(order_number=order_number)
    result = PutniNaloziPaymentSyncResult(view_rows=len(paid_amounts))
    if not paid_amounts:
        return result

    updates = []
    for chunk in _chunks(list(paid_amounts)):
        orders = PutniNalog.objects.filter(order_number__in=chunk).only("id", "order_number", "isplaceno")
        for order in orders:
            result.matched_orders += 1
            new_amount = paid_amounts.get(order.order_number, Decimal("0.00"))
            if order.isplaceno == new_amount:
                result.skipped_unchanged += 1
                continue
            order.isplaceno = new_amount
            updates.append(order)

    result.updated_orders = len(updates)
    if updates and not dry_run:
        PutniNalog.objects.bulk_update(updates, ["isplaceno"], batch_size=500)

    return result
