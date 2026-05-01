from io import BytesIO

from django.test import SimpleTestCase
from openpyxl import load_workbook

from .exporting import (
    csv_attachment_response,
    dataframe_xlsx_response,
    rows_to_xlsx_response,
    xlsx_attachment_response,
)


class ExportingTests(SimpleTestCase):
    def test_csv_attachment_response_sets_download_headers(self):
        response = csv_attachment_response("vozila.csv")

        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="vozila.csv"')

    def test_xlsx_attachment_response_sets_download_headers(self):
        response = xlsx_attachment_response("report.xlsx")

        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(response["Content-Disposition"], "attachment; filename=report.xlsx")

    def test_rows_to_xlsx_response_creates_valid_workbook(self):
        response = rows_to_xlsx_response(
            "report.xlsx",
            "Report",
            ["Name", "Value"],
            [["Alpha", 12]],
            bold_header=True,
            auto_width=True,
        )

        workbook = load_workbook(BytesIO(response.content))
        worksheet = workbook.active

        self.assertEqual(worksheet.title, "Report")
        self.assertEqual(worksheet["A1"].value, "Name")
        self.assertTrue(worksheet["A1"].font.bold)
        self.assertEqual(worksheet["A2"].value, "Alpha")
        self.assertEqual(worksheet["B2"].value, 12)

    def test_dataframe_xlsx_response_creates_valid_workbook(self):
        response = dataframe_xlsx_response(
            [{"Name": "Alpha", "Value": 12}],
            "data.xlsx",
            "Data",
        )

        workbook = load_workbook(BytesIO(response.content))
        worksheet = workbook.active

        self.assertEqual(worksheet.title, "Data")
        self.assertEqual(worksheet["A1"].value, "Name")
        self.assertEqual(worksheet["A2"].value, "Alpha")
        self.assertEqual(worksheet["B2"].value, 12)
