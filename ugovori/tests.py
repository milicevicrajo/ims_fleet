import os
import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from mobilni.models import MobilePackage

from .forms import ContractDocumentForm, ContractForm
from .models import Contract, ContractDocument, ContractType


class ContractDocumentTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        self.user = get_user_model().objects.create_superuser(
            username="contract-document-admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        contract_type = ContractType.objects.create(code="MOB", name="Mobilni")
        self.contract = Contract.objects.create(
            kind=Contract.MAIN,
            contract_type=contract_type,
            contract_number="20-965/2026",
            title="Ugovor za mobilne usluge",
            contract_date=date(2026, 1, 15),
            created_by=self.user,
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()

    def upload_document(self, description, filename, document_type):
        return self.client.post(
            reverse(
                "ugovori:contract_document_create",
                kwargs={"pk": self.contract.pk},
            ),
            {
                "document_type": document_type,
                "description": description,
                "file": SimpleUploadedFile(
                    filename,
                    b"test document content",
                    content_type="application/pdf",
                ),
            },
        )

    def test_multiple_documents_can_be_uploaded_and_seen_on_contract_detail(self):
        first_response = self.upload_document(
            "Potpisani ugovor",
            "ugovor-20-965.pdf",
            ContractDocument.TYPE_CONTRACT,
        )
        second_response = self.upload_document(
            "Specifikacija tarifnih paketa",
            "tarifni-paketi.pdf",
            ContractDocument.TYPE_ATTACHMENT,
        )

        self.assertRedirects(
            first_response,
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk}),
        )
        self.assertRedirects(
            second_response,
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk}),
        )
        self.assertEqual(self.contract.documents.count(), 2)
        self.assertEqual(
            set(self.contract.documents.values_list("document_type", flat=True)),
            {ContractDocument.TYPE_ATTACHMENT},
        )
        self.assertTrue(
            self.contract.documents.filter(uploaded_by=self.user).exists()
        )

        detail_response = self.client.get(
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk})
        )
        self.assertContains(detail_response, "Okači ugovor")
        self.assertContains(detail_response, "Okači prilog")
        self.assertContains(detail_response, "Potpisani ugovor")
        self.assertContains(detail_response, "Specifikacija tarifnih paketa")
        self.assertContains(detail_response, "ugovor-20-965.pdf")
        self.assertContains(detail_response, "tarifni-paketi.pdf")

    def test_description_is_required(self):
        response = self.upload_document(
            "",
            "bez-opisa.pdf",
            ContractDocument.TYPE_ATTACHMENT,
        )

        self.assertRedirects(
            response,
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk}),
        )
        self.assertFalse(self.contract.documents.exists())

    def test_contract_and_attachments_use_separate_fields(self):
        self.assertIn("file", ContractForm().fields)
        self.assertNotIn("document_type", ContractDocumentForm().fields)

    def test_contract_file_upload_does_not_create_an_attachment(self):
        response = self.client.post(
            reverse(
                "ugovori:contract_file_upload",
                kwargs={"pk": self.contract.pk},
            ),
            {
                "file": SimpleUploadedFile(
                    "glavni-ugovor.pdf",
                    b"signed contract",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk}),
        )
        self.contract.refresh_from_db()
        self.assertTrue(self.contract.file.name.endswith("glavni-ugovor.pdf"))
        self.assertFalse(self.contract.documents.exists())

    def test_linked_mobile_packages_are_visible_on_contract_detail(self):
        MobilePackage.objects.create(
            name="Tarifni paket 1",
            description="Paket sa neograničenim pozivima",
            net_amount="1000.00",
            contract=self.contract,
        )

        response = self.client.get(
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk})
        )

        self.assertContains(response, "Povezani tarifni paketi (1)")
        self.assertContains(response, "Tarifni paket 1")
        self.assertContains(response, "Paket sa neograničenim pozivima")

    def test_document_can_be_deleted_from_contract_detail(self):
        self.upload_document(
            "Dokument za brisanje",
            "brisanje.pdf",
            ContractDocument.TYPE_OTHER,
        )
        document = self.contract.documents.get()
        stored_path = document.file.path
        self.assertTrue(os.path.exists(stored_path))

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse(
                    "ugovori:contract_document_delete",
                    kwargs={
                        "pk": self.contract.pk,
                        "document_pk": document.pk,
                    },
                )
            )

        self.assertRedirects(
            response,
            reverse("ugovori:contract_detail", kwargs={"pk": self.contract.pk}),
        )
        self.assertFalse(ContractDocument.objects.filter(pk=document.pk).exists())
        self.assertFalse(os.path.exists(stored_path))


class PregledUgovoraTests(TestCase):
    """Detalj ugovora: delovodni broj se samo prikazuje, PDF ugovora se vidi na dnu (od 07.10.2026.)."""

    def setUp(self):
        from core.models import PermissionCode, Role
        from hr.permissions import KADROVI_UGOVORI_CODES

        self.media = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media.name)
        self.media_override.enable()
        tip = ContractType.objects.create(code="USL", name="Usluge")
        self.ugovor = Contract.objects.create(kind=Contract.MAIN, contract_type=tip, contract_number="43-100/2026",
                                              title="Ispitivanje", contract_date=date(2026, 3, 1),
                                              delovodni_broj="1234", delovodni_godina=2026,
                                              file=SimpleUploadedFile("ugovor.pdf", b"%PDF-1.4 ugovor"))
        uloga = Role.objects.create(name="Kadrovi test", slug="kadrovi-ugovori-test")
        for kod in KADROVI_UGOVORI_CODES:
            uloga.permissions.add(PermissionCode.objects.get_or_create(code=kod)[0])
        self.kadrovik = get_user_model().objects.create_user("kadrovik-ugovori", password="x")
        self.kadrovik.roles.add(uloga)
        self.client.force_login(self.kadrovik)

    def tearDown(self):
        self.media_override.disable()
        self.media.cleanup()

    def test_detalj_prikazuje_delovodni_broj_i_pdf_bez_izmena(self):
        detalj = self.client.get(reverse("ugovori:contract_detail", args=[self.ugovor.pk]))
        self.assertContains(detalj, "2026-1234")
        self.assertNotContains(detalj, 'name="delovodni_broj"')  # na detalju nema unosa
        adresa = reverse("ugovori:contract_file_view", args=[self.ugovor.pk])
        self.assertContains(detalj, f'<iframe src="{adresa}"')
        self.assertNotContains(detalj, reverse("ugovori:contract_update", args=[self.ugovor.pk]))
        self.assertNotContains(detalj, reverse("ugovori:contract_delete", args=[self.ugovor.pk]))
        pdf = self.client.get(adresa)
        self.assertEqual((pdf.status_code, pdf["X-Frame-Options"]), (200, "SAMEORIGIN"))
        self.assertTrue(pdf["Content-Disposition"].startswith("inline"))
        self.assertEqual(b"".join(pdf.streaming_content), b"%PDF-1.4 ugovor")
        spisak = self.client.get(reverse("ugovori:contract_list"), {"search": "2026-1234"})
        self.assertContains(spisak, "del. br. 2026-1234")
        self.assertNotContains(self.client.get(reverse("ugovori:contract_list"), {"search": "2025-1234"}), "del. br. 2026-1234")

    def test_bez_fajla_nema_pregleda(self):
        Contract.objects.filter(pk=self.ugovor.pk).update(file="")
        detalj = self.client.get(reverse("ugovori:contract_detail", args=[self.ugovor.pk]))
        self.assertNotContains(detalj, "<iframe")
        self.assertEqual(self.client.get(reverse("ugovori:contract_file_view", args=[self.ugovor.pk])).status_code, 404)

    def test_dozvole_kadrova(self):
        from hr.permissions import collect_kadrovi_permission_codes

        kadrovi = collect_kadrovi_permission_codes()
        self.assertIn("ugovori:contract_file_view", kadrovi)
        self.assertNotIn("ugovori:contract_update", kadrovi)


class DelovodniBrojUFormiTests(TestCase):
    """Delovodni broj Pravne službe u formi za unos i izmenu ugovora (od 07.10.2026.)."""

    def test_forma_ugovora_cuva_i_proverava_delovodni_broj(self):
        tip = ContractType.objects.create(code="USL", name="Usluge")
        postojeci = Contract.objects.create(kind=Contract.MAIN, contract_type=tip, contract_number="43-1/2026",
                                            title="Prvi", contract_date=date(2026, 1, 10),
                                            delovodni_broj="77", delovodni_godina=2026)
        podaci = {"kind": Contract.MAIN, "contract_type": tip.pk, "contract_number": "43-2/2026", "title": "Drugi",
                  "contract_date": "10.02.2026", "value_type": Contract.VALUE_TYPE_UNDEFINED, "currency": "RSD",
                  "status": Contract.STATUS_ACTIVE, "delovodni_broj": " 77 ", "delovodni_godina": "2026"}
        forma = ContractForm(data=podaci)
        self.assertFalse(forma.is_valid())
        self.assertIn("Delovodni broj 2026-77 već ima ugovor 43-1/2026.", forma.errors["delovodni_broj"])
        forma = ContractForm(data=dict(podaci, delovodni_broj="78"))
        self.assertTrue(forma.is_valid(), forma.errors)
        self.assertEqual(forma.save().delovodni, "2026-78")
        self.assertTrue(ContractForm(data=dict(podaci, contract_number="43-3/2026", delovodni_broj="")).is_valid())
        self.assertIn("delovodni_broj", ContractForm(instance=postojeci).fields)

    def test_strana_forme_ima_karticu(self):
        admin = get_user_model().objects.create_superuser("ugovori-forma", "f@example.com", "x")
        self.client.force_login(admin)
        odgovor = self.client.get(reverse("ugovori:contract_create"))
        self.assertContains(odgovor, "Delovodni broj Pravne službe")
        self.assertContains(odgovor, 'name="delovodni_broj"')
        self.assertContains(odgovor, 'name="delovodni_godina"')

    def test_spisak_ima_link_na_pdf(self):
        tip = ContractType.objects.create(code="PDF", name="Sa fajlom")
        media = tempfile.TemporaryDirectory()
        with override_settings(MEDIA_ROOT=media.name):
            ugovor = Contract.objects.create(kind=Contract.MAIN, contract_type=tip, contract_number="41-9/2026", title="Sa PDF-om",
                                             contract_date=date(2026, 5, 1), file=SimpleUploadedFile("u.pdf", b"%PDF-1.4"))
            admin = get_user_model().objects.create_superuser("ugovori-spisak", "s@example.com", "x")
            self.client.force_login(admin)
            spisak = self.client.get(reverse("ugovori:contract_list"))
        media.cleanup()
        self.assertContains(spisak, reverse("ugovori:contract_file_view", args=[ugovor.pk]))
        self.assertContains(spisak, "mdi-file-pdf-box")
