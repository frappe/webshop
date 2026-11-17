import unittest
from unittest.mock import patch

import webshop.webshop.api as webshop_api


class TestCountryStateOptions(unittest.TestCase):
        @patch.object(webshop_api, "frappe")
        def test_invalid_country_returns_empty_list(self, mock_frappe):
                mock_frappe.db.exists.return_value = False

                result = webshop_api.get_country_state_options("Invalid Country")

                self.assertEqual(result, [])
                mock_frappe.db.exists.assert_called_once_with("Country", "Invalid Country")

        @patch.object(webshop_api, "frappe")
        def test_no_providers_returns_empty_list(self, mock_frappe):
                mock_frappe.db.exists.return_value = True
                mock_frappe.get_hooks.return_value = []

                self.assertEqual(webshop_api.get_country_state_options("India"), [])

        @patch.object(webshop_api, "frappe")
        def test_provider_returns_state_options(self, mock_frappe):
                mock_frappe.db.exists.return_value = True
                mock_frappe.get_hooks.return_value = ["test.provider"]
                mock_frappe.get_attr.return_value = lambda country: ["Maharashtra", "Gujarat"]

                result = webshop_api.get_country_state_options("India")

                self.assertEqual(
                        result,
                        [
                                {"label": "Maharashtra", "value": "Maharashtra"},
                                {"label": "Gujarat", "value": "Gujarat"},
                        ],
                )
                mock_frappe.get_attr.assert_called_once_with("test.provider")

        @patch.object(webshop_api, "frappe")
        def test_provider_error_uses_next_provider(self, mock_frappe):
                mock_frappe.db.exists.return_value = True
                mock_frappe.get_hooks.return_value = [
                        "test.broken_provider",
                        "test.valid_provider",
                ]

                def resolve_provider(path):
                        if path == "test.broken_provider":
                                raise RuntimeError("Provider failed")
                        return lambda country: ["Maharashtra"]

                mock_frappe.get_attr.side_effect = resolve_provider
                mock_frappe.get_traceback.return_value = "provider traceback"

                result = webshop_api.get_country_state_options("India")

                self.assertEqual(
                        result,
                        [{"label": "Maharashtra", "value": "Maharashtra"}],
                )
                mock_frappe.log_error.assert_called_once()

        @patch.object(webshop_api, "frappe")
        def test_provider_results_are_sanitized_and_deduplicated(self, mock_frappe):
                mock_frappe.db.exists.return_value = True
                mock_frappe.get_hooks.return_value = ["test.provider"]
                mock_frappe.get_attr.return_value = lambda country: [
                        " Maharashtra ",
                        {"label": "Gujarat", "value": "Gujarat"},
                        "Maharashtra",
                        "",
                        {"label": "Invalid", "value": ""},
                        123,
                ]

                result = webshop_api.get_country_state_options("India")

                self.assertEqual(
                        result,
                        [
                                {"label": "Maharashtra", "value": "Maharashtra"},
                                {"label": "Gujarat", "value": "Gujarat"},
                        ],
                )

        @patch.object(webshop_api, "frappe")
        def test_first_non_empty_provider_wins(self, mock_frappe):
                mock_frappe.db.exists.return_value = True
                mock_frappe.get_hooks.return_value = [
                        "test.empty_provider",
                        "test.provider",
                        "test.other",
                ]
                mock_frappe.get_attr.side_effect = [
                        lambda country: [],
                        lambda country: ["Maharashtra"],
                        lambda country: ["Gujarat"],
                ]

                result = webshop_api.get_country_state_options("India")

                self.assertEqual(
                        result,
                        [{"label": "Maharashtra", "value": "Maharashtra"}],
                )
                self.assertEqual(mock_frappe.get_attr.call_count, 2)

        @patch.object(webshop_api, "frappe")
        def test_empty_or_oversized_country_returns_empty_list(self, mock_frappe):
                self.assertEqual(webshop_api.get_country_state_options(""), [])
                self.assertEqual(webshop_api.get_country_state_options("x" * 141), [])
                mock_frappe.db.exists.assert_not_called()


if __name__ == "__main__":
        unittest.main()
