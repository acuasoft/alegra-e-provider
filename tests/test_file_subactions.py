import unittest
from unittest.mock import patch

from alegra.client import ApiClient
from alegra.config import ApiConfig

FILE_TYPES = ["XML", "JSON", "GOVERNMENT_RESPONSE", "ATTACHED_DOCUMENT", "PDF", "ZIP"]

RESOURCES_AND_ENDPOINTS = [
    ("invoices", "invoices"),
    ("credit_notes", "credit-notes"),
    ("debit_notes", "debit-notes"),
]


class TestFileSubactions(unittest.TestCase):
    def setUp(self):
        self.config = ApiConfig(api_key="REDACTED", environment="sandbox")
        patcher = patch.object(
            ApiClient, "_request", return_value={"file": {"content": "abc"}}
        )
        self.mock_request = patcher.start()
        self.addCleanup(patcher.stop)
        self.client = ApiClient(self.config)

    def test_file_pdf_subaction_allowed_for_invoices_and_notes(self):
        for attr, endpoint in RESOURCES_AND_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.mock_request.reset_mock()
                resource = getattr(self.client, attr)
                file_response = resource.perform_subaction("some-id", "file_pdf")
                self.assertEqual(file_response.content, "abc")
                self.mock_request.assert_called_once_with(
                    "GET", f"{endpoint}/some-id/files/PDF"
                )

    def test_all_documented_file_types_are_registered(self):
        for attr, endpoint in RESOURCES_AND_ENDPOINTS:
            resource = getattr(self.client, attr)
            for file_type in FILE_TYPES:
                subaction = f"file_{file_type.lower()}"
                with self.subTest(endpoint=endpoint, subaction=subaction):
                    self.mock_request.reset_mock()
                    resource.perform_subaction("some-id", subaction)
                    self.mock_request.assert_called_once_with(
                        "GET", f"{endpoint}/some-id/files/{file_type}"
                    )
