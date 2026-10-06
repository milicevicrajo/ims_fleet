"""Testovi za ispravke obracuna troskova flote iz 19.09.2026.

Pokriva probleme P-02, P-04, P-06, P-07 i P-09 iz registra problema
(dokumentacija/docs/10-poznati-problemi.md). Svaki test opisuje sta je bilo
pogresno pre ispravke, da se ne bi slucajno vratilo.
"""
import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .models import FuelConsumption
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
