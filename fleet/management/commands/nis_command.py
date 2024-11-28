from ...utils import get_latest_download_file, import_nis_fuel_consumption, import_nis_transactions
import time
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Command(BaseCommand):
    help = 'Downloads a report from NIS website and imports data into the database'

    def handle(self, *args, **kwargs):
        # Define the URLs and credentials
        login_url = "https://cards.nis.rs"
        username = "zoran.institutims"
        password = "3RrrvvVg"

        # Set up Chrome options to download files to a specific location
        download_path = r"C:\nis_repo"
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

            # # Interact with the date picker
            # date_input = WebDriverWait(driver, 20).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "input.read-only-normal"))
            # )
            # date_input.click()  # Click to open the date picker

            # # Select the date from the date picker, e.g., September 6, 2024
            # date_to_select = WebDriverWait(driver, 20).until(
            #     EC.element_to_be_clickable((By.XPATH, "//td[@data-value='6' and @class='rdtDay rdtToday']"))
            # )
            # date_to_select.click()  # Click the specific day

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
            import_nis_transactions(csv_file_path)
            print(f"Data imported successfully from {csv_file_path}")

        finally:
            # Close the browser
            driver.quit()
            print("Browser closed")