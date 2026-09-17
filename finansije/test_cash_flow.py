from datetime import date
from decimal import Decimal as D

from django.db import DataError
from django.test import SimpleTestCase

from .services.cash_flow import calculate, unique_map, vat_period


DAY = date(2026, 8, 1)
END = date(2026, 8, 31)


def posting(account, debit="0", credit="0", kind="BANK", day=DAY):
    return dict(account=account, debit=D(debit), credit=D(credit), kind=kind, date=day)


class CashFlowCalculationTests(SimpleTestCase):
    def calculate(self, rows, accounts=None, wages=None, vat="0", active=None, end=END):
        return calculate(rows, accounts if accounts is not None else {r["account"]: "" for r in rows} | {"47900": ""},
                         {"BANK": "NT", "ON": "ON", "IF": "IF"}, wages or set(), D(vat),
                         {8} if active is None else active, end)

    def test_inflow_outflow_net_and_bank_account_exclusion(self):
        result = self.calculate([posting("20400", credit="1000"), posting("43500", debit="300"),
                                 posting("24100", debit="1000", credit="300"), posting("20400", credit="999", kind="IF")])
        self.assertEqual((result["inflow"], result["outflow"], result["net"]), (D("1000"), D("300"), D("700")))

    def test_account_nt_null_and_missing_journal_mappings_are_excluded(self):
        rows = [posting("20400", credit="100"), posting("20500", credit="200"), posting("20600", credit="300"),
                posting("20700", credit="400", kind="UNKNOWN")]
        result = self.calculate(rows, accounts={"20400": "NT", "20500": None, "20700": ""})
        self.assertEqual(result["net"], D("0"))

    def test_special_on_postings_are_included_and_other_on_accounts_are_not(self):
        result = self.calculate([posting("61420", credit="150", kind="ON"), posting("53011", debit="40", kind="ON"),
                                 posting("61000", credit="5000", kind="ON")])
        self.assertEqual((result["inflow"], result["outflow"]), (D("150"), D("40")))

    def test_vat_replaces_ledger_vat_and_negative_corrections_keep_sign(self):
        result = self.calculate([posting("47900", debit="900")], vat="-30")
        self.assertEqual(result["outflow"], D("-30"))
        self.assertEqual(result["net"], D("30"))

    def test_contract_payroll_and_refund_replacements(self):
        rows = [posting("46520", debit="999"), posting("52400", debit="100", credit="20", kind="ON"),
                posting("45000", debit="999"), posting("52000", debit="200", credit="50", kind="ON"),
                posting("22500", debit="10", credit="30"), posting("45400", debit="999")]
        result = self.calculate(rows, wages={"52000"})
        self.assertEqual((result["inflow"], result["outflow"], result["net"]), (D("20"), D("300"), D("-280")))

    def test_each_contract_account_has_its_own_replacement(self):
        rows = [posting("46520", debit="999"), posting("46510", debit="999"), posting("46500", debit="999"), posting("46400", debit="999")]
        rows += [posting(code, debit="25", kind="ON") for code in ("52400", "52300", "52200", "52600")]
        self.assertEqual(self.calculate(rows)["outflow"], D("100"))

    def test_inactive_months_and_missing_evidence_are_not_mislabeled_as_zero(self):
        self.assertFalse(self.calculate([], active=set())["available"])
        result = self.calculate([posting("20400", credit="100"), posting("20400", credit="500", day=date(2026, 9, 1))],
                                vat="900", active={8}, end=date(2026, 12, 31))
        self.assertEqual((result["inflow"], result["outflow"]), (D("100"), D("0")))

    def test_vat_month_shift_and_duplicate_metadata_guard(self):
        self.assertEqual(vat_period(1, 1), (-1, -1, 12))
        self.assertEqual(vat_period(1, 12), (-1, 11, 12))
        self.assertEqual(vat_period(8, 8), (7, 7, -1))
        self.assertEqual(vat_period(None, None), (-1, -1, -1))
        with self.assertRaises(DataError):
            unique_map([("20400 ", "NT"), ("20400", "NT")])
