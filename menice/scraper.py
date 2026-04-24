from __future__ import annotations

import argparse
import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urljoin

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://webappcenter.nbs.rs/PnWebApp"
SEARCH_PATH = "/BondMandate/Bond"
AVALIST_PATH = "/BondMandate/Bond/Details_Children_BondAvalist"

DEFAULT_HEADERS = {
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
		"AppleWebKit/537.36 (KHTML, like Gecko) "
		"Chrome/134.0.0.0 Safari/537.36"
	),
	"Accept-Language": "sr-Latn-RS,sr;q=0.9,en;q=0.8",
}

META_COLUMNS = [
	"Naziv duznika",
	"Maticni broj duznika",
	"Poreski broj duznika",
	"Strana rezultata",
	"Izvor URL",
]

BOND_COLUMNS = [
	"Serijski broj menice",
	"Datum izdavanja",
	"Iznos menice",
	"Valuta menice",
	"Datum dospeca",
	"Izdavalac menice",
	"Vrsta menice",
	"Redni broj",
	"Osnov izdavanja",
	"Iznos iz osnova",
	"Valuta osnova",
	"Datum registracije",
	"Naziv banke",
	"Status",
]

AVALIST_COLUMNS = ["Avalisti detalji", "Avalisti broj zapisa"]

NBS_COLUMN_ALIASES = {
	"Назив дужника": "Naziv duznika",
	"Naziv dužnika": "Naziv duznika",
	"Naziv duznika": "Naziv duznika",
	"Матични број дужника": "Maticni broj duznika",
	"Matični broj dužnika": "Maticni broj duznika",
	"Maticni broj duznika": "Maticni broj duznika",
	"Порески број дужника": "Poreski broj duznika",
	"Poreski broj dužnika": "Poreski broj duznika",
	"Poreski broj duznika": "Poreski broj duznika",
	"Страна резултата": "Strana rezultata",
	"Strana rezultata": "Strana rezultata",
	"Серијски број менице": "Serijski broj menice",
	"Serijski broj menice": "Serijski broj menice",
	"Датум издавања": "Datum izdavanja",
	"Datum izdavanja": "Datum izdavanja",
	"Износ менице": "Iznos menice",
	"Iznos menice": "Iznos menice",
	"Валута менице": "Valuta menice",
	"Valuta menice": "Valuta menice",
	"Датум доспећа": "Datum dospeca",
	"Datum dospeća": "Datum dospeca",
	"Datum dospeca": "Datum dospeca",
	"Издавалац менице": "Izdavalac menice",
	"Izdavalac menice": "Izdavalac menice",
	"Врста менице": "Vrsta menice",
	"Vrsta menice": "Vrsta menice",
	"Редни број": "Redni broj",
	"Redni broj": "Redni broj",
	"Основ издавања": "Osnov izdavanja",
	"Osnov izdavanja": "Osnov izdavanja",
	"Износ из основа": "Iznos iz osnova",
	"Iznos iz osnova": "Iznos iz osnova",
	"Валута основа": "Valuta osnova",
	"Valuta osnova": "Valuta osnova",
	"Датум регистрације": "Datum registracije",
	"Datum registracije": "Datum registracije",
	"Назив банке": "Naziv banke",
	"Naziv banke": "Naziv banke",
	"Статус": "Status",
	"Status": "Status",
	"Авалисти": "Avalisti",
	"Avalisti": "Avalisti",
}


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Scrape NBS registry bonds and export them to CSV or XLSX."
	)
	parser.add_argument("--tax-code", default="100223617", help="Debtor tax code.")
	parser.add_argument("--national-code", default="", help="Debtor national code.")
	parser.add_argument("--serial-number", default="", help="Bond serial number filter.")
	parser.add_argument(
		"--registration-date",
		default="",
		help="Registration date filter exactly as expected by the site.",
	)
	parser.add_argument(
		"--page-size",
		type=int,
		default=100,
		help="Number of results requested per page.",
	)
	parser.add_argument(
		"--output",
		default="menice_100223617.csv",
		help="Output file path. Use .csv or .xlsx extension.",
	)
	parser.add_argument(
		"--skip-avalists",
		action="store_false",
		dest="include_avalists",
		help="Do not load avalist details from the child endpoint.",
	)
	parser.set_defaults(include_avalists=True)
	parser.add_argument(
		"--max-pages",
		type=int,
		default=None,
		help="Optional limit for the number of pages to scrape.",
	)
	parser.add_argument(
		"--timeout",
		type=int,
		default=30,
		help="HTTP timeout per request in seconds.",
	)
	return parser.parse_args()


def build_session() -> requests.Session:
	session = requests.Session()
	session.headers.update(DEFAULT_HEADERS)
	retry = Retry(
		total=3,
		backoff_factor=1,
		status_forcelist=(429, 500, 502, 503, 504),
		allowed_methods=("GET",),
	)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount("https://", adapter)
	session.mount("http://", adapter)
	return session


def set_latin_language(session: requests.Session, timeout: int) -> None:
	response = session.get(f"{BASE_URL}/", timeout=timeout)
	response.raise_for_status()
	if not response.encoding:
		response.encoding = response.apparent_encoding or "utf-8"

	soup = BeautifulSoup(response.text, "html.parser")
	form = soup.find("form", action=lambda value: value and "CultureInfo/SetLanguage" in value)
	if form is None:
		return

	token = form.find("input", attrs={"name": "__RequestVerificationToken"})
	data = {"language": "sr-Latn"}
	if token is not None and token.get("value"):
		data["__RequestVerificationToken"] = token["value"]

	action = urljoin(BASE_URL, form.get("action", "/PnWebApp/CultureInfo/SetLanguage"))
	session.post(action, data=data, timeout=timeout).raise_for_status()


def clean_text(value: str | None) -> str:
	if not value:
		return ""
	return " ".join(value.replace("\xa0", " ").split())


def normalize_column_name(value: str) -> str:
	return NBS_COLUMN_ALIASES.get(clean_text(value), clean_text(value))


def fetch_search_page(
	session: requests.Session, params: dict[str, Any], timeout: int
) -> requests.Response:
	response = session.get(
		f"{BASE_URL}{SEARCH_PATH}",
		params=params,
		timeout=timeout,
	)
	response.raise_for_status()
	if not response.encoding:
		response.encoding = response.apparent_encoding or "utf-8"
	return response


def fetch_avalists(
	session: requests.Session, operation_query: str, timeout: int
) -> tuple[str, int]:
	if not operation_query:
		return "", 0

	response = session.get(
		f"{BASE_URL}{AVALIST_PATH}",
		params=dict(parse_qsl(operation_query, keep_blank_values=True)),
		timeout=timeout,
	)
	response.raise_for_status()
	if not response.encoding:
		response.encoding = response.apparent_encoding or "utf-8"

	soup = BeautifulSoup(response.text, "html.parser")
	plain_text = clean_text(soup.get_text(" ", strip=True))
	if not plain_text or "Нема података" in plain_text or "Nema podataka" in plain_text:
		return "", 0

	entries: list[str] = []
	for table in soup.find_all("table"):
		row_values: list[list[str]] = []
		for row in table.find_all("tr"):
			cells = [
				clean_text(cell.get_text(" ", strip=True))
				for cell in row.find_all(["th", "td"])
			]
			cells = [cell for cell in cells if cell]
			if cells:
				row_values.append(cells)

		if not row_values:
			continue

		if all(len(row) == 2 for row in row_values):
			entries.append("; ".join(f"{key}: {value}" for key, value in row_values))
			continue

		for row in row_values:
			entries.append(" | ".join(row))

	if not entries:
		entries.append(plain_text)

	return " || ".join(entries), len(entries)


def extract_total_pages(soup: BeautifulSoup) -> int:
	paging_panel = soup.find("div", id="myIndexOutput")
	if paging_panel is None:
		return 1
	raw_total = paging_panel.get("my-total-page", "1")
	try:
		return max(1, int(raw_total))
	except ValueError:
		return 1


def extract_debtor_info(soup: BeautifulSoup) -> dict[str, str]:
	for table in soup.find_all("table", class_="table"):
		headers = [clean_text(th.get_text(" ", strip=True)) for th in table.find_all("th")]
		rows = table.find_all("tr")
		if len(headers) == 3 and len(rows) >= 2:
			cells = [clean_text(td.get_text(" ", strip=True)) for td in rows[1].find_all("td")]
			if len(cells) == 3:
				return {
					"Naziv duznika": cells[0],
					"Maticni broj duznika": cells[1],
					"Poreski broj duznika": cells[2],
				}
	return {
		"Naziv duznika": "",
		"Maticni broj duznika": "",
		"Poreski broj duznika": "",
	}


def parse_bond_panels(soup: BeautifulSoup) -> list[dict[str, str]]:
	records: list[dict[str, str]] = []

	for panel in soup.find_all("div", class_="myColapsiblePanel"):
		table = panel.find("table", class_="table")
		if table is None:
			continue

		record: dict[str, str] = {}
		operation_query = ""
		for row in table.find_all("tr"):
			cells = row.find_all("td")
			if len(cells) < 2:
				continue

			key = normalize_column_name(cells[0].get_text(" ", strip=True))
			if not key:
				continue

			button = cells[1].find("button", attrs={"my-button-type": "ContentPartialLoad"})
			if button is not None:
				operation_query = clean_text(button.get("my-operationQuery", ""))

			value = clean_text(cells[1].get_text(" ", strip=True))
			record[key] = value

		if "Serijski broj menice" not in record:
			continue

		record["_operation_query"] = operation_query
		records.append(record)

	return records


def build_search_params(args: argparse.Namespace, page: int) -> dict[str, str]:
	return {
		"isSearchExecuted": "true",
		"DebtorNationalCode": args.national_code,
		"DebtorTaxCode": args.tax_code,
		"BondSerialNumber": args.serial_number,
		"RegistrationDate": args.registration_date,
		"PageSize": str(args.page_size),
		"OrderBy": "",
		"Pagging.CurrentPage": str(page),
		"Pagging.PageSize": str(args.page_size),
	}


def collect_extra_columns(records: Iterable[dict[str, str]]) -> list[str]:
	seen = set(META_COLUMNS + BOND_COLUMNS + AVALIST_COLUMNS + ["_operation_query", "Avalisti", "Авалисти"])
	extras: list[str] = []
	for record in records:
		for key in record:
			if key in seen:
				continue
			seen.add(key)
			extras.append(key)
	return extras


def export_csv(output_path: Path, records: list[dict[str, str]], columns: list[str]) -> None:
	with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=columns)
		writer.writeheader()
		writer.writerows(records)


def export_xlsx(output_path: Path, records: list[dict[str, str]], columns: list[str]) -> None:
	workbook = Workbook()
	worksheet = workbook.active
	worksheet.title = "Menice"
	worksheet.append(columns)

	for record in records:
		worksheet.append([record.get(column, "") for column in columns])

	for column_cells in worksheet.columns:
		values = [str(cell.value) if cell.value is not None else "" for cell in column_cells]
		max_length = max((len(value) for value in values), default=0)
		worksheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 60)

	workbook.save(output_path)


def export_records(output_path: Path, records: list[dict[str, str]], columns: list[str]) -> None:
	if output_path.suffix.lower() == ".xlsx":
		export_xlsx(output_path, records, columns)
		return
	export_csv(output_path, records, columns)


def scrape(args: argparse.Namespace) -> list[dict[str, str]]:
	session = build_session()
	set_latin_language(session, args.timeout)
	first_response = fetch_search_page(session, build_search_params(args, 1), args.timeout)
	first_soup = BeautifulSoup(first_response.text, "html.parser")

	debtor_info = extract_debtor_info(first_soup)
	total_pages = extract_total_pages(first_soup)
	if args.max_pages is not None:
		total_pages = min(total_pages, args.max_pages)

	all_records: list[dict[str, str]] = []

	for page in range(1, total_pages + 1):
		response = first_response if page == 1 else fetch_search_page(
			session,
			build_search_params(args, page),
			args.timeout,
		)
		soup = first_soup if page == 1 else BeautifulSoup(response.text, "html.parser")
		page_records = parse_bond_panels(soup)

		for record in page_records:
			flattened = {
				**debtor_info,
				"Strana rezultata": str(page),
				"Izvor URL": response.url,
			}

			for column in BOND_COLUMNS:
				flattened[column] = record.get(column, "")

			if args.include_avalists:
				avalist_details, avalist_count = fetch_avalists(
					session,
					record.get("_operation_query", ""),
					args.timeout,
				)
				flattened["Avalisti detalji"] = avalist_details
				flattened["Avalisti broj zapisa"] = str(avalist_count)
			else:
				flattened["Avalisti detalji"] = ""
				flattened["Avalisti broj zapisa"] = ""

			for key, value in record.items():
				normalized_key = normalize_column_name(key)
				if normalized_key.startswith("_") or normalized_key in BOND_COLUMNS or normalized_key == "Avalisti":
					continue
				flattened[normalized_key] = value

			all_records.append(flattened)

	if not all_records:
		raise RuntimeError("Nijedna menica nije pronadjena za zadate kriterijume.")

	return all_records


def main() -> None:
	args = parse_args()
	output_path = Path(args.output).resolve()
	records = scrape(args)
	columns = META_COLUMNS + BOND_COLUMNS + AVALIST_COLUMNS + collect_extra_columns(records)
	export_records(output_path, records, columns)
	print(f"Sacuvano {len(records)} menica u: {output_path}")


if __name__ == "__main__":
	main()
