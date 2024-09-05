import csv
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from .models import FuelConsumption, Vehicle, TrafficCard, JobCode, TrafficCard, Lease, Policy,Employee
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

def get_latest_download_file(download_path):

    # Dobij sve fajlove iz direktorijuma za preuzimanje
    files = os.listdir(download_path)
    
    # Pronađi najnoviji fajl na osnovu vremena modifikacije
    paths = [os.path.join(download_path, basename) for basename in files]
    latest_file = max(paths, key=os.path.getctime)
    
    return latest_file

def format_license_plate(plate):
    # Uklanjanje svih belina i crtice iz tablice
    plate = plate.replace(" ", "").replace("-", "").upper()

    # Proba da preoblikuje tablicu, na primer BG1461DX -> BG1461-DX
    match = re.match(r'^([A-Z]{2})(\d{3,4})([A-Z]{2})$', plate)
    if match:
        return f"{match.group(1)}{match.group(2)}-{match.group(3)}"

    # Ako nije moguće preoblikovati tablicu, vrati originalnu vrednost (ili baci grešku)
    return plate  # Ili podigni grešku ako je to potrebno


def import_omv_fuel_consumption_from_csv(csv_file_path):
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            try:
                # Formatiraj tablice
                formatted_plate = format_license_plate(row['License plate No'])

                # Pronađi vozilo prema formatiranoj tablici u TrafficCard
                traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
                vehicle = traffic_card.vehicle

                # Konvertuj vrednosti i pripremi ih za unos u bazu
                transaction_date = datetime.strptime(row['Transactiondate'], '%Y-%m-%d %H:%M:%S').date()
                amount = float(row['Quantity'].replace(',', '.'))

                # Ispravna konverzija troška
                cost_bruto = row['Gross CC'].replace(',', '')
                cost_neto = row['Amount other'].replace(',', '')

                # Kreiraj FuelConsumption instancu i sačuvaj je u bazi
                FuelConsumption.objects.create(
                    vehicle=vehicle,
                    date=transaction_date,
                    amount=amount,
                    fuel_type=row['Product INV'],
                    cost_bruto=cost_bruto,
                    cost_neto=cost_neto,
                    supplier="OMV"
                )
                print(f"Successfully imported fuel consumption for vehicle {vehicle.chassis_number}")
            
            except ObjectDoesNotExist:
                print(f"Vehicle with license plate {row['License plate No']} not found.")
            except Exception as e:
                print(f"Error importing row: {row}. Error: {str(e)}")


#python manage.py crontab add
class OMVCommand(BaseCommand):
    help = 'Downloads a report from OMV website and imports data into the database'

    def handle(self, *args, **kwargs):
        # Define the URLs and credentials
        login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
        username = "710111107258"
        password = "OMV-107258"

        # Set up Chrome options to download files to a specific location
        download_path = r"C:\Users\Rajo\Downloads"
        chrome_options = webdriver.ChromeOptions()
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

            # Clear and set the 'date from' input
            date_from_input.clear()
            date_from_input.send_keys("2024-05-11")
            print("Entered date from")

            # Clear and set the 'date to' input
            date_to_input = driver.find_element(By.NAME, "Transactiondate1")
            date_to_input.clear()
            date_to_input.send_keys("2024-07-11")
            print("Entered date to")

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
            print(f"Data imported successfully from {csv_file_path}")

        finally:
            # Close the browser
            driver.quit()
            print("Browser closed")

def format_license_plate(plate):
    # Ukloni sve beline i crtice iz registracionog broja
    plate = plate.replace(" ", "").replace("-", "").upper()

    # Dodaj crtu na odgovarajuće mesto da dobiješ format AA999-AA ili AA9999-AA
    match = re.match(r'^([A-Z]{2})(\d{3,4})([A-Z]{2})$', plate)
    if match:
        return f"{match.group(1)}{match.group(2)}-{match.group(3)}"
    
    # Ako nije moguće preoblikovati tablicu, vrati originalnu vrednost (ili baci grešku)
    return plate  # Ili podigni grešku ako je to potrebno

def import_nis_fuel_consumption(file_path):

    # Učitaj Excel fajl
    df = pd.read_excel(file_path, sheet_name=0, header=1)  # Koristi prvi sheet i drugi red kao zaglavlje

    # Ostatak funkcije ostaje isti...
    for index, row in df.iterrows():
        try:
            # Formatiraj registarski broj pre nego što ga upotrebiš
            formatted_plate = format_license_plate(row['Br. tablica'].strip().upper())

            # Pronađi vozilo prema formatiranom registracionom broju u TrafficCard modelu
            traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
            vehicle = traffic_card.vehicle


            transaction_date = pd.to_datetime(row['Datum transakcije'], format='%d.%m.%Y %H:%M:%S').date()

           
            FuelConsumption.objects.create(
                vehicle=vehicle,
                date=transaction_date,
                amount=row['Količina'],
                fuel_type=row['Naziv proizvoda'],
                cost_bruto=row['Total sa kase'],
                cost_neto=row['Total'],
                supplier="NIS"
            )
            print(f"Successfully imported fuel consumption for vehicle {vehicle.chassis_number}")
        
        except ObjectDoesNotExist:
            print(f"Vehicle with registration number {row['Br. tablica']} (formatted as {formatted_plate}) not found.")
        except Exception as e:
            print(f"Error importing row {index}: {e}")
            
class NISCommand(BaseCommand):
    help = 'Downloads a report from NIS website and imports data into the database'

    def handle(self, *args, **kwargs):
        # Define the URLs and credentials
        login_url = "https://cards.nis.rs"
        username = "zoran.institutims"
        password = "3RrrvvVg"

        # Set up Chrome options to download files to a specific location
        download_path = r"C:\Users\Rajo\Downloads"
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": download_path}
        chrome_options.add_experimental_option("prefs", prefs)

        # Initialize WebDriver
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Open the login page
            driver.get(login_url)
            print("Opened login page")

            # Locate the element by its placeholder attribute and enter the username
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Korisničko ime']"))
            )
            username_input.send_keys(username)
            print("Entered username")

            # Locate the password input element by its placeholder attribute and enter the password
            password_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Lozinka']"))
            )
            password_input.send_keys(password)
            print("Entered password")

            # Locate and click the submit button
            login_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//button[@type='submit' and contains(@class, 'pure-button-primary')]"))
            )
            login_button.click()
            print("Clicked submit button")

            # Wait for some time to ensure the page loads completely
            time.sleep(1)

            # Click on the 'Izveštaji' link
            reports_link = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'Izveštaji')]"))
            )
            reports_link.click()
            print("Clicked on 'Izveštaji' link")

            # Click on 'Transakcije po klijentima'
            client_transactions_link = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/reports/client-transactions' and contains(text(),'Transakcije po klijentima')]"))
            )
            client_transactions_link.click()
            print("Clicked on 'Transakcije po klijentima' link")

            # Locate and click the 'Prikaži izveštaj' button
            show_report_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'pure-button-primary') and contains(., 'Prikaži izveštaj')]"))
            )
            show_report_button.click()
            print("Clicked 'Prikaži izveštaj' button")

            # Click on the download dropdown and select 'CSV'
            dropdown_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'download-button')]"))
            )
            dropdown_button.click()
            print("Clicked on download dropdown")

            csv_option = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//li[@class='option']//button[contains(., 'CSV')]"))
            )
            csv_option.click()
            print("Clicked on CSV option")

            # Wait for the download to complete
            time.sleep(5)
            print("CSV file downloaded successfully")

            # Pronađi najnovije preuzeti fajl
            csv_file_path = get_latest_download_file(download_path)
            print(csv_file_path)

            # Importuj podatke u bazu
            import_nis_fuel_consumption(csv_file_path)
            print(f"Data imported successfully from {csv_file_path}")

        finally:
            # Close the browser
            driver.quit()
            print("Browser closed")


def import_job_codes_from_excel(file_path):
    # Učitaj Excel sheet
    df = pd.read_excel(file_path, sheet_name='sif_pos_dodeljeno')

    # Prođi kroz svaki red u DataFrame-u
    for index, row in df.iterrows():
        try:
            # Formatiraj registracioni broj
            reg_br = row['RegBr'].strip().upper()

            # Pronađi TrafficCard prema registracionom broju
            traffic_card = TrafficCard.objects.get(registration_number=reg_br)
            vehicle = traffic_card.vehicle  # Pronađi povezano vozilo

            # Pravilno učitaj datum
            assigned_date = pd.to_datetime(row['od'], format='%d/%m/%Y').date()

            # Kreiraj novi JobCode zapis
            JobCode.objects.create(
                vehicle=vehicle,
                job_code=str(row['SifPos']),
                assigned_date=assigned_date
            )
            print(f"Successfully imported job code {row['SifPos']} for vehicle with registration number {reg_br}")
        
        except ObjectDoesNotExist:
            print(f"Traffic card with registration number {reg_br} not found.")
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
