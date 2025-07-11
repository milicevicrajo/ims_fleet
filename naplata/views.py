from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connections
import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font
from django.shortcuts import render, get_object_or_404
from .forms import KontaktiForm, NapomeneForm, OpomeneForm, PoziviTelForm, PozivPismoForm, TuzbeForm
from .models import Kontakti, Napomene, Opomene, PozivPismo, PoziviTel, Tuzbe

def lista_dugovanja(request):
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("SELECT sif_par, naz_par, dug, pot FROM dbo.baza ORDER BY dug DESC")
        dugovanja = cursor.fetchall()

    return render(request, 'fleet/naplata/dugovanja.html', {'dugovanja': dugovanja})

def lista_dugovanja_po_bucketima(request):
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

    return render(request, 'fleet/naplata/dugovanja_bucketi.html', {'dugovanja': dugovanja})


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


def detalji_partner(request, sif_par):
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
        cursor.execute("""
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
            ORDER BY datum
        """, [sif_par])
        dugovanja = cursor.fetchall()


    # 2.2 Dugovanja baketi (view baza)
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
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
            ORDER BY b.baket
        """, [sif_par])
        dugovanja_baket = cursor.fetchall()

        
    # 2.3 Dugovanja po fakturama
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
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
            GROUP BY br_naloga, sif_par, naz_par, sif_vrs
            ORDER BY poslednji_datum DESC
        """, [sif_par])
        dugovanja_sumarno = cursor.fetchall()


    # 3. Dospela potraživanja po bucketima (view dodela_bucketa)
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par, vez_dok, sif_pos, duguje, potražuje, saldo,
                   dpo, danasnji_datum, broj_dana, baket, kategorija
            FROM dodela_baketa
            WHERE sif_par = %s
            ORDER BY baket
        """, [sif_par])
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
        cursor.execute("""
            SELECT sif_par, naz_par as Naziv, TRIM(vez_dok) AS veza, sif_pos as [šifra posla], 
                    SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 181 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """,[sif_par])
        spisak_utuzenje = cursor.fetchall()

    # 7. Spisak faktura iz baketa 5
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par, TRIM(vez_dok) AS veza, sif_pos, 
                SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, 
                SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 180 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """, [sif_par])
        opomene_fakture = cursor.fetchall()

    # 8. Spisak faktura iz baketa 4
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par, LTRIM(RTRIM(vez_dok)) AS veza, sif_pos,
                SUM(duguje) AS duguje, SUM(potrazuje) AS potrazuje, SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 90 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """, [sif_par])
        fakture_baket_90 = cursor.fetchall()

    # 9. Spisak faktura iz baketa 3
    with connections['naplata_db'].cursor() as cursor:
        cursor.execute("""
            SELECT sif_par, naz_par as Naziv, 
                   LTRIM(RTRIM(vez_dok)) AS veza, 
                   sif_pos AS [šifra posla], 
                   SUM(duguje) AS duguje, 
                   SUM(potrazuje) AS potrazuje, 
                   SUM(saldo) AS saldo
            FROM dodela_baketa
            WHERE baket = 60 AND sif_par = %s
            GROUP BY sif_par, naz_par, vez_dok, sif_pos
            ORDER BY sif_par
        """,[sif_par])
        fakture_baket_60 = cursor.fetchall()

    # Slanje svih podataka u template
    return render(request, 'fleet/naplata/detalji_partner.html', {
        'partner': partner,
        'dugovanja': dugovanja,
        'baketi': baketi,
        # 'ispravke': ispravke,
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
        'fakture_baket_60':fakture_baket_60
    })

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

def lista_kontakata(request):
    kontakti = Kontakti.objects.using('naplata_db').all()
    return render(request, 'fleet/naplata/kontakti_lista.html', {'kontakti': kontakti})


def dodaj_kontakt(request, sif_par, naz_par):
    if request.method == "POST":
        form = KontaktiForm(request.POST)
        if form.is_valid():
            kontakt = form.save(commit=False)
            kontakt.sif_par = sif_par  # Automatski dodeljujemo šifru partnera
            kontakt.naz_par = naz_par
            kontakt.save(using='naplata_db')  # Upisujemo u eksternu bazu
            return redirect('detalji_partner', sif_par = sif_par)
    else:
        form = KontaktiForm(initial={'sif_par': sif_par, 'naz_par': naz_par})

    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})


def izmeni_kontakt(request, sif_par):
    kontakt = get_object_or_404(Kontakti.objects.using('naplata_db'), sif_par=sif_par)
    if request.method == "POST":
        form = KontaktiForm(request.POST, instance=kontakt)
        if form.is_valid():
            kontakt = form.save(commit=False)

            kontakt.save(using='naplata_db')
            return redirect('detalji_partner', sif_par = sif_par)
    else:
        form = KontaktiForm(instance=kontakt)
    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def obrisi_kontakt(request, id):
    kontakt = get_object_or_404(Kontakti.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        kontakt.delete(using='naplata_db')
    return redirect(request.META.get('HTTP_REFERER', 'lista_kontakata'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- NAPOMENE -->
# <!-- ======================================================================= -->
def lista_napomena(request):
    napomene = Napomene.objects.using('naplata_db').all()
    return render(request, 'fleet/naplata/napomena_lista.html', {'napomene': napomene})

def dodaj_napomenu(request, sif_par, naz_par):
    if request.method == "POST":
        form = NapomeneForm(request.POST)
        if form.is_valid():
            napomena = form.save(commit=False)
            napomena.sif_par = sif_par  # Postavljamo partnera automatski
            napomena.naz_par = naz_par
            napomena.save(using='naplata_db')
            return redirect('detalji_partner', sif_par = sif_par)
    else:
        form = NapomeneForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  # Automatsko popunjavanje

    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

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
    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def obrisi_napomenu(request, id):
    napomena = get_object_or_404(Napomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        napomena.delete(using='naplata_db')
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- OPOMENE -->
# <!-- ======================================================================= -->
def lista_opomena(request):
    opomene = Opomene.objects.using('naplata_db').all()
    return render(request, 'opomene/lista.html', {'opomene': opomene})

def dodaj_opomenu(request, sif_par, naz_par):
    if request.method == "POST":
        form = OpomeneForm(request.POST)
        if form.is_valid():
            opomena = form.save(commit=False)
            opomena.sif_par = sif_par  
            opomena.naz_par = naz_par
            opomena.save(using='naplata_db')
            return redirect('detalji_partner', sif_par = sif_par)
        else:
            print("Forma nije validna!", form.errors)  # Ispis grešaka u konzoli
    else:
        form = OpomeneForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def izmeni_opomenu(request, id):
    opomena = get_object_or_404(Opomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = OpomeneForm(request.POST, instance=opomena)
        if form.is_valid():
            form.save(using='naplata_db')
            return redirect('lista_opomena')
    else:
        form = OpomeneForm(instance=opomena)
    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def obrisi_opomenu(request, id):
    opomena = get_object_or_404(Opomene.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        opomena.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici

    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- POZIVI -->
# <!-- ======================================================================= -->
def lista_poziva(request):
    pozivi = PoziviTel.objects.using('naplata_db').all()
    return render(request, 'pozivi_tel/lista.html', {'pozivi': pozivi})

def dodaj_poziv(request, sif_par, naz_par):
    if request.method == "POST":
        form = PoziviTelForm(request.POST)
        if form.is_valid():
            poziv = form.save(commit=False)
            poziv.sif_par = sif_par  # Automatski postavljamo vrednost
            poziv.naz_par = naz_par
            poziv.save(using='naplata_db')
            return redirect('detalji_partner', sif_par = sif_par)

    else:
        form = PoziviTelForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def izmeni_poziv(request, id):
    poziv = get_object_or_404(PoziviTel.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = PoziviTelForm(request.POST, instance=poziv)
        if form.is_valid():
            form.save(using='naplata_db')
            return redirect('lista_poziva')
    else:
        form = PoziviTelForm(instance=poziv)
    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def obrisi_poziv(request, id):
    poziv = get_object_or_404(PoziviTel.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        poziv.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici


# <!-- ======================================================================= -->
#                           <!-- POZIVI/PISMA -->
# <!-- ======================================================================= -->
def lista_pozivnih_pisma(request):
    pozivi = PozivPismo.objects.using('naplata_db').all()
    return render(request, 'poziv_pismo/lista.html', {'pozivi': pozivi})

def dodaj_poziv_pismo(request, sif_par, naz_par):
    if request.method == "POST":
        form = PozivPismoForm(request.POST)
        if form.is_valid():
            poziv = form.save(commit=False)
            poziv.sif_par = sif_par  # Automatski postavljamo vrednost
            poziv.naz_par = naz_par
            poziv.save(using='naplata_db')
            return redirect('detalji_partner', sif_par = sif_par)
    else:
        form = PozivPismoForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def izmeni_poziv_pismo(request, id):
    poziv = get_object_or_404(PozivPismo.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = PozivPismoForm(request.POST, instance=poziv)
        if form.is_valid():
            form.save(using='naplata_db')
            return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    else:
        form = PozivPismoForm(instance=poziv)
    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def obrisi_poziv_pismo(request, id):
    poziv = get_object_or_404(PozivPismo.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        poziv.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return render(request, 'poziv_pismo/obrisi.html', {'poziv': poziv})


# <!-- ======================================================================= -->
#                           <!-- TUZBE -->
# <!-- ======================================================================= -->
def lista_tuzbi(request):
    tuzbe = Tuzbe.objects.using('naplata_db').all()
    return render(request, 'tuzbe/lista.html', {'tuzbe': tuzbe})

def dodaj_tuzbu(request, sif_par, naz_par):
    if request.method == "POST":
        form = TuzbeForm(request.POST)
        if form.is_valid():
            tuzba = form.save(commit=False)
            tuzba.sif_par = sif_par  # Automatski postavljamo vrednost
            tuzba.naz_par = naz_par
            tuzba.save(using='naplata_db')
            return redirect('detalji_partner', sif_par = sif_par)
    else:
        form = TuzbeForm(initial={'sif_par': sif_par, 'naz_par': naz_par})  

    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def izmeni_tuzbu(request, id):
    tuzba = get_object_or_404(Tuzbe.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        form = TuzbeForm(request.POST, instance=tuzba)
        if form.is_valid():
            form.save(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    else:
        form = TuzbeForm(instance=tuzba)
    return render(request, 'fleet/naplata/form_naplata.html', {'form': form})

def obrisi_tuzbu(request, id):
    tuzba = get_object_or_404(Tuzbe.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        tuzba.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici

def obrisi_tuzbu(request, id):
    tuzba = get_object_or_404(Tuzbe.objects.using('naplata_db'), id=id)
    if request.method == "POST":
        tuzba.delete(using='naplata_db')
        return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici
    return redirect(request.META.get('HTTP_REFERER', 'lista_napomena'))  # Ostaje na istoj stranici



