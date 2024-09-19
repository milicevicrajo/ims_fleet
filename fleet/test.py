
from django.test import TestCase
from django.contrib.humanize.templatetags.humanize import intcomma
class IntcommaFunctionTests(TestCase):
    
    def test_intcomma_basic(self):
        """Test a basic large number."""
        self.assertEqual(intcomma(1000), '1,000')
    
    def test_intcomma_large_number(self):
        """Test a very large number."""
        self.assertEqual(intcomma(1234567890), '1,234,567,890')
    
    def test_intcomma_small_number(self):
        """Test a number smaller than 1000 (should not have commas)."""
        self.assertEqual(intcomma(999), '999')
    
    def test_intcomma_negative_number(self):
        """Test a negative number."""
        self.assertEqual(intcomma(-123456), '-123,456')
    
    def test_intcomma_float_number(self):
        """Test a floating-point number."""
        self.assertEqual(intcomma(1234567.89), '1,234,567.89')
    
    def test_intcomma_zero(self):
        """Test the number zero."""
        self.assertEqual(intcomma(0), '0')

# def get_latest_download_file(download_path):

#     # Dobij sve fajlove iz direktorijuma za preuzimanje
#     files = os.listdir(download_path)
    
#     # Pronađi najnoviji fajl na osnovu vremena modifikacije
#     paths = [os.path.join(download_path, basename) for basename in files]
#     latest_file = max(paths, key=os.path.getctime)
    
#     return latest_file

# def format_license_plate(plate):
#     # Uklanjanje svih belina i crtice iz tablice
#     plate = plate.replace(" ", "").replace("-", "").upper()

#     # Proba da preoblikuje tablicu, na primer BG1461DX -> BG1461-DX
#     match = re.match(r'^([A-Z]{2})(\d{3,4})([A-Z]{2})$', plate)
#     if match:
#         return f"{match.group(1)}{match.group(2)}-{match.group(3)}"

#     # Ako nije moguće preoblikovati tablicu, vrati originalnu vrednost (ili baci grešku)
#     return plate  # Ili podigni grešku ako je to potrebno


# def import_omv_fuel_consumption_from_csv(csv_file_path):
#     # Database connection
#     SERVER = "SMS-SERVER"
#     DATABASE = "Vozila"
#     USERNAME = "sa"
#     PWD = "Sms2005"
#     connection_string = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PWD}'
#     conn = pyodbc.connect(connection_string)
#     cursor = conn.cursor()

#     # Read the CSV file
#     with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile, delimiter=';')
#         for row in reader:
#             try:
#                 # Map CSV data to your database fields
#                 sap_sifra = row['SAPsifra']
#                 pan = row['Pan']
#                 kompanijski_kod_kupca = row['KompanijskiKodKupca']
#                 zemlja_sipanja = row['ZemljaSipanja']
#                 benzinska_stanica = row['BenzinskaStanica']
#                 id_transakcije = row['IDtransakcije']
#                 app_kod = row['AppKod']
#                 datum_transakcije = row['DatumTransakcije']
#                 tociono_mesto = row['TocionoMesto']
#                 nosilac_kartice = row['NosilacKartice']
#                 licenca = row['Licenca']
#                 gazdinstvo = row['Gazdinstvo']
#                 reg_br = row['RegBr']
#                 broj_racuna = row['BrojRacuna']
#                 kilometraza = row['Kilometraza']
#                 sipano_van_rezervoara = row['SipanoVanRezervoara']
#                 naziv_proizvoda = row['NazivProizvoda']
#                 kol = row['Kol']
#                 kol_kg = row['KolKG']
#                 popust = row['Popust']
#                 primenjen_popust = row['PrimenjenPopust']
#                 cena_sa_kase = row['CenaSaKase']
#                 cena = row['Cena']
#                 total_sa_kase = row['TotalSaKase']
#                 total = row['Total']
#                 valuta = row['Valuta']

#                 # Prepare the SQL INSERT statement
#                 sql = """
#                 INSERT INTO YourTableName (
#                     SAPsifra, Pan, KompanijskiKodKupca, ZemljaSipanja, BenzinskaStanica,
#                     IDtransakcije, AppKod, DatumTransakcije, TocionoMesto, NosilacKartice,
#                     Licenca, Gazdinstvo, RegBr, BrojRacuna, Kilometraza,
#                     SipanoVanRezervoara, NazivProizvoda, Kol, KolKG, Popust,
#                     PrimenjenPopust, CenaSaKase, Cena, TotalSaKase, Total, Valuta
#                 )
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """
#                 cursor.execute(sql, (
#                     sap_sifra, pan, kompanijski_kod_kupca, zemlja_sipanja, benzinska_stanica,
#                     id_transakcije, app_kod, datum_transakcije, tociono_mesto, nosilac_kartice,
#                     licenca, gazdinstvo, reg_br, broj_racuna, kilometraza,
#                     sipano_van_rezervoara, naziv_proizvoda, kol, kol_kg, popust,
#                     primenjen_popust, cena_sa_kase, cena, total_sa_kase, total, valuta
#                 ))
#                 conn.commit()

#                 print(f"Successfully imported transaction for vehicle {reg_br}")

#             except Exception as e:
#                 print(f"Error importing row: {row}. Error: {str(e)}")

#     # Close the connection
#     cursor.close()
#     conn.close()

# def handle():
#     # Define the URLs and credentials
#     login_url = "https://fleet.omv.com/FleetServicesProduction/Login.jsp"
#     username = "710111107258"
#     password = "OMV-107258"

#     # Set up Chrome options to download files to a specific location
#     download_path = r"C:\Users\rajo.milicevic\Downloads"
#     chrome_options = webdriver.ChromeOptions()
#     prefs = {"download.default_directory": download_path}
#     chrome_options.add_experimental_option("prefs", prefs)

#     # Initialize WebDriver
#     driver = webdriver.Chrome(options=chrome_options)

#     try:
#         # Open the login page
#         driver.get(login_url)
#         print("Opened login page")

#         # Enter username
#         username_input = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.ID, "username"))
#         )
#         username_input.send_keys(username)
#         print("Entered username")

#         # Enter password
#         password_input = driver.find_element(By.NAME, "password")
#         password_input.send_keys(password)
#         print("Entered password")

#         # Select language
#         language_select = driver.find_element(By.NAME, "language")
#         for option in language_select.find_elements(By.TAG_NAME, 'option'):
#             if option.text == 'English':
#                 option.click()
#                 break
#         print("Selected language")

#         # Click the login button
#         login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
#         login_button.click()
#         print("Clicked login button")

#         # Wait for some time to ensure the page loads completely
#         time.sleep(1)

#         # Switch to the header frame to find the 'Transaction information' link
#         driver.switch_to.default_content()
#         WebDriverWait(driver, 20).until(
#             EC.frame_to_be_available_and_switch_to_it((By.NAME, "header"))
#         )
#         print("Switched to header frame")

#         # Click on 'Transaction information'
#         transaction_information_link = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, "//a[@href='header.do?selectModule=transactioninformation']"))
#         )
#         transaction_information_link.click()
#         print("Clicked on 'Transaction information'")

#         # Switch back to default content
#         driver.switch_to.default_content()

#         # Switch to the functionnavigation frame to proceed
#         WebDriverWait(driver, 20).until(
#             EC.frame_to_be_available_and_switch_to_it((By.NAME, "functionnavigation"))
#         )
#         print("Switched to functionnavigation")

#         # Click on 'Reports'
#         reports_link = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, "//a[@href='functionNavigation.do?openFunction=transactioninformation.report.overview']"))
#         )
#         reports_link.click()
#         print("Clicked on 'Reports'")

#         # Click on 'Transactions'
#         transactions_link = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, "//a[@href='genSearchCriteria.do?activateFunction=transactioninformation.report.transaction&openFunction=transactioninformation.report.overview']"))
#         )
#         transactions_link.click()
#         print("Clicked on 'Transactions'")

#         # Switch back to default content
#         driver.switch_to.default_content()

#         # Switch to the searchcriteria frame
#         WebDriverWait(driver, 20).until(
#             EC.frame_to_be_available_and_switch_to_it((By.NAME, "searchcriteria"))
#         )
#         print("Switched to searchcriteria frame")

#         # Wait for the date inputs to be present
#         date_from_input = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.NAME, "Transactiondatefrom"))
#         )
#         print("Date from input found")

#         # Clear and set the 'date from' input
#         date_from_input.clear()
#         date_from_input.send_keys("2024-05-11")
#         print("Entered date from")

#         # Clear and set the 'date to' input
#         date_to_input = driver.find_element(By.NAME, "Transactiondate1")
#         date_to_input.clear()
#         date_to_input.send_keys("2024-07-11")
#         print("Entered date to")

#         # Click the 'Result' link using JavaScript
#         driver.execute_script("goContent()")
#         print("Clicked 'Result' link")

#         # Switch back to default content
#         driver.switch_to.default_content()
        
#         # Switch to the content frame
#         WebDriverWait(driver, 20).until(
#             EC.frame_to_be_available_and_switch_to_it((By.NAME, "content"))
#         )

#         # Wait for the download link to appear
#         download_link = WebDriverWait(driver, 30).until(
#             EC.presence_of_element_located((By.XPATH, "//a[@href=\"javascript:openURL_Loading('browseTransactionList.do?event=CsvFileRequest');\"]"))
#         )
#         print("Download link found")

#         # Click the download link
#         download_link.click()
#         print("Clicked download link")
#         time.sleep(5)  # Očekuj da se preuzimanje završi

#         print("Report downloaded successfully")

#         # Pronađi najnovije preuzeti fajl
#         csv_file_path = get_latest_download_file(download_path)

#         # Importuj podatke u bazu
#         import_omv_fuel_consumption_from_csv(csv_file_path)
#         print(f"Data imported successfully from {csv_file_path}")

#     finally:
#         # Close the browser
#         driver.quit()
#         print("Browser closed")

# handle()