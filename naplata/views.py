from django.shortcuts import render, redirect
from django.http import HttpResponse
from decimal import Decimal
from django.db import connections
from django.core.exceptions import PermissionDenied
import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from fleet.mixins import role_permission_required
from .forms import KontaktiForm, NapomeneForm, OpomeneForm, PoziviTelForm, PozivPismoForm, TuzbeForm
from .models import Kontakti, Napomene, Opomene, PozivPismo, PoziviTel, Tuzbe, AvansKlijent


def _allowed_sif_pos_from_user(user):
    if user.is_superuser:
        return []

    codes = user.allowed_centers.values_list('code', flat=True)
    return sorted({str(code).strip() for code in codes if str(code).strip()})

@role_permission_required()
def lista_dugovanja(request):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("SELECT sif_par, naz_par, dug, pot FROM dbo.baza ORDER BY dug DESC")
        dugovanja = cursor.fetchall()
    total_dug = sum((Decimal(row[2] or 0) for row in dugovanja), Decimal("0"))
    total_pot = sum((Decimal(row[3] or 0) for row in dugovanja), Decimal("0"))

    return render(request, 'naplata/dugovanja.html', {
        'dugovanja': dugovanja,
        'total_dug': total_dug,
        'total_pot': total_pot,
    })


@never_cache
@role_permission_required()
def lista_tuzenih(request):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT
                god,
                sif_par,
                naz_par,
                datum,
                knt,
                naz_knt,
                duguju,
                platili
            FROM dbo.v_tuzeni
            ORDER BY god DESC, duguju DESC
        """)
        tuzeni = cursor.fetchall()

    total_duguju = sum((Decimal(row[6] or 0) for row in tuzeni), Decimal("0"))
    total_platili = sum((Decimal(row[7] or 0) for row in tuzeni), Decimal("0"))

    return render(request, 'naplata/tuzeni_list.html', {
        'tuzeni': tuzeni,
        'total_duguju': total_duguju,
        'total_platili': total_platili,
        'title': 'Utuženi Klijenti',
    })

@never_cache
@role_permission_required()
def lista_dugovanja_po_bucketima(request):
    marked_ids = set(AvansKlijent.objects.values_list('sif_par', flat=True))
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
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
                GROUP BY db.sif_par, db.naz_par, n.veliki, db.ino
                ORDER BY Ukupno DESC
            """)
        dugovanja = cursor.fetchall()

    return render(request, 'naplata/dugovanja_bucketi.html', {
        'dugovanja': dugovanja,
        'marked_ids': marked_ids,
        'title': 'Lista dugovanja po bucketima',
    })


@never_cache
def lista_avans_klijenti(request):
    marked_ids = list(AvansKlijent.objects.values_list('sif_par', flat=True))
    if not marked_ids:
        dugovanja = []
    else:
        placeholders = ",".join(["%s"] * len(marked_ids))
        with connections['naplata_db'].cursor() as cursor:
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
                    WHERE db.sif_par IN ({placeholders})
                    GROUP BY db.sif_par, db.naz_par, n.veliki, db.ino
                    ORDER BY Ukupno DESC
                """, marked_ids)
            dugovanja = cursor.fetchall()

    return render(request, 'naplata/dugovanja_bucketi_avans.html', {
        'dugovanja': dugovanja,
        'marked_ids': set(marked_ids),
        'title': 'Spisak za proveru',
    })


@never_cache
@role_permission_required()
def izvestaj_po_siframa_posla(request):
    allowed_sif_pos = _allowed_sif_pos_from_user(request.user)
    dugovanja = []
    marked_ids = set(AvansKlijent.objects.values_list('sif_par', flat=True))

    if request.user.is_superuser or allowed_sif_pos:
        with connections['naplata_db'].cursor() as cursor:
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
            if not request.user.is_superuser:
                placeholders = ",".join(["%s"] * len(allowed_sif_pos))
                sql += f" WHERE db.sif_pos IN ({placeholders})"
                params.extend(allowed_sif_pos)

            sql += """
                    GROUP BY db.sif_par, db.naz_par, n.veliki, db.ino
                    ORDER BY Ukupno DESC
                """
            cursor.execute(sql, params)
            dugovanja = cursor.fetchall()

    return render(request, 'naplata/izvestaj_sifra_posla.html', {
        'dugovanja': dugovanja,
        'marked_ids': marked_ids,
        'title': 'Izveštaj po šiframa posla',
        'report_mode': True,
        'report_allowed_sif_pos': allowed_sif_pos,
    })


@require_POST
@role_permission_required()
def toggle_avans_klijent(request):
    sif_par = request.POST.get('sif_par')
    if not sif_par:
        return redirect(request.META.get('HTTP_REFERER', 'naplata:lista_dugovanja_po_bucketima'))

    try:
        sif_par_int = int(sif_par)
    except (TypeError, ValueError):
        return redirect(request.META.get('HTTP_REFERER', 'naplata:lista_dugovanja_po_bucketima'))

    obj, created = AvansKlijent.objects.get_or_create(
        sif_par=sif_par_int,
        defaults={'created_by': request.user if request.user.is_authenticated else None},
    )
    if not created:
        obj.delete()

    return redirect(request.META.get('HTTP_REFERER', 'naplata:lista_dugovanja_po_bucketima'))


@role_permission_required()
def export_dugovanja_bucketi_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Dugovanja po baketima"

    # Header
    headers = [
        "Šifra partnera", "Naziv partnera", "Nedospelo", "Dospelo - baket 1", "Dospelo - baket 2",
        "Dospelo - baket 3", "Dospelo - baket 4", "Dospelo - baket 5", "Dospelo - baket 6", "Ukupno - Dospelo",
        "Ukupno", "Veliki", "INO"
    ]
    ws.append(headers)

    # SQL data
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
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
                GROUP BY db.sif_par, db.naz_par, n.veliki, db.ino
                ORDER BY Ukupno DESC
            """)
        rows = cursor.fetchall()
        for row in rows:
            ws.append(row)

    # Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=dugovanja_po_baketima.xlsx'
    wb.save(response)
    return response


@never_cache
@role_permission_required()
def detalji_partner(request, sif_par):
    report_mode = request.GET.get('report') == '1'
    report_allowed_sif_pos = _allowed_sif_pos_from_user(request.user) if report_mode else []

    if report_mode and not request.user.is_superuser and not report_allowed_sif_pos:
        raise PermissionDenied('Nije definisana šifra posla za korisnika.')

    if report_mode and not request.user.is_superuser:
        with connections['naplata_db'].cursor() as cursor:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            cursor.execute(f"""
                SELECT TOP 1 1
                FROM dodela_baketa
                WHERE sif_par = %s AND sif_pos IN ({placeholders})
            """, [sif_par, *report_allowed_sif_pos])
            if cursor.fetchone() is None:
                raise PermissionDenied('Nemate pristup ovom partneru za vašu šifru posla.')

    # 1. Osnovne informacije o partneru (view partneri)
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_pred, grupa, sif_par, naz_par, ulica_par, p_b_par, mesto_par, 
                   zr, mb, telefon, fax, email, lice, web, proc_rabata, br_dana, vlasnik, pib, zemlja, 
                   proc_rabata1, proc_rabata2, pdv_obveznik, sif_ter, JBKJS, CRF
            FROM partneri
            WHERE sif_par = %s
        """, [sif_par])
        partner = cursor.fetchone()


    # 2.1 Dugovanja (view baza)
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT 
                god AS Godina,
                oj AS OJ,
                sif_pos AS [šifra posla],
                sif_vrs AS vrsta,
                datum,
                vez_dok AS veza,
                dpo,
                skr_naz AS valuta,
                dug AS duguje,
                pot AS potražuje
            FROM baza
            WHERE sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            ORDER BY datum
        """
        cursor.execute(sql, params)
        dugovanja = cursor.fetchall()


    # 2.2 Dugovanja baketi (view baza)
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT 
                sb.opis,
                b.baket,
                b.sif_pos,
                b.vez_dok,
                b.dpo,
                b.duguje,
                b.potrazuje,
                b.saldo,
                sb.akcija
            FROM dodela_baketa b
            LEFT JOIN sif_baket sb ON b.baket = sb.baket
            WHERE b.sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND b.sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            ORDER BY b.baket
        """
        cursor.execute(sql, params)
        dugovanja_baket = cursor.fetchall()

        
    # 2.3 Dugovanja po fakturama
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT 
                br_naloga, 
                sif_par, 
                naz_par, 
                sif_vrs, 
                MAX(dat_naloga) AS poslednji_datum,  
                SUM(dug) AS ukupno_duguje, 
                SUM(pot) AS ukupno_potrazuje, 
                SUM(dug) - SUM(pot) AS saldo
            FROM baza
            WHERE sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            GROUP BY br_naloga, sif_par, naz_par, sif_vrs
            ORDER BY poslednji_datum DESC
        """
        cursor.execute(sql, params)
        dugovanja_sumarno = cursor.fetchall()


    # 3. Dospela potraživanja po bucketima (view dodela_bucketa)
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT sif_par, naz_par, vez_dok, sif_pos, duguje, potražuje, saldo,
                   dpo, danasnji_datum, broj_dana, baket, kategorija
            FROM dodela_baketa
            WHERE sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            ORDER BY baket
        """
        cursor.execute(sql, params)
        baketi = cursor.fetchall()

    # 4. Otpisana potraživanja (view ispravke)
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                god,
                oj,
                sif_pos AS [šifra posla],
                sif_vrs,
                datum,
                dpo,
                knt,
                naz_knt,
                dug,
                pot
            FROM ispravke
            WHERE sif_par = %s
            ORDER BY datum DESC
        """, [sif_par])
        ispravke = cursor.fetchall()




    # # 5. Ostale tabele (kontakti, pozivi, opomene, tužbe, napomene)
    kontakti = Kontakti.objects.using('naplata_db').filter(sif_par=sif_par)
    napomene = Napomene.objects.using('naplata_db').filter(sif_par=sif_par)
    opomene = Opomene.objects.using('naplata_db').filter(sif_par=sif_par)
    poziv_pismo = PozivPismo.objects.using('naplata_db').filter(sif_par=sif_par)
    pozivi_tel = PoziviTel.objects.using('naplata_db').filter(sif_par=sif_par)
    tuzbe = Tuzbe.objects.using('naplata_db').filter(sif_par=sif_par)
    

    # 6. Spisak faktura iz baketa 6
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT sif_par, naz_par as Naziv, TRIM(vez_dok) AS veza, sif_pos as [šifra posla], 
                    SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 181 AND sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """
        cursor.execute(sql, params)
        spisak_utuzenje = cursor.fetchall()

    # 7. Spisak faktura iz baketa 5
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT sif_par, naz_par, TRIM(vez_dok) AS veza, sif_pos, 
                SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, 
                SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 180 AND sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """
        cursor.execute(sql, params)
        opomene_fakture = cursor.fetchall()

    # 8. Spisak faktura iz baketa 4
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT sif_par, naz_par, LTRIM(RTRIM(vez_dok)) AS veza, sif_pos,
                SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 90 AND sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """
        cursor.execute(sql, params)
        fakture_baket_90 = cursor.fetchall()

    # 9. Spisak faktura iz baketa 3
    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT sif_par, naz_par as Naziv, 
                   LTRIM(RTRIM(vez_dok)) AS veza, 
                   sif_pos AS [šifra posla], 
                   SUM(duguje) AS duguje, 
                   SUM(potrazuje) AS potrazuje, 
                   SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 60 AND sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += """
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """
        cursor.execute(sql, params)
        fakture_baket_60 = cursor.fetchall()

    # Slanje svih podataka u template
    return render(request, 'naplata/detalji_partner.html', {
        'partner': partner,
        'dugovanja': dugovanja,
        'baketi': baketi,
        'ispravke': ispravke,
        'kontakti': kontakti,
        'pozivi_tel': pozivi_tel,
        'opomene': opomene,
        'poziv_pismo': poziv_pismo,
        'tuzbe': tuzbe,
        'napomene': napomene,
        'dugovanja_baket':dugovanja_baket,
        'dugovanja_sumarno':dugovanja_sumarno,
        'spisak_utuzenje': spisak_utuzenje,
        'opomene_fakture': opomene_fakture,
        'fakture_baket_90': fakture_baket_90,
        'fakture_baket_60':fakture_baket_60,
        'report_mode': report_mode,
        'report_allowed_sif_pos': report_allowed_sif_pos,
    })


@role_permission_required()
def export_partner_baketi_excel(request, sif_par):
    report_mode = request.GET.get('report') == '1'
    report_allowed_sif_pos = _allowed_sif_pos_from_user(request.user) if report_mode else []

    if report_mode and not request.user.is_superuser and not report_allowed_sif_pos:
        raise PermissionDenied('Nije definisana šifra posla za korisnika.')

    with connections['naplata_db'].cursor() as cursor:
        sql = """
            SELECT
                sb.opis,
                b.baket,
                b.sif_pos,
                b.vez_dok,
                b.dpo,
                b.duguje,
                b.potrazuje,
                b.saldo,
                sb.akcija
            FROM dodela_baketa b
            LEFT JOIN sif_baket sb ON b.baket = sb.baket
            WHERE b.sif_par = %s
        """
        params = [sif_par]
        if report_mode and not request.user.is_superuser:
            placeholders = ",".join(["%s"] * len(report_allowed_sif_pos))
            sql += f" AND b.sif_pos IN ({placeholders})"
            params.extend(report_allowed_sif_pos)
        sql += " ORDER BY b.baket"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dugovanja baketi"

    headers = [
        "Opis", "Baketi", "Šifra posla", "Veza", "DPO", "Duguje", "Potražuje", "Saldo", "Akcija"
    ]
    ws.append(headers)
    for row in rows:
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=dugovanja_baketi_partner_{sif_par}.xlsx'
    wb.save(response)
    return response

@role_permission_required()
def export_utuzene_fakture_excel(request, sif_par):
    # 1. Izvrši upit
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par as Naziv, TRIM(vez_dok) AS veza, sif_pos as [šifra posla], 
                   SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 181 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """, [sif_par])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    # 2. Kreiraj Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Za utuženje"

    # 3. Naslovi kolona
    header_font = Font(bold=True)
    for col_num, column_title in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_num, value=column_title)
        cell.font = header_font
        ws.column_dimensions[get_column_letter(col_num)].width = 18

    # 4. Dodaj redove
    for row_index, row in enumerate(rows, 2):
        for col_index, value in enumerate(row, 1):
            ws.cell(row=row_index, column=col_index, value=value)

    # 5. Pripremi fajl za slanje kao response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=utuzene_fakture.xlsx'
    wb.save(response)
    return response

@role_permission_required()
def export_opomene_excel(request,sif_par):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par as Naziv, TRIM(vez_dok) AS veza, sif_pos as [šifra posla], 
                   SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 180 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """, [sif_par])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

    # Kreiraj Excel fajl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Za opomene"

    # Zaglavlje
    header_font = Font(bold=True)
    for col_num, column_title in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_num, value=column_title)
        cell.font = header_font
        ws.column_dimensions[get_column_letter(col_num)].width = 18

    # Podaci
    for row_index, row in enumerate(rows, 2):
        for col_index, value in enumerate(row, 1):
            ws.cell(row=row_index, column=col_index, value=value)

    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=opomene_fakture.xlsx'
    wb.save(response)
    return response


@role_permission_required()
def export_baket_90_excel(request, sif_par):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par, LTRIM(RTRIM(vez_dok)), sif_pos,
                   SUM(duguje), SUM(potrazuje), SUM(saldo)
            FROM dodela_baketa
            WHERE baket = 90 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """, [sif_par])
        data = cursor.fetchall()

    # Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Baket 90"

    headers = ['Šifra partnera', 'Naziv', 'Veza', 'Šifra posla', 'Duguje', 'Potražuje', 'Saldo']
    ws.append(headers)

    for row in data:
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=baket_90.xlsx'
    wb.save(response)
    return response

@role_permission_required()
def export_baket_60_excel(request, sif_par):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par, LTRIM(RTRIM(vez_dok)), sif_pos,
                   SUM(duguje), SUM(potrazuje), SUM(saldo)
            FROM dodela_baketa
            WHERE baket = 60 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """, [sif_par])
        data = cursor.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Baket 60"

    headers = ['Šifra partnera', 'Naziv', 'Veza', 'Šifra posla', 'Duguje', 'Potražuje', 'Saldo']
    ws.append(headers)

    for row in data:
        ws.append(row)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=baket_60_sifpar_{sif_par}.xlsx'
    wb.save(response)
    return response

# <!-- ======================================================================= -->
#                           <!-- KONTAKTI -->
# <!-- ======================================================================= -->

@role_permission_required()
def lista_kontakata(request):
    kontakti = Kontakti.objects.using('naplata_db').all()
    return render(request, 'naplata/kontakti_lista.html', {'kontakti': kontakti})


@role_permission_required()
def dodaj_kontakt(request, sif_par, naz_par):
    if request.method == "POST":
        form = KontaktiForm(request.POST)
        if form.is_valid():
            kontakt = form.save(commit=False)
            kontakt.sif_par = sif_par  # Automatski dodeljujemo šifru partnera
            kontakt.naz_par = naz_par
            kontakt.save(using='naplata_db')  # Upisujemo u eksternu bazu
            return redirect('naplata:detalji_partner', sif_par = sif_par)
    else:
        form = KontaktiForm(initial={'sif_par': sif_par, 'naz_par': naz_par})

    return render(request, 'naplata/form_naplata.html', {'form': form})


@role_permission_required()
def izmeni_kontakt(request, sif_par):
    kontakt = get_object_or_404(Kontakti.objects.using('naplata_db'), sif_par=sif_par)
    if request.method == "POST":
        form = KontaktiForm(request.POST, instance=kontakt)
        if form.is_valid():
            kontakt = form.save(commit=False)

            kontakt.save(using='naplata_db')
            return redirect('naplata:detalji_partner', sif_par = sif_par)
    else:
        form = KontaktiForm(instance=kontakt)
    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def obrisi_kontakt(request, id):
    kontakt = get_object_or_404(Kontakti.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        kontakt.delete(using='naplata_db')
    return redirect(request.META.get('HTTP_REFERER', 'lista_kontakata'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- NAPOMENE -->
# <!-- ======================================================================= -->
@role_permission_required()
def lista_napomena(request):
    napomene = Napomene.objects.using('naplata_db').all()
    return render(request, 'naplata/napomena_lista.html', {'napomene': napomene})

@role_permission_required()
def dodaj_napomenu(request, sif_par, naz_par):
    if request.method == "POST":
        form = NapomeneForm(request.POST)
        if form.is_valid():
            napomena = form.save(commit=False)
            napomena.sif_par = sif_par  # Postavljamo partnera automatski
            napomena.naz_par = naz_par
            napomena.save(using='naplata_db')
            return redirect('naplata:detalji_partner', sif_par = sif_par)
    else:
        form = NapomeneForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  # Automatsko popunjavanje

    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def izmeni_napomenu(request, id):
    napomena = get_object_or_404(Napomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = NapomeneForm(request.POST, instance=napomena)
        if form.is_valid():
            napomena = form.save(commit=False)
            napomena.save(using='naplata_db')
            return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    else:
        form = NapomeneForm(instance=napomena)
    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def obrisi_napomenu(request, id):
    napomena = get_object_or_404(Napomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        napomena.delete(using='naplata_db')
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- OPOMENE -->
# <!-- ======================================================================= -->
@role_permission_required()
def lista_opomena(request):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT
                sif_par,
                naz_par,
                god,
                br_opomene,
                datum,
                iznos,
                fakture,
                napomene,
                id
            FROM opomene
            WHERE god = 2024
            ORDER BY god DESC, datum DESC
        """)
        opomene = cursor.fetchall()
    return render(request, 'naplata/opomene_list.html', {
        'opomene': opomene,
        'title': 'Lista opomena',
    })

@role_permission_required()
def dodaj_opomenu(request, sif_par, naz_par):
    if request.method == "POST":
        form = OpomeneForm(request.POST)
        if form.is_valid():
            opomena = form.save(commit=False)
            opomena.sif_par = sif_par  
            opomena.naz_par = naz_par
            opomena.save(using='naplata_db')
            return redirect('naplata:detalji_partner', sif_par = sif_par)
        else:
            print("Forma nije validna!", form.errors)  # Ispis grešaka u konzoli
    else:
        form = OpomeneForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def izmeni_opomenu(request, id):
    opomena = get_object_or_404(Opomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = OpomeneForm(request.POST, instance=opomena)
        if form.is_valid():
            form.save(using='naplata_db')
            return redirect('lista_opomena')
    else:
        form = OpomeneForm(instance=opomena)
    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def obrisi_opomenu(request, id):
    opomena = get_object_or_404(Opomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        opomena.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici

    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- POZIVI -->
# <!-- ======================================================================= -->
@role_permission_required()
def lista_poziva(request):
    pozivi = PoziviTel.objects.using('naplata_db').all()
    return render(request, 'naplata/pozivi_tel/lista.html', {'pozivi': pozivi})

@role_permission_required()
def dodaj_poziv(request, sif_par, naz_par):
    if request.method == "POST":
        form = PoziviTelForm(request.POST)
        if form.is_valid():
            poziv = form.save(commit=False)
            poziv.sif_par = sif_par  # Automatski postavljamo vrednost
            poziv.naz_par = naz_par
            poziv.save(using='naplata_db')
            return redirect('naplata:detalji_partner', sif_par = sif_par)

    else:
        form = PoziviTelForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def izmeni_poziv(request, id):
    poziv = get_object_or_404(PoziviTel.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = PoziviTelForm(request.POST, instance=poziv)
        if form.is_valid():
            form.save(using='naplata_db')
            return redirect('lista_poziva')
    else:
        form = PoziviTelForm(instance=poziv)
    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def obrisi_poziv(request, id):
    poziv = get_object_or_404(PoziviTel.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        poziv.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- POZIVI/PISMA -->
# <!-- ======================================================================= -->
@role_permission_required()
def lista_pozivnih_pisma(request):
    pozivi = PozivPismo.objects.using('naplata_db').all()
    return render(request, 'naplata/poziv_pismo/lista.html', {'pozivi': pozivi})

@role_permission_required()
def dodaj_poziv_pismo(request, sif_par, naz_par):
    if request.method == "POST":
        form = PozivPismoForm(request.POST)
        if form.is_valid():
            poziv = form.save(commit=False)
            poziv.sif_par = sif_par  # Automatski postavljamo vrednost
            poziv.naz_par = naz_par
            poziv.save(using='naplata_db')
            return redirect('naplata:detalji_partner', sif_par = sif_par)
    else:
        form = PozivPismoForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def izmeni_poziv_pismo(request, id):
    poziv = get_object_or_404(PozivPismo.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = PozivPismoForm(request.POST, instance=poziv)
        if form.is_valid():
            form.save(using='naplata_db')
            return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    else:
        form = PozivPismoForm(instance=poziv)
    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def obrisi_poziv_pismo(request, id):
    poziv = get_object_or_404(PozivPismo.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        poziv.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return render(request, 'naplata/poziv_pismo/obrisi.html', {'poziv': poziv})


# <!-- ======================================================================= -->
#                           <!-- TUZBE -->
# <!-- ======================================================================= -->
@role_permission_required()
def lista_tuzbi(request):
    tuzbe = Tuzbe.objects.using('naplata_db').all()
    return render(request, 'naplata/tuzbe/lista.html', {'tuzbe': tuzbe})

@role_permission_required()
def dodaj_tuzbu(request, sif_par, naz_par):
    if request.method == "POST":
        form = TuzbeForm(request.POST)
        if form.is_valid():
            tuzba = form.save(commit=False)
            tuzba.sif_par = sif_par  # Automatski postavljamo vrednost
            tuzba.naz_par = naz_par
            tuzba.save(using='naplata_db')
            return redirect('naplata:detalji_partner', sif_par = sif_par)
    else:
        form = TuzbeForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def izmeni_tuzbu(request, id):
    tuzba = get_object_or_404(Tuzbe.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = TuzbeForm(request.POST, instance=tuzba)
        if form.is_valid():
            form.save(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    else:
        form = TuzbeForm(instance=tuzba)
    return render(request, 'naplata/form_naplata.html', {'form': form})

@role_permission_required()
def obrisi_tuzbu(request, id):
    tuzba = get_object_or_404(Tuzbe.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        tuzba.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici

@role_permission_required()
def obrisi_tuzbu(request, id):
    tuzba = get_object_or_404(Tuzbe.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        tuzba.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici



