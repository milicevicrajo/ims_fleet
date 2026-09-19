"""Testovi za ispravke obracuna troskova flote iz 19.09.2026.

Pokriva probleme P-02, P-04, P-06, P-07 i P-09 iz registra problema
(dokumentacija/docs/10-poznati-problemi.md). Svaki test opisuje sta je bilo
pogresno pre ispravke, da se ne bi slucajno vratilo.
"""
import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .models import FuelConsumption, Lease, LeaseInterest, Policy
from .support.dashboard import _best_reading_pair, vehicle_cost_per_km_rows
from .support.fuel import calculate_average_fuel_consumption
from .test_vehicle_onboarding import vehicle


def fueling(car, day, mileage, amount="50", cost="7500"):
    return FuelConsumption.objects.create(
        vehicle=car,
        date=timezone.make_aware(datetime.datetime.combine(day, datetime.time(8, 0))),
        mileage=mileage,
        amount=Decimal(amount),
        cost_bruto=Decimal(cost),
        cost_neto=Decimal(cost),
    )


class AverageFuelConsumptionTests(TestCase):
    """P-02 — obe granice prozora moraju imati upisanu kilometrazu."""

    def setUp(self):
        self.car = vehicle()

    def test_ignores_zero_mileage_on_the_older_boundary(self):
        # Deset tocenja: najstarije ima kilometrazu 0, ostala rastu 1000 po tocenju.
        # Pre ispravke je put racunat kao 129000 - 0, pa je potrosnja ispadala
        # oko 0,35 l/100 km umesto oko 5.
        day = datetime.date(2026, 1, 1)
        mileages = [0, 121000, 122000, 123000, 124000, 125000, 126000, 127000, 128000, 129000]
        for offset, mileage in enumerate(mileages):
            fueling(self.car, day + datetime.timedelta(days=offset), mileage)

        result = calculate_average_fuel_consumption(self.car)

        # Granice su 121000 i 129000 -> 8000 km. Tocenja od najstarijeg sa
        # kilometrazom do najnovijeg ukljucivo: 9 x 50 l = 450 l.
        self.assertAlmostEqual(float(result), 450 / 8000 * 100, places=6)

    def test_returns_none_when_mileage_never_grows(self):
        day = datetime.date(2026, 1, 1)
        for offset in range(10):
            fueling(self.car, day + datetime.timedelta(days=offset), 100000)

        self.assertIsNone(calculate_average_fuel_consumption(self.car))

    def test_returns_none_when_only_one_reading_has_mileage(self):
        day = datetime.date(2026, 1, 1)
        for offset in range(9):
            fueling(self.car, day + datetime.timedelta(days=offset), 0)
        fueling(self.car, day + datetime.timedelta(days=9), 130000)

        self.assertIsNone(calculate_average_fuel_consumption(self.car))


class BestReadingPairTests(TestCase):
    """P-04 — brzi izbor para mora dati isti rezultat kao ranija dvostruka petlja."""

    @staticmethod
    def brute_force(readings, period_start, period_end):
        best_pair, best_score = None, None
        for start in readings:
            for end in readings:
                if (end["date"] - start["date"]).days <= 0:
                    continue
                if end["mileage"] - start["mileage"] <= 0:
                    continue
                score = abs((start["date"] - period_start).days) + abs(
                    (end["date"] - period_end).days
                )
                if best_score is None or score < best_score:
                    best_score, best_pair = score, (start, end)
        return best_pair

    def test_matches_brute_force_on_pseudo_random_readings(self):
        import random

        period_start = datetime.date(2026, 3, 1)
        period_end = datetime.date(2026, 3, 31)
        random_source = random.Random(20260919)

        for case in range(40):
            count = random_source.randint(2, 25)
            readings = []
            for _ in range(count):
                readings.append(
                    {
                        "date": datetime.date(2026, 1, 1)
                        + datetime.timedelta(days=random_source.randint(0, 150)),
                        # Namerno i padovi kilometraze, da se proveri uslov rasta.
                        "mileage": float(random_source.randint(0, 30) * 1000),
                        "source": "Točenje",
                    }
                )
            readings.sort(key=lambda reading: (reading["date"], reading["mileage"]))

            expected = self.brute_force(readings, period_start, period_end)
            actual = _best_reading_pair(readings, period_start, period_end)

            if expected is None:
                self.assertIsNone(actual, msg=f"slucaj {case}")
            else:
                self.assertIsNotNone(actual, msg=f"slucaj {case}")
                expected_start, expected_end = expected
                actual_start, actual_end = actual
                # Isti zbir udaljenosti i isti preracunati put.
                self.assertEqual(
                    abs((expected_start["date"] - period_start).days)
                    + abs((expected_end["date"] - period_end).days),
                    abs((actual_start["date"] - period_start).days)
                    + abs((actual_end["date"] - period_end).days),
                    msg=f"slucaj {case}",
                )
                self.assertEqual(expected_start, actual_start, msg=f"slucaj {case}")
                self.assertEqual(expected_end, actual_end, msg=f"slucaj {case}")

    def test_returns_none_when_mileage_only_falls(self):
        readings = [
            {"date": datetime.date(2026, 1, 1), "mileage": 300.0, "source": "Točenje"},
            {"date": datetime.date(2026, 2, 1), "mileage": 200.0, "source": "Točenje"},
        ]
        self.assertIsNone(
            _best_reading_pair(readings, datetime.date(2026, 1, 1), datetime.date(2026, 2, 1))
        )


class PeriodCostShareTests(TestCase):
    """P-06, P-07 i P-09 — troskovi perioda i vozila bez troska."""

    def setUp(self):
        self.car = vehicle()
        # Dva tocenja daju rast kilometraze, da cena po km uopste postoji.
        fueling(self.car, datetime.date(2026, 3, 1), 100000, amount="10")
        fueling(self.car, datetime.date(2026, 3, 31), 101000, amount="10")

    def row_for(self, start, end):
        rows = vehicle_cost_per_km_rows(start, end, vehicle_ids=self.car.pk)
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_policy_premium_is_split_over_period_days(self):
        # Godisnja polisa od 60.000 za 2026. Pre ispravke je ceo iznos ulazio i
        # u jednomesecni period.
        Policy.objects.create(
            vehicle=self.car,
            invoice_id=1,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 12, 31),
            premium_amount=Decimal("60000"),
        )

        row = self.row_for(datetime.date(2026, 3, 1), datetime.date(2026, 3, 31))

        # 31 dan od 365 dana vazenja polise.
        self.assertAlmostEqual(row["policy_cost"], 60000 * 31 / 365, places=6)
        self.assertLess(row["policy_cost"], 60000)

    def test_whole_policy_enters_a_matching_whole_period(self):
        Policy.objects.create(
            vehicle=self.car,
            invoice_id=2,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 12, 31),
            premium_amount=Decimal("60000"),
        )

        row = self.row_for(datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))

        self.assertAlmostEqual(row["policy_cost"], 60000, places=6)

    def test_financial_lease_interest_is_split_per_calendar_year(self):
        lease = Lease.objects.create(
            vehicle=self.car,
            partner_code="1",
            partner_name="Test",
            job_code="A",
            contract_number="UG-1",
            current_payment_amount=Decimal("1000"),
            lease_type="finansijski",
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2027, 1, 1),
        )
        LeaseInterest.objects.create(lease=lease, year=2025, interest_amount=Decimal("36500"))
        LeaseInterest.objects.create(lease=lease, year=2026, interest_amount=Decimal("36500"))

        # Period dodiruje dve godine: decembar 2025 (31 dan) i januar 2026 (31 dan).
        # Pre ispravke su ulazile dve PUNE godisnje kamate = 73.000.
        row = self.row_for(datetime.date(2025, 12, 1), datetime.date(2026, 1, 31))

        expected = 36500 * 31 / 365 + 36500 * 31 / 365
        self.assertAlmostEqual(row["lease_annual_cost"], expected, places=6)
        self.assertLess(row["lease_annual_cost"], 73000)

    def test_vehicle_without_cost_stays_in_the_list(self):
        # Vozilo ima ocitavanja kilometraze, ali nijedan evidentiran trosak.
        # Pre ispravke je potpuno nestajalo sa spiska, bez objasnjenja.
        empty = vehicle("2")
        fueling(empty, datetime.date(2026, 3, 1), 50000, amount="0", cost="0")
        fueling(empty, datetime.date(2026, 3, 31), 50500, amount="0", cost="0")

        rows = vehicle_cost_per_km_rows(
            datetime.date(2026, 3, 1), datetime.date(2026, 3, 31), vehicle_ids=empty.pk
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["total_cost"], 0)
        self.assertFalse(row["has_cost"])
        self.assertIsNone(row["cost_per_km"])
        self.assertEqual(row["no_cost_note"], "Nema evidentiranog troška u periodu")

    def test_vehicle_with_recovery_above_costs_is_marked(self):
        from .models import Insurance

        refunded = vehicle("3")
        fueling(refunded, datetime.date(2026, 3, 1), 70000, amount="0", cost="1000")
        fueling(refunded, datetime.date(2026, 3, 31), 70500, amount="0", cost="0")
        Insurance.objects.create(
            vehicle=refunded,
            kola=True,
            datum=datetime.date(2026, 3, 15),
            potrazuje=Decimal("5000"),
        )

        rows = vehicle_cost_per_km_rows(
            datetime.date(2026, 3, 1), datetime.date(2026, 3, 31), vehicle_ids=refunded.pk
        )

        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["has_cost"])
        self.assertLess(rows[0]["total_cost"], 0)
        self.assertEqual(
            rows[0]["no_cost_note"],
            "Naknade osiguranja su veće od evidentiranih troškova u periodu",
        )
