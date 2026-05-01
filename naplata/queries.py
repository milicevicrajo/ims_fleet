from django.db import connections


def neodobrene_if_filters_from_request(request):
    return {
        'god': (request.GET.get('god') or '').strip(),
        'sifra_partnera': (request.GET.get('sifra_partnera') or '').strip(),
        'naziv_partnera': (request.GET.get('naziv_partnera') or '').strip(),
        'status_na_sefu': (request.GET.get('status_na_sefu') or '').strip(),
    }


def neodobrene_if_options():
    with connections['server_db'].cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT CAST(god AS NVARCHAR(10)) AS god
            FROM v_neodobreneIF
            WHERE god IS NOT NULL
            ORDER BY CAST(god AS NVARCHAR(10)) DESC
        """)
        god_options = [
            str(row[0]).strip()
            for row in cursor.fetchall()
            if row and row[0] is not None and str(row[0]).strip()
        ]

        cursor.execute("""
            SELECT DISTINCT LTRIM(RTRIM([Status na sefu])) AS status_na_sefu
            FROM v_neodobreneIF
            WHERE [Status na sefu] IS NOT NULL
              AND LTRIM(RTRIM([Status na sefu])) <> ''
            ORDER BY LTRIM(RTRIM([Status na sefu]))
        """)
        status_options = [
            str(row[0]).strip()
            for row in cursor.fetchall()
            if row and row[0] is not None and str(row[0]).strip()
        ]

        cursor.execute("""
            SELECT DISTINCT
                CAST([sifra partnera] AS NVARCHAR(50)) AS sifra_partnera,
                LTRIM(RTRIM([naziv partnera])) AS naziv_partnera
            FROM v_neodobreneIF
            WHERE [sifra partnera] IS NOT NULL
            ORDER BY CAST([sifra partnera] AS NVARCHAR(50))
        """)
        partner_options = [
            {
                'sifra': str(row[0]).strip(),
                'naziv': str(row[1]).strip() if row[1] is not None else '',
            }
            for row in cursor.fetchall()
            if row and row[0] is not None and str(row[0]).strip()
        ]

        cursor.execute("""
            SELECT DISTINCT LTRIM(RTRIM([naziv partnera])) AS naziv_partnera
            FROM v_neodobreneIF
            WHERE [naziv partnera] IS NOT NULL
              AND LTRIM(RTRIM([naziv partnera])) <> ''
            ORDER BY LTRIM(RTRIM([naziv partnera]))
        """)
        naziv_options = [
            str(row[0]).strip()
            for row in cursor.fetchall()
            if row and row[0] is not None and str(row[0]).strip()
        ]

    return god_options, status_options, partner_options, naziv_options


def neodobrene_if_rows(filters):
    sql = """
        SELECT
            oj,
            CAST(god AS NVARCHAR(10)) AS god,
            datum,
            [sifra partnera] AS sifra_partnera,
            LTRIM(RTRIM([naziv partnera])) AS naziv_partnera,
            LTRIM(RTRIM(faktura)) AS faktura,
            LTRIM(RTRIM([Status na sefu])) AS status_na_sefu,
            [vreme statusa] AS vreme_statusa,
            komentar
        FROM v_neodobreneIF
    """
    params = []
    where_clauses = []

    if filters.get('god'):
        where_clauses.append("CAST(god AS NVARCHAR(10)) = %s")
        params.append(filters['god'])

    if filters.get('sifra_partnera'):
        where_clauses.append("CAST([sifra partnera] AS NVARCHAR(50)) = %s")
        params.append(filters['sifra_partnera'])

    if filters.get('naziv_partnera'):
        where_clauses.append("LTRIM(RTRIM([naziv partnera])) = %s")
        params.append(filters['naziv_partnera'])

    if filters.get('status_na_sefu'):
        where_clauses.append("LTRIM(RTRIM([Status na sefu])) = %s")
        params.append(filters['status_na_sefu'])

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += " ORDER BY [vreme statusa] DESC, datum DESC, [sifra partnera] ASC"

    with connections['server_db'].cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()
