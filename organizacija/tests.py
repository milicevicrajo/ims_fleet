"""Testovi centralnog registra organizacije.

Slucajevi su uzeti iz stvarnih podataka izmerenih 21.09.2026.
(`dokumentacija/popis-sifara-posla-korak-0.md`), da test brani bas ono sto je izmereno,
a ne izmisljeni primer.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import OrganizationalUnit, PermissionCode, Role, RolePermission
from finansije.models import FinanceJob, LedgerEntry
from organizacija.models import (
    ExternalOrgMapping,
    LegacyOrgLink,
    OrgNode,
    OrgNodeVersion,
    UnresolvedOrgCode,
)
from organizacija.services import classification as klas
from organizacija.services.importer import collect_known_units, run_import
from organizacija.services.report import build_report, ledger_reconciliation, structural_checks

# Jedinice i nazivi tacno kako stoje u knjizenjima produkcije.
UNITS = {
    "1": "IMS",
    "11": "Telo za tehnicko ocenjivanje",
    "20": "POSLOVNI BLOK",
    "30": "Naucno istrazivacki blok",
    "41": "Centar za materijale",
    "43": "Centar za puteve i geotehniku",
}


class ClassificationTests(TestCase):
    """Razvrstavanje je cista funkcija, pa se proverava bez baze."""

    def test_business_code_splits_into_three_segments(self):
        result = klas.classify("430111", set(UNITS), name="Strucni nadzor")
        self.assertEqual(result.family, klas.FAMILY_BUSINESS)
        self.assertEqual(result.segments, ("43", "0", "111"))

    def test_center_field_is_not_used_because_source_truncates_it(self):
        """`209001` u izvoru ima center='2'; tacan centar je 20 i cita se iz sifre."""
        result = klas.classify("209001", set(UNITS), name="Organizacija i poslovanje")
        self.assertEqual(result.family, klas.FAMILY_BUSINESS)
        self.assertEqual(result.center, "20")

    def test_code_with_empty_center_in_source_still_resolves(self):
        """`110002` i `430001` imaju prazan center u izvoru."""
        for code, center in (("110002", "11"), ("430001", "43")):
            result = klas.classify(code, set(UNITS), name="Nesto")
            self.assertEqual(result.family, klas.FAMILY_BUSINESS, code)
            self.assertEqual(result.center, center, code)

    def test_science_root_is_not_read_as_center(self):
        """`315400` je osoba (Delic Ivana), a ne centar 31."""
        result = klas.classify("315400", set(UNITS), name="Delic Ivana")
        self.assertEqual(result.family, klas.FAMILY_SCIENCE)
        self.assertIsNone(result.segments)

    def test_science_project_code_is_science(self):
        result = klas.classify("3154190170", set(UNITS), name="P190170-Delic I.")
        self.assertEqual(result.family, klas.FAMILY_SCIENCE)

    def test_science_code_ending_with_letter_is_science_not_exception(self):
        result = klas.classify("320519206A", set(UNITS), name="P19206A-Milicic Ljiljana")
        self.assertEqual(result.family, klas.FAMILY_SCIENCE)

    def test_job_of_unit_thirty_stays_in_the_tree(self):
        """`300001` je posao same jedinice 30, ne naucna sifra."""
        result = klas.classify("300001", set(UNITS), name="Troskovi amortizacije")
        self.assertEqual(result.family, klas.FAMILY_BUSINESS)
        self.assertEqual(result.segments, ("30", "0", "001"))

    def test_text_codes_are_exceptions(self):
        for code in ("vranj", "vranjs"):
            result = klas.classify(code, set(UNITS), name="Nesto")
            self.assertEqual(result.family, klas.FAMILY_EXCEPTION, code)
            self.assertTrue(result.needs_review)

    def test_short_code_is_exception(self):
        result = klas.classify("432", set(UNITS), name="Uvodjenje grejanja")
        self.assertEqual(result.family, klas.FAMILY_EXCEPTION)

    def test_code_without_name_is_not_added_silently(self):
        """`111111` strukturno lici na 11/1/111, ali nema naziv — ide na proveru."""
        result = klas.classify("111111", set(UNITS), name="")
        self.assertEqual(result.family, klas.FAMILY_EXCEPTION)
        self.assertEqual(result.reason, klas.REASON_NO_NAME)

    def test_unknown_center_is_exception(self):
        result = klas.classify("960001", set(UNITS), name="Test centar")
        self.assertEqual(result.family, klas.FAMILY_EXCEPTION)
        self.assertEqual(result.reason, klas.REASON_UNKNOWN_CENTER)

    def test_trailing_spaces_do_not_change_the_result(self):
        with_spaces = klas.classify("430111    ", set(UNITS), name="Strucni nadzor")
        without = klas.classify("430111", set(UNITS), name="Strucni nadzor")
        self.assertEqual(with_spaces.segments, without.segments)

    def test_leading_zero_is_preserved(self):
        result = klas.classify("430001", set(UNITS), name="Amortizacija")
        self.assertEqual(result.job, "001")

    def test_science_split_separates_holder_from_project(self):
        self.assertEqual(klas.split_science("3154190170"), ("3154", "190170"))
        self.assertEqual(klas.split_science("315400"), ("3154", "00"))
        self.assertIsNone(klas.split_science("430111"))


class ImportTestCase(TestCase):
    """Zajednicki izvor podataka za uvoz."""

    JOBS = [
        ("430111", "43", "Strucni nadzor", True, "P"),
        ("430001", "", "Troskovi amortizacije", True, "N"),
        ("431112", "43", "Terenske lab.", False, "P"),
        ("410001", "41", "Troskovi amortizacije", True, "N"),
        ("209001", "2", "Organizacija i poslovanje", True, "N"),
        ("110002", "", "Telo za tehnicku ocenu", True, "N"),
        ("300001", "3", "Troskovi amortizacije", True, "N"),
        ("315400", "3", "Delic Ivana", True, "N"),
        ("3154190170", "3", "P190170-Delic I.", True, "N"),
        ("vranjs", "43", "Troskovi amortizacije", True, "P"),
        ("111111", "3", "", True, "N"),
    ]

    def setUp(self):
        for code, center, name, active, profit in self.JOBS:
            FinanceJob.objects.create(
                company=1, code=code, center=center, name=name, active=active, profit_type=profit
            )
        self._line = 0
        for job_code, unit in (
            ("430111", "43"),
            ("430001", "43"),
            ("410001", "41"),
            ("209001", "20"),
            ("110002", "11"),
            ("315400", "30"),
            ("vranjs", "43"),
            ("3154190170", "1"),
        ):
            self._ledger(job_code, unit)

    def _ledger(self, job_code, unit):
        self._line += 1
        line = self._line
        now = timezone.now()
        LedgerEntry.objects.create(
            company=1,
            year=2026,
            journal_type="001",
            journal_number=line,
            line_number=line,
            organizational_unit=int(unit),
            organizational_unit_name=UNITS[unit],
            account="204000",
            document_date=date(2026, 3, 1),
            booking_date=date(2026, 3, 1),
            debit=Decimal("100.00"),
            credit=Decimal("0.00"),
            job_code=job_code,
            center=unit,
            source_hash=f"h{job_code}{line}",
            changed_at=now,
        )


class KnownUnitTests(ImportTestCase):
    def test_unit_names_come_from_ledger_not_from_codebook(self):
        """Nazivi centara ne postoje u sifarniku; jedini izvor su knjizenja."""
        units = collect_known_units(company=1)
        self.assertEqual(units["43"], "Centar za puteve i geotehniku")
        self.assertEqual(units["20"], "POSLOVNI BLOK")
        self.assertEqual(units["30"], "Naucno istrazivacki blok")

    def test_import_refuses_when_there_are_no_postings(self):
        LedgerEntry.objects.all().delete()
        with self.assertRaises(Exception):
            run_import(company=1)


class TreeBuildTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        self.run = run_import(company=1)

    def test_three_levels_are_created(self):
        structure = structural_checks(1)
        # Pet od sest poznatih jedinica nosi poslove; `1 IMS` ne nosi nijedan.
        self.assertEqual(structure["centers"], 5)
        self.assertEqual(structure["jobs"], 7)
        self.assertEqual(structure["duplicate_codes"], [])
        self.assertEqual(structure["orphans"], [])

    def test_parent_chain_is_explicit(self):
        version = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True)
        unit = OrgNodeVersion.objects.get(node=version.parent, valid_to__isnull=True)
        center = OrgNodeVersion.objects.get(node=unit.parent, valid_to__isnull=True)
        self.assertEqual(unit.full_code, "430")
        self.assertEqual(center.full_code, "43")
        self.assertEqual(center.name, "Centar za puteve i geotehniku")

    def test_second_level_has_no_invented_name(self):
        unit = OrgNodeVersion.objects.get(full_code="430", valid_to__isnull=True)
        self.assertEqual(unit.name, "")
        self.assertIn("nije potvrdjen", unit.note)

    def test_profit_flag_keeps_unknown_as_unknown(self):
        job = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True)
        self.assertIs(job.is_profit, True)
        job = OrgNodeVersion.objects.get(full_code="430001", valid_to__isnull=True)
        self.assertIs(job.is_profit, False)

    def test_inactive_job_is_imported_but_marked(self):
        job = OrgNodeVersion.objects.get(full_code="431112", valid_to__isnull=True)
        self.assertFalse(job.is_active)

    def test_science_codes_stay_out_of_the_tree(self):
        codes = set(
            OrgNodeVersion.objects.filter(valid_to__isnull=True).values_list("full_code", flat=True)
        )
        self.assertNotIn("315400", codes)
        self.assertNotIn("3154190170", codes)
        science = UnresolvedOrgCode.objects.filter(family=UnresolvedOrgCode.FAMILY_SCIENCE)
        self.assertEqual(set(science.values_list("code", flat=True)), {"315400", "3154190170"})

    def test_exceptions_are_listed_with_a_reason(self):
        exceptions = UnresolvedOrgCode.objects.filter(family=UnresolvedOrgCode.FAMILY_EXCEPTION)
        self.assertEqual(set(exceptions.values_list("code", flat=True)), {"vranjs", "111111"})
        for row in exceptions:
            self.assertTrue(row.reason)

    def test_unit_without_any_job_does_not_become_a_center(self):
        """`1 IMS` je cela ustanova; javlja se u knjizenjima, ali nije centar."""
        codes = set(
            OrgNodeVersion.objects.filter(
                valid_to__isnull=True, node__level=OrgNode.LEVEL_CENTER
            ).values_list("full_code", flat=True)
        )
        self.assertNotIn("1", codes)
        self.assertIn("43", codes)
        self.assertIn("nisu unete u stablo: 1", self.run.report)

    def test_raw_value_is_kept_untouched(self):
        mapping = ExternalOrgMapping.objects.get(
            source=ExternalOrgMapping.SOURCE_FINANCE_JOB, source_key="430111"
        )
        self.assertEqual(mapping.raw_value, "430111")

    def test_legacy_link_points_to_the_finance_job_row(self):
        job = FinanceJob.objects.get(code="430111")
        link = LegacyOrgLink.objects.get(
            legacy_label=LegacyOrgLink.LEGACY_FINANCE_JOB, legacy_id=job.pk
        )
        version = OrgNodeVersion.objects.get(node=link.node, valid_to__isnull=True)
        self.assertEqual(version.full_code, "430111")


class IdempotencyTests(ImportTestCase):
    def test_second_import_creates_nothing(self):
        first = run_import(company=1)
        nodes = OrgNode.objects.count()
        versions = OrgNodeVersion.objects.count()

        second = run_import(company=1)
        self.assertEqual(OrgNode.objects.count(), nodes)
        self.assertEqual(OrgNodeVersion.objects.count(), versions)
        self.assertEqual(second.nodes_created, 0)
        self.assertEqual(second.versions_created, 0)
        self.assertGreater(first.nodes_created, 0)

    def test_name_change_on_a_later_day_closes_the_old_version(self):
        run_import(company=1, valid_from=date(2026, 1, 1))
        job = FinanceJob.objects.get(code="430111")
        job.name = "Strucni nadzor i terenska ispitivanja"
        job.save()

        run_import(company=1, valid_from=date(2026, 6, 1))
        versions = OrgNodeVersion.objects.filter(full_code="430111").order_by("valid_from")
        self.assertEqual(versions.count(), 2)
        self.assertEqual(versions[0].valid_to, date(2026, 6, 1))
        self.assertEqual(versions[0].name, "Strucni nadzor")
        self.assertIsNone(versions[1].valid_to)
        self.assertEqual(versions[1].name, "Strucni nadzor i terenska ispitivanja")

    def test_identity_survives_a_name_change(self):
        run_import(company=1, valid_from=date(2026, 1, 1))
        node_id = OrgNodeVersion.objects.get(full_code="430111").node_id
        job = FinanceJob.objects.get(code="430111")
        job.name = "Novi naziv"
        job.save()
        run_import(company=1, valid_from=date(2026, 6, 1))
        current = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True)
        self.assertEqual(current.node_id, node_id)

    def test_correction_on_the_same_day_does_not_fake_history(self):
        run_import(company=1, valid_from=date(2026, 1, 1))
        job = FinanceJob.objects.get(code="430111")
        job.name = "Ispravljen naziv"
        job.save()
        run_import(company=1, valid_from=date(2026, 1, 1))
        versions = OrgNodeVersion.objects.filter(full_code="430111")
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().name, "Ispravljen naziv")

    def test_failed_import_leaves_no_half_tree(self):
        from organizacija.services import importer

        original = importer._link_fleet_units
        importer._link_fleet_units = lambda company: (_ for _ in ()).throw(RuntimeError("pad"))
        try:
            with self.assertRaises(RuntimeError):
                run_import(company=1)
        finally:
            importer._link_fleet_units = original
        self.assertEqual(OrgNode.objects.count(), 0)
        self.assertEqual(OrgNodeVersion.objects.count(), 0)


class FleetLinkTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        OrganizationalUnit.objects.create(code="430111  ", name="Strucni nadzor", center="43")
        OrganizationalUnit.objects.create(code="960001", name="Test centar", center="96")

    def test_fleet_unit_is_linked_by_code_ignoring_trailing_spaces(self):
        run_import(company=1)
        unit = OrganizationalUnit.objects.get(code="430111  ")
        link = LegacyOrgLink.objects.get(
            legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT, legacy_id=unit.pk
        )
        version = OrgNodeVersion.objects.get(node=link.node, valid_to__isnull=True)
        self.assertEqual(version.full_code, "430111")

    def test_fleet_unit_without_a_pair_is_not_invented(self):
        run_import(company=1)
        unit = OrganizationalUnit.objects.get(code="960001")
        self.assertFalse(
            LegacyOrgLink.objects.filter(
                legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT, legacy_id=unit.pk
            ).exists()
        )


class ReconciliationTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)

    def test_no_posting_disappears(self):
        ledger = ledger_reconciliation(1)
        self.assertEqual(
            ledger["resolved_rows"] + ledger["unresolved_rows"], ledger["total_rows"]
        )
        self.assertEqual(
            ledger["resolved_debit"] + ledger["unresolved_debit"], ledger["total_debit"]
        )

    def test_unresolved_amount_stays_visible(self):
        """Nauka i izuzeci se ne razresavaju — i to mora da se vidi, ne da se precuti."""
        ledger = ledger_reconciliation(1)
        codes = {item["job_code"] for item in ledger["unresolved"]}
        self.assertEqual(codes, {"315400", "3154190170", "vranjs"})
        self.assertEqual(ledger["unresolved_debit"], Decimal("300.00"))

    def test_center_totals_use_the_tree_not_the_text_field(self):
        """`209001` ima center='2' u sifarniku; preko stabla mora pasti pod 20."""
        ledger = ledger_reconciliation(1)
        self.assertIn("20", ledger["per_center"])
        self.assertEqual(ledger["per_center"]["20"]["rows"], 1)

    def test_report_has_all_three_parts(self):
        report = build_report(1)
        self.assertIn("structure", report)
        self.assertIn("ledger", report)
        self.assertIn("unresolved", report)


class VersionRuleTests(TestCase):
    """Pravila koja cuvaju istoriju od tihog kvarenja."""

    def setUp(self):
        self.center = OrgNode.objects.create(company=1, level=OrgNode.LEVEL_CENTER)
        self.unit = OrgNode.objects.create(company=1, level=OrgNode.LEVEL_UNIT)

    def _version(self, node, parent, code, valid_from, valid_to=None):
        return OrgNodeVersion(
            node=node,
            parent=parent,
            segment=code[-1],
            full_code=code,
            name="x",
            valid_from=valid_from,
            valid_to=valid_to,
        )

    def test_first_level_must_not_have_a_parent(self):
        version = self._version(self.center, self.unit, "43", date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            version.clean()

    def test_lower_level_must_have_a_parent(self):
        version = self._version(self.unit, None, "430", date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            version.clean()

    def test_parent_must_be_exactly_one_level_up(self):
        job = OrgNode.objects.create(company=1, level=OrgNode.LEVEL_JOB)
        version = self._version(job, self.center, "430111", date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            version.clean()

    def test_parent_must_be_in_the_same_company(self):
        other = OrgNode.objects.create(company=2, level=OrgNode.LEVEL_CENTER)
        version = self._version(self.unit, other, "430", date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            version.clean()

    def test_only_one_open_version_per_node(self):
        self._version(self.center, None, "43", date(2026, 1, 1)).save()
        with self.assertRaises(Exception):
            self._version(self.center, None, "43", date(2026, 6, 1)).save()

    def test_version_lookup_by_day_uses_half_open_interval(self):
        self._version(self.center, None, "43", date(2026, 1, 1), date(2026, 6, 1)).save()
        self._version(self.center, None, "44", date(2026, 6, 1)).save()
        self.assertEqual(self.center.version_on(date(2026, 5, 31)).full_code, "43")
        self.assertEqual(self.center.version_on(date(2026, 6, 1)).full_code, "44")
        self.assertIsNone(self.center.version_on(date(2025, 12, 31)))

    def test_valid_to_must_be_after_valid_from(self):
        version = self._version(
            self.center, None, "43", date(2026, 6, 1), date(2026, 1, 1)
        )
        with self.assertRaises(Exception):
            version.save()


class NothingElseChangedTests(ImportTestCase):
    """Faza 1 ne sme dodirnuti nijedan postojeci model."""

    def test_import_does_not_touch_finance_jobs(self):
        before = sorted(
            FinanceJob.objects.values_list("code", "name", "center", "active", "profit_type")
        )
        run_import(company=1)
        after = sorted(
            FinanceJob.objects.values_list("code", "name", "center", "active", "profit_type")
        )
        self.assertEqual(before, after)

    def test_import_does_not_touch_ledger_entries(self):
        before = sorted(LedgerEntry.objects.values_list("source_hash", "job_code", "center"))
        run_import(company=1)
        after = sorted(LedgerEntry.objects.values_list("source_hash", "job_code", "center"))
        self.assertEqual(before, after)

    def test_import_does_not_touch_fleet_units(self):
        OrganizationalUnit.objects.create(code="430111", name="Strucni nadzor", center="43")
        before = sorted(OrganizationalUnit.objects.values_list("code", "name", "center"))
        run_import(company=1)
        after = sorted(OrganizationalUnit.objects.values_list("code", "name", "center"))
        self.assertEqual(before, after)


class TreeServiceTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)

    def test_tree_nests_three_levels(self):
        from organizacija.services.tree import build_tree

        tree = {center["code"]: center for center in build_tree(1)}
        self.assertIn("43", tree)
        unit_codes = {unit["code"] for unit in tree["43"]["units"]}
        self.assertEqual(unit_codes, {"430", "431"})
        jobs = {
            job["code"] for unit in tree["43"]["units"] for job in unit["jobs"]
        }
        self.assertEqual(jobs, {"430111", "430001", "431112"})

    def test_counts_are_summed_up_the_tree(self):
        from organizacija.services.tree import build_tree, totals

        tree = build_tree(1)
        center = next(item for item in tree if item["code"] == "43")
        self.assertEqual(center["job_count"], 3)
        self.assertEqual(center["active_jobs"], 2)
        self.assertEqual(totals(tree)["jobs"], 7)

    def test_search_keeps_the_branch_of_a_matching_job(self):
        from organizacija.services.tree import build_tree

        tree = build_tree(1, query="431112")
        self.assertEqual([center["code"] for center in tree], ["43"])
        self.assertEqual([unit["code"] for unit in tree[0]["units"]], ["431"])
        self.assertEqual([job["code"] for job in tree[0]["units"][0]["jobs"]], ["431112"])
        self.assertTrue(tree[0]["units"][0]["jobs"][0]["match"])

    def test_search_by_name_is_case_insensitive(self):
        from organizacija.services.tree import build_tree

        tree = build_tree(1, query="NADZOR")
        codes = [job["code"] for center in tree for unit in center["units"] for job in unit["jobs"]]
        self.assertEqual(codes, ["430111"])

    def test_search_without_a_hit_returns_nothing(self):
        from organizacija.services.tree import build_tree

        self.assertEqual(build_tree(1, query="nepostojece"), [])

    def test_science_is_not_in_the_tree_but_is_listed_separately(self):
        from organizacija.services.tree import build_tree, unresolved_groups

        codes = {job["code"] for c in build_tree(1) for u in c["units"] for job in u["jobs"]}
        self.assertNotIn("315400", codes)
        families = {group["family"] for group in unresolved_groups()}
        self.assertEqual(families, {"B", "C"})


class TreeViewTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.url = reverse("organizacija:stablo")
        self.user = get_user_model().objects.create_user("org", password="t")
        self.user.is_superuser = False
        self.user.save()

    def _grant(self):
        role = Role.objects.create(name="Registar", slug="registar")
        permission, _ = PermissionCode.objects.get_or_create(code="organizacija:stablo")
        RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)

    def test_every_logged_in_user_sees_the_tree(self):
        """Organizaciju vide svi prijavljeni korisnici, bez posebne uloge."""
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 301))

    def test_with_permission_the_tree_renders(self):
        self._grant()
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Centar za puteve i geotehniku", content)
        self.assertIn("430111", content)
        self.assertIn("Otvori sve", content)
        self.assertIn("Zatvori sve", content)

    def test_open_all_button_sits_above_the_tree(self):
        """Dugme mora biti u zaglavlju, odmah vidljivo, a ne ispod stabla."""
        self._grant()
        self.client.force_login(self.user)
        content = self.client.get(self.url).content.decode()
        self.assertLess(content.index("data-org-open"), content.index('<div class="org-tree"'))
        self.assertLess(content.index("data-org-close"), content.index('<div class="org-tree"'))

    def test_open_and_close_buttons_appear_once_each(self):
        self._grant()
        self.client.force_login(self.user)
        content = self.client.get(self.url).content.decode()
        # Broji se atribut na dugmetu (`data-org-open>`), ne i selektor u skripti
        # (`[data-org-open]`), koji se takodje javlja u izlazu.
        self.assertEqual(content.count("data-org-open>"), 1)
        self.assertEqual(content.count("data-org-close>"), 1)

    def test_science_codes_are_shown_outside_the_tree(self):
        self._grant()
        self.client.force_login(self.user)
        content = self.client.get(self.url).content.decode()
        self.assertIn("Šifre van stabla", content)
        self.assertIn("315400", content)

    def test_second_level_without_a_name_says_so_instead_of_inventing_one(self):
        self._grant()
        self.client.force_login(self.user)
        content = self.client.get(self.url).content.decode()
        self.assertIn("naziv drugog nivoa nije potvrđen", content)

    def test_search_narrows_the_page(self):
        self._grant()
        self.client.force_login(self.user)
        content = self.client.get(self.url, {"q": "431112"}).content.decode()
        # Trazi se bas veza posla, jer se sifra javlja i u primeru u polju za pretragu.
        self.assertIn(">431112</a>", content)
        self.assertNotIn(">430111</a>", content)

    def test_view_switches_the_current_app(self):
        self._grant()
        self.client.force_login(self.user)
        self.client.get(self.url)
        self.assertEqual(self.client.session["current_app"], "organizacija")

    def test_styles_stay_inside_the_page(self):
        """Svaki selektor mora biti pod `.org-page` da ne dodirne druge ekrane."""
        from django.template.loader import render_to_string

        css = render_to_string("organizacija/_styles.html")
        for line in css.splitlines():
            line = line.strip()
            if not line or line.startswith(("<", "@", "}", "/*", "{%")) or "{" not in line:
                continue
            selector = line.split("{")[0].strip()
            self.assertTrue(
                selector.startswith(".org-page"),
                f"selektor nije ogranicen na stranicu: {selector}",
            )


class EmptyRegistryViewTests(TestCase):
    """Prazan registar mora da kaze sta da se uradi, ne da bude prazna stranica."""

    def setUp(self):
        self.url = reverse("organizacija:stablo")
        self.user = get_user_model().objects.create_user("prazno", password="t")
        self.user.is_superuser = False
        self.user.save()
        role = Role.objects.create(name="Registar prazan", slug="registar-prazan")
        permission, _ = PermissionCode.objects.get_or_create(code="organizacija:stablo")
        RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)

    def test_empty_registry_explains_how_to_fill_it(self):
        self.client.force_login(self.user)
        content = self.client.get(self.url).content.decode()
        self.assertIn("uvezi_organizaciju", content)
        self.assertIn("Registar je prazan", content)


class PermissionRegistrationTests(TestCase):
    def test_route_name_becomes_a_permission_code(self):
        from core.permissions import collect_permission_codes

        self.assertIn("organizacija:stablo", collect_permission_codes())


class PluralTests(TestCase):
    """Brojevi u prikazu moraju biti na srpskom, ne „1 poslova“."""

    def _form(self, number):
        from organizacija.templatetags.organizacija_extras import mnozina

        return mnozina(number, "posao,posla,poslova")

    def test_singular_few_and_many(self):
        self.assertEqual(self._form(1), "posao")
        self.assertEqual(self._form(2), "posla")
        self.assertEqual(self._form(4), "posla")
        self.assertEqual(self._form(5), "poslova")
        self.assertEqual(self._form(0), "poslova")

    def test_teens_always_take_the_third_form(self):
        for number in (11, 12, 13, 14, 111, 112):
            self.assertEqual(self._form(number), "poslova", number)

    def test_last_digit_decides_above_twenty(self):
        self.assertEqual(self._form(21), "posao")
        self.assertEqual(self._form(22), "posla")
        self.assertEqual(self._form(25), "poslova")

    def test_bad_input_does_not_break_the_page(self):
        from organizacija.templatetags.organizacija_extras import mnozina

        self.assertEqual(mnozina(None, "a,b,c"), "")
        self.assertEqual(mnozina(3, ""), "")


class NodeDetailServiceTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1, valid_from=date(2026, 1, 1))
        self.job = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True).node

    def test_path_goes_from_center_to_job(self):
        from organizacija.services.detail import node_detail

        data = node_detail(self.job.pk)
        self.assertEqual([step.full_code for step in data["path"]], ["43", "430", "430111"])

    def test_center_lists_its_units_as_children(self):
        from organizacija.services.detail import node_detail

        center = OrgNodeVersion.objects.get(full_code="43", valid_to__isnull=True).node
        data = node_detail(center.pk)
        self.assertEqual([child.full_code for child in data["children"]], ["430", "431"])

    def test_missing_node_returns_none(self):
        from organizacija.services.detail import node_detail

        self.assertIsNone(node_detail(999999))

    def test_history_names_what_changed(self):
        from organizacija.services.detail import node_detail

        job = FinanceJob.objects.get(code="430111")
        job.name = "Novi naziv"
        job.save()
        run_import(company=1, valid_from=date(2026, 6, 1))

        data = node_detail(self.job.pk)
        self.assertEqual(len(data["history"]), 2)
        self.assertEqual(data["history"][0]["changes"], ["prvi upis"])
        self.assertEqual(data["history"][1]["changes"], ["naziv"])
        self.assertTrue(data["history"][1]["is_current"])
        self.assertFalse(data["history"][0]["is_current"])

    def test_history_shows_the_parent_code_of_its_own_time(self):
        from organizacija.services.detail import node_detail

        data = node_detail(self.job.pk)
        self.assertEqual(data["history"][0]["parent_code"], "430")

    def test_links_to_old_models_are_listed(self):
        from organizacija.services.detail import node_detail

        data = node_detail(self.job.pk)
        labels = {link.legacy_label for link in data["legacy_links"]}
        self.assertIn(LegacyOrgLink.LEGACY_FINANCE_JOB, labels)
        sources = {mapping.source for mapping in data["mappings"]}
        self.assertIn(ExternalOrgMapping.SOURCE_FINANCE_JOB, sources)

    def test_ledger_usage_counts_every_code_the_job_ever_had(self):
        from organizacija.services.detail import ledger_usage, node_detail

        usage = ledger_usage(node_detail(self.job.pk))
        self.assertEqual(usage["rows"], 1)
        self.assertEqual(usage["codes"], ["430111"])

    def test_ledger_usage_is_not_offered_for_a_center(self):
        """Knjizenja se vezuju za sifru posla, pa za centar nema sta da se broji."""
        from organizacija.services.detail import ledger_usage, node_detail

        center = OrgNodeVersion.objects.get(full_code="43", valid_to__isnull=True).node
        self.assertIsNone(ledger_usage(node_detail(center.pk)))


class NodeDetailViewTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.job = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True).node
        self.user = get_user_model().objects.create_user("detalj", password="t")
        self.user.is_superuser = False
        self.user.save()
        role = Role.objects.create(name="Registar detalj", slug="registar-detalj")
        for code in ("organizacija:stablo", "organizacija:cvor"):
            permission, _ = PermissionCode.objects.get_or_create(code=code)
            RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)
        self.url = reverse("organizacija:cvor", args=[self.job.pk])

    def test_detail_renders_with_path_and_history(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("430111", content)
        self.assertIn("Istorija", content)
        self.assertIn("Povezivanja", content)
        self.assertIn("i dalje važi", content)

    def test_unknown_node_gives_404_not_500(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("organizacija:cvor", args=[999999])).status_code, 404)

    def test_every_logged_in_user_sees_the_node_without_ledger_amounts(self):
        other = get_user_model().objects.create_user("bez", password="t")
        self.client.force_login(other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Duguje")

    def test_ledger_amounts_need_the_finance_ledger_permission(self):
        role = Role.objects.create(name="Knjiženja", slug="knjizenja")
        permission, _ = PermissionCode.objects.get_or_create(code="finansije:ledger")
        RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(self.url), "Duguje")

    def test_tree_links_to_the_detail(self):
        self.client.force_login(self.user)
        content = self.client.get(reverse("organizacija:stablo")).content.decode()
        self.assertIn(reverse("organizacija:cvor", args=[self.job.pk]), content)

    def test_unit_detail_says_the_name_is_not_confirmed(self):
        unit = OrgNodeVersion.objects.get(full_code="430", valid_to__isnull=True).node
        self.client.force_login(self.user)
        content = self.client.get(reverse("organizacija:cvor", args=[unit.pk])).content.decode()
        self.assertIn("naziv nije potvrđen", content)


class TreeFilterTests(ImportTestCase):
    """Filteri oznaka: neaktivni, profitni, neprofitni, nepoznato."""

    def setUp(self):
        super().setUp()
        run_import(company=1)

    def _codes(self, **kwargs):
        from organizacija.services.tree import build_tree

        tree = build_tree(1, **kwargs)
        return {job["code"] for c in tree for u in c["units"] for job in u["jobs"]}

    def test_no_filter_shows_everything(self):
        self.assertEqual(len(self._codes()), 7)

    def test_only_inactive(self):
        self.assertEqual(self._codes(status="neaktivni"), {"431112"})

    def test_only_active(self):
        codes = self._codes(status="aktivni")
        self.assertNotIn("431112", codes)
        self.assertEqual(len(codes), 6)

    def test_only_profitable(self):
        self.assertEqual(self._codes(profit="profitni"), {"430111", "431112"})

    def test_only_nonprofitable(self):
        codes = self._codes(profit="neprofitni")
        self.assertIn("430001", codes)
        self.assertNotIn("430111", codes)

    def test_filters_combine(self):
        """Profitni i neaktivni istovremeno — presek, ne unija."""
        self.assertEqual(self._codes(status="neaktivni", profit="profitni"), {"431112"})

    def test_filter_combines_with_search(self):
        self.assertEqual(self._codes(query="43", profit="profitni"), {"430111", "431112"})

    def test_empty_branches_are_dropped_when_filtering(self):
        from organizacija.services.tree import build_tree

        tree = build_tree(1, status="neaktivni")
        self.assertEqual([center["code"] for center in tree], ["43"])
        self.assertEqual([unit["code"] for unit in tree[0]["units"]], ["431"])

    def test_unknown_filter_value_is_ignored_instead_of_breaking(self):
        self.assertEqual(len(self._codes(status="bilo-sta", profit="bilo-sta")), 7)

    def test_searching_a_center_name_keeps_its_contents(self):
        """Pogodak na centru ne sme vratiti prazan centar."""
        codes = self._codes(query="puteve")
        self.assertEqual(codes, {"430111", "430001", "431112"})


class FilterLinkTests(TestCase):
    def test_active_filter_link_switches_it_off(self):
        from organizacija.services.tree import filter_links

        links = {link["label"]: link for link in filter_links(status="neaktivni")}
        self.assertTrue(links["Prikaži neaktivne"]["active"])
        self.assertEqual(links["Prikaži neaktivne"]["url"], "?")

    def test_reset_link_clears_everything_but_keeps_the_search(self):
        from organizacija.services.tree import filter_links

        links = {link["label"]: link for link in filter_links(query="nadzor", status="aktivni")}
        self.assertEqual(links["Svi"]["url"], "?q=nadzor")

    def test_svi_is_active_when_no_filter_is_set(self):
        from organizacija.services.tree import filter_links

        links = {link["label"]: link for link in filter_links()}
        self.assertTrue(links["Svi"]["active"])
        self.assertFalse(links["Profitni"]["active"])


class FilterViewTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1)
        self.url = reverse("organizacija:stablo")
        self.user = get_user_model().objects.create_user("filter", password="t")
        self.user.is_superuser = False
        self.user.save()
        role = Role.objects.create(name="Registar filter", slug="registar-filter")
        permission, _ = PermissionCode.objects.get_or_create(code="organizacija:stablo")
        RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)
        self.client.force_login(self.user)

    def test_all_filter_buttons_render(self):
        content = self.client.get(self.url).content.decode()
        for label in ("Otvori sve", "Zatvori sve", "Prikaži neaktivne", "Profitni", "Neprofitni"):
            self.assertIn(label, content)

    def test_inactive_filter_narrows_the_page(self):
        content = self.client.get(self.url, {"status": "neaktivni"}).content.decode()
        self.assertIn(">431112</a>", content)
        self.assertNotIn(">430111</a>", content)

    def test_filtered_page_says_how_much_is_shown(self):
        content = self.client.get(self.url, {"status": "neaktivni"}).content.decode()
        self.assertIn("Prikazano <strong>1</strong> od 7", content)

    def test_filtered_branches_open_by_themselves(self):
        content = self.client.get(self.url, {"profit": "profitni"}).content.decode()
        self.assertIn('<details class="org-center" open>', content)

    def test_bad_filter_value_does_not_break_the_page(self):
        response = self.client.get(self.url, {"status": "<script>", "profit": "x"})
        self.assertEqual(response.status_code, 200)


class ActivityMeasureTests(ImportTestCase):
    """Merenje obrta. Knjizenja iz pripreme su 01.03.2026."""

    def setUp(self):
        super().setUp()
        run_import(company=1, valid_from=date(2026, 1, 1))

    def _measure(self, today=date(2026, 6, 1), months=12):
        from organizacija.services.activity import measure, summarize

        result = measure(1, months, today)
        return result, summarize(result)

    def test_jobs_with_postings_in_the_window_have_turnover(self):
        _, summary = self._measure()
        self.assertEqual(summary["jobs"], 7)
        # Knjizenja postoje za 430111, 430001, 410001, 209001 i 110002.
        self.assertEqual(summary["with_turnover"], 5)

    def test_window_that_ends_before_the_postings_finds_no_turnover(self):
        _, summary = self._measure(today=date(2028, 1, 1))
        self.assertEqual(summary["with_turnover"], 0)
        self.assertEqual(summary["without_turnover"], 7)

    def test_only_active_jobs_without_turnover_are_listed_for_deactivation(self):
        _, summary = self._measure()
        codes = {item["code"] for item in summary["to_deactivate"]}
        self.assertNotIn("431112", codes)  # vec neaktivan u izvoru
        self.assertIn("300001", codes)

    def test_already_inactive_is_kept_separate(self):
        _, summary = self._measure()
        codes = {item["code"] for item in summary["already_inactive"]}
        self.assertEqual(codes, {"431112"})

    def test_source_and_registry_activity_are_reported_separately(self):
        result, _ = self._measure()
        row = next(item for item in result["findings"] if item["code"] == "431112")
        self.assertFalse(row["source_active"])
        self.assertFalse(row["current_active"])

    def test_zero_amount_posting_is_not_turnover(self):
        from decimal import Decimal

        from organizacija.services.activity import measure, summarize

        LedgerEntry.objects.filter(job_code="430001").update(
            debit=Decimal("0.00"), credit=Decimal("0.00")
        )
        summary = summarize(measure(1, 12, date(2026, 6, 1)))
        self.assertIn("430001", {item["code"] for item in summary["to_deactivate"]})

    def test_turnover_counts_every_code_the_same_node_ever_had(self):
        """Kad jedan cvor promeni sifru, obrt sa stare sifre i dalje pripada njemu."""
        from organizacija.services.activity import measure

        version = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True)
        version.valid_to = date(2026, 4, 1)
        version.save(update_fields=["valid_to"])
        OrgNodeVersion.objects.create(
            node=version.node, parent=version.parent, segment="119",
            full_code="430119", name=version.name, is_active=True,
            is_profit=version.is_profit, valid_from=date(2026, 4, 1),
        )
        result = measure(1, 12, date(2026, 6, 1))
        row = next(item for item in result["findings"] if item["code"] == "430119")
        self.assertTrue(row["has_turnover"], "obrt sa stare sifre mora da se racuna")
        self.assertEqual(row["rows"], 1)

    def test_changing_the_code_in_the_source_creates_a_new_node(self):
        """Zabelezeno ponasanje, ne zeljeno: uvoz prepoznaje posao po sifri.

        Plan trazi da promena sifre ostane isti posao, ali **samo uz potvrdjenu mapu
        staro -> novo**, koja jos nije napravljena. Do tada uvoz vidi novu sifru kao nov
        posao. Ovaj test to drzi vidljivim da ne prodje neprimetno.
        """
        job = FinanceJob.objects.get(code="430111")
        job.code = "430119"
        job.save()
        run_import(company=1, valid_from=date(2026, 4, 1))

        codes = set(
            OrgNodeVersion.objects.filter(valid_to__isnull=True).values_list("full_code", flat=True)
        )
        self.assertIn("430119", codes)
        self.assertIn("430111", codes)
        stari = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True)
        novi = OrgNodeVersion.objects.get(full_code="430119", valid_to__isnull=True)
        self.assertNotEqual(stari.node_id, novi.node_id)


class ActivityApplyTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1, valid_from=date(2026, 1, 1))

    def _apply(self, today=date(2026, 6, 1)):
        from organizacija.services.activity import apply_reviews

        return apply_reviews(1, 12, today)

    def test_active_job_without_turnover_is_switched_off(self):
        self._apply()
        version = OrgNodeVersion.objects.get(full_code="300001", valid_to__isnull=True)
        self.assertFalse(version.is_active)
        self.assertIn("nema obrta", version.note)

    def test_job_with_turnover_stays_active(self):
        self._apply()
        self.assertTrue(
            OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True).is_active
        )

    def test_switching_off_closes_the_old_version_instead_of_rewriting_it(self):
        self._apply()
        versions = OrgNodeVersion.objects.filter(full_code="300001").order_by("valid_from")
        self.assertEqual(versions.count(), 2)
        self.assertEqual(versions[0].valid_to, date(2026, 6, 1))
        self.assertTrue(versions[0].is_active)
        self.assertFalse(versions[1].is_active)

    def test_same_day_does_not_create_a_zero_length_version(self):
        self._apply(today=date(2026, 1, 1))
        self.assertEqual(OrgNodeVersion.objects.filter(full_code="300001").count(), 1)

    def test_a_job_the_source_calls_inactive_is_switched_on_when_it_has_data(self):
        """Odluka 21.09.2026.: obrt je merodavan u oba smera."""
        self._ledger("431112", "43")
        summary = self._apply()
        self.assertTrue(
            OrgNodeVersion.objects.get(full_code="431112", valid_to__isnull=True).is_active
        )
        self.assertEqual({item["code"] for item in summary["to_activate"]}, {"431112"})

    def test_disagreement_with_the_source_stays_visible(self):
        self._ledger("431112", "43")
        summary = self._apply()
        codes = {item["code"] for item in summary["disagreements"]}
        self.assertIn("431112", codes)

    def test_reimport_does_not_undo_the_finding(self):
        """Bez ovoga bi oznaka oscilovala izmedju dva uvoza."""
        self._apply()
        run_import(company=1, valid_from=date(2026, 9, 1))
        version = OrgNodeVersion.objects.get(full_code="300001", valid_to__isnull=True)
        self.assertFalse(version.is_active)

    def test_running_twice_changes_nothing_the_second_time(self):
        self._apply()
        count = OrgNodeVersion.objects.count()
        second = self._apply(today=date(2026, 7, 1))
        self.assertEqual(OrgNodeVersion.objects.count(), count)
        self.assertEqual(second["versions_changed"], 0)

    def test_review_row_records_the_basis(self):
        from organizacija.models import JobActivityReview

        self._apply()
        node = OrgNodeVersion.objects.get(full_code="430111", valid_to__isnull=True).node
        review = JobActivityReview.objects.get(node=node)
        self.assertTrue(review.has_turnover)
        self.assertEqual(review.rows, 1)
        self.assertFalse(review.deactivates)
        self.assertEqual(review.window_to, date(2026, 6, 1))

    def test_finding_does_not_touch_the_source_codebook(self):
        before = sorted(FinanceJob.objects.values_list("code", "active"))
        self._apply()
        self.assertEqual(sorted(FinanceJob.objects.values_list("code", "active")), before)


class ActivityOnDetailTests(ImportTestCase):
    def setUp(self):
        super().setUp()
        run_import(company=1, valid_from=date(2026, 1, 1))
        from organizacija.services.activity import apply_reviews

        apply_reviews(1, 12, date(2026, 6, 1))
        self.user = get_user_model().objects.create_user("nalaz", password="t")
        self.user.is_superuser = False
        self.user.save()
        role = Role.objects.create(name="Registar nalaz", slug="registar-nalaz")
        for code in ("organizacija:stablo", "organizacija:cvor"):
            permission, _ = PermissionCode.objects.get_or_create(code=code)
            RolePermission.objects.create(role=role, permission=permission)
        self.user.roles.add(role)
        self.client.force_login(self.user)

    def _detail(self, code):
        node = OrgNodeVersion.objects.get(full_code=code, valid_to__isnull=True).node
        return self.client.get(reverse("organizacija:cvor", args=[node.pk])).content.decode()

    def test_switched_off_job_says_why(self):
        content = self._detail("300001")
        self.assertIn("Ugašeno nalazom", content)
        self.assertIn("nema obrta", content)

    def test_job_with_turnover_shows_the_count(self):
        content = self._detail("430111")
        self.assertIn("Nalaz o obrtu", content)

    def test_disagreement_with_the_source_is_shown_on_the_card(self):
        """Izvor kaze neaktivna, obrt kaze aktivna — kartica mora da prikaze obe strane."""
        self._ledger("431112", "43")
        from organizacija.services.activity import apply_reviews

        apply_reviews(1, 12, date(2026, 6, 1))
        content = self._detail("431112")
        self.assertIn("Razilazi se sa izvorom", content)
        self.assertIn("izvorni šifarnik se ne menja", content)

    def test_no_disagreement_notice_when_both_agree(self):
        content = self._detail("430111")
        self.assertNotIn("Razilazi se sa izvorom", content)


class OrgSemaViewTests(TestCase):
    """Organizaciona šema: poseban ekran za sve prijavljene korisnike, sa linkom u bočnom meniju."""

    def setUp(self):
        self.url = reverse("organizacija:sema")
        self.user = get_user_model().objects.create_user("sema", password="t")

    def test_anonymous_is_redirected_to_login(self):
        self.assertIn(self.client.get(self.url).status_code, (301, 302))

    def test_every_logged_in_user_sees_the_chart_and_sidebar_link(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="sema-img"')
        self.assertContains(response, 'id="sc-trazi"')
        self.assertContains(response, "organizacija/ims-organizaciona-sema.svg")
        self.assertContains(response, "organizacija/ims-organizaciona-sema.png")
        self.assertContains(response, "Laboratorija za ispitivanje geotehničkih konstrukcija")
        self.assertContains(response, "Materijali 9 · Metali i energetika 2 · Putevi i geotehnika 4 · Konstrukcije 1")
        self.assertContains(response, "Centar za materijale")
        self.assertContains(response, f'href="{self.url}"')
        self.assertEqual(self.client.session["current_app"], "organizacija")

    def test_schema_counts_match_the_drawing(self):
        from organizacija.services.sema import sema

        self.assertEqual(sema()["ukupno"], {"centri": 4, "laboratorije": 16, "ostale_celine": 8, "sluzbe": 2})

    def test_route_is_a_permission_code(self):
        from core.permissions import collect_permission_codes

        self.assertIn("organizacija:sema", collect_permission_codes())
