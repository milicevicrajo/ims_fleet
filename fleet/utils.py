import csv
import re
import os
import time
import logging
import pytz
from datetime import datetime
from openpyxl import load_workbook

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from .models import TransactionNIS, TransactionOMV, FuelConsumption, Vehicle, TrafficCard, JobCode, TrafficCard, Lease, Policy,Employee, OrganizationalUnit, Requisition,DraftRequisition, ServiceTransaction, DraftServiceTransaction, Policy, DraftPolicy

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import connections, transaction
from django.db.models import F, Value, CharField, Subquery, OuterRef
from django.http import JsonResponse

def get_latest_download_file(download_path):
    
    # Dobij sve fajlove iz direktorijuma za preuzimanje
    files = os.listdir(download_path)
    
    # Pronađi najnoviji fajl na osnovu vremena modifikacije
    paths = [os.path.join(download_path, basename) for basename in files]
    latest_file = max(paths, key=os.path.getctime)
    
    return latest_file

def format_license_plate(plate):
    # Zameni sve vrste crtica (– ili -) standardnom crticom
    plate = plate.replace("–", "-").replace("-", "").replace(" ", "").upper()  # Uklanja sve beline i crtice

    # Zadrži samo brojeve i slova
    plate = re.sub(r'[^A-Za-z0-9]', '', plate)

    # Proba da preoblikuje tablicu, na primer BG1461DX -> BG1461-DX
    match = re.match(r'^([A-Z]{2})(\d{3,4})([A-Z]{2})$', plate)
    if match:
        return f"{match.group(1)}{match.group(2)}-{match.group(3)}"

    # Ako nije moguće preoblikovati tablicu, vrati originalnu vrednost (ili baci grešku)
    return plate

import pandas as pd
from django.utils.dateparse import parse_date
from fleet.models import Vehicle  # Update 'your_app' with the actual app name

def import_vehicles_from_excel(excel_file_path):
    try:
        # Load data from both sheets
        df1 = pd.read_excel(excel_file_path, sheet_name=0)  # Adjust if there are specific sheet names
        df2 = pd.read_excel(excel_file_path, sheet_name=1)

        print("Sheets loaded successfully.")

        # Merge the data on 'broj_sasije' or another appropriate key
        df = pd.merge(df1, df2, on='broj_sasije')
        print(f"Data merged successfully. Total records: {len(df)}")

        # Iterate through the merged DataFrame
        for index, row in df.iterrows():
            try:
                vehicle, created = Vehicle.objects.update_or_create(
                    chassis_number=row['broj_sasije'],
                    defaults={
                        'inventory_number': row['sif_osn'],
                        'brand': row['Marka'].strip(),
                        'model': row['Model'].strip(),
                        'year_of_manufacture': int(row['GodinaProizvodnje']),
                        'first_registration_date': parse_date(row['DatumPrveRegistracije']),
                        'color': row['Boja'],
                        'number_of_axles': int(row['BrojOsovina']),
                        'engine_volume': float(row['ZapreminaMotora']),
                        'engine_number': row['BrojMotora'],
                        'weight': float(row['Masa']),
                        'engine_power': float(row['SnagaMotora']),
                        'load_capacity': float(row['Nosivost']),
                        'category': row['Kategorija'],
                        'maximum_permissible_weight': float(row['NajvecaDozvoljenaMasa']),
                        'fuel_type': row['PogonskoGorivo'],
                        'number_of_seats': int(row['BrojMestaZaSedenje']),
                        'purchase_value': float(row['nab_vred']),
                        'purchase_date': parse_date(row['dat_stavlj']),
                        'center_code': str(row['oj']),
                        'partner_code': str(row['sif_par']),
                        'partner_name': row['naz_par'].strip(),
                        'invoice_number': row['br_fakture'].strip(),
                        'description': row['opis'].strip(),
                        'otpis': bool(int(row['otpis']))
                    }
                )
                print(f"Processed vehicle {vehicle.inventory_number}: {'Created' if created else 'Updated'}")
            except Exception as e:
                print(f"Error processing record {index}: {e}")
    except Exception as e:
        print(f"Failed to load or process Excel file: {e}")


def import_omv_fuel_consumption_from_csv(csv_file_path):
    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            try:
                # Formatiraj registarske tablice
                formatted_plate = format_license_plate(row['License plate No'])

                # Pronađi vozilo prema formatiranoj tablici u TrafficCard modelu
                traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
                vehicle = traffic_card.vehicle

                # Konvertuj datume i druge vrednosti
                transaction_date = datetime.strptime(row['Transactiondate'], '%Y-%m-%d %H:%M:%S').date()
                amount = float(row['Quantity'].replace(',', '.'))

                # Konvertuj bruto trošak i PDV u decimalne vrednosti
                cost_bruto = float(row['Gross CC'].replace(',', '').strip())
                vat = float(row['VAT'].replace(',', '').strip())

                job_code = vehicle.job_codes.first().organizational_unit.code
                # Izračunaj neto trošak
                cost_neto = cost_bruto - vat

                # Kreiraj FuelConsumption instancu i sačuvaj je u bazi
                FuelConsumption.objects.create(
                    vehicle=vehicle,
                    date=transaction_date,
                    amount=amount,
                    fuel_type=row['Product INV'],
                    cost_bruto=cost_bruto,
                    cost_neto=cost_neto,
                    supplier="OMV",
                    job_code=job_code,
                    mileage=row['Mileage'],
                )
                print(f"Successfully imported fuel consumption for vehicle {vehicle.chassis_number}")
            
            except ObjectDoesNotExist:
                print(f"Vehicle with license plate {row['License plate No']} not found.")
            except Exception as e:
                print(f"Error importing row: {row}. Error: {str(e)}")


def import_omv_transactions_from_csv(csv_file_path):
    timezone = pytz.timezone(settings.TIME_ZONE)

    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')  # Pazi na delimiter ';'
        for row in reader:
            try:
                # Formatiraj tablice
                formatted_plate = format_license_plate(row['License plate No'])
                
                # Pronađi vozilo prema formatiranoj tablici u TrafficCard
                traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
                vehicle = traffic_card.vehicle

                # Konverzija datuma sa vremenskom zonom
                def to_aware_datetime(value, format='%Y-%m-%d %H:%M:%S'):
                    if value:
                        naive_datetime = datetime.strptime(value, format)
                        return timezone.localize(naive_datetime)
                    return None

                # Konverzija numeričkih vrednosti, ostavi kao None ako je prazno
                def to_float(value):
                    return float(value.replace(',', '')) if value else None

                quantity = to_float(row['Quantity'])
                gross_cc = to_float(row['Gross CC'])
                vat = to_float(row['VAT'])
                discount = to_float(row['Discount'])
                surcharge = to_float(row['Surcharge'])
                cost_1 = to_float(row['Cost 1'])
                cost_2 = to_float(row['Cost 2'])
                amount_other = to_float(row['Amount other'])
                unit_price = to_float(row['Unitprice'])
                amount = to_float(row['Amount'])
                mileage = to_float(row['Mileage'])
                corrected_mileage = to_float(row['Corrected mileage'])

                # Polja koja zahtevaju datetime konverziju
                transaction_date = to_aware_datetime(row['Transactiondate'])  # 'Transactiondate'
                invoice_date = to_aware_datetime(row['Invoice date'], format='%Y-%m-%d') if row['Invoice date'] else None  # 'Invoice date'
                date_to = to_aware_datetime(row['Date to'], format='%Y-%m-%d') if row['Date to'] else None  # 'Date to'
                
                # Kreiraj instancu TransactionOMV modela i sačuvaj je u bazi
                TransactionOMV.objects.create(
                    vehicle = vehicle,
                    issuer=row['Issuer'].strip(),
                    customer=row['Customer'],
                    card=row['Card'],
                    license_plate_no=formatted_plate,
                    transaction_date=transaction_date,
                    product_inv=row['Product INV'],
                    quantity=quantity,
                    gross_cc=gross_cc,
                    vat=vat,
                    voucher=row['Voucher'],
                    mileage=mileage,
                    corrected_mileage=corrected_mileage,
                    additional_info=row['Additional info'],
                    supply_country=row['Supply country'],
                    site_town=row['Site Town'],
                    product_del=row['Product DEL'],
                    unit_price=unit_price,
                    amount=amount,
                    discount=discount,
                    surcharge=surcharge,
                    vat_2010=row['VAT2010'],
                    supplier_currency=row['Suppliercurrency'],
                    invoice_no=row['Invoice No'],
                    invoice_date=invoice_date,
                    invoiced=True if row['Invoiced?'] == 'Yes' else False,
                    state=row['State'],
                    supplier=row['Supplier'],
                    cost_1=cost_1,
                    cost_2=cost_2,
                    reference_no=row['Reference No'],
                    record_type=row['Recordtype'],
                    amount_other=amount_other,
                    is_list_price=True if row['is listprice ?'] == 'Yes' else False,
                    approval_code=row['Approval code'],
                    date_to=date_to,
                    final_trx=row['Final Trx.'],
                    lpi=row['LPI']
                )
                print(f"Successfully imported transaction for vehicle {formatted_plate}")
            
            except ObjectDoesNotExist:
                print(f"Vehicle with license plate {row['License plate No']} not found.")
            except Exception as e:
                print(f"Error importing row: {row}. Error: {str(e)}")


def import_nis_fuel_consumption(file_path):
    # Preuzmi vremensku zonu iz Django podešavanja
    timezone = pytz.timezone(settings.TIME_ZONE)
    
    # Učitaj Excel fajl
    df = pd.read_excel(file_path, sheet_name=0, header=1, engine="openpyxl")

    # Ostatak funkcije ostaje isti...
    for index, row in df.iterrows():
        try:
            # Formatiraj registarski broj pre nego što ga upotrebiš
            formatted_plate = format_license_plate(row['Registarska oznaka vozila'].strip().upper())

            # Pronađi vozilo prema formatiranom registracionom broju u TrafficCard modelu
            traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
            vehicle = traffic_card.vehicle

            # Konverzija datuma transakcije sa vremenskom zonom
            naive_transaction_date = pd.to_datetime(row['Datum transakcije'], format='%d.%m.%Y %H:%M:%S')
            transaction_date = timezone.localize(naive_transaction_date)  # Dodaj vremensku zonu
            
            job_code = vehicle.job_codes.first().organizational_unit.code
           
            FuelConsumption.objects.create(
                vehicle=vehicle,
                date=transaction_date,
                amount=row['Količina'],
                fuel_type=row['Naziv proizvoda'],
                cost_bruto=row['Total'],
                cost_neto=round(row['Total']*5/6,2),
                supplier="NIS",
                job_code=job_code,
                mileage=row['Kilometraža'] if isinstance(row['Kilometraža'], (int, float)) and not pd.isna(row['Kilometraža']) else 0,
            )
            print(f"Successfully imported fuel consumption for vehicle {vehicle.chassis_number}")
        
        except ObjectDoesNotExist:
            print(f"Vehicle with registration number {formatted_plate} not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")


def import_nis_transactions(file_path):
    # Preuzmi vremensku zonu iz Django podešavanja
    timezone = pytz.timezone(settings.TIME_ZONE)
    # Učitaj Excel fajl
    df = pd.read_excel(file_path, sheet_name=0, header=1)  # Koristi prvi sheet i drugi red kao zaglavlje

    for index, row in df.iterrows():
        try:
            # Formatiraj registarski broj pre nego što ga upotrebiš
            formatted_plate = format_license_plate(row['Registarska oznaka vozila'].strip().upper())

            # Pronađi vozilo prema formatiranom registracionom broju u TrafficCard modelu
            traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
            vehicle = traffic_card.vehicle

            # Konverzija datuma transakcije sa vremenskom zonom
            naive_transaction_date = pd.to_datetime(row['Datum transakcije'], format='%d.%m.%Y %H:%M:%S')
            transaction_date = timezone.localize(naive_transaction_date)  # Dodaj vremensku zonu

            # Konverzija numeričkih vrednosti gde je potrebno
            kolicina = row['Količina']
            popust = row['Popust']
            total = row['Total']
            cena_sa_kase = row['Cena sa kase']

            # Postavi kilometražu na None ako nije dostupna
            kilometraza = int(row['Kilometraža']) if pd.notna(row['Kilometraža']) else None

            # Kreiraj instancu TransactionIMS modela
            TransactionNIS.objects.create(
                vehicle=vehicle,
                kupac=row['Kupac'],
                sifra_kupca=row['Šifra kupca'],
                broj_kartice=row['Broj kartice'],
                kompanijski_kod_kupca=row['Šifra kupca'],
                zemlja_sipanja=row['Država sipanja'],
                benzinska_stanica=row['Benzinska stanica'],
                id_transakcije=row['ID transakcije'],
                app_kod=row['App kod'],
                datum_transakcije=transaction_date,
                tociono_mesto=row['Točiono mesto'],
                naziv_kartice=row['Naziv kartice'],
                licenca=row.get('Licenca', ''),
                broj_gazdinstva=row.get('Broj gazdinstva', ''),
                registarska_oznaka_vozila=formatted_plate,
                broj_racuna=row['Broj računa'],
                kilometraza=kilometraza,
                sipanje_van_rezervoara=row['Sipanje van rezervoara'],
                naziv_proizvoda=row['Naziv proizvoda'],
                kolicina=kolicina,
                kolicina_kg=row.get('Količina KG', None),
                popust=popust,
                primenjen_popust=row['Primenjen popust'],
                cena_sa_kase=cena_sa_kase,
                cena=row['Cena'],
                total_sa_kase=row['Total sa kase'],
                total=total,
                valuta=row['Valuta'],
                aktivirano_prekoracenje=row['Aktivirano prekoračenje'],
                kolicinsko_prekoracenje=row['Količinsko prekoračenje'],
                finansijsko_prekoracenje=row['Finansijsko prekoračenje'],
                nacin_ocitavanja_kartice=row['Način očitavanja kartice']
            )
            print(f"Successfully imported transaction for vehicle {formatted_plate}")
        
        except ObjectDoesNotExist:
            print(f"Vehicle with registration number {row['Registarska oznaka vozila']} (formatted as {formatted_plate}) not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")


def import_job_codes_from_excel(file_path):
    # Load the Excel sheet
    df = pd.read_excel(file_path, sheet_name='sif_pos_dodeljeno')

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        try:
            # Format the registration number (convert from AA0000AA to AA0000-AA)
            reg_br_raw = row['RegBr'].strip().upper()
            reg_br = format_license_plate(reg_br_raw)

            # Find the TrafficCard by the formatted registration number
            traffic_card = TrafficCard.objects.get(registration_number=reg_br)
            vehicle = traffic_card.vehicle  # Find the associated vehicle

            # Convert the 'assigned_date' to the proper date format
            assigned_date = pd.to_datetime(row['od'], format='%d/%m/%Y').date()

            # Find the OrganizationalUnit by job code ('SifPos')
            job_code_str = str(row['SifPos'])
            organizational_unit = OrganizationalUnit.objects.get(code=job_code_str)

            # Create a new JobCode record
            JobCode.objects.create(
                vehicle=vehicle,
                organizational_unit=organizational_unit,
                assigned_date=assigned_date
            )
            print(f"Successfully imported job code {job_code_str} for vehicle with registration number {reg_br}")
        
        except TrafficCard.DoesNotExist:
            print(f"Traffic card with registration number {reg_br} not found.")
        except OrganizationalUnit.DoesNotExist:
            print(f"Organizational unit with job code {job_code_str} not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")



def import_lease_data_from_excel(file_path):
    # Učitaj Excel sheet
    df = pd.read_excel(file_path, sheet_name='lizing_ug')  # Ako se sheet zove drugačije, promeni naziv

    # Prođi kroz svaki red u DataFrame-u
    for index, row in df.iterrows():
        try:

            # Pronađi vozilo prema registarskoj oznaci
            vehicle = Vehicle.objects.get(inventory_number=row['Inv. Broj'])

            # Pravilno učitaj datume
            start_date = pd.to_datetime(row['Od datuma'], format='%d/%m/%Y').date()
            end_date = pd.to_datetime(row['Do datuma'], format='%d/%m/%Y').date()

            # Kreiraj novi Lease zapis
            Lease.objects.create(
                vehicle=vehicle,
                partner_code=str(row['Sif Partnera']),
                partner_name=row['naziv partnera'],
                job_code=str(row['Sifra posla']),
                contract_number=row['Ugovor'],
                current_payment_amount=row['Nabavna vrednost'],
                start_date=start_date,
                end_date=end_date,
                note=row.get('napomena', '')  # Ako postoji napomena
            )
            print(f"Successfully imported lease for vehicle {vehicle.chassis_number}")
        
        except ObjectDoesNotExist:
            print(f"Vehicle with chassis number {row['Inv. Broj']} not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")

def import_policy_data_from_excel(file_path):
    # Učitaj Excel sheet
    df = pd.read_excel(file_path, sheet_name='polise')  # Ako se sheet zove drugačije, promeni naziv

    # Prođi kroz svaki red u DataFrame-u
    for index, row in df.iterrows():
        try:
            # Formatiraj registarsku oznaku
            reg_br = format_license_plate(str(row['RegistraskaOznaka']))

            # Pronađi TrafficCard prema registracionom broju
            traffic_card = TrafficCard.objects.get(registration_number=reg_br)
            vehicle = traffic_card.vehicle  # Pronađi povezano vozilo

            # Pravilno učitaj datume
            issue_date = pd.to_datetime(row['issuedate'], format='%d/%m/%Y').date()
            start_date = pd.to_datetime(row['PeriodOd'], format='%d/%m/%Y').date()
            end_date = pd.to_datetime(row['PeriodDo'], format='%d/%m/%Y').date()

            # Učitaj podatke, osiguravajući da su vrednosti decimalne
            first_installment_amount = float(row.get('IznosPrveRate', 0))
            other_installments_amount = float(row.get('IznosOstalihRata', 0))
            number_of_installments = int(row.get('BrojRata', 0))

            # Kreiraj novi Policy zapis
            Policy.objects.create(
                vehicle=vehicle,
                partner_pib=row['PartnerPIB'],
                partner_name=row['PartnerIme'],
                invoice_id=row['ID'],
                invoice_number=row['BrojFakture'],
                issue_date=issue_date,
                insurance_type=row['VrstaOsiguranja'],
                policy_number=row['BrojPolise'],
                premium_amount=row['IznosPremije'],
                start_date=start_date,
                end_date=end_date,
                first_installment_amount=first_installment_amount,
                other_installments_amount=other_installments_amount,
                number_of_installments=number_of_installments
            )
            print(f"Successfully imported policy {row['BrojPolise']} for vehicle with registration number {reg_br}")
        
        except ObjectDoesNotExist:
            print(f"Vehicle with registration number {reg_br} not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")


import pandas as pd
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from .models import Service, ServiceTransaction, Vehicle, ServiceType

def import_services_from_excel(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name='servisi1')

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        try:
            
            vehicle = None

            try:
                # Provera da li postoji i validno je polje RegOzn
                if pd.notna(row.get('RegOzn')) and row['RegOzn']:
                    reg_br = format_license_plate(str(row['RegOzn']))
                    traffic_card = TrafficCard.objects.get(registration_number=reg_br)
                    vehicle = traffic_card.vehicle  # Povezuje vozilo
            except TrafficCard.DoesNotExist:
                print(f"TrafficCard with registration number {reg_br} not found. Proceeding with vehicle=None.")


            # Check required fields
            required_fields = [
                'god', 'sif_par_pl', 'naz_par_pl', 'datum', 'sif_vrs', 'br_naloga',
                'vez_dok', 'knt_pl', 'potrazuje', 'sif_par_npl', 'knt_npl', 'duguje', 'konto_vozila','popravka_kategorija','kilometraza'
            ]
            missing_fields = [field for field in required_fields if pd.isna(row.get(field))]

            if missing_fields or not vehicle:
                # Save as DraftServiceTransaction
                DraftServiceTransaction.objects.create(
                    vehicle=vehicle,
                    god=int(row['god']) if pd.notna(row['god']) else None,
                    sif_par_pl=str(row['sif_par_pl']).strip() if pd.notna(row['sif_par_pl']) else None,
                    naz_par_pl=str(row['naz_par_pl']).strip() if pd.notna(row['naz_par_pl']) else None,
                    datum=pd.to_datetime(row['datum'], format='%d/%m/%Y').date() if pd.notna(row['datum']) else None,
                    sif_vrs=str(row['sif_vrs']).strip() if pd.notna(row['sif_vrs']) else None,
                    br_naloga=str(row['br_naloga']).strip() if pd.notna(row['br_naloga']) else None,
                    vez_dok=str(row['vez_dok']).strip() if pd.notna(row['vez_dok']) else None,
                    knt_pl=str(row['knt_pl']).strip() if pd.notna(row['knt_pl']) else None,
                    potrazuje=float(row['potrazuje']) if pd.notna(row['potrazuje']) else None,
                    sif_par_npl=str(row['sif_par_npl']).strip() if pd.notna(row['sif_par_npl']) else None,
                    knt_npl=str(row['knt_npl']).strip() if pd.notna(row['knt_npl']) else None,
                    duguje=float(row['duguje']) if pd.notna(row['duguje']) else None,
                    konto_vozila=str(row['konto_vozila']).strip() if pd.notna(row['konto_vozila']) else None,
                    kom=row['kom'] if pd.notna(row['kom']) else None,
                    popravka_kategorija=str(row['popravka_kategorija']).strip() if pd.notna(row['popravka_kategorija']) else None,
                    kilometraza=int(row['kilometraza']) if pd.notna(row['kilometraza']) else None,
                    napomena=str(row['napomena']).strip() if pd.notna(row['napomena']) else None,
                    nije_garaza=row.get('nije_garaza') if pd.notna(row.get('nije_garaza')) else None,
                )
                print(f"Row {index} saved as draft due to missing fields: {missing_fields}")
                continue

            # Create or update ServiceTransaction
            ServiceTransaction.objects.update_or_create(
                vehicle=vehicle,
                god=int(row['god']),
                sif_par_pl=str(row['sif_par_pl']).strip(),
                naz_par_pl=str(row['naz_par_pl']).strip(),
                datum=pd.to_datetime(row['datum'], format='%d/%m/%Y').date(),
                sif_vrs=str(row['sif_vrs']).strip(),
                br_naloga=str(row['br_naloga']).strip(),
                vez_dok=str(row['vez_dok']).strip() if pd.notna(row['vez_dok']) else None,
                knt_pl=str(row['knt_pl']).strip(),
                potrazuje=float(row['potrazuje']),
                sif_par_npl=str(row['sif_par_npl']).strip(),
                knt_npl=str(row['knt_npl']).strip(),
                duguje=float(row['duguje']),
                konto_vozila=str(row['konto_vozila']).strip(),
                kom=row['kom'] if pd.notna(row['kom']) else None,
                popravka_kategorija=str(row['popravka_kategorija']).strip() if pd.notna(row['popravka_kategorija']) else None,
                kilometraza=int(row['kilometraza']),
                napomena=str(row['napomena']).strip() if pd.notna(row['napomena']) else None,
                nije_garaza=row['nije_garaza'],
            )
            print(f"Successfully imported service for vehicle {reg_br}")

        except Exception as e:
            print(f"Error importing row {index}: {e}")


def import_requisitions_from_excel(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name='trebovanja1')  # Adjust the sheet name as necessary

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        try:
            vehicle = None  # Initialize vehicle as None

            try:
                # Check if RegOzn is valid
                if pd.notna(row.get('RegOzn')) and row['RegOzn']:
                    reg_br = format_license_plate(str(row['RegOzn']))
                    traffic_card = TrafficCard.objects.get(registration_number=reg_br)
                    vehicle = traffic_card.vehicle
            except TrafficCard.DoesNotExist:
                print(f"TrafficCard with registration number {reg_br} not found. Proceeding with vehicle=None.")

            # Check required fields
            required_fields = [
                'sif_pred', 'god', 'br_dok', 'sif_vrsart', 'stavka',
                'sif_art', 'naz_art', 'kol', 'cena', 'vrednost_nab',
                'mesec_unosa', 'datum_trebovanja','kilometraza','nije_garaza'
            ]
            missing_fields = [field for field in required_fields if pd.isna(row.get(field))]

            if missing_fields or not vehicle:
                # Save as DraftRequisition
                DraftRequisition.objects.create(
                    vehicle=vehicle,
                    sif_pred=int(row['sif_pred']) if pd.notna(row['sif_pred']) else None,
                    god=int(row['god']) if pd.notna(row['god']) else None,
                    br_dok=str(row['br_dok']).strip() if pd.notna(row['br_dok']) else None,
                    sif_vrsart=str(row['sif_vrsart']).strip() if pd.notna(row['sif_vrsart']) else None,
                    stavka=int(row['stavka']) if pd.notna(row['stavka']) else None,
                    sif_art=str(row['sif_art']).strip() if pd.notna(row['sif_art']) else None,
                    naz_art=str(row['naz_art']).strip() if pd.notna(row['naz_art']) else None,
                    kol=float(row['kol']) if pd.notna(row['kol']) else None,
                    cena=float(row['cena']) if pd.notna(row['cena']) else None,
                    vrednost_nab=float(row['vrednost_nab']) if pd.notna(row['vrednost_nab']) else None,
                    mesec_unosa=int(row['mesec_unosa']) if pd.notna(row['mesec_unosa']) else None,
                    datum_trebovanja=pd.to_datetime(row['datum_trebovanja'], format='%d/%m/%Y').date() if pd.notna(row['datum_trebovanja']) else None,
                    popravka_kategorija=str(row['popravka_kategorija']).strip() if pd.notna(row['popravka_kategorija']) else None,
                    kilometraza=int(row['kilometraza']) if pd.notna(row['kilometraza']) else None,
                    nije_garaza=int(row['nije_garaza']) if pd.notna(row['kilometraza']) else None,
                    napomena=str(row['napomena']).strip() if pd.notna(row['napomena']) else None,
                )
                print(f"Row {index} saved as draft due to missing fields: {missing_fields}")
                continue

            # Create or update Requisition
            Requisition.objects.update_or_create(
                vehicle=vehicle,
                sif_pred=int(row['sif_pred']),
                god=int(row['god']),
                br_dok=str(row['br_dok']).strip(),
                sif_vrsart=str(row['sif_vrsart']).strip(),
                stavka=int(row['stavka']),
                sif_art=str(row['sif_art']).strip(),
                naz_art=str(row['naz_art']).strip(),
                kol=float(row['kol']),
                cena=float(row['cena']),
                vrednost_nab=float(row['vrednost_nab']),
                mesec_unosa=int(row['mesec_unosa']),
                datum_trebovanja=pd.to_datetime(row['datum_trebovanja'], format='%d/%m/%Y').date(),
                popravka_kategorija=str(row['popravka_kategorija']).strip(),
                kilometraza=int(row['kilometraza']),
                nije_garaza=int(row['nije_garaza']),
                napomena=str(row['napomena']).strip() if pd.notna(row['napomena']) else None,
            )
            print(f"Successfully imported requisition {row['br_dok']} for vehicle {vehicle}")

        except Exception as e:
            print(f"Error importing row {index}: {e}")



def import_employee_data_from_excel(file_path):
    # Učitaj Excel sheet
    df = pd.read_excel(file_path, sheet_name='zaposleni')  # Ako se sheet zove drugačije, promeni naziv

    # Prođi kroz svaki red u DataFrame-u
    for index, row in df.iterrows():
        try:
            # Pravilno učitaj i formatiraj datume
            date_of_birth = pd.to_datetime(row['dat_rodj']).date()
            date_of_joining = pd.to_datetime(row['dat_dolaska']).date()

            # Proveri da li je phone_number `null` ili prazan
            phone_number = row['mob_br'].strip() if pd.notnull(row['mob_br']) else None

            # Kreiraj novi Employee zapis
            Employee.objects.create(
                employee_code=str(row['rasif']),
                name=row['ranaz'].strip(),
                position=row['naz_sis'].strip(),
                department_code=int(row['oj']),
                gender=row['pol'].strip(),
                date_of_birth=date_of_birth,
                date_of_joining=date_of_joining,
                phone_number=phone_number
            )
            print(f"Successfully imported employee {row['ranaz']}")
        
        except Exception as e:
            print(f"Error importing row {index}: {e}")

def populate_service_types():
    from fleet.models import ServiceType 

    # Podaci koje želiš da ubaciš u bazu
    service_types = [
        {"name": "Redovan servis van IMS", "description": "Motorno ulje, Filteri ulja, vazduha, klime I goriva, svecice, wd sprej"},
        {"name": "Redovan servis u IMS", "description": "Motorno ulje, Filteri ulja, vazduha, klime I goriva, svecice, wd sprej"},
        {"name": "Veliki servis u IMS", "description": "Motorno ulje, filteri ulja, vazduha i klime, vodena pumpa, pk kais komplet, PK kais i set zupcastog kaisa, G-12, diht masa, wd sprej, svecice, antifriz"},
        {"name": "Veliki servis van IMS", "description": "Motorno ulje, filteri ulja, vazduha i klime, vodena pumpa, pk kais komplet, PK kais i set zupcastog kaisa, G-12, diht masa, wd sprej, svecice, antifriz"},
        {"name": "Popravka u IMS", "description": "Set kvacila (lamela, korpa, druk lezaj), Migavac, Metlice, Gumice balans stangle, zamena Akumulatora, Amortizeri, Bobina, kablovi za svecice, Dobosi zadnjeg tocka, zadnji kocioni cilindri, sajla rucne kocnice, paknovi, plocice, menjacko ulje, plasticne vezice, Hladnjak motora, kais ventilatora, bobina, grejaci, termostat, lager, lamela, lezajevi, retrovizori"},
        {"name": "Popravka van IMS", "description": None},
        {"name": "Potrosni materijal", "description": "Komplet sijalica, Nalepnice ogranicenja brzine, PP aparat, Lanci za sneg, Prva pomoc, Florescentni prsluk, Sajla za vucu, Trougao, Antifriz, ATF ulje, Motorno ulje, Zimska tecnost, AD blue, G-12, Tecnost za brisace"},
        {"name": "Dopuna taga, tag, putarina", "description": None},
        {"name": "Tehnicki pregled, registracija", "description": None},
        {"name": "Odjava vozila", "description": None},
        {"name": "Gorivo", "description": None},
        {"name": "Gume - zamena", "description": None},
        {"name": "Gume - kupovina", "description": None},
        {"name": "Pranje vozila", "description": None},
    ]

    # Popuni bazu podataka
    for service_type_data in service_types:
        ServiceType.objects.create(
            name=service_type_data["name"],
            description=service_type_data["description"]
        )

    print("Podaci su uspešno uneti u bazu.")

def formiranje_org_jedinica():
    import django
    django.setup()  # Inicijalizacija Django okruženja

    from fleet.models import OrganizationalUnit  
    # Lista organizacionih jedinica i njihovih kodova
    units = [
        ('Geotehnička ispitivanja i projektovanje', '436111', '43'),
        ('Superkontrola na izgradnji gasovoda', '425002', '42'),
        ('Građevinska keramika', '412111', '41'),
        ('Laboratorijsko ispitivanje betona', '413111', '41'),
        ('Ispitivanja opreme i konstrukcija', '421114', '42'),
        ('Poslovi u garazi', '832111', '83'),
        ('Pravni i kadrovski poslovi', '821001', '82'),
        ('Organizacija i poslovanje', '209001', '2'),
        ('Kamen i agregat', '411111', '41'),
        ('HE Đerdap', '421111', '42'),
        ('Veziva, hemije i malteri', '414111', '41'),
        ('Etaloniranje', '422111', '42'),
        ('Poslovi magacina', '811002', '81'),
        ('Stručni nadzor', '436222', '43'),
        ('Istražni radovi na proj.sanac.', '442112', '44'),
        ('Asfaltna ispitivanja', '437222', '43'),
        ('Prednaprezanje', '441111', '44'),
        ('Geomehanička ispitivanja', '437111', '43'),
        ('Stručni nadzor i ter.ispitivanja', '431111', '43'),
        ('Projektovanje saobraćajnica', '439111', '43'),
        ('Mehan.-tehn.ispit.metala', '421116', '42'),
        ('Ispitivanja konstrukcija', '443111', '44'),
        ('PP zaštita, zaštita na radu', '825003', '82'),
        ('Toplotna tehnika', '415113', '41'),
        ('Drvo i sintetički materijali', '416111', '41'),
        ('Poslovi nabavke', '811001', '81')
    ]

    # Unos podataka u bazu
    for name, code, center_code in units:
        unit, created = OrganizationalUnit.objects.get_or_create(
            code=code,
            defaults={'name': name, 'center': center_code}
        )
        if not created:
            print(f"Jedinica sa kodom {code} već postoji.")
        else:
            print(f"Uspješno dodata jedinica: {name} sa kodom {code} i šifrom centra {center_code}.")

    print("Proces unosa je završen.")


def calculate_average_fuel_consumption(vehicle):
    # poslednjih 10 tocenja
    last_10_consumptions = vehicle.fuel_consumptions.order_by('-date')[:10]
    
    if len(last_10_consumptions) < 10:
        return None
    
    first_entry = last_10_consumptions[0]
    start_entry = None
    # Pronađi prvi validan unos
    for i in range(9):
        if last_10_consumptions[i].mileage > 0:
            first_entry = last_10_consumptions[9 - i]
            start_entry = 9 - i
            break

    last_entry = last_10_consumptions[9]
    end_entry = None
    # Pronađi poslednji validan unos
    for i in range(9):
        if last_10_consumptions[i].mileage > 0:
            last_entry = last_10_consumptions[i]
            end_entry = i
            break

    # Računanje prosečne potrošnje goriva
    if start_entry is not None and end_entry is not None and start_entry >= end_entry:
        total_amount = sum(c.amount for c in last_10_consumptions[end_entry:start_entry + 1])
        total_mileage = last_entry.mileage - first_entry.mileage

        if total_mileage > 0:
            return total_amount / total_mileage * 100
        else:
            return None
    else:
        return None
    
def calculate_average_fuel_consumption_ever(vehicle):
        # Broj tocenja goriva
    fueling_count = vehicle.fuel_consumptions.count()

    if fueling_count < 2:
        return None

    # Sva tocenja goriva, poređana po datumu
    fuel_consumptions = vehicle.fuel_consumptions.order_by('-date')

    first_entry = None
    last_entry = None

    # Pronađi prvi validan unos (najranije točenje s validnim kilometražama)
    for i in range(fueling_count):
        if fuel_consumptions[i].mileage > 0:
            first_entry = fuel_consumptions[i]
            break

    # Pronađi poslednji validan unos (najkasnije točenje s validnim kilometražama)
    for i in range(fueling_count):
        if fuel_consumptions[fueling_count - i - 1].mileage > 0:
            last_entry = fuel_consumptions[fueling_count - i - 1]
            break

    # Proveri da li su oba unosa validna
    if first_entry is not None and last_entry is not None and first_entry != last_entry:
        total_amount = sum(c.amount for c in fuel_consumptions if c.date <= first_entry.date and c.date >= last_entry.date)
        total_mileage = first_entry.mileage - last_entry.mileage

        if total_mileage > 0:
            return total_amount / total_mileage * 100
        else:
            return None
    else:
        return None



from django.db import IntegrityError
from django.db import connections
from .models import Policy, DraftPolicy, Vehicle

import logging
from django.db import connections, transaction
from datetime import datetime # Make sure datetime is imported, not just date

# Assuming these models are defined and imported correctly
# from .models import Policy, DraftPolicy, Vehicle

logger = logging.getLogger(__name__)

import logging
from django.db import connections, transaction
from datetime import datetime
from decimal import Decimal # Import Decimal for number conversion if needed

# Assuming these models are defined and imported correctly
# from .models import Policy, DraftPolicy, Vehicle

logger = logging.getLogger(__name__)

import logging
from django.db import connections, transaction
from datetime import datetime
from decimal import Decimal # Import Decimal for number conversion if needed

# Assuming these models are defined and imported correctly
# from .models import Policy, DraftPolicy, Vehicle

logger = logging.getLogger(__name__)

def fetch_policy_data(last_24_hours=True, days=None):
    """
    Improved function to fetch insurance policy data with better security and error handling.
    Maps SQL view columns to specific DraftPolicy model field names.
    """
    try:
        logger.info("Starting data fetching process...")

        base_query = """
            SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate,
                   VrstaOsiguranja, BrojPolise, IznosPremije, RegistraskaOznaka,
                   PeriodOd, PeriodDo, IznosPrveRate, IznosOstalihRata, BrojRata
            FROM dbo.v_polise
        """
        params = []
        where_clauses = []

        # Build WHERE clause safely
        if days is not None:
            where_clauses.append("issuedate > DATEADD(day, -%s, GETDATE())")
            params.append(days)
            logger.info(f"Filtering data for last {days} days")
        elif last_24_hours:
            where_clauses.append("issuedate > DATEADD(day, -1, GETDATE())")
            logger.info("Filtering data for last 24 hours")

        query = base_query
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        with connections['test_db'].cursor() as cursor:
            logger.info("Executing SQL query...")
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            logger.info(f"Fetched {len(rows)} rows")
            if not rows:
                return "No new data found"

        new_policies = 0
        new_drafts = 0
        errors = 0

        with transaction.atomic():
            for row in rows:
                row_data = dict(zip(columns, row))
                invoice_id_from_db = row_data['ID'] # Get the ID from the database row

                try:
                    # Check existing records using the actual invoice_id from the DB
                    exists = (Policy.objects.filter(invoice_id=invoice_id_from_db).exists() or
                              DraftPolicy.objects.filter(invoice_id=invoice_id_from_db).exists())
                    if exists:
                        logger.debug(f"Skipping existing invoice {invoice_id_from_db}")
                        continue

                    # Process vehicle using RegistraskaOznaka
                    vehicle = None
                    if reg_plate := row_data.get('RegistraskaOznaka'):
                        vehicle = Vehicle.objects.filter(
                            registration_number=reg_plate
                        ).first()

                    # Define the mapping from SQL View Column Names to Django Model Field Names
                    model_field_map = {
                        'PartnerPIB': 'partner_pib',
                        'PartnerIme': 'partner_name',
                        'ID': 'invoice_id',
                        'BrojFakture': 'invoice_number',
                        'issuedate': 'issue_date',
                        'VrstaOsiguranja': 'insurance_type',
                        'BrojPolise': 'policy_number',
                        'IznosPremije': 'premium_amount',
                        'PeriodOd': 'start_date',
                        'PeriodDo': 'end_date',
                        'IznosPrveRate': 'first_installment_amount',
                        'IznosOstalihRata': 'other_installments_amount',
                        'BrojRata': 'number_of_installments',
                    }

                    # Prepare the data dictionary for model creation
                    policy_data_to_save = {}
                    for sql_col, model_field in model_field_map.items():
                        value = row_data.get(sql_col)

                        # --- REVISED TYPE CONVERSIONS ---
                        if model_field in ['issue_date', 'start_date', 'end_date']:
                            if value is None:
                                value = None # Already None, keep it
                            elif isinstance(value, str):
                                if not value.strip(): # Handle empty string
                                    value = None
                                else:
                                    try:
                                        value = datetime.strptime(value, "%Y-%m-%d").date()
                                    except ValueError:
                                        logger.warning(f"Invalid date format for {model_field}: '{value}'. Setting to None for invoice {invoice_id_from_db}.")
                                        value = None
                            elif not isinstance(value, datetime.date):
                                # If it's not None, not a string, and not already a datetime.date
                                logger.warning(f"Unexpected date type for {model_field}: {type(value)}. Setting to None for invoice {invoice_id_from_db}.")
                                value = None

                        elif model_field in ['premium_amount', 'first_installment_amount', 'other_installments_amount']:
                            if value is None:
                                value = None
                            elif isinstance(value, str):
                                if not value.strip(): # Handle empty string
                                    value = None
                                else:
                                    try:
                                        value = Decimal(value)
                                    except Exception: # Catch broader exceptions for conversion (e.g., non-numeric string)
                                        logger.warning(f"Invalid decimal format for {model_field}: '{value}'. Setting to None for invoice {invoice_id_from_db}.")
                                        value = None
                            elif not isinstance(value, (Decimal, int, float)): # Check for Decimal, int, or float
                                logger.warning(f"Unexpected numeric type for {model_field}: {type(value)}. Setting to None for invoice {invoice_id_from_db}.")
                                value = None
                            else: # If it's already int or float, convert to Decimal
                                try:
                                    value = Decimal(value)
                                except Exception:
                                    logger.warning(f"Could not convert {model_field} {value} to Decimal. Setting to None for invoice {invoice_id_from_db}.")
                                    value = None


                        elif model_field in ['partner_pib', 'invoice_id', 'number_of_installments']:
                            if value is None:
                                value = None
                            elif isinstance(value, str):
                                if not value.strip(): # Handle empty string
                                    value = None
                                else:
                                    try:
                                        value = int(value)
                                    except ValueError:
                                        logger.warning(f"Invalid integer format for {model_field}: '{value}'. Setting to None for invoice {invoice_id_from_db}.")
                                        value = None
                            elif not isinstance(value, int): # Only accept int or None
                                logger.warning(f"Unexpected integer type for {model_field}: {type(value)}. Setting to None for invoice {invoice_id_from_db}.")
                                value = None
                        # --- END REVISED TYPE CONVERSIONS ---

                        policy_data_to_save[model_field] = value

                    # Add the 'vehicle' foreign key
                    policy_data_to_save['vehicle'] = vehicle


                    # Determine if it's complete for Policy or DraftPolicy
                    # Create a temporary object to use is_complete method
                    temp_draft_policy = DraftPolicy(**policy_data_to_save)
                    if temp_draft_policy.is_complete():
                        # Create a full Policy instance
                        Policy.objects.create(**policy_data_to_save)
                        new_policies += 1
                        logger.info(f"Created complete Policy for invoice {invoice_id_from_db}.")
                    else:
                        # Create a DraftPolicy instance
                        DraftPolicy.objects.create(**policy_data_to_save)
                        new_drafts += 1
                        logger.info(f"Created DraftPolicy for invoice {invoice_id_from_db} (incomplete).")

                except Exception as e:
                    logger.error(f"Error processing invoice {invoice_id_from_db}: {str(e)}", exc_info=True)
                    errors += 1
                    # Continue to the next row even if one fails

        msg = (f"Successfully processed {new_policies} policies, "
               f"{new_drafts} drafts. Errors: {errors}")
        logger.info(msg)
        return msg

    except Exception as e:
        logger.error(f"Critical error in data fetch: {str(e)}", exc_info=True)
        return f"Critical error: {str(e)}"
    

from django.db import connections
from datetime import datetime
# Uverite se da su ovi modeli definisani i uvezeni
from .models import ServiceTransaction, DraftServiceTransaction, Vehicle, TrafficCard, ServiceType


def fetch_service_data(last_24_hours=True, days=None):
    """
    Funkcija za povlačenje podataka o servisnim transakcijama.
    Svi novi podaci se čuvaju u DraftServiceTransaction tabeli,
    dok se duplikati preskaču.
    Polje 'popravka_kategorija' će biti postavljeno na None ako je vrednost iz baze prazna ili nevalidna.
    """
    try:
        print("Pokrećem funkciju za povlačenje podataka o servisnim transakcijama...")

        # SQL upit za povlačenje svih kolona iz view-a `dbo.v_servisi`
        # VAŽNO: Redosled kolona ovde mora TAČNO odgovarati redosledu u vašem SQL Server View-u.
        # Kolone sif_pos i RegOzn (registracija) se povlače, ali se neće direktno koristiti za kreiranje modela
        query = """
            SELECT god, sif_par_pl, naz_par_pl, datum, sif_vrs, br_naloga, vez_dok, knt_pl, potrazuje,
                   sif_par_npl, knt_npl, duguje, sif_pos, konto_vozila, kom, RegOzn, kilometraza,
                   poptavka_kategorija, nije_garaza, napomena
            FROM dbo.v_servisi
        """

        # Dodajte WHERE klauzulu u zavisnosti od parametara
        if days is not None:
            query += f" WHERE datum > DATEADD(day, -{days}, GETDATE())"
            print(f"Filtriram podatke za poslednjih {days} dana.")
        elif last_24_hours:
            query += " WHERE datum > DATEADD(day, -1, GETDATE())"
            print("Filtriram podatke za poslednja 24 sata.")

        # Izvršite upit i preuzmite podatke
        with connections['test_db'].cursor() as cursor:
            print(f"Izvršavam SQL upit za preuzimanje podataka: {query}")
            cursor.execute(query)
            rows = cursor.fetchall()
            print(f"Broj povučenih redova: {len(rows)}")

        expected_columns = 20

        for index, row in enumerate(rows):
            if len(row) != expected_columns:
                print(f"UPOZORENJE: Red {index+1} ima {len(row)} kolona, očekivano je {expected_columns}. Preskačem red: {row}")
                continue

            try:
                unique_fields = {
                    'datum': row[3],
                    'duguje': row[11],
                    'vez_dok': row[6],
                    'br_naloga': row[5]
                }

                transaction_exists = ServiceTransaction.objects.filter(**unique_fields).exists()
                draft_exists = DraftServiceTransaction.objects.filter(**unique_fields).exists()

                if transaction_exists or draft_exists:
                    print(f"Transakcija sa brojem naloga {row[5]} već postoji u sistemu (u glavnoj ili draft tabeli), preskačem unos.")
                    continue

                # Konverzija vrednosti za 'potrazuje' i 'duguje'
                potrazuje = float(row[8]) if row[8] is not None and str(row[8]).strip() != '' else None
                duguje = float(row[11]) if row[11] is not None and str(row[11]).strip() != '' else None

                # Konverzija za 'kilometraza'
                kilometraza = int(row[16]) if row[16] is not None and str(row[16]).strip() != '' else 0

                # Konverzija za 'nije_garaza'
                nije_garaza_val = False
                if isinstance(row[18], bool):
                    nije_garaza_val = row[18]
                elif isinstance(row[18], str):
                    nije_garaza_val = (row[18].strip().upper() == 'DA')
                elif row[18] is not None:
                    try:
                        nije_garaza_val = bool(int(row[18]))
                    except (ValueError, TypeError):
                        pass

                # Obrada popravka_kategorija
                service_type_value = row[17]
                service_type_instance = None
                if service_type_value is not None and str(service_type_value).strip() != '':
                    try:
                        service_type_instance = ServiceType.objects.get(name=str(service_type_value).strip())
                    except ServiceType.DoesNotExist:
                        print(f"UPOZORENJE: ServiceType '{service_type_value}' ne postoji u bazi. Polje 'popravka_kategorija' će biti postavljeno na None.")
                    except Exception as st_e:
                        print(f"Greška pri traženju ServiceType '{service_type_value}': {st_e}. Polje 'popravka_kategorija' će biti postavljeno na None.")

                # Pokušaj pronalaženja vozila. RegOzn je na row[15], ali se NE prosleđuje modelu kao 'registracija' polje.
                vehicle = Vehicle.objects.filter(traffic_cards__registration_number=row[15]).first() if row[15] else None

                print(f"Novi zapis za br_naloga {row[5]} se dodaje u draft tabelu DraftServiceTransaction.")

                # Kreiraj zapis u draft tabeli
                draft_transaction = DraftServiceTransaction(
                    vehicle=vehicle, # Ostaje povezano ako vozilo postoji
                    god=row[0],
                    sif_par_pl=row[1],
                    naz_par_pl=row[2],
                    datum=row[3],
                    sif_vrs=row[4],
                    br_naloga=row[5],
                    vez_dok=row[6],
                    knt_pl=row[7],
                    potrazuje=potrazuje,
                    sif_par_npl=row[9],
                    knt_npl=row[10],
                    duguje=duguje,
                    # OVDJE SE NE PROSLEĐUJU `sif_pos` (row[12]) i `registracija` (row[15])
                    konto_vozila=row[13], # Ovo polje ti je definisano u modelu
                    kom=row[14],
                    kilometraza=kilometraza,
                    popravka_kategorija=service_type_instance,
                    nije_garaza=nije_garaza_val,
                    napomena=row[19]
                )
                draft_transaction.save()
                print(f"Zapis sa brojem naloga {row[5]} je uspešno sačuvan u draft tabeli.")

            except ValueError as ve:
                print(f"Greška pri konverziji podataka u redu {index+1} (nalog: {row[5]}): {ve}. Cela kolona: {row}")
            except Exception as e:
                print(f"Nepredviđena greška pri obradi reda {index+1} (nalog: {row[5]}): {e}. Cela kolona: {row}")

        return "Podaci su uspešno povučeni i sačuvani u draft tabeli, preskočeni su duplikati."

    except Exception as e:
        print(f"Došlo je do opšte greške prilikom povlačenja podataka: {e}")
        return f"Došlo je do opšte greške prilikom povlačenja podataka: {e}"



def migrate_draft_to_service_transaction(draft_id):
    """
    Funkcija za migraciju zapisa iz DraftServiceTransaction u ServiceTransaction.
    Ako podaci u draftu zadovoljavaju sve uslove za unos, oni se prebacuju u glavnu tabelu.
    """
    try:
        draft = DraftServiceTransaction.objects.get(id=draft_id)

        # Provera da li su svi podaci dostupni
        if draft.is_complete():
            with transaction.atomic():
                service_transaction = ServiceTransaction.objects.create(
                    vehicle_id=draft.vehicle_id,
                    god=draft.god,
                    sif_par_pl=draft.sif_par_pl,
                    naz_par_pl=draft.naz_par_pl,
                    datum=draft.datum,
                    sif_vrs=draft.sif_vrs,
                    br_naloga=draft.br_naloga,
                    vez_dok=draft.vez_dok,
                    knt_pl=draft.knt_pl,
                    potrazuje=draft.potrazuje,
                    sif_par_npl=draft.sif_par_npl,
                    knt_npl=draft.knt_npl,
                    duguje=draft.duguje,
                    konto_vozila=draft.konto_vozila,
                    kom=draft.kom,
                    popravka_kategorija=draft.popravka_kategorija,
                    napomena=draft.napomena,
                    kilometraza=draft.kilometraza
                )
                # Brisanje iz draft tabele nakon uspešnog migriranja
                draft.delete()
            return service_transaction
        else:
            raise ValueError("Podaci nisu kompletni za migraciju")

    except DraftServiceTransaction.DoesNotExist:
        raise ValueError("Nepotpuni zapis ne postoji ili nije validan")


def fetch_requisition_data(last_24_hours=True, days=None):
    """
    Funkcija za povlačenje podataka o trebovanjima sa proverom opcionalnih polja.
    """
    try:
        print("Pokrećem funkciju za povlačenje podataka o trebovanjima...")

        # SQL upit za povlačenje podataka
        query = """
            SELECT sif_pred, god, br_dok, sif_vrsart, stavka, sif_art, naz_art, kol, cena, vrednost_nab, napomena
            FROM dbo.v_trebovanja
        """
        
        # Dodaj WHERE klauzulu u zavisnosti od parametara (ako je potrebno vremensko filtriranje)
        if days is not None:
            query += f" WHERE GETDATE() - {days} > '2000-01-01'"  # Dummy condition since no date filtering
            print(f"Filtriram podatke za poslednjih {days} dana.")
        elif last_24_hours:
            print("Napomena: Nema vremenskog filtriranja jer nema dostupnog datuma.")

        # Izvrši upit i preuzmi podatke
        with connections['test_db'].cursor() as cursor:
            print("Izvršavam SQL upit za preuzimanje podataka...")
            cursor.execute(query)
            rows = cursor.fetchall()
            print(f"Broj povučenih redova: {len(rows)}")

        # Iteracija kroz povučene redove
        for index, row in enumerate(rows):
            print(f"Obrađujem red {index+1} sa {len(row)} kolona.")

            # Provera broja kolona
            if len(row) < 11:
                print(f"Red {index+1} ima manje od očekivanih 11 kolona: {row}")
                continue

            try:
                br_dok = row[2]  # Broj dokumenta
                sif_art = row[5]  # Šifra artikla
                stavka = row[4] 

                # Provera postojanja zapisa u glavnoj i draft tabeli
                requisition_exists = Requisition.objects.filter(br_dok=br_dok, sif_art=sif_art, stavka=stavka).exists()
                draft_exists = DraftRequisition.objects.filter(br_dok=br_dok, sif_art=sif_art, stavka=stavka).exists()

                if not requisition_exists and not draft_exists:
                    print(f"Zapis {br_dok} - {sif_art} ne postoji. Dodajem u draft tabelu.")

                    # Konverzija vrednosti za validaciju
                    kol = float(row[7]) if row[7] else None
                    cena = float(row[8]) if row[8] else None
                    vrednost_nab = float(row[9]) if row[9] else None

                    # Kreiraj zapis u draft tabeli
                    draft = DraftRequisition(
                        sif_pred=row[0] if row[0] else None,
                        god=row[1] if row[1] else None,
                        br_dok=br_dok,
                        sif_vrsart=row[3] if row[3] else None,
                        stavka=row[4] if row[4] else None,
                        sif_art=sif_art,
                        naz_art=row[6] if row[6] else None,
                        kol=kol,
                        cena=cena,
                        vrednost_nab=vrednost_nab,
                        napomena=row[10] if row[10] else None
                    )
                    draft.save()
                    print(f"Zapis {br_dok} - {sif_art} je uspešno sačuvan u draft tabeli.")
                else:
                    print(f"Zapis {br_dok} - {sif_art} već postoji. Preskačem unos.")

            except ValueError as ve:
                print(f"Greška pri konverziji podataka u redu {index+1}: {ve}")
            except Exception as e:
                print(f"Neprikazana greška u redu {index+1}: {e}")

        return "Podaci su uspešno povučeni i sačuvani, preskočeni su duplikati."

    except Exception as e:
        print(f"Došlo je do greške prilikom povlačenja podataka: {e}")
        return f"Došlo je do greške prilikom povlačenja podataka: {e}"




def migrate_draft_to_requisition(draft_id, vehicle_id):
    try:
        draft = DraftRequisition.objects.get(id=draft_id)
        
        if draft.is_complete() and vehicle_id:
            with transaction.atomic():
                requisition = Requisition.objects.create(
                    vehicle_id=vehicle_id,
                    sif_pred=draft.sif_pred,
                    god=draft.god,
                    br_dok=draft.br_dok,
                    sif_vrsart=draft.sif_vrsart,
                    stavka=draft.stavka,
                    sif_art=draft.sif_art,
                    naz_art=draft.naz_art,
                    kol=draft.kol,
                    cena=draft.cena,
                    vrednost_nab=draft.vrednost_nab,
                    datum_trebovanja=draft.datum_trebovanja,
                    napomena=draft.napomena
                )
                draft.delete()
            return requisition

    except DraftRequisition.DoesNotExist:
        raise ValueError("Nepotpuni zapis ne postoji ili nije validan")


def get_fuel_consumption_queryset(start_date=None, end_date=None):
    # Subquery to get the latest TrafficCard for each Vehicle
    latest_traffic_card_subquery = TrafficCard.objects.filter(
        vehicle=OuterRef('vehicle')
    ).order_by('-issue_date').values('registration_number')[:1]

    # Filtriranje datuma za OMV
    omv_queryset = TransactionOMV.objects.annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        annotated_transaction_date=F('transaction_date'),
        annotated_receipt_number=F('invoice_no'),
        annotated_quantity=F('quantity'),
        price_per_liter=F('unit_price'),
        total_net=F('amount'),
        total_gross=F('gross_cc'),
        annotated_supplier=Value('OMV', output_field=CharField()),
        annotated_mileage=F('mileage')
    )

    if start_date:
        omv_queryset = omv_queryset.filter(transaction_date__gte=start_date)
    if end_date:
        omv_queryset = omv_queryset.filter(transaction_date__lte=end_date)

    omv_queryset = omv_queryset.values(
        'registration_number', 'annotated_transaction_date', 'annotated_receipt_number',
        'annotated_quantity', 'price_per_liter', 'total_net', 'total_gross',
        'annotated_supplier', 'annotated_mileage'
    )

    # Filtriranje datuma za NIS
    nis_queryset = TransactionNIS.objects.annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        annotated_transaction_date=F('datum_transakcije'),
        annotated_receipt_number=F('broj_racuna'),
        annotated_quantity=F('kolicina'),
        price_per_liter=F('cena'),
        total_net=F('total'),
        total_gross=F('total_sa_kase'),
        annotated_supplier=Value('NIS', output_field=CharField()),
        annotated_mileage=F('kilometraza')
    )

    if start_date:
        nis_queryset = nis_queryset.filter(datum_transakcije__gte=start_date)
    if end_date:
        nis_queryset = nis_queryset.filter(datum_transakcije__lte=end_date)

    nis_queryset = nis_queryset.values(
        'registration_number', 'annotated_transaction_date', 'annotated_receipt_number',
        'annotated_quantity', 'price_per_liter', 'total_net', 'total_gross',
        'annotated_supplier', 'annotated_mileage'
    )

    # Combine both querysets
    combined_queryset = omv_queryset.union(nis_queryset)

    return combined_queryset


def nis_data_import():
    try:

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(r"C:\djangoapps\ims_fleet\nis_debug.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Define the URLs and credentials
        login_url = "https://cards.nis.rs"
        username = "zoran.institutims"
        password = "3RrrvvVg"

        # Opcije za Chrome
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Podesavanje lokacije za preuzimanje fajlova
        download_path = r"C:\nis_repo"
        prefs = {"download.default_directory": download_path}
        chrome_options.add_experimental_option("prefs", prefs)

        # Inicijalizacija WebDriver-a
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)  # Povećanje veličine prozora

        try:
            # Otvori login stranicu
            driver.get(login_url)
            print("Opened login page")
            logger.info("Opened login page") 

            # Unesi korisničko ime
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Korisničko ime']"))
            )
            username_input.send_keys(username)
            print("Entered username")
            logger.info("Entered username")  

            # Unesi lozinku
            password_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Lozinka']"))
            )
            password_input.send_keys(password)
            print("Entered password")
            logger.info("Entered password")

            # Klik na dugme za prijavu
            login_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(@class, 'pure-button-primary')]"))
            )
            login_button.click()
            print("Clicked submit button")
            logger.info("Clicked submit button")

            # Sačekaj učitavanje stranice
            time.sleep(5)

            # Klik na link "Izveštaji"
            reports_link = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Izveštaji')]"))
            )
            reports_link.click()
            print("Clicked on 'Izveštaji' link")

            time.sleep(2)

            # Klik na "Transakcije po klijentima"
            client_transactions_link = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/reports/client-transactions' and contains(text(),'Transakcije po kupcima')]"))
            )
            client_transactions_link.click()
            print("Clicked on 'Transakcije po klijentima' link")

            time.sleep(2)

            # Sačekaj da se loader završi pre nego što klikneš
            try:
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "loader"))
                )
            except:
                pass  # Ako loader ne postoji, nastavi dalje

            # Klik na dugme "Prikaži izveštaj"
            show_report_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pure-button-primary') and contains(., 'Prikaži izveštaj')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_report_button)
            ActionChains(driver).move_to_element(show_report_button).click().perform()
            print("Clicked 'Prikaži izveštaj' button")

            time.sleep(2)

            # Klik na dugme za preuzimanje
            dropdown_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'download-button')]"))
            )
            dropdown_button.click()
            print("Clicked on download dropdown")

            time.sleep(1)

            # Izaberi opciju "XLSX"
            xlsx_option = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//li[@class='option']//button[contains(., 'XLSX')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", xlsx_option)
            ActionChains(driver).move_to_element(xlsx_option).click().perform()
            print("Clicked on XLSX option")

            # Sačekaj da se fajl preuzme
            time.sleep(5)
            print("XLSX file downloaded successfully")

            # Pronađi najnovije preuzeti fajl
            xlsx_file_path = get_latest_download_file(download_path)
            print(xlsx_file_path)

            # Import podataka
            import_nis_fuel_consumption(xlsx_file_path)
            import_nis_transactions(xlsx_file_path)
            print(f"Data imported successfully from {xlsx_file_path}")
            return f"Funkcija NIS Data Import je uspešno izvršena"

        finally:
            # Zatvori browser
            driver.quit()
            print("Browser closed")

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

import time
from datetime import datetime, timedelta

def omv_putnicka_data_import(*args, **kwargs):
    # Logika iz `omv_command_putnicka`
    print("OMV Putnička komanda se izvršava...")
    # Define the URLs and credentials
    login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
    username = "710111107248"
    password = "OMV-107248"

    # Definišite datume
    today = datetime.now().strftime("%Y-%m-%d")  # Današnji datum
    # default_date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # Podrazumevani datum "od"
    default_date_from = datetime(2024, 1, 1).strftime("%Y-%m-%d")

    # Proverite da li je "date from" unesen
    date_from = kwargs.get('date_from', default_date_from)  # Koristi uneseni datum ili podrazumevani
    date_to = today  # Zadaje se današnji datum za "date to"

    # Opcije za Chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set up Chrome options to download files to a specific location
    download_path = r"C:\omv_repo"
    prefs = {"download.default_directory": download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the login page
        driver.get(login_url)
        print("Opened login page")

        # Enter username
        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.send_keys(username)
        print("Entered username")

        # Enter password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        print("Entered password")

        # Select language
        language_select = driver.find_element(By.NAME, "language")
        for option in language_select.find_elements(By.TAG_NAME, 'option'):
            if option.text == 'English':
                option.click()
                break
        print("Selected language")

        # Click the login button
        login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        login_button.click()
        print("Clicked login button")

        # Wait for some time to ensure the page loads completely
        time.sleep(1)

        # Switch to the header frame to find the 'Transaction information' link
        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "header"))
        )
        print("Switched to header frame")

        # Click on 'Transaction information'
        transaction_information_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='header.do?selectModule=transactioninformation']"))
        )
        transaction_information_link.click()
        print("Clicked on 'Transaction information'")

        # Switch back to default content
        driver.switch_to.default_content()

        # Switch to the functionnavigation frame to proceed
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "functionnavigation"))
        )
        print("Switched to functionnavigation")

        # Click on 'Reports'
        reports_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='functionNavigation.do?openFunction=transactioninformation.report.overview']"))
        )
        reports_link.click()
        print("Clicked on 'Reports'")

        # Click on 'Transactions'
        transactions_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='genSearchCriteria.do?activateFunction=transactioninformation.report.transaction&openFunction=transactioninformation.report.overview']"))
        )
        transactions_link.click()
        print("Clicked on 'Transactions'")

        # Switch back to default content
        driver.switch_to.default_content()

        # Switch to the searchcriteria frame
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "searchcriteria"))
        )
        print("Switched to searchcriteria frame")

        # Wait for the date inputs to be present
        date_from_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Transactiondatefrom"))
        )
        print("Date from input found")
        time.sleep(2)
        # Clear and set the 'date from' input
        date_from_input.clear()
        date_from_input.send_keys(date_from)
        print(f"Entered 'date from': {date_from}")

        # Clear and set the 'date to' input
        date_to_input = driver.find_element(By.NAME, "Transactiondate1")
        date_to_input.clear()
        date_to_input.send_keys(date_to)
        print(f"Entered 'date to': {date_to}")
        time.sleep(2)
        # Click the 'Result' link using JavaScript
        driver.execute_script("goContent()")
        print("Clicked 'Result' link")

        # Switch back to default content
        driver.switch_to.default_content()
        
        # Switch to the content frame
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "content"))
        )

        # Wait for the download link to appear
        download_link = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href=\"javascript:openURL_Loading('browseTransactionList.do?event=CsvFileRequest');\"]"))
        )
        print("Download link found")

        # Click the download link
        download_link.click()
        print("Clicked download link")
        time.sleep(5)  # Očekuj da se preuzimanje završi

        print("Report downloaded successfully")

        # Pronađi najnovije preuzeti fajl
        csv_file_path = get_latest_download_file(download_path)

        # Importuj podatke u bazu
        import_omv_fuel_consumption_from_csv(csv_file_path)            
        import_omv_transactions_from_csv(csv_file_path)            
        print(f"Data imported successfully from {csv_file_path}")

    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")

    return "OMV Putnička komanda uspešno završena."

def omv_teretna_data_import(*args, **kwargs):
    # Define the URLs and credentials
    login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
    username = "710111107258"
    password = "OMV-107258"

    # Definišite datume
    today = datetime.now().strftime("%Y-%m-%d")  # Današnji datum
    # default_date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # Podrazumevani datum "od"
    default_date_from = datetime(2024, 1, 1).strftime("%Y-%m-%d")


    # Proverite da li je "date from" unesen
    date_from = kwargs.get('date_from', default_date_from)  # Koristi uneseni datum ili podrazumevani
    date_to = today  # Zadaje se današnji datum za "date to"

    # Opcije za Chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set up Chrome options to download files to a specific location
    download_path = r"C:\omv_repo"
    prefs = {"download.default_directory": download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the login page
        driver.get(login_url)
        print("Opened login page")

        # Enter username
        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.send_keys(username)
        print("Entered username")

        # Enter password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        print("Entered password")

        # Select language
        language_select = driver.find_element(By.NAME, "language")
        for option in language_select.find_elements(By.TAG_NAME, 'option'):
            if option.text == 'English':
                option.click()
                break
        print("Selected language")

        # Click the login button
        login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        login_button.click()
        print("Clicked login button")

        # Wait for some time to ensure the page loads completely
        time.sleep(1)

        # Switch to the header frame to find the 'Transaction information' link
        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "header"))
        )
        print("Switched to header frame")

        # Click on 'Transaction information'
        transaction_information_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='header.do?selectModule=transactioninformation']"))
        )
        transaction_information_link.click()
        print("Clicked on 'Transaction information'")

        # Switch back to default content
        driver.switch_to.default_content()

        # Switch to the functionnavigation frame to proceed
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "functionnavigation"))
        )
        print("Switched to functionnavigation")
        time.sleep(2)
        # Click on 'Reports'
        reports_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='functionNavigation.do?openFunction=transactioninformation.report.overview']"))
        )
        reports_link.click()
        print("Clicked on 'Reports'")
        time.sleep(2)
        # Click on 'Transactions'
        transactions_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='genSearchCriteria.do?activateFunction=transactioninformation.report.transaction&openFunction=transactioninformation.report.overview']"))
        )
        transactions_link.click()
        print("Clicked on 'Transactions'")

        # Switch back to default content
        driver.switch_to.default_content()

        # Switch to the searchcriteria frame
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "searchcriteria"))
        )
        print("Switched to searchcriteria frame")
        time.sleep(2)
        # Wait for the date inputs to be present
        date_from_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Transactiondatefrom"))
        )
        print("Date from input found")
        time.sleep(2)
        # Clear and set the 'date from' input
        date_from_input.clear()
        date_from_input.send_keys(date_from)
        print(f"Entered 'date from': {date_from}")

        # Clear and set the 'date to' input
        date_to_input = driver.find_element(By.NAME, "Transactiondate1")
        date_to_input.clear()
        date_to_input.send_keys(date_to)
        print(f"Entered 'date to': {date_to}")

        # Click the 'Result' link using JavaScript
        driver.execute_script("goContent()")
        print("Clicked 'Result' link")
        time.sleep(2)
        # Switch back to default content
        driver.switch_to.default_content()
        
        # Switch to the content frame
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "content"))
        )

        # Wait for the download link to appear
        download_link = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href=\"javascript:openURL_Loading('browseTransactionList.do?event=CsvFileRequest');\"]"))
        )
        print("Download link found")

        # Click the download link
        download_link.click()
        print("Clicked download link")
        time.sleep(5)  # Očekuj da se preuzimanje završi

        print("Report downloaded successfully")

        # Pronađi najnovije preuzeti fajl
        csv_file_path = get_latest_download_file(download_path)

        # Importuj podatke u bazu
        import_omv_fuel_consumption_from_csv(csv_file_path)            
        import_omv_transactions_from_csv(csv_file_path)            
        print(f"Data imported successfully from {csv_file_path}")

    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")


logger = logging.getLogger(__name__)

def update_vehicle_values():
    """
    Povlači vrednosti vozila iz eksterne baze i ažurira model Vehicle.
    """
    updated_vehicles_count = 0

    try:
        # Povlačenje podataka iz druge baze
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT sif_osn, sad_vrednost FROM dbo.vrednost_vozila
            """)
            rows = cursor.fetchall()

        # Iteracija kroz redove i ažuriranje vozila
        vehicles_to_update = []
        for row in rows:
            sif_osn = row[0].strip()
            vrednost = row[1]

            try:
                vehicle = Vehicle.objects.get(inventory_number=sif_osn)
                vehicle.value = vrednost
                vehicles_to_update.append(vehicle)
            except Vehicle.DoesNotExist:
                logger.warning(f"Vozilo sa inventory_number {sif_osn} nije pronađeno.")
            except Exception as e:
                logger.error(f"Greška prilikom ažuriranja vozila {sif_osn}: {e}")

        # Grupno ažuriranje vozila radi optimizacije
        Vehicle.objects.bulk_update(vehicles_to_update, ['value'])
        updated_vehicles_count = len(vehicles_to_update)

    except Exception as e:
        logger.error(f"Greška prilikom povlačenja podataka iz baze: {e}")

    return updated_vehicles_count


def delete_complete_drafts():
    """
    Briše sve `DraftRequisition` zapise koji su kompletni (`is_complete()` vraća True).
    """
    # Dohvati sve zapise iz `DraftRequisition`
    drafts = DraftRequisition.objects.all()

    # Prođi kroz sve zapise i obriši one koji su kompletni
    for draft in drafts:
        if draft.is_complete():
            draft.delete()

def sanitize_filename(filename):
    """
    Uklanja nedozvoljene znakove iz naziva fajla.
    Dozvoljeni znakovi: slova, brojevi, crtice i donje crte.
    """
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', filename)

def populate_putni_nalog_template(putni_nalog):
    """
    Popunjava Excel šablon sa podacima putnog naloga i vraća generisani fajl.
    """
    # Proveri postojanje fajla pre otvaranja
    template_path = os.path.join(settings.BASE_DIR, "dokumenta", "iz077.xlsx")
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Šablon ne postoji: {template_path}")

    # Učitavanje Excel fajla
    workbook = load_workbook(template_path)

    # Popunjavanje prvog radnog lista - "zadnja strana"
    if "zadnja strana" in workbook.sheetnames:
        sheet1 = workbook["zadnja strana"]
        sheet1["P1"] = str(putni_nalog.job_code.name)  # Organizacija
        sheet1["N2"] = str(putni_nalog.order_number)  # Broj naloga
        sheet1["M3"] = str(putni_nalog.order_date.strftime("%d.%m.%Y"))  # Datum naloga
        sheet1["O6"] = str(putni_nalog.employee)  # Zaposleni
        sheet1["M8"] = str(putni_nalog.employee.position)  # Pozicija radnika
        sheet1["R9"] = putni_nalog.travel_date.strftime("%d.%m.%Y")  # Datum polaska
        sheet1["N10"] = putni_nalog.travel_location
        sheet1["M12"] = putni_nalog.task
        sheet1["M12"] = putni_nalog.contract_offer
        sheet1["M16"] = str(putni_nalog.vehicle)  # Prevozno sredstvo
        sheet1["S17"] = putni_nalog.daily_allowance
        sheet1["R18"] = putni_nalog.number_of_days
        sheet1["R22"] = float(putni_nalog.advance_payment)  # Avans
        sheet1["R23"] = putni_nalog.job_code.code  # Šifra posla
    else:
        raise ValueError("Nema radnog lista 'zadnja strana' u šablonu.")

    # Popunjavanje drugog radnog lista - "prednja strana"
    if "prednja strana" in workbook.sheetnames:
        sheet2 = workbook["prednja strana"]
        sheet2["P1"] = str(putni_nalog.job_code.name)  # Organizacija
        sheet2["N2"] = str(putni_nalog.order_number)  # Broj naloga
        sheet2["M3"] = str(putni_nalog.order_date.strftime("%d.%m.%Y"))  # Datum naloga
        sheet2["O6"] = str(putni_nalog.employee)  # Zaposleni
        sheet2["M8"] = str(putni_nalog.employee.position)  # Pozicija radnika
        sheet2["R9"] = putni_nalog.travel_date.strftime("%d.%m.%Y")  # Datum polaska
        sheet2["N10"] = putni_nalog.travel_location
        sheet2["M12"] = putni_nalog.task
        sheet1["M12"] = putni_nalog.contract_offer
        sheet2["M16"] = str(putni_nalog.vehicle)  # Prevozno sredstvo
        sheet2["S17"] = putni_nalog.daily_allowance
        sheet2["R18"] = putni_nalog.number_of_days
        sheet2["R22"] = float(putni_nalog.advance_payment)  # Avans
        sheet2["R23"] = putni_nalog.job_code.code  # Šifra posla
    else:
        raise ValueError("Nema radnog lista 'prednja strana' u šablonu.")

    # Kreiranje foldera ako ne postoji
    output_dir = os.path.join(settings.MEDIA_ROOT, "travel_orders")
    os.makedirs(output_dir, exist_ok=True)

    # Sanitizacija naziva fajla
    sanitized_order_number = sanitize_filename(putni_nalog.order_number)
    file_name = f"PutniNalog_{sanitized_order_number}.xlsx"
    file_path = os.path.join(output_dir, file_name)

     # ✅ Čuvanje fajla
    try:
        workbook.save(file_path)
    except Exception as e:
        return JsonResponse({"error": f"Greška pri čuvanju fajla: {str(e)}"}, status=500)

    # ✅ Proveri da li fajl postoji
    if not os.path.exists(file_path):
        return JsonResponse({"error": f"Fajl nije pronađen nakon čuvanja: {file_path}"}, status=500)

    # ✅ Kreiranje URL-a za preuzimanje
    file_url = os.path.join(settings.MEDIA_URL, "travel_orders", file_name)

    return JsonResponse({"file_url": file_url})


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def kerio_login():
    # Define the URLs and credentials
    login_url = "https://control.ims.rs:4081/login/?NTLM=0&orig=Y29udHJvbC5pbXMucnM=&dest=aHR0cDovL3d3dy5nc3RhdGljLmNvbS9nZW5lcmF0ZV8yMDQ=&host=MTkyLjE2OC42LjcgMWYzYTA5ODgyYzIxYWJjNjM2Y2FlNzAzZjQ1YjRmZGU="
    username = "tatko"
    password = "Abacus236"

    # Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize WebDriver
    print("Starting WebDriver...")
    driver = webdriver.Chrome(options=chrome_options)
    print("WebDriver started.")
    
    try:
        driver.get(login_url)
        print("Opened login page")
        
        # Wait until username field is present
        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        driver.execute_script("arguments[0].removeAttribute('readonly')", username_input)
        username_input.clear()
        username_input.send_keys(username)
        print("Entered username")

        # Enter password
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.send_keys(password)
        print("Entered password")

        # Wait until the login button is clickable
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "login-button"))
        )
        
        # Scroll into view if hidden
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)

        try:
            login_button.click()
            print("Clicked login button")
        except Exception as click_error:
            print("Standard click failed. Using JavaScript click.")
            driver.execute_script("arguments[0].click();", login_button)

        # Wait for a successful login indicator (adjust selector accordingly)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Logged in successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()
        print("Browser closed")


from datetime import date

def update_job_codes_from_view():
    today = date.today()
    updated = 0

    with connections['test_db'].cursor() as cursor:
        cursor.execute("SELECT regbr, sifpos FROM dbo.sif_pos_trenutno")
        rows = cursor.fetchall()

    for regbr, sifpos in rows:
        try:
            traffic_card = TrafficCard.objects.select_related('vehicle').get(registration_number=regbr)
            vehicle = traffic_card.vehicle
        except TrafficCard.DoesNotExist:
            continue

        try:
            org_unit = OrganizationalUnit.objects.get(code=sifpos)
        except OrganizationalUnit.DoesNotExist:
            continue

        latest_job = vehicle.job_codes.order_by('-assigned_date').first()

        if not latest_job or latest_job.organizational_unit != org_unit:
            JobCode.objects.create(
                vehicle=vehicle,
                organizational_unit=org_unit,
                assigned_date=today
            )
            updated += 1

    return updated


def sync_organizational_units_from_view():
    with connections['test_db'].cursor() as cursor:  # zameni 'external' imenom tvoje konekcije
        cursor.execute("SELECT sif_pos, naz_pos, blok FROM dbo.v_sifre_posla")
        rows = cursor.fetchall()

    created = 0
    updated = 0

    for sif_pos, naz_pos, blok in rows:
        obj, created_flag = OrganizationalUnit.objects.update_or_create(
            code=sif_pos,
            defaults={
                'name': naz_pos,
                'center': blok
            }
        )
        if created_flag:
            created += 1
        else:
            updated += 1

    print(f"Organizacione jedinice: {created} dodatih, {updated} ažuriranih.")