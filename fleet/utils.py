import logging
import os
import re
import time
from datetime import date, datetime, timedelta, time as datetime_time
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, transaction
from django.db.models import F, Value, CharField, Subquery, OuterRef, Q
from django.http import JsonResponse
from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.translation import gettext_lazy as _
from openpyxl import load_workbook
from core.models import OrganizationalUnit

from .models import (
    DraftInsurance,
    DraftPolicy,
    DraftRequisition,
    DraftServiceTransaction,
    Employee,
    FuelConsumption,
    Insurance,
    JobCode,
    Lease,
    Policy,
    Requisition,
    ServiceTransaction,
    ServiceType,
    TrafficCard,
    TransactionNIS,
    TransactionOMV,
    Vehicle,
)

logger = logging.getLogger(__name__)

from .sync_services import (
    delete_complete_drafts,
    fetch_requisition_data,
    fetch_service_data,
    migrate_draft_to_service_transaction,
)
from .travel_order_documents import populate_putni_nalog_template, sanitize_filename


FUEL_PRODUCT_KEYWORDS = (
    "dizel",
    "diesel",
    "benzin",
    "petrol",
    "maxxmotion",
    "maxxm",
    "bmb",
    "lpg",
    "autogas",
    "cng",
    "tng",
    "ngv",
)


def _fuel_product_filter(field_name):
    product_filter = Q()
    for keyword in FUEL_PRODUCT_KEYWORDS:
        product_filter |= Q(**{f"{field_name}__icontains": keyword})
    return product_filter


def filter_omv_fuel_queryset(queryset):
    return queryset.filter(_fuel_product_filter("product_inv"))


def filter_nis_fuel_queryset(queryset):
    return queryset.filter(_fuel_product_filter("naziv_proizvoda"))


def date_range_for_datetime_field(start_date=None, end_date=None):
    """
    Convert date-only filter values to timezone-aware datetime bounds.
    DateTimeField filters with plain dates produce naive datetime warnings when
    USE_TZ is enabled.
    """
    def _to_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def _aware(value, bound):
        value = _to_date(value)
        if value is None:
            return None
        dt = datetime.combine(value, datetime_time.min if bound == "start" else datetime_time.max)
        return django_timezone.make_aware(dt) if django_timezone.is_naive(dt) else dt

    return _aware(start_date, "start"), _aware(end_date, "end")

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

def import_vehicles_from_excel(excel_file_path):
    try:
        # Load data from both sheets
        df1 = pd.read_excel(excel_file_path, sheet_name=0)  # Adjust if there are specific sheet names
        df2 = pd.read_excel(excel_file_path, sheet_name=1)

        logger.info("Sheets loaded successfully.")

        # Merge the data on 'broj_sasije' or another appropriate key
        df = pd.merge(df1, df2, on='broj_sasije')
        logger.info(f"Data merged successfully. Total records: {len(df)}")

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
                logger.info(f"Processed vehicle {vehicle.inventory_number}: {'Created' if created else 'Updated'}")
            except Exception as e:
                logger.error(f"Error processing record {index}: {e}")
    except Exception as e:
        logger.error(f"Failed to load or process Excel file: {e}")


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
            logger.info(f"Successfully imported job code {job_code_str} for vehicle with registration number {reg_br}")
        
        except TrafficCard.DoesNotExist:
            logger.warning(f"Traffic card with registration number {reg_br} not found.")
        except OrganizationalUnit.DoesNotExist:
            logger.warning(f"Organizational unit with job code {job_code_str} not found.")
        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")



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
            logger.info(f"Successfully imported lease for vehicle {vehicle.chassis_number}")
        
        except ObjectDoesNotExist:
            logger.warning(f"Vehicle with chassis number {row['Inv. Broj']} not found.")
        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")

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
            logger.info(f"Successfully imported policy {row['BrojPolise']} for vehicle with registration number {reg_br}")
        
        except ObjectDoesNotExist:
            logger.warning(f"Vehicle with registration number {reg_br} not found.")
        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")


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
                logger.warning(f"TrafficCard with registration number {reg_br} not found. Proceeding with vehicle=None.")


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
                logger.info(f"Row {index} saved as draft due to missing fields: {missing_fields}")
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
            logger.info(f"Successfully imported service for vehicle {reg_br}")

        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")


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
                logger.warning(f"TrafficCard with registration number {reg_br} not found. Proceeding with vehicle=None.")

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
                logger.info(f"Row {index} saved as draft due to missing fields: {missing_fields}")
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
            logger.info(f"Successfully imported requisition {row['br_dok']} for vehicle {vehicle}")

        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")



def populate_service_types():
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

    logger.info("Podaci su uspešno uneti u bazu.")

def formiranje_org_jedinica():
    import django
    django.setup()  # Inicijalizacija Django okruženja

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
            logger.info(f"Jedinica sa kodom {code} već postoji.")
        else:
            logger.info(f"Uspješno dodata jedinica: {name} sa kodom {code} i šifrom centra {center_code}.")

    logger.info("Proces unosa je završen.")


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
            FROM dbo.fleet_polise
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

        with connections['server_db'].cursor() as cursor:
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
    

def normalize_decimal(value):
    try:
        return Decimal(str(value).strip()).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except:
        return None

def process_vehicle_retirements():
    """
    Funkcija za obradu otpisanih vozila iz dbo.otpis view-a.
    Ako vozilo postoji u view-u (po inv_br), postavlja 'otpis' polje na True.
    """
    try:
        logger.info("Pokrećem funkciju za obradu otpisanih vozila...")

        # SQL upit za povlačenje SAMO inventarnih brojeva iz view-a dbo.otpis
        # Bez ikakvih dodatnih WHERE uslova za 'otpis' kolonu.
        query = """
            SELECT inv_br
            FROM dbo.otpis;
        """

        retired_vehicles_from_db = []
        with connections['server_db'].cursor() as cursor:
            logger.info(f"Izvršavam SQL upit za preuzimanje otpisanih vozila: {query}")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Broj povučenih redova iz dbo.otpis: {len(rows)}")

            for row in rows:
                if row[0] is not None:
                    # Očisti inv_br od potencijalnih belina ako je CHAR ili NVARCHAR
                    retired_vehicles_from_db.append(str(row[0]).strip())
        
        if not retired_vehicles_from_db:
            logger.info("Nema inventarnih brojeva u dbo.otpis za obradu.")
            return "Nema otpisanih vozila za obradu."

        updated_count = 0
        skipped_count = 0

        # Koristimo transakciju kako bi se osigurala konzistentnost baze
        with transaction.atomic():
            for inv_br_from_db in retired_vehicles_from_db:
                try:
                    # Pokušaj pronaći vozilo po inventory_number
                    # Koristimo __iexact za case-insensitive poređenje
                    vehicle = Vehicle.objects.get(inventory_number__iexact=inv_br_from_db)

                    # Ako je vozilo već otpisano, preskoči
                    if vehicle.otpis:
                        logger.debug(f"Vozilo sa inventarnim brojem '{inv_br_from_db}' je već otpisano. Preskačem.")
                        skipped_count += 1
                        continue
                    
                    # Postavi 'otpis' na True i sačuvaj
                    vehicle.otpis = True
                    vehicle.save(update_fields=['otpis'])
                    updated_count += 1
                    logger.info(f"Uspešno otpisano vozilo: {vehicle.inventory_number} - {vehicle.brand} {vehicle.model}.")

                except Vehicle.DoesNotExist:
                    logger.warning(f"Vozilo sa inventarnim brojem '{inv_br_from_db}' iz dbo.otpis nije pronađeno u Django bazi.")
                except Exception as e:
                    logger.error(f"Greška pri obradi vozila '{inv_br_from_db}': {e}", exc_info=True)
        
        message = (f"Proces otpisa završen: "
                   f"Ažurirano vozila: {updated_count}, "
                   f"Već otpisana (preskočena): {skipped_count}, "
                   f"Nije pronađeno u Django bazi: {len(retired_vehicles_from_db) - updated_count - skipped_count}")
        logger.info(message)
        return message

    except Exception as e:
        logger.critical(f"Kritična greška u funkciji 'process_vehicle_retirements': {e}", exc_info=True)
        return f"Kritična greška prilikom obrade otpisanih vozila: {e}"


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
                    napomena=draft.napomena,
                    kvar=draft.kvar,
                )
                draft.delete()
            return requisition

    except DraftRequisition.DoesNotExist:
        raise ValueError("Nepotpuni zapis ne postoji ili nije validan")


def get_fuel_consumption_queryset(start_date=None, end_date=None):
    start_dt, end_dt = date_range_for_datetime_field(start_date, end_date)

    # Subquery to get the latest TrafficCard for each Vehicle
    latest_traffic_card_subquery = TrafficCard.objects.filter(
        vehicle=OuterRef('vehicle')
    ).order_by('-issue_date').values('registration_number')[:1]

    # Filtriranje datuma za OMV
    omv_queryset = filter_omv_fuel_queryset(TransactionOMV.objects.all()).annotate(
        registration_number=Subquery(latest_traffic_card_subquery),
        annotated_transaction_date=F('transaction_date'),
        annotated_receipt_number=F('voucher'),
        annotated_quantity=F('quantity'),
        price_per_liter=F('unit_price'),
        total_net=F('amount'),
        total_gross=F('gross_cc'),
        annotated_supplier=Value('OMV', output_field=CharField()),
        annotated_mileage=F('mileage')
    )

    if start_dt:
        omv_queryset = omv_queryset.filter(transaction_date__gte=start_dt)
    if end_dt:
        omv_queryset = omv_queryset.filter(transaction_date__lte=end_dt)

    omv_queryset = omv_queryset.values(
        'registration_number', 'annotated_transaction_date', 'annotated_receipt_number',
        'annotated_quantity', 'price_per_liter', 'total_net', 'total_gross',
        'annotated_supplier', 'annotated_mileage'
    )

    # Filtriranje datuma za NIS
    nis_queryset = filter_nis_fuel_queryset(TransactionNIS.objects.all()).annotate(
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

    if start_dt:
        nis_queryset = nis_queryset.filter(datum_transakcije__gte=start_dt)
    if end_dt:
        nis_queryset = nis_queryset.filter(datum_transakcije__lte=end_dt)

    nis_queryset = nis_queryset.values(
        'registration_number', 'annotated_transaction_date', 'annotated_receipt_number',
        'annotated_quantity', 'price_per_liter', 'total_net', 'total_gross',
        'annotated_supplier', 'annotated_mileage'
    )

    # Combine both querysets
    combined_queryset = omv_queryset.union(nis_queryset)

    return combined_queryset



def update_vehicle_values():
    """
    Povlači vrednosti vozila iz eksterne baze i ažurira model Vehicle.
    """
    updated_vehicles_count = 0

    try:
        # Povlačenje podataka iz druge baze
        with connections['server_db'].cursor() as cursor:
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


def update_job_codes_from_view():
    today = date.today()
    updated = 0

    with connections['server_db'].cursor() as cursor:
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
    with connections['server_db'].cursor() as cursor:  # zameni 'external' imenom tvoje konekcije
        cursor.execute("SELECT sif_pos, naz_pos, blok FROM dbo.v_organizationalunit")
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

    logger.info(f"Organizacione jedinice: {created} dodatih, {updated} ažuriranih.")


INS_VIEW = "dbo.fleet_potrazivanje_ddor"   # naziv SQL view-a
DB_ALIAS = "server_db"                        # promeni ako koristiš drugi alias

# Stabilni ključ za detekciju duplikata (isti u draft/final)
KEY_FIELDS = ("god", "sif_vrs", "br_naloga", "stavka", "knt")


def fetch_ddor_insurance_data():
    """
    Povlači podatke iz [dbo.fleet_potrazivanje_ddor] u DraftInsurance.
    Nema vremenskog filtera (view ga ne podržava).
    Preskače zapise koji već postoje u final/draft po ključu KEY_FIELDS.
    """
    try:
        logger.info("Pokrećem fetch_ddor_insurance_data...")

        query = f"""
            SELECT
                god, sif_vrs, br_naloga, stavka, oj, knt, datum, vez_dok, potrazuje, kola
            FROM {INS_VIEW}
        """

        with connections[DB_ALIAS].cursor() as cursor:
            logger.info("Izvršavam SQL upit...")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Preuzeto redova: {len(rows)}")

        for i, row in enumerate(rows, start=1):
            try:
                god, sif_vrs, br_naloga, stavka, oj, knt, datum_dt, vez_dok, potrazuje, kola = row

                # datum u view-u može biti datetime → pretvori u date
                if datum_dt is not None:
                    if hasattr(datum_dt, "date"):
                        datum = datum_dt.date()
                    else:
                        dt = parse_datetime(str(datum_dt))
                        datum = dt.date() if dt else None
                else:
                    datum = None

                # Priprema vrednosti (string-stripping, tipovi)
                god = int(god) if god is not None else None
                sif_vrs = str(sif_vrs).strip() if sif_vrs is not None else None
                br_naloga = str(br_naloga).strip() if br_naloga is not None else ""
                stavka = str(stavka).strip() if stavka is not None else None
                oj = str(oj).strip() if oj is not None else None
                knt = str(knt).strip() if knt is not None else None
                vez_dok = str(vez_dok).strip() if vez_dok is not None else None
                kola = str(kola).strip() if kola is not None else None
                potrazuje = None if potrazuje in (None, "") else float(potrazuje)

                # duplikat čuvar
                key_filter = dict(god=god, sif_vrs=sif_vrs, br_naloga=br_naloga, stavka=stavka, knt=knt)
                if Insurance.objects.filter(**key_filter).exists() or DraftInsurance.objects.filter(**key_filter).exists():
                    logger.warning(f"[{i}] Postoji (final/draft): {key_filter} — preskačem.")
                    continue

                DraftInsurance.objects.create(
                    god=god, sif_vrs=sif_vrs, br_naloga=br_naloga, stavka=stavka,
                    oj=oj, knt=knt, datum=datum, vez_dok=vez_dok, potrazuje=potrazuje, kola=kola
                )
                logger.info(f"[{i}] Sačuvan draft: {br_naloga}/{stavka} ({god})")

            except Exception as e:
                logger.info(f"[{i}] Greška u obradi reda: {e}")

        return "DDOR: podaci uspešno povučeni u draft; duplikati preskočeni."

    except Exception as e:
        logger.info(f"Greška u fetch_ddor_insurance_data: {e}")
        return f"Greška u fetch_ddor_insurance_data: {e}"


def migrate_draft_to_insurance_single(draft_id: int, vehicle_id: int):
    """
    Migrira jedan (single) draft zapis u final Insurance.
    Nema propagacije/sibling-a — pretpostavka je da je stavka jedina.
    """
    try:
        draft = DraftInsurance.objects.get(id=draft_id)

        if not vehicle_id:
            raise ValueError("Nedostaje vehicle_id.")

        # minimalni kriterijumi (po tvom DraftInsurance.is_complete):
        if not (draft.vehicle or vehicle_id) or draft.datum is None:
            raise ValueError("Draft nije kompletan (potrebni: vehicle i datum).")

        with transaction.atomic():
            # koristi stabilni ključ
            key_kwargs = dict(
                god=draft.god,
                sif_vrs=draft.sif_vrs,
                br_naloga=draft.br_naloga,
                stavka=draft.stavka,
                knt=draft.knt,
            )

            ins, created = Insurance.objects.get_or_create(
                **key_kwargs,
                defaults=dict(
                    vehicle_id=vehicle_id,
                    oj=draft.oj,
                    datum=draft.datum,
                    vez_dok=draft.vez_dok,
                    potrazuje=draft.potrazuje,
                    kola=draft.kola,
                ),
            )

            if not created:
                # Meko ažuriranje postojećeg final zapisa
                ins.vehicle_id = vehicle_id
                ins.oj = draft.oj
                ins.datum = draft.datum
                ins.vez_dok = draft.vez_dok
                ins.potrazuje = draft.potrazuje
                ins.kola = draft.kola
                ins.save()

            draft.delete()

        return ins

    except DraftInsurance.DoesNotExist:
        raise ValueError("Draft zapis ne postoji.")
