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
