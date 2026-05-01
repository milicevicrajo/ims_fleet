from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

from .queries import (
    dugovanja_po_bucketima_rows,
    izvestaj_po_siframa_posla_data,
    neodobrene_if_filters_from_request,
)


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


class DugovanjaPoBucketimaQueryTests(SimpleTestCase):
    def test_returns_empty_rows_without_query_when_filter_values_are_empty(self):
        self.assertEqual(dugovanja_po_bucketima_rows([]), [])

    def test_uses_sif_par_filter_when_values_are_provided(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [("row",)]
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        with patch("naplata.queries.connections", {"server_db": connection}):
            result = dugovanja_po_bucketima_rows([123, 456])

        sql, params = cursor.execute.call_args.args
        self.assertEqual(result, [("row",)])
        self.assertIn("WHERE db.sif_par IN (%s,%s)", sql)
        self.assertEqual(params, [123, 456])


class IzvestajPoSiframaPoslaQueryTests(SimpleTestCase):
    def test_returns_empty_data_without_query_when_user_has_no_allowed_sif_pos(self):
        self.assertEqual(izvestaj_po_siframa_posla_data(False, [], ""), ([], []))

    def test_filters_options_and_rows_for_non_superuser(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [[(" 100 ",), (None,), ("200",)], [("row",)]]
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        with patch("naplata.queries.connections", {"server_db": connection}):
            dugovanja, sif_pos_options = izvestaj_po_siframa_posla_data(
                False,
                ["100", "200"],
                "100",
            )

        first_sql, first_params = cursor.execute.call_args_list[0].args
        second_sql, second_params = cursor.execute.call_args_list[1].args

        self.assertEqual(dugovanja, [("row",)])
        self.assertEqual(sif_pos_options, ["100", "200"])
        self.assertIn("WHERE db.sif_pos IN (%s,%s)", first_sql)
        self.assertEqual(first_params, ["100", "200"])
        self.assertIn("db.sif_pos IN (%s,%s)", second_sql)
        self.assertIn("db.sif_pos = %s", second_sql)
        self.assertEqual(second_params, ["100", "200", "100"])
