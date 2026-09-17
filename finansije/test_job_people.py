from datetime import date
from unittest.mock import patch

from django.db import connection
from django.test import TestCase

from .services.job_people import payroll_employees


class PayrollEvidenceTests(TestCase):
    """Run the read-only selection against small source-shaped fixture tables."""

    def setUp(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE TEMP TABLE Zarada (sif_pred int, god text, mesec int, br_obr int, rasif int, sif_pos text, dinara decimal, rekol decimal)")
            cursor.execute("CREATE TEMP TABLE PomLD (sif_pred int, god text, mesec int, br_obr int, status_obr text)")
            cursor.execute("CREATE TEMP TABLE Radnik (sif_pred int, rasif int, ranaz text)")
            cursor.executemany("INSERT INTO PomLD VALUES (%s,%s,%s,%s,%s)", [
                (1, "2026", 2, 1, "Z"), (1, "2026", 2, 2, "Z"), (1, "2026", 2, 3, "O"),
                (1, "2026", 3, 1, "Z"), (2, "2026", 2, 1, "Z"), (1, "2025", 2, 1, "Z"),
            ])
            cursor.executemany("INSERT INTO Radnik VALUES (%s,%s,%s)", [(1, 10, "Person A"), (2, 10, "Other company")])
            cursor.executemany("INSERT INTO Zarada VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", [
                (1, "2026", 2, 1, 10, "410001", 100, 8),
                (1, "2026", 2, 1, 10, "410001", 20, 0),
                (1, "2026", 2, 2, 10, "410001", -5, 0),
                (1, "2026", 2, 3, 20, "410001", 100, 8),  # open
                (1, "2026", 2, 4, 21, "410001", 100, 8),  # no header
                (1, "2026", 2, 1, 22, "410001", 0, 0),
                (1, "2026", 2, 1, 23, "420001", 100, 8),
                (1, "2026", 3, 1, 10, "410001", 100, 8),
                (2, "2026", 2, 1, 10, "410001", 100, 8),
                (1, "2025", 2, 1, 10, "410001", 100, 8),
                (1, "2026", 2, 1, 24, "410001", None, 4),  # missing directory, hours only
            ])
        self.source = patch("finansije.services.job_people.PAYROLL", "temp")
        self.connections = patch("finansije.services.job_people.connections", {"server_db": connection})
        self.source.start()
        self.connections.start()
        self.addCleanup(self.source.stop)
        self.addCleanup(self.connections.stop)

    def tearDown(self):
        with connection.cursor() as cursor:
            for table in ("Zarada", "PomLD", "Radnik"):
                cursor.execute(f"DROP TABLE temp.{table}")

    def test_month_excludes_open_zero_other_job_company_year_and_deduplicates_elements(self):
        data = payroll_employees(1, "410001", date(2026, 2, 1), date(2026, 2, 28))
        self.assertEqual(data["rows"],
                         [(2, 10, "Person A", 2), (2, 24, None, 1)])
        self.assertEqual(data["closed_months"], [2])
        self.assertEqual(data["open_months"], [2])

    def test_year_retains_separate_months_and_parameterizes_job(self):
        rows = payroll_employees(1, "410001", date(2026, 1, 1), date(2026, 12, 31))["rows"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[-1], (3, 10, "Person A", 1))
        self.assertEqual(payroll_employees(1, "' OR 1=1--", date(2026, 1, 1), date(2026, 12, 31))["rows"], [])
