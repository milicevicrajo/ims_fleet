import pandas as pd
from django.core.management.base import BaseCommand
from fleet.models import Vehicle, TrafficCard
from decimal import Decimal, InvalidOperation
import logging
class Command(BaseCommand):
    help = 'Učitavanje podataka o vozilima iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        file_path = 'Baza 10 07 2024.xlsx'  # Zamenite putanju do vaše Excel datoteke

        # Konfigurišite logovanje
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Učitajte Excel datoteku
        file_path = 'Baza 10 07 2024.xlsx'  # Zamenite putanju do vaše Excel datoteke

        # Učitajte sheet-ove iz Excel datoteke
        df_inv = pd.read_excel(file_path, sheet_name='Inv_broj')
        df_saobracajne = pd.read_excel(file_path, sheet_name='saobracajne')

        # Spojite podatke iz oba sheet-a na osnovu broja šasije
        # Modify your merge command to include an indicator
        merged_df = pd.merge(df_inv, df_saobracajne, left_on='broj_sasije', right_on='BrojSasije', how='outer', indicator=True)

        # Log entries from 'saobracajne' that didn't match
        unmatched_entries = merged_df[merged_df['_merge'] == 'right_only']
        logger.info("Unmatched entries from 'saobracajne':")
        for index, row in unmatched_entries.iterrows():
            logger.info(f"*************************************************************************Unmatched BrojSasije: {row['BrojSasije']} at index {index}")

        # Funkcija za validaciju i konverziju decimalnih vrednosti
        def validate_decimal(value, column_name, row_index, default=0):
            try:
                clean_value = str(value).strip().replace(',', '.').replace(' ', '')
                # logger.info(f"Attempting to convert cleaned value: {clean_value} from column: {column_name} at row: {row_index}")
                return Decimal(clean_value)
            except (InvalidOperation, ValueError) as e:
                # logger.error(f"Invalid decimal value: {value} (cleaned: {clean_value}) in column: {column_name} at row: {row_index}, Error: {e}")
                return Decimal(default)

        # Prolazak kroz redove u merged DataFrame-u i kreiranje unosa u bazi podataka
        for index, row in merged_df.iterrows():
            try:
                vehicle_data = {
                    'inventory_number': row['sif_osn'],
                    'brand': row['Marka'],
                    'model': row['Model'],
                    'year_of_manufacture': row['GodinaProizvodnje'],
                    'first_registration_date': row['DatumPrveRegistracije'],
                    'color': row['Boja'],
                    'number_of_axles': row['BrojOsovina'],
                    'engine_volume': validate_decimal(row['ZapreminaMotora'], 'ZapreminaMotora', index),
                    'engine_number': row['BrojMotora'],
                    'weight': validate_decimal(row['Masa'], 'Masa', index),
                    'engine_power': validate_decimal(row['SnagaMotora'], 'SnagaMotora', index),
                    'load_capacity': validate_decimal(row['Nosivost'], 'Nosivost', index),
                    'category': row['Kategorija'],
                    'maximum_permissible_weight': validate_decimal(row['NajvecaDozvoljenaMasa'], 'NajvecaDozvoljenaMasa', index),
                    'fuel_type': row['PogonskoGorivo'],
                    'number_of_seats': row['BrojMestaZaSedenje'],
                    'purchase_value': validate_decimal(row['nab_vred'], 'nab_vred', index),
                    'purchase_date': row['dat_stavlj'],
                    'center_code' : row['oj'],
                    'partner_code': str(row['sif_par']),
                    'partner_name': row['naz_par'],
                    'invoice_number': row['br_fakture'],
                    'description': row['opis'],
                    'otpis': bool(int(row['otpis']))
                }

                # logger.info(f"First registration date type: {type(row['DatumPrveRegistracije'])}, value: {row['DatumPrveRegistracije']}")
                # logger.info(f"Creating/updating Vehicle with data: {vehicle_data} at row: {index}")

                # for key, value in vehicle_data.items():
                    # logger.info(f"Vehicle Data - {key}: {value} (type: {type(value)})")

                # Kreirajte ili ažurirajte Vehicle
                vehicle, created = Vehicle.objects.update_or_create(
                    chassis_number=row['BrojSasije'],
                    defaults=vehicle_data
                )

                traffic_card_data = {
                    'issue_date': row['DatumIzdavanja'],
                    'valid_until': row['VaziDo'],
                    'traffic_card_number': row['BrojSaobracajne'],
                    'serial_number': row['SerijskiBroj'],
                    'owner': row['Vlasnik'],
                    'homologation_number': row['HomologacijskaOznaka'],
                }

                # logger.info(f"Creating/updating TrafficCard with data: {traffic_card_data} for vehicle {vehicle} at row: {index}")

                # Kreirajte ili ažurirajte TrafficCard
                TrafficCard.objects.update_or_create(
                    vehicle=vehicle,
                    registration_number=row['RegistarskaOznaka'],
                    defaults=traffic_card_data
                )
                print('UNETO USPESNO',{row['BrojSasije']})
            except InvalidOperation as e:
                logger.error(f"Error processing row {index} with chassis number {row['BrojSasije']}: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error processing row {index} with chassis number {row['BrojSasije']}: {e}")

        logger.info("Data import completed.")


