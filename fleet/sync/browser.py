import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


BASE_DIR = Path(__file__).resolve().parents[2]
CHROME_FOR_TESTING_DIR = BASE_DIR / "chrome-for-testing" / "current"
CHROME_BINARY_PATH = os.getenv(
    "CHROME_BINARY_PATH",
    str(CHROME_FOR_TESTING_DIR / "chrome-win64" / "chrome.exe"),
)
CHROMEDRIVER_PATH = os.getenv(
    "CHROMEDRIVER_PATH",
    str(CHROME_FOR_TESTING_DIR / "chromedriver-win64" / "chromedriver.exe"),
)


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
