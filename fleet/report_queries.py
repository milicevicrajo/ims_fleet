OMV_PUTNICKA_SQL = """
        SELECT sifpos, godina, mesec, tipvozila, polovina, bruto, neto
        FROM OMV_putnicka_sp
        WHERE 1=1
    """

NIS_PUTNICKA_SQL = """
        SELECT tipvozila, sifpos, godina, mesec, polovina, bruto, neto
        FROM dbo.NIS_putnicka_sp
        WHERE 1=1
    """

NIS_TERETNA_SQL = """
        SELECT tipvozila, sifpos, regozn, kartica, datum, proizvod, kolicina, cena, bruto, neto
        FROM dbo.nis_teretna
        WHERE 1=1
    """

OMV_TERETNA_SQL = """
        SELECT tipvozila, sifpos, godina, mesec, polovina, bruto, neto
        FROM dbo.OMV_teretna_sp
        WHERE 1=1
    """
