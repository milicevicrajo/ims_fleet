import csv
import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import pytz

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.utils import timezone as dj_timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException

from fleet.models import FuelConsumption, TrafficCard, TransactionNIS, TransactionOMV
from fleet.selenium_utils import create_chrome_driver, create_chrome_options
from fleet.utils import (
    format_license_plate,

)


def dismiss_disclaimer_overlay(driver):
    try:
        overlays = driver.find_elements(By.CLASS_NAME, "disclaimer-component")
        if overlays:
            driver.execute_script(
                "document.querySelectorAll('.disclaimer-component').forEach(el => el.style.display='none');"
            )
    except Exception:
        pass

def get_latest_download_file(download_path):
    files = os.listdir(download_path)
    paths = [os.path.join(download_path, basename) for basename in files]
    latest_file = max(paths, key=os.path.getctime)
    return latest_file


def wait_for_download_file(download_path, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        files = [
            f for f in os.listdir(download_path)
            if not f.endswith(".crdownload") and not f.endswith(".tmp")
        ]
        if files:
            paths = [os.path.join(download_path, basename) for basename in files]
            return max(paths, key=os.path.getctime)
        time.sleep(1)
    raise TimeoutException("Download file not found within timeout.")


def kerio_login():
    login_url = "https://control.ims.rs:4081/login/?NTLM=0&orig=Y29udHJvbC5pbXMucnM=&dest=aHR0cDovL3d3dy5nc3RhdGljLmNvbS9nZW5lcmF0ZV8yMDQ=&host=MTkyLjE2OC42LjcgMWYzYTA5ODgyYzIxYWJjNjM2Y2FlNzAzZjQ1YjRmZGU="
    username = "tatko"
    password = "Abacus236"

    chrome_options = create_chrome_options()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = create_chrome_driver(chrome_options)

    try:
        driver.get(login_url)

        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        driver.execute_script("arguments[0].removeAttribute('readonly')", username_input)
        username_input.clear()
        username_input.send_keys(username)

        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.send_keys(password)

        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "login-button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)

        try:
            login_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", login_button)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

    finally:
        driver.quit()

def nis_data_import():
    try:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(r"C:\djangoapps\ims_fleet\nis_debug.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        login_url = "https://cards.nis.rs"
        username = "zoran.institutims"
        password = "3RrrvvVg"

        chrome_options = create_chrome_options()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        download_path = r"C:\nis_repo"
        prefs = {"download.default_directory": download_path}
        chrome_options.add_experimental_option("prefs", prefs)

        driver = create_chrome_driver(chrome_options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)
        driver.implicitly_wait(5)
        driver.set_window_size(1920, 1080)

        try:
            logger.info("NIS: opening login page")
            driver.get(login_url)
            logger.info("Opened login page")

            logger.info("NIS: waiting for username input")
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Korisničko ime']"))
            )
            username_input.send_keys(username)
            logger.info("Entered username")

            logger.info("NIS: waiting for password input")
            password_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Lozinka']"))
            )
            password_input.send_keys(password)
            logger.info("Entered password")

            logger.info("NIS: waiting for login button")
            login_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(@class, 'pure-button-primary')]"))
            )
            login_button.click()
            logger.info("Clicked submit button")

            time.sleep(5)

            dismiss_disclaimer_overlay(driver)
            logger.info("NIS: waiting for reports link")
            reports_link = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Izveštaji')]"))
            )
            driver.execute_script("arguments[0].click();", reports_link)

            time.sleep(2)

            logger.info("NIS: waiting for client transactions link")
            client_transactions_link = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/reports/client-transactions' and contains(text(),'Transakcije po kupcima')]"))
            )
            client_transactions_link.click()

            time.sleep(2)

            try:
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "loader"))
                )
            except Exception:
                pass

            logger.info("NIS: waiting for show report button")
            show_report_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pure-button-primary') and contains(., 'Prikaži izveštaj')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_report_button)
            ActionChains(driver).move_to_element(show_report_button).click().perform()

            time.sleep(2)

            logger.info("NIS: waiting for download dropdown")
            dropdown_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'download-button')]"))
            )
            dropdown_button.click()

            time.sleep(1)

            logger.info("NIS: waiting for XLSX option")
            xlsx_option = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//li[@class='option']//button[contains(., 'XLSX')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", xlsx_option)
            ActionChains(driver).move_to_element(xlsx_option).click().perform()

            time.sleep(2)

            logger.info("NIS: waiting for download file")
            xlsx_file_path = wait_for_download_file(download_path, timeout=90)
            import_nis_fuel_consumption(xlsx_file_path)
            import_nis_transactions(xlsx_file_path)
            return "Funkcija NIS Data Import je uspešno izvršena"

        finally:
            driver.quit()

    except Exception as e:
        return f"Error: {str(e)}"

def omv_putnicka_data_import(*args, **kwargs):
    login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
    username = "710111107248"
    password = "OMV-107248"

    today = datetime.now().strftime("%Y-%m-%d")
    default_date_from = datetime(2024, 1, 1).strftime("%Y-%m-%d")

    date_from = kwargs.get('date_from', default_date_from)
    date_to = today

    chrome_options = create_chrome_options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    download_path = r"C:\omv_repo"
    prefs = {"download.default_directory": download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = create_chrome_driver(chrome_options)

    try:
        driver.get(login_url)

        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.send_keys(username)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        language_select = driver.find_element(By.NAME, "language")
        for option in language_select.find_elements(By.TAG_NAME, 'option'):
            if option.text == 'English':
                option.click()
                break

        login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        login_button.click()

        time.sleep(1)

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "header"))
        )

        transaction_information_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='header.do?selectModule=transactioninformation']"))
        )
        transaction_information_link.click()

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "functionnavigation"))
        )

        reports_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='functionNavigation.do?openFunction=transactioninformation.report.overview']"))
        )
        reports_link.click()

        transactions_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='genSearchCriteria.do?activateFunction=transactioninformation.report.transaction&openFunction=transactioninformation.report.overview']"))
        )
        transactions_link.click()

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "searchcriteria"))
        )

        date_from_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Transactiondatefrom"))
        )
        date_from_input.clear()
        date_from_input.send_keys(date_from)

        date_to_input = driver.find_element(By.NAME, "Transactiondate1")
        date_to_input.clear()
        date_to_input.send_keys(date_to)

        driver.execute_script("goContent()")

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "content"))
        )

        download_link = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href=\"javascript:openURL_Loading('browseTransactionList.do?event=CsvFileRequest');\"]"))
        )
        download_link.click()
        time.sleep(5)

        csv_file_path = get_latest_download_file(download_path)
        import_omv_fuel_consumption_from_csv(csv_file_path)
        import_omv_transactions_from_csv(csv_file_path)

    finally:
        driver.quit()

    return "OMV Putnička komanda uspešno završena."


def omv_teretna_data_import(*args, **kwargs):
    login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
    username = "710111107258"
    password = "OMV-107258"

    today = datetime.now().strftime("%Y-%m-%d")
    default_date_from = datetime(2024, 1, 1).strftime("%Y-%m-%d")

    date_from = kwargs.get('date_from', default_date_from)
    date_to = today

    chrome_options = create_chrome_options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    download_path = r"C:\omv_repo"
    prefs = {"download.default_directory": download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = create_chrome_driver(chrome_options)

    try:
        driver.get(login_url)

        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.send_keys(username)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        language_select = driver.find_element(By.NAME, "language")
        for option in language_select.find_elements(By.TAG_NAME, 'option'):
            if option.text == 'English':
                option.click()
                break

        login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        login_button.click()

        time.sleep(1)

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "header"))
        )

        transaction_information_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='header.do?selectModule=transactioninformation']"))
        )
        transaction_information_link.click()

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "functionnavigation"))
        )
        time.sleep(2)

        reports_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='functionNavigation.do?openFunction=transactioninformation.report.overview']"))
        )
        reports_link.click()
        time.sleep(2)

        transactions_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='genSearchCriteria.do?activateFunction=transactioninformation.report.transaction&openFunction=transactioninformation.report.overview']"))
        )
        transactions_link.click()

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "searchcriteria"))
        )
        time.sleep(2)

        date_from_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Transactiondatefrom"))
        )
        date_from_input.clear()
        date_from_input.send_keys(date_from)

        date_to_input = driver.find_element(By.NAME, "Transactiondate1")
        date_to_input.clear()
        date_to_input.send_keys(date_to)

        driver.execute_script("goContent()")
        time.sleep(2)

        driver.switch_to.default_content()
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "content"))
        )

        download_link = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href=\"javascript:openURL_Loading('browseTransactionList.do?event=CsvFileRequest');\"]"))
        )
        download_link.click()
        time.sleep(5)

        csv_file_path = get_latest_download_file(download_path)
        import_omv_fuel_consumption_from_csv(csv_file_path)
        import_omv_transactions_from_csv(csv_file_path)

    finally:
        driver.quit()

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
                naive_dt = datetime.strptime(row['Transactiondate'], '%Y-%m-%d %H:%M:%S')
                transaction_date = dj_timezone.make_aware(naive_dt, dj_timezone.get_current_timezone()) if dj_timezone.is_naive(naive_dt) else naive_dt
                amount = float(row['Quantity'].replace(',', '.'))

                # Konvertuj bruto trošak i PDV u decimalne vrednosti
                cost_bruto = float(row['Gross CC'].replace(',', '').strip())
                vat = float(row['VAT'].replace(',', '').strip())

                job_code = vehicle.job_codes.first().organizational_unit.code
                # Izračunaj neto trošak
                cost_neto = cost_bruto - vat

                try:
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
                except IntegrityError:
                    print(f"Duplicate fuel consumption skipped for {formatted_plate} {transaction_date} {cost_bruto} {amount}.")
            
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
                    invoice_no=row['Voucher'],
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
                naive_dt = datetime.strptime(row['Transactiondate'], '%Y-%m-%d %H:%M:%S')
                transaction_date = dj_timezone.make_aware(naive_dt, dj_timezone.get_current_timezone()) if dj_timezone.is_naive(naive_dt) else naive_dt
                amount = float(row['Quantity'].replace(',', '.'))

                # Konvertuj bruto trošak i PDV u decimalne vrednosti
                cost_bruto = float(row['Gross CC'].replace(',', '').strip())
                vat = float(row['VAT'].replace(',', '').strip())

                job_code = vehicle.job_codes.first().organizational_unit.code
                # Izračunaj neto trošak
                cost_neto = cost_bruto - vat

                try:
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
                except IntegrityError:
                    print(f"Duplicate fuel consumption skipped for {formatted_plate} {transaction_date} {cost_bruto} {amount}.")
            
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
                    invoice_no=row['Voucher'],
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

            # Pronađi vozilo prema formatiranom registracionom brcoju u TrafficCard modelu
            traffic_card = TrafficCard.objects.using("server_db").get(registration_number=formatted_plate)
            vehicle = traffic_card.vehicle

            # Konverzija datuma transakcije sa vremenskom zonom
            naive_transaction_date = pd.to_datetime(row['Datum transakcije'], format='%d.%m.%Y %H:%M:%S')
            transaction_date = timezone.localize(naive_transaction_date)  # Dodaj vremensku zonu
            
            job_code = vehicle.job_codes.first().organizational_unit.code
           
            FuelConsumption.objects.using("server_db").create(
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
            traffic_card = TrafficCard.objects.using("server_db").get(registration_number=formatted_plate)
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
            TransactionNIS.objects.using("server_db").create(
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
