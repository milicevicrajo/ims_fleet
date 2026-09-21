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

    def test_without_permission_access_is_denied(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

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
        # Trazi se bas red posla, jer se sifra javlja i u primeru u polju za pretragu.
        self.assertIn('org-code-3">431112<', content)
        self.assertNotIn('org-code-3">430111<', content)

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
