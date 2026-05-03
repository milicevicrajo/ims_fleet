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

def fetch_service_data(last_24_hours=True, days=None):
    """
    Funkcija za povlačenje podataka o servisnim transakcijama.
    Svi novi podaci se čuvaju u DraftServiceTransaction tabeli,
    dok se duplikati preskaču.
    Polje 'popravka_kategorija' će biti postavljeno na None ako je vrednost iz baze prazna ili nevalidna.
    """
    try:
        logger.info("Pokrećem funkciju za povlačenje podataka o servisnim transakcijama...")

        # SQL upit za povlačenje svih kolona iz view-a `dbo.fleet_servisi`
        # VAŽNO: Redosled kolona ovde mora TAČNO odgovarati redosledu u vašem SQL Server View-u.
        # Kolone sif_pos i RegOzn (registracija) se povlače, ali se neće direktno koristiti za kreiranje modela
        query = """
            SELECT god, sif_par_pl, naz_par_pl, datum, sif_vrs, br_naloga, vez_dok, knt_pl, potrazuje,
                   sif_par_npl, knt_npl, duguje, sif_pos, konto_vozila, kom, RegOzn, kilometraza,
                   poptavka_kategorija, nije_garaza, napomena
            FROM dbo.fleet_servisi
        """

        # Dodajte WHERE klauzulu u zavisnosti od parametara
        if days is not None:
            query += f" WHERE datum > DATEADD(day, -{days}, GETDATE())"
            logger.info(f"Filtriram podatke za poslednjih {days} dana.")
        elif last_24_hours:
            query += " WHERE datum > DATEADD(day, -1, GETDATE())"
            logger.info("Filtriram podatke za poslednja 24 sata.")

        # Izvršite upit i preuzmite podatke
        with connections['server_db'].cursor() as cursor:
            logger.info(f"Izvršavam SQL upit za preuzimanje podataka: {query}")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Broj povučenih redova: {len(rows)}")

        expected_columns = 20

        for index, row in enumerate(rows):
            if len(row) != expected_columns:
                logger.warning(f"UPOZORENJE: Red {index+1} ima {len(row)} kolona, očekivano je {expected_columns}. Preskačem red: {row}")
                continue

            try:
                god = str(row[0]).strip() if row[0] else None
                vez_dok = str(row[6]).strip() if row[6] else None
                br_naloga = str(row[5]).strip() if row[5] else None
                sif_vrs = str(row[4]).strip() if row[4] else None

                transaction_exists = ServiceTransaction.objects.filter(
                    god=god,
                    vez_dok__iexact=vez_dok,
                    br_naloga__iexact=br_naloga,
                    sif_vrs=sif_vrs
                ).exists()

                unique_fields = {
                    'god': row[0],
                    'sif_vrs': row[4],
                    'vez_dok': row[6],
                    'br_naloga': row[5]
                }
                logger.debug(unique_fields)
                
                #transaction_exists = ServiceTransaction.objects.filter(**unique_fields).exists()
                draft_exists = DraftServiceTransaction.objects.filter(**unique_fields).exists()
                # draft_exists = DraftServiceTransaction.objects.filter(
                #     god=god,
                #     vez_dok__iexact=vez_dok,
                #     br_naloga__iexact=br_naloga,
                #     sif_vrs=sif_vrs
                # ).exists()

                if transaction_exists:
                    logger.warning(f"Transakcija sa brojem naloga {row[5]} već postoji u sistemu u Finalnoj tabeli, preskačem unos.")
                    continue
                if draft_exists:
                    logger.warning(f"Transakcija sa brojem naloga {row[5]} već postoji u sistemu u Draft tabeli, preskačem unos.")
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
                        logger.warning(f"UPOZORENJE: ServiceType '{service_type_value}' ne postoji u bazi. Polje 'popravka_kategorija' će biti postavljeno na None.")
                    except Exception as st_e:
                        logger.info(f"Greška pri traženju ServiceType '{service_type_value}': {st_e}. Polje 'popravka_kategorija' će biti postavljeno na None.")

                # Pokušaj pronalaženja vozila. RegOzn je na row[15], ali se NE prosleđuje modelu kao 'registracija' polje.
                vehicle = Vehicle.objects.filter(traffic_cards__registration_number=row[15]).first() if row[15] else None

                logger.info(f"Novi zapis za br_naloga {row[5]} se dodaje u draft tabelu DraftServiceTransaction.")

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
                logger.info(f"Zapis sa brojem naloga {row[5]} je uspešno sačuvan u draft tabeli.")

            except ValueError as ve:
                logger.info(f"Greška pri konverziji podataka u redu {index+1} (nalog: {row[5]}): {ve}. Cela kolona: {row}")
            except Exception as e:
                logger.error(f"Nepredviđena greška pri obradi reda {index+1} (nalog: {row[5]}): {e}. Cela kolona: {row}")

        return "Podaci su uspešno povučeni i sačuvani u draft tabeli, preskočeni su duplikati."

    except Exception as e:
        logger.info(f"Došlo je do opšte greške prilikom povlačenja podataka: {e}")
        return f"Došlo je do opšte greške prilikom povlačenja podataka: {e}"

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
                    # napomena=draft.napomena,
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
        logger.info("Pokrećem funkciju za povlačenje podataka o trebovanjima...")

        # SQL upit za povlačenje podataka
        query = """
            SELECT sif_pred, god, br_dok, sif_vrsart, stavka, sif_art, naz_art, kol, cena, vrednost_nab, napomena
            FROM dbo.fleet_trebovanja
        """
        
        # Dodaj WHERE klauzulu u zavisnosti od parametara (ako je potrebno vremensko filtriranje)
        if days is not None:
            query += f" WHERE GETDATE() - {days} > '2000-01-01'"  # Dummy condition since no date filtering
            logger.info(f"Filtriram podatke za poslednjih {days} dana.")
        elif last_24_hours:
            logger.warning("Napomena: Nema vremenskog filtriranja jer nema dostupnog datuma.")

        # Izvrši upit i preuzmi podatke
        with connections['server_db'].cursor() as cursor:
            logger.info("Izvršavam SQL upit za preuzimanje podataka...")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Broj povučenih redova: {len(rows)}")

        # Iteracija kroz povučene redove
        for index, row in enumerate(rows):
            logger.info(f"Obrađujem red {index+1} sa {len(row)} kolona.")

            # Provera broja kolona
            if len(row) < 11:
                logger.info(f"Red {index+1} ima manje od očekivanih 11 kolona: {row}")
                continue

            try:
                br_dok = row[2]  # Broj dokumenta
                sif_art = row[5]  # Šifra artikla
                stavka = row[4] 

                # Provera postojanja zapisa u glavnoj i draft tabeli
                requisition_exists = Requisition.objects.filter(br_dok=br_dok, sif_art=sif_art, stavka=stavka).exists()
                draft_exists = DraftRequisition.objects.filter(br_dok=br_dok, sif_art=sif_art, stavka=stavka).exists()

                if not requisition_exists and not draft_exists:
                    logger.warning(f"Zapis {br_dok} - {sif_art} ne postoji. Dodajem u draft tabelu.")

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
                    logger.info(f"Zapis {br_dok} - {sif_art} je uspešno sačuvan u draft tabeli.")
                else:
                    logger.info(f"Zapis {br_dok} - {sif_art} već postoji. Preskačem unos.")

            except ValueError as ve:
                logger.info(f"Greška pri konverziji podataka u redu {index+1}: {ve}")
            except Exception as e:
                logger.error(f"Neprikazana greška u redu {index+1}: {e}")

        return "Podaci su uspešno povučeni i sačuvani, preskočeni su duplikati."

    except Exception as e:
        logger.info(f"Došlo je do greške prilikom povlačenja podataka: {e}")
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
