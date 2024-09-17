import csv
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from .models import TransactionNIS, TransactionOMV, FuelConsumption, Vehicle, TrafficCard, JobCode, TrafficCard, Lease, Policy,Employee, OrganizationalUnit, Requisition
import re
import os
import time
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
import pytz
from django.conf import settings

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
    df = pd.read_excel(file_path, sheet_name=0, header=1)  # Koristi prvi sheet i drugi red kao zaglavlje

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
                kompanijski_kod_kupca=row['Kompanijski kod kupca'],
                zemlja_sipanja=row['Zemlja sipanja'],
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
            reg_br = row['RegistraskaOznaka'].strip().upper()

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
    df = pd.read_excel(file_path, sheet_name='servisi')

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        try:
            # Handle the registration number format
            reg_br = format_license_plate(row['RegOzn'])
            # Find the TrafficCard by the formatted registration number
            traffic_card = TrafficCard.objects.get(registration_number=reg_br)
            vehicle = traffic_card.vehicle  # Find the associated vehicle

            # Create or update ServiceTransaction
            service_transaction = ServiceTransaction.objects.update_or_create(
                vehicle=vehicle,
                god=row['god'],
                sif_par_pl=row['sif_par_pl'],
                naz_par_pl=row['naz_par_pl'].strip(),
                datum=pd.to_datetime(row['datum'], format='%d/%m/%Y').date(),
                sif_vrs=row['sif_vrs'].strip(),
                br_naloga=row['br_naloga'],
                vez_dok=row['vez_dok'].strip() if pd.notna(row['vez_dok']) else None,
                knt_pl=row['knt_pl'],
                potrazuje=float(row['potrazuje']),
                sif_par_npl=row['sif_par_npl'],
                knt_npl=row['knt_npl'],
                duguje=float(row['duguje']),
                konto_vozila=row['konto_vozila'].strip(),
                kom=row['kom'] if pd.notna(row['kom']) else None,
                popravka_kategorija=row['popravka_kategorija'].strip() if pd.notna(row['popravka_kategorija']) else None,
                napomena=row['napomena'].strip() if pd.notna(row['napomena']) else None,
            )[0]

            # Handle the service type, ensuring the name is not empty
            service_type_name = row['popravka_kategorija'].strip()
            print(service_type_name)
            if service_type_name:
                service_type, created = ServiceType.objects.get_or_create(
                    name=service_type_name,
                    defaults={'description': 'Automatically created from import'}
                )
            else:
                continue  # Skip this entry if no service type name is provided

            # Create or update Service
            service = Service.objects.update_or_create(
                vehicle=vehicle,
                service_type=service_type,
                service_date=pd.to_datetime(row['datum'], format='%d/%m/%Y').date(),
                cost=float(row['duguje']),  # Assuming 'duguje' is the cost
                provider=row['naz_par_pl'].strip(),
                description=row['napomena'].strip() if pd.notna(row['napomena']) else ""
            )[0]

            print(f"Successfully imported service for vehicle {reg_br}")

        except Vehicle.DoesNotExist:
            print(f"Vehicle with registration number {reg_br} not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")


def import_requisitions_from_excel(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path, sheet_name='trebovanja1')  # Adjust the sheet name as necessary

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        try:
            # Format and find the associated Vehicle by registration number
            reg_br = format_license_plate(row['RegOzn'])
            
            # Find the TrafficCard by the formatted registration number
            traffic_card = TrafficCard.objects.get(registration_number=reg_br)
            print(traffic_card)
            vehicle = traffic_card.vehicle  # Find the associated vehicle

            # Create or update Requisition instance
            requisition, created = Requisition.objects.update_or_create(
                vehicle=vehicle,
                sif_pred=row['sif_pred'],
                god=row['god'],
                br_dok=row['br_dok'],
                sif_vrsart=row['sif_vrsart'].strip(),
                stavka=row['stavka'],
                sif_art=row['sif_art'],
                naz_art=row['naz_art'].strip(),
                kol=row['kol'],
                cena=row['cena'],
                vrednost_nab=row['vrednost_nab'],
                mesec_unosa=row['mesec_unosa'],
                datum_trebovanja=pd.to_datetime(row['datum_trebovanja'], format='%d/%m/%Y').date(),
                napomena=row.get('napomena', '').strip() if pd.notna(row['napomena']) else None
            )

            print(f"Successfully imported requisition {requisition.br_dok} for {vehicle}")

        except Vehicle.DoesNotExist:
            print(f"Vehicle with registration number {reg_br} not found.")
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