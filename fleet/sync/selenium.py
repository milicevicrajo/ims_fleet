import csv
import logging
import os
import re
import time
import unicodedata
from datetime import date, datetime, timedelta

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
from fleet.sync.browser import create_chrome_driver, create_chrome_options
from fleet.support.vehicle import (
    format_license_plate,

)

logger = logging.getLogger(__name__)


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


def get_vehicle_job_code(vehicle):
    job_code = vehicle.job_codes.select_related("organizational_unit").first()
    if job_code and job_code.organizational_unit:
        return job_code.organizational_unit.code
    return None


def previous_month_range(reference_date=None):
    reference_date = reference_date or date.today()
    first_this_month = reference_date.replace(day=1)
    last_previous_month = first_this_month - timedelta(days=1)
    first_previous_month = last_previous_month.replace(day=1)
    return first_previous_month, last_previous_month


def nis_date_prefix(value):
    return f"{value.day:02d}.{value.month:02d}.{value.year}."


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    replacements = {
        "Ã„Â": "c",
        "Ã„â€¡": "c",
        "Ã„â€˜": "dj",
        "Ã…Â¡": "s",
        "Ã…Â¾": "z",
        "Ã…Â ": "s",
        "Ä": "c",
        "Ä‡": "c",
        "Ä‘": "dj",
        "Å¡": "s",
        "Å¾": "z",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def visible_nis_picker(driver):
    for picker in driver.find_elements(By.CSS_SELECTOR, ".rdtPicker"):
        if picker.is_displayed():
            return picker
    return None


def active_nis_picker_month(driver):
    picker = visible_nis_picker(driver)
    if picker is None:
        return None
    return picker.find_element(By.CSS_SELECTOR, ".rdtSwitch").text.strip().lower()


def parse_nis_picker_month(value):
    if not value:
        return None

    value = normalized(value)
    months = {
        "jan": 1, "januar": 1, "january": 1,
        "feb": 2, "februar": 2, "february": 2,
        "mar": 3, "mart": 3, "march": 3,
        "apr": 4, "april": 4,
        "maj": 5, "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "avg": 8, "avgust": 8, "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "septembar": 9, "september": 9,
        "okt": 10, "oktobar": 10, "oct": 10, "october": 10,
        "nov": 11, "novembar": 11, "november": 11,
        "dec": 12, "decembar": 12, "december": 12,
    }

    year_match = re.search(r"(20\d{2}|19\d{2})", value)
    if not year_match:
        return None
    year = int(year_match.group(1))
    month_text = value[:year_match.start()]
    for month_name, month_number in months.items():
        if month_name in month_text:
            return year, month_number
    return None


def open_nis_datetime_picker(driver, label):
    input_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'form-field-wrapper')][.//label[contains(normalize-space(.),"
            f"'{label}')]]//input[@type='text']",
        ))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_element)
    time.sleep(0.5)
    input_element.click()
    time.sleep(0.2)
    input_element.click()
    WebDriverWait(driver, 10).until(lambda current_driver: visible_nis_picker(current_driver) is not None)
    return True


def click_active_nis_picker_nav(driver, direction):
    picker = visible_nis_picker(driver)
    if picker is None:
        return False
    selector = ".rdtPrev" if direction < 0 else ".rdtNext"
    picker.find_element(By.CSS_SELECTOR, selector).click()
    return True


def select_day_in_active_nis_picker(driver, target_date):
    picker = visible_nis_picker(driver)
    if picker is None:
        return False
    cells = picker.find_elements(By.CSS_SELECTOR, "td.rdtDay:not(.rdtOld):not(.rdtNew)")
    for cell in cells:
        if cell.get_attribute("data-value") == str(target_date.day):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cell)
            time.sleep(0.2)
            cell.click()
            return True
    return False


def get_nis_datetime_field_value(driver, label):
    script = """
    const labelText = arguments[0];
    const wrappers = Array.from(document.querySelectorAll('.form-field-wrapper'));
    const wrapper = wrappers.find((item) => {
      const label = item.querySelector('label.key');
      return label && label.textContent.replace(/\\s+/g, ' ').trim().includes(labelText);
    });
    const input = wrapper && wrapper.querySelector('input[type="text"]');
    return input ? input.value : null;
    """
    return driver.execute_script(script, label)


def select_nis_date_with_widget(driver, label, target_date, fixed_prev_clicks=0):
    if not open_nis_datetime_picker(driver, label):
        return "field_not_found"

    for _ in range(20):
        if active_nis_picker_month(driver):
            break
        time.sleep(0.25)
    else:
        return "picker_not_open"

    if fixed_prev_clicks:
        for _ in range(fixed_prev_clicks):
            if not click_active_nis_picker_nav(driver, -1):
                return "nav_not_found"
            time.sleep(0.5)
    else:
        target_month_index = target_date.year * 12 + target_date.month
        for _ in range(36):
            current = parse_nis_picker_month(active_nis_picker_month(driver))
            if not current:
                return "month_not_read"
            current_month_index = current[0] * 12 + current[1]
            if current_month_index == target_month_index:
                break
            if not click_active_nis_picker_nav(driver, -1 if current_month_index > target_month_index else 1):
                return "nav_not_found"
            time.sleep(0.5)
        else:
            return "month_not_reached"

    if not select_day_in_active_nis_picker(driver, target_date):
        return "day_not_found"
    time.sleep(1)

    value = get_nis_datetime_field_value(driver, label) or ""
    if not value.startswith(nis_date_prefix(target_date)):
        return f"value_not_changed:{value}"
    return "ok"


def kerio_login():
    step_pause_seconds = 2
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
    time.sleep(step_pause_seconds)

    try:
        driver.get(login_url)
        time.sleep(step_pause_seconds)

        username_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        time.sleep(step_pause_seconds)
        driver.execute_script("arguments[0].removeAttribute('readonly')", username_input)
        time.sleep(step_pause_seconds)
        username_input.clear()
        time.sleep(step_pause_seconds)
        username_input.send_keys(username)
        time.sleep(step_pause_seconds)

        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        time.sleep(step_pause_seconds)
        password_input.send_keys(password)
        time.sleep(step_pause_seconds)

        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "login-button"))
        )
        time.sleep(step_pause_seconds)
        driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
        time.sleep(step_pause_seconds)

        try:
            login_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", login_button)
        time.sleep(step_pause_seconds)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(step_pause_seconds)

    finally:
        driver.quit()

def nis_data_import():
    step = "start"
    driver = None
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_dir = os.path.join(settings.BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "nis_debug.log")
    if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == log_path for handler in logger.handlers):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    try:
        login_url = "https://cards.nis.rs"
        username = "zoran.institutims"
        password = "3RrrvvVg"
        date_from, date_to = previous_month_range()

        chrome_options = create_chrome_options()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-web-security")
        # NIS se namerno pokrece vidljivo dok stabilizujemo Selenium tok.
        # Kada zavrsimo debug, ovo moze nazad na "--headless".
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        download_path = r"C:\nis_repo"
        os.makedirs(download_path, exist_ok=True)
        prefs = {"download.default_directory": download_path}
        chrome_options.add_experimental_option("prefs", prefs)

        step = "create_chrome_driver"
        driver = create_chrome_driver(chrome_options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)
        driver.implicitly_wait(5)
        driver.set_window_size(1920, 1080)

        try:
            step = "open_login_page"
            logger.info("NIS: opening login page")
            driver.get(login_url)
            logger.info("Opened login page")

            step = "username_input"
            logger.info("NIS: waiting for username input")
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Koris') or @name='username' or @type='text']"))
            )
            username_input.clear()
            username_input.send_keys(username)
            logger.info("Entered username")

            step = "password_input"
            logger.info("NIS: waiting for password input")
            password_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Lozinka') or @name='password' or @type='password']"))
            )
            password_input.clear()
            password_input.send_keys(password)
            logger.info("Entered password")

            step = "login_button"
            logger.info("NIS: waiting for login button")
            login_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(@class, 'pure-button-primary')]"))
            )
            login_button.click()
            logger.info("Clicked submit button")
            time.sleep(1)
            logger.info("NIS: after login url=%s title=%s", driver.current_url, driver.title)

            step = "client_transactions_page"
            dismiss_disclaimer_overlay(driver)
            logger.info("NIS: opening client transactions page")
            driver.get(login_url.rstrip("/") + "/reports/client-transactions")

            time.sleep(2)

            step = "report_form_loaded"
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(., 'Datum od')]"))
            )

            step = "date_from"
            logger.info("NIS: setting Datum od to previous month start: %s", date_from)
            date_from_result = select_nis_date_with_widget(driver, "Datum od", date_from, fixed_prev_clicks=2)
            if date_from_result != "ok":
                raise RuntimeError(f"NIS sync nije uspeo da postavi Datum od: {date_from_result}.")
            time.sleep(2)

            try:
                step = "date_to"
                logger.info("NIS: setting Datum do to previous month end: %s", date_to)
                date_to_result = select_nis_date_with_widget(driver, "Datum do", date_to)
                if date_to_result != "ok":
                    logger.warning("NIS sync nije uspeo da postavi Datum do: %s", date_to_result)
                time.sleep(2)
            except Exception:
                logger.exception("NIS: Datum do nije postavljen, nastavljam sa podrazumevanim datumom na portalu.")

            step = "date_validation"
            actual_from = get_nis_datetime_field_value(driver, "Datum od")
            expected_from = nis_date_prefix(date_from)
            if not (actual_from or "").startswith(expected_from):
                raise RuntimeError(
                    "NIS datum nije prihvacen. "
                    f"Ocekivano Datum od: {expected_from}; na stranici: {actual_from}."
                )

            try:
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "loader"))
                )
            except Exception:
                pass

            step = "show_report_button"
            logger.info("NIS: waiting for show report button")
            show_report_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pure-button-primary') and (contains(normalize-space(.), 'Prika') or contains(normalize-space(.), 'izve'))]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_report_button)
            time.sleep(2)
            ActionChains(driver).move_to_element(show_report_button).click().perform()

            time.sleep(2)

            step = "download_dropdown"
            logger.info("NIS: waiting for download dropdown")
            dropdown_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'download-button')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_button)
            time.sleep(2)
            dropdown_button.click()

            time.sleep(2)

            step = "xlsx_option"
            logger.info("NIS: waiting for XLSX option")
            xlsx_option = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//li[@class='option']//button[contains(., 'XLSX')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", xlsx_option)
            time.sleep(2)
            ActionChains(driver).move_to_element(xlsx_option).click().perform()

            time.sleep(2)

            step = "download_file"
            logger.info("NIS: waiting for download file")
            xlsx_file_path = wait_for_download_file(download_path, timeout=90)
            import_nis_fuel_consumption(xlsx_file_path)
            import_nis_transactions(xlsx_file_path)
            return "Funkcija NIS Data Import je uspesno izvrsena"

        except Exception:
            logger.exception("NIS data import failed at step '%s'.", step)
            if driver:
                logger.error("NIS browser ostaje otvoren 5 minuta za pregled.")
                time.sleep(300)
            raise
        finally:
            driver.quit()

    except Exception as e:
        raise RuntimeError(f"NIS data import failed at step '{step}': {e}") from e


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

    return "OMV PutniÄka komanda uspeÅ¡no zavrÅ¡ena."


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

                # PronaÄ‘i vozilo prema formatiranoj tablici u TrafficCard modelu
                traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
                vehicle = traffic_card.vehicle

                # Konvertuj datume i druge vrednosti
                naive_dt = datetime.strptime(row['Transactiondate'], '%Y-%m-%d %H:%M:%S')
                transaction_date = dj_timezone.make_aware(naive_dt, dj_timezone.get_current_timezone()) if dj_timezone.is_naive(naive_dt) else naive_dt
                amount = float(row['Quantity'].replace(',', '.'))

                # Konvertuj bruto troÅ¡ak i PDV u decimalne vrednosti
                cost_bruto = float(row['Gross CC'].replace(',', '').strip())
                vat = float(row['VAT'].replace(',', '').strip())

                job_code = get_vehicle_job_code(vehicle)
                # IzraÄunaj neto troÅ¡ak
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
                    logger.info(f"Successfully imported fuel consumption for vehicle {vehicle.chassis_number}")
                except IntegrityError:
                    logger.warning(f"Duplicate fuel consumption skipped for {formatted_plate} {transaction_date} {cost_bruto} {amount}.")
            
            except ObjectDoesNotExist:
                logger.warning(f"Vehicle with license plate {row['License plate No']} not found.")
            except Exception as e:
                logger.error(f"Error importing row: {row}. Error: {str(e)}")


def import_omv_transactions_from_csv(csv_file_path):
    timezone = pytz.timezone(settings.TIME_ZONE)

    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')  # Pazi na delimiter ';'
        for row in reader:
            try:
                # Formatiraj tablice
                formatted_plate = format_license_plate(row['License plate No'])
                
                # PronaÄ‘i vozilo prema formatiranoj tablici u TrafficCard
                traffic_card = TrafficCard.objects.get(registration_number=formatted_plate)
                vehicle = traffic_card.vehicle

                def to_aware_datetime(value, format='%Y-%m-%d %H:%M:%S'):
                    if value:
                        naive_datetime = datetime.strptime(value, format)
                        return timezone.localize(naive_datetime)
                    return None

                # Konverzija numeriÄkih vrednosti, ostavi kao None ako je prazno
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
                
                # Kreiraj instancu TransactionOMV modela i saÄuvaj je u bazi
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
                logger.info(f"Successfully imported transaction for vehicle {formatted_plate}")
            
            except ObjectDoesNotExist:
                logger.warning(f"Vehicle with license plate {row['License plate No']} not found.")
            except Exception as e:
                logger.error(f"Error importing row: {row}. Error: {str(e)}")

def import_nis_fuel_consumption(file_path):
    # Preuzmi vremensku zonu iz Django podeÅ¡avanja
    timezone = pytz.timezone(settings.TIME_ZONE)
    
    # UÄitaj Excel fajl
    df = pd.read_excel(file_path, sheet_name=0, header=1, engine="openpyxl")

    # Ostatak funkcije ostaje isti...
    for index, row in df.iterrows():
        try:
            # Formatiraj registarski broj pre nego Å¡to ga upotrebiÅ¡
            formatted_plate = format_license_plate(row['Registarska oznaka vozila'].strip().upper())

            # PronaÄ‘i vozilo prema formatiranom registracionom brcoju u TrafficCard modelu
            traffic_card = TrafficCard.objects.using("server_db").get(registration_number=formatted_plate)
            vehicle = traffic_card.vehicle

            # Konverzija datuma transakcije sa vremenskom zonom
            naive_transaction_date = pd.to_datetime(row['Datum transakcije'], format='%d.%m.%Y %H:%M:%S')
            transaction_date = timezone.localize(naive_transaction_date)  # Dodaj vremensku zonu
            
            job_code = get_vehicle_job_code(vehicle)
           
            FuelConsumption.objects.using("server_db").create(
                vehicle=vehicle,
                date=transaction_date,
                amount=row['KoliÄina'],
                fuel_type=row['Naziv proizvoda'],
                cost_bruto=row['Total'],
                cost_neto=round(row['Total']*5/6,2),
                supplier="NIS",
                job_code=job_code,
                mileage=row['KilometraÅ¾a'] if isinstance(row['KilometraÅ¾a'], (int, float)) and not pd.isna(row['KilometraÅ¾a']) else 0,
            )
            logger.info(f"Successfully imported fuel consumption for vehicle {vehicle.chassis_number}")
        
        except ObjectDoesNotExist:
            logger.warning(f"Vehicle with registration number {formatted_plate} not found.")
        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")


def import_nis_transactions(file_path):
    # Preuzmi vremensku zonu iz Django podeÅ¡avanja
    timezone = pytz.timezone(settings.TIME_ZONE)
    # UÄitaj Excel fajl
    df = pd.read_excel(file_path, sheet_name=0, header=1)  # Koristi prvi sheet i drugi red kao zaglavlje

    for index, row in df.iterrows():
        try:
            # Formatiraj registarski broj pre nego Å¡to ga upotrebiÅ¡
            formatted_plate = format_license_plate(row['Registarska oznaka vozila'].strip().upper())

            # PronaÄ‘i vozilo prema formatiranom registracionom broju u TrafficCard modelu
            traffic_card = TrafficCard.objects.using("server_db").get(registration_number=formatted_plate)
            vehicle = traffic_card.vehicle

            # Konverzija datuma transakcije sa vremenskom zonom
            naive_transaction_date = pd.to_datetime(row['Datum transakcije'], format='%d.%m.%Y %H:%M:%S')
            transaction_date = timezone.localize(naive_transaction_date)  # Dodaj vremensku zonu

            # Konverzija numeriÄkih vrednosti gde je potrebno
            kolicina = row['KoliÄina']
            popust = row['Popust']
            total = row['Total']
            cena_sa_kase = row['Cena sa kase']

            # Postavi kilometraÅ¾u na None ako nije dostupna
            kilometraza = int(row['KilometraÅ¾a']) if pd.notna(row['KilometraÅ¾a']) else None

            # Kreiraj instancu TransactionIMS modela
            TransactionNIS.objects.using("server_db").create(
                vehicle=vehicle,
                kupac=row['Kupac'],
                sifra_kupca=row['Å ifra kupca'],
                broj_kartice=row['Broj kartice'],
                kompanijski_kod_kupca=row['Å ifra kupca'],
                zemlja_sipanja=row['DrÅ¾ava sipanja'],
                benzinska_stanica=row['Benzinska stanica'],
                id_transakcije=row['ID transakcije'],
                app_kod=row['App kod'],
                datum_transakcije=transaction_date,
                tociono_mesto=row['ToÄiono mesto'],
                naziv_kartice=row['Naziv kartice'],
                licenca=row.get('Licenca', ''),
                broj_gazdinstva=row.get('Broj gazdinstva', ''),
                registarska_oznaka_vozila=formatted_plate,
                broj_racuna=row['Broj raÄuna'],
                kilometraza=kilometraza,
                sipanje_van_rezervoara=row['Sipanje van rezervoara'],
                naziv_proizvoda=row['Naziv proizvoda'],
                kolicina=kolicina,
                kolicina_kg=row.get('KoliÄina KG', None),
                popust=popust,
                primenjen_popust=row['Primenjen popust'],
                cena_sa_kase=cena_sa_kase,
                cena=row['Cena'],
                total_sa_kase=row['Total sa kase'],
                total=total,
                valuta=row['Valuta'],
                aktivirano_prekoracenje=row['Aktivirano prekoraÄenje'],
                kolicinsko_prekoracenje=row['KoliÄinsko prekoraÄenje'],
                finansijsko_prekoracenje=row['Finansijsko prekoraÄenje'],
                nacin_ocitavanja_kartice=row['NaÄin oÄitavanja kartice']
            )
            logger.info(f"Successfully imported transaction for vehicle {formatted_plate}")
        
        except ObjectDoesNotExist:
            logger.warning(f"Vehicle with registration number {row['Registarska oznaka vozila']} (formatted as {formatted_plate}) not found.")
        except Exception as e:
            logger.error(f"Error importing row {index}: {e}")

