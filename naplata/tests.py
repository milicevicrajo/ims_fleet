from django.test import RequestFactory, SimpleTestCase

from .queries import neodobrene_if_filters_from_request


class NeodobreneIfQueryTests(SimpleTestCase):
    def test_filters_from_request_strips_values_and_defaults_missing_fields(self):
        request = RequestFactory().get(
            "/naplata/neodobrene-if/",
            {
                "god": " 2026 ",
                "sifra_partnera": " 123 ",
                "naziv_partnera": "",
                "status_na_sefu": " Odobreno ",
            },
        )

        self.assertEqual(
            neodobrene_if_filters_from_request(request),
            {
                "god": "2026",
                "sifra_partnera": "123",
                "naziv_partnera": "",
                "status_na_sefu": "Odobreno",
            },
        )
