KASKO_RATE_SQL = "SELECT * FROM dbo.kasko_rate"

MAGACIN_SQL = """
        SELECT sif_pred, god, oj, sif_mag, sif_art, kolul, koliz, popkol, vrulnab, vriznab,
               vrulvp, vrizvp, revalzal, razliz, mag_cena, kolpon, cenapon, naz_art,
               sif_vrsart, naz_vrsart
        FROM dbo.fleet_magacin_rez
    """

OTPIS_SQL = """
        SELECT sif_pred, god, sif_osn, rb, naz_osn, inv_br, kol, jed_mere, sif_par, knt, oj, sif_lok,
               sif_amort, sif_reval, stopa_dogam, dat_stavlj, dat_prest, iznos_val, skr_naz, poreklo,
               nab_vred, osnovica, otpis, status, br_fakture, zemljiste_ar, zemljiste_m, u_gramima,
               sif_amortP, sif_revalP, otpisP, otudjena_vrednost, ind_trosak, opis, osnovicaP,
               ind_manjak, ind_amort, knt_ispravka, sif_kor, stopa_amort
        FROM dbo.fleet_otpis
    """

TRO_GORIVO_MESEC_SQL = """
        SELECT god, mesec, kategorija, iznos
        FROM dbo.fleet_tro_goriva_m
    """

TROSKOVI_SVI_SQL = """
        SELECT god, sif_vrs, datum, br_naloga, stavka, oj, knt, naz_knt, duguje, sif_pos
        FROM dbo.fleet_tro_svi
    """

TRO_PRACENJA_VOZILA_SQL = """
        SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, ZaPlacanje, Konto_tro
        FROM dbo.fleet_tro_pracenje
    """

TAHOGRAF_PARTNERI_SQL = """
        SELECT *
        FROM dbo.fleet_tro_taho
    """

TRO_ZARADE_SQL = """
        SELECT oj, god, mesec, rasif, ranaz, neto, bruto, bruto2
        FROM dbo.tro_zarade
    """

TRO_PARKING_SQL = """
        SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, note, naziv, ZaPlacanje
        FROM dbo.fleet_tro_parking
    """

PO_DOBAVLJACIMA_SQL = """
        SELECT naz_par, sif_pred, god, sif_vrs, br_naloga, stavka, oj, knt, grupa, sif_par, datum, vez_dok,
               duguje, potrazuje, skr_naz, deviza, kom, stavka_k, dpo, promena, sif_pos, dat_naloga, d_p, placeno
        FROM dbo.fleet_dobavljaci
    """

POTRAZIVANJE_DDOR_SQL = """
        SELECT god, sif_vrs, br_naloga, stavka, oj, knt, datum, vez_dok, potrazuje
        FROM dbo.fleet_potrazivanje_ddor
    """
