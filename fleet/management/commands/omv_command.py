from ...utils import get_latest_download_file, import_omv_fuel_consumption_from_csv, import_omv_transactions_from_csv
import time
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Command(BaseCommand):
    help = 'Downloads a report from OMV website and imports data into the database'

    def handle(self, *args, **kwargs):
        # Define the URLs and credentials
        login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
        username = "710111107258"
        password = "OMV-107258"

        # Set up Chrome options to download files to a specific location
        download_path = r"C:\omv_repo"
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
            date_from_input.send_keys("2024-01-01")
            print("Entered date from")

            # Clear and set the 'date to' input
            date_to_input = driver.find_element(By.NAME, "Transactiondate1")
            date_to_input.clear()
            date_to_input.send_keys("2024-09-14")
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
            # import_omv_transactions_from_csv(csv_file_path)            
            print(f"Data imported successfully from {csv_file_path}")

        finally:
            # Close the browser
            driver.quit()
            print("Browser closed")