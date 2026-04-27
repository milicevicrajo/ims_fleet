import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


CHROME_BINARY_PATH = r"C:\DjangoApps\chrome-for-testing\current\chrome-win64\chrome.exe"
CHROMEDRIVER_PATH = r"C:\DjangoApps\chrome-for-testing\current\chromedriver-win64\chromedriver.exe"


def _validate_chrome_for_testing_paths():
    if not os.path.exists(CHROME_BINARY_PATH):
        raise FileNotFoundError(f"Chrome for Testing nije pronadjen: {CHROME_BINARY_PATH}")
    if not os.path.exists(CHROMEDRIVER_PATH):
        raise FileNotFoundError(f"ChromeDriver nije pronadjen: {CHROMEDRIVER_PATH}")


def create_chrome_options():
    options = webdriver.ChromeOptions()
    options.binary_location = CHROME_BINARY_PATH
    return options


def create_chrome_driver(options=None):
    _validate_chrome_for_testing_paths()
    options = options or create_chrome_options()
    options.binary_location = CHROME_BINARY_PATH
    return webdriver.Chrome(
        service=Service(CHROMEDRIVER_PATH),
        options=options,
    )
