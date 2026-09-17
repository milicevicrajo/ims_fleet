from datetime import date
from decimal import Decimal as D
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.shared_costs import allocate


def rule(code, month=1, criterion="", coefficients=(D("25"), D("0"), D("0")), profit="P"):
    return dict(code=code, month=month, criterion=criterion, coefficients=coefficients, profit=profit)


class SharedAllocationTests(SimpleTestCase):
    def test_cost_sign_two_stage_allocation_and_revenue_offsets(self):
        rules = [rule("pool", criterion="1"), rule("job")]
        balances = [dict(job_code="pool", month=1, revenue=D("20"), expense=D("120")),
                    dict(job_code="unrelated", month=1, revenue=D("0"), expense=D("10000"))]
        result = allocate(rules, (D("40"), D("0"), D("0")), balances, "job", 1)
        self.assertEqual(result["cost"], D("10.00"))
        self.assertTrue(result["complete"])
        balances[0]["revenue"] = D("220")
        self.assertEqual(allocate(rules, (D("40"), D("0"), D("0")), balances, "job", 1)["cost"], D("-10.00"))

    def test_annual_coefficient_matches_procedure_period_average_and_marks_gaps(self):
        rules = [rule("pool", criterion="1"), rule("job", coefficients=(D("20"), D("0"), D("0"))),
                 rule("job", month=2, coefficients=(D("40"), D("0"), D("0")))]
        balances = [dict(job_code="pool", month=1, revenue=D("0"), expense=D("1200"))]
        result = allocate(rules, (D("100"), D("0"), D("0")), balances, "job", 12)
        self.assertEqual(result["cost"], D("60.00"))
        self.assertFalse(result["complete"])
        self.assertIn("2 od 12", result["note"])

    def test_three_criteria_and_missing_or_duplicate_rules(self):
        rules = [rule("p1", criterion="1"), rule("p2", criterion="2"), rule("p3", criterion="3"),
                 rule("job", coefficients=(D("100"), D("50"), D("25")))]
        balances = [dict(job_code=f"p{i}", month=1, revenue=D("0"), expense=D("100")) for i in range(1, 4)]
        self.assertEqual(allocate(rules, (D("100"),)*3, balances, "job", 1)["cost"], D("175.00"))
        self.assertFalse(allocate(rules, None, balances, "job", 1)["available"])
        self.assertFalse(allocate(rules, (D("100"),)*3, balances, "missing", 1)["available"])
        self.assertFalse(allocate(rules + [rules[0]], (D("100"),)*3, balances, "job", 1)["available"])
