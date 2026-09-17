"""Read-only employee evidence; payroll amounts await confirmed allocation rules."""
from django.db import connections


PAYROLL = "[PUTGEO-SERVER].[bazaldims].dbo"


def payroll_employees(company, code, start, end):
    """A person is listed once per month, across all closed payroll runs.

    This is evidence of payroll entries on a job, not a historical HR roster
    or a calculation of hours, headcount equivalents, or employer cost.
    """
    if start.year != end.year or start > end:
        raise ValueError("Expected a period within one year")
    with connections["server_db"].cursor() as cursor:
        cursor.execute(f"""
            SELECT z.mesec, z.rasif, MAX(RTRIM(r.ranaz)),
                   COUNT(DISTINCT z.br_obr)
            FROM {PAYROLL}.Zarada z
            LEFT JOIN {PAYROLL}.Radnik r
              ON r.sif_pred = z.sif_pred AND r.rasif = z.rasif
            WHERE z.sif_pred = %s AND z.god = %s
              AND z.mesec BETWEEN %s AND %s AND z.sif_pos = %s
              AND (COALESCE(z.dinara, 0) <> 0 OR COALESCE(z.rekol, 0) <> 0)
              AND EXISTS (
                  SELECT 1 FROM {PAYROLL}.PomLD p
                  WHERE p.sif_pred = z.sif_pred AND p.god = z.god
                    AND p.mesec = z.mesec AND p.br_obr = z.br_obr
                    AND p.status_obr = 'Z'
              )
            GROUP BY z.mesec, z.rasif
            ORDER BY z.mesec, z.rasif
        """, [company, str(start.year), start.month, end.month, code])
        rows = list(cursor.fetchall())
        cursor.execute(f"""
            SELECT mesec, status_obr FROM {PAYROLL}.PomLD
            WHERE sif_pred = %s AND god = %s AND mesec BETWEEN %s AND %s
            GROUP BY mesec, status_obr
            ORDER BY mesec, status_obr
        """, [company, str(start.year), start.month, end.month])
        periods = cursor.fetchall()
    return {"rows": rows,
            "closed_months": sorted({month for month, status in periods if (status or "").strip() == "Z"}),
            "open_months": sorted({month for month, status in periods if (status or "").strip() == "O"})}
