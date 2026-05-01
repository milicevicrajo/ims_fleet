from django.db import connections


def dugovanja_po_bucketima_rows(sif_par_values=None):
    params = []
    where_clause = ""
    if sif_par_values is not None:
        sif_par_values = list(sif_par_values)
        if not sif_par_values:
            return []
        placeholders = ",".join(["%s"] * len(sif_par_values))
        where_clause = f"WHERE db.sif_par IN ({placeholders})"
        params.extend(sif_par_values)

    with connections['server_db'].cursor() as cursor:
        cursor.execute(f"""
                SELECT
                    db.sif_par,
                    db.naz_par,
                    SUM(CASE WHEN db.baket = 0.1 THEN db.saldo ELSE 0 END) AS Nedospelo,
                    SUM(CASE WHEN db.baket = 30 THEN db.saldo ELSE 0 END) AS "Dospelo - baket 1",
                    SUM(CASE WHEN db.baket = 45 THEN db.saldo ELSE 0 END) AS "Dospelo - baket 2",
                    SUM(CASE WHEN db.baket = 60 THEN db.saldo ELSE 0 END) AS "Dospelo - baket 3",
                    SUM(CASE WHEN db.baket = 90 THEN db.saldo ELSE 0 END) AS "Dospelo - baket 4",
                    SUM(CASE WHEN db.baket = 180 THEN db.saldo ELSE 0 END) AS "Dospelo - baket 5",
                    SUM(CASE WHEN db.baket = 181 THEN db.saldo ELSE 0 END) AS "Dospelo - baket 6",
                    -- Nova kolona: DOSPELO (sve osim 0.1)
                    SUM(CASE WHEN db.baket != 0.1 THEN db.saldo ELSE 0 END) AS Dospelo,
                    SUM(db.saldo) AS Ukupno,
                    n.veliki,
                    db.ino
                FROM dodela_baketa db
                LEFT JOIN (
                    SELECT sif_par, MAX(veliki) AS veliki
                    FROM napomene
                    GROUP BY sif_par
                ) n ON db.sif_par = n.sif_par
                {where_clause}
                GROUP BY db.sif_par, db.naz_par, n.veliki, db.ino
                ORDER BY Ukupno DESC
            """, params)
        return cursor.fetchall()


def izvestaj_po_siframa_posla_data(is_superuser, allowed_sif_pos, selected_sif_pos):
    if not is_superuser and not allowed_sif_pos:
        return [], []

    with connections['server_db'].cursor() as cursor:
        options_sql = "SELECT DISTINCT db.sif_pos FROM dodela_baketa db"
        options_params = []
        if not is_superuser:
            option_placeholders = ",".join(["%s"] * len(allowed_sif_pos))
            options_sql += f" WHERE db.sif_pos IN ({option_placeholders})"
            options_params.extend(allowed_sif_pos)
        options_sql += " ORDER BY db.sif_pos"
        cursor.execute(options_sql, options_params)
        sif_pos_options = [
            str(row[0]).strip()
            for row in cursor.fetchall()
            if row and row[0] is not None
        ]

        sql = """
                SELECT
                    db.sif_par,
                    db.naz_par,
                    SUM(CASE WHEN db.baket = 0.1 THEN db.saldo ELSE 0 END) AS Nedospelo,
                    SUM(CASE WHEN db.baket = 30 THEN db.saldo ELSE 0 END) AS [Dospelo - baket 1],
                    SUM(CASE WHEN db.baket = 45 THEN db.saldo ELSE 0 END) AS [Dospelo - baket 2],
                    SUM(CASE WHEN db.baket = 60 THEN db.saldo ELSE 0 END) AS [Dospelo - baket 3],
                    SUM(CASE WHEN db.baket = 90 THEN db.saldo ELSE 0 END) AS [Dospelo - baket 4],
                    SUM(CASE WHEN db.baket = 180 THEN db.saldo ELSE 0 END) AS [Dospelo - baket 5],
                    SUM(CASE WHEN db.baket = 181 THEN db.saldo ELSE 0 END) AS [Dospelo - baket 6],
                    SUM(CASE WHEN db.baket != 0.1 THEN db.saldo ELSE 0 END) AS Dospelo,
                    SUM(db.saldo) AS Ukupno,
                    n.veliki,
                    db.ino
                FROM dodela_baketa db
                LEFT JOIN (
                    SELECT sif_par, MAX(veliki) AS veliki
                    FROM napomene
                    GROUP BY sif_par
                ) n ON db.sif_par = n.sif_par
        """
        params = []
        where_clauses = []
        if not is_superuser:
            placeholders = ",".join(["%s"] * len(allowed_sif_pos))
            where_clauses.append(f"db.sif_pos IN ({placeholders})")
            params.extend(allowed_sif_pos)

        if selected_sif_pos:
            where_clauses.append("db.sif_pos = %s")
            params.append(selected_sif_pos)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        sql += """
                GROUP BY db.sif_par, db.naz_par, n.veliki, db.ino
                ORDER BY Ukupno DESC
            """
        cursor.execute(sql, params)
        dugovanja = cursor.fetchall()

    return dugovanja, sif_pos_options


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
