import vcr
from vcr.unittest import VCRTestCase

from alegra.client import ApiClient
from alegra.config import ApiConfig
from alegra.models.note import CreditNote, DebitNote


class TestCreditNoteResource(VCRTestCase):
    def setUp(self):
        self.config = ApiConfig(api_key="REDACTED", environment="sandbox")
        self.client = ApiClient(self.config)

    @vcr.use_cassette(
        "tests/fixtures/vcr_cassettes/test_create_credit_note.yaml",
        filter_headers=["authorization"],
    )
    def test_create_credit_note(self):
        credit_note_data = CreditNote(
            **{
                "associatedDocuments": [
                    {
                        "date": "2025-02-26",
                        "documentType": "01",
                        "number": 995000000,
                        "prefix": "SETP",
                        "uuid": "a452a6c20b15927c0a234ef6d28e638aecd4f7fcfe22368942f4fb3e3590cd0e993fe5a8973172e087aa3030b240353c",
                    }
                ],
                "company": {
                    "id": "01JN298D48XKSBK5T4XXKD27DS",
                },
                "customer": {
                    "taxCode": {"id": "ZZ"},
                    "address": {
                        "address": "Cra. 13 #12-12 Edificio A & A",
                        "city": "11001",
                        "department": "11",
                        "country": "CO",
                    },
                    "name": "Customer Name",
                    "organizationType": 2,
                    "identificationType": "13",
                    "identificationNumber": "222222222222",
                    "dv": "2",
                    "email": "email@email.com",
                    "phone": "3223334455",
                },
                "totalAmounts": {
                    "grossTotal": 10000,
                    "taxableTotal": 10000,
                    "taxTotal": 1900,
                    "discountTotal": 0,
                    "chargeTotal": 0,
                    "advanceTotal": 0,
                    "payableTotal": 11900,
                    "currencyCode": "COP",
                },
                "documentType": "91",
                "prefix": "NC",
                "number": 1,
                "conceptCode": "2",
                "note": "Anulación de factura",
                "items": [
                    {
                        "code": "BM3",
                        "standardCode": {"identificationId": "11001", "id": "001"},
                        "description": "Botella de M3",
                        "price": 10000,
                        "discount": 0,
                        "discountAmount": 0,
                        "quantity": 1,
                        "unitCode": "94",
                        "subtotal": 10000,
                        "taxAmount": 1900,
                        "total": 11900,
                        "taxes": [
                            {
                                "taxCode": "01",
                                "taxAmount": 1900,
                                "taxPercentage": "19.00",
                                "taxableAmount": 10000,
                                "taxBaseUnitMeasure": 1,
                                "taxPerUnitAmount": 1,
                            }
                        ],
                    }
                ],
                "payments": [
                    {
                        "paymentForm": "1",
                        "paymentMethod": "ZZZ",
                        "paymentDueDate": "2025-02-26",
                    }
                ],
            }
        )
        credit_note = self.client.credit_notes.create(credit_note_data)
        self.assertIsNotNone(credit_note.id)


class TestDebitNoteResource(VCRTestCase):
    def setUp(self):
        self.config = ApiConfig(api_key="REDACTED", environment="sandbox")
        self.client = ApiClient(self.config)

    @vcr.use_cassette(
        "tests/fixtures/vcr_cassettes/test_create_debit_note.yaml",
        filter_headers=["authorization"],
    )
    def test_create_debit_note(self):
        debit_note_data = DebitNote(
            **{
                "associatedDocuments": [
                    {
                        "date": "2025-02-26",
                        "documentType": "01",
                        "number": 995000000,
                        "prefix": "SETP",
                        "uuid": "a452a6c20b15927c0a234ef6d28e638aecd4f7fcfe22368942f4fb3e3590cd0e993fe5a8973172e087aa3030b240353c",
                    }
                ],
                "company": {
                    "id": "01JN298D48XKSBK5T4XXKD27DS",
                },
                "customer": {
                    "taxCode": {"id": "ZZ"},
                    "address": {
                        "address": "Cra. 13 #12-12 Edificio A & A",
                        "city": "11001",
                        "department": "11",
                        "country": "CO",
                    },
                    "name": "Customer Name",
                    "organizationType": 2,
                    "identificationType": "13",
                    "identificationNumber": "222222222222",
                    "dv": "2",
                    "email": "email@email.com",
                    "phone": "3223334455",
                },
                "totalAmounts": {
                    "grossTotal": 10000,
                    "taxableTotal": 10000,
                    "taxTotal": 1900,
                    "discountTotal": 0,
                    "chargeTotal": 0,
                    "advanceTotal": 0,
                    "payableTotal": 11900,
                    "currencyCode": "COP",
                },
                "prefix": "ND",
                "number": 1,
                "conceptCode": "2",
                "note": "Cobro de botella faltante",
                "items": [
                    {
                        "code": "BM1",
                        "standardCode": {"identificationId": "11001", "id": "001"},
                        "description": "Botella de M1",
                        "price": 10000,
                        "discount": 0,
                        "discountAmount": 0,
                        "quantity": 1,
                        "unitCode": "94",
                        "subtotal": 10000,
                        "taxAmount": 1900,
                        "total": 11900,
                        "taxes": [
                            {
                                "taxCode": "01",
                                "taxAmount": 1900,
                                "taxPercentage": "19.00",
                                "taxableAmount": 10000,
                                "taxBaseUnitMeasure": 1,
                                "taxPerUnitAmount": 1,
                            }
                        ],
                    }
                ],
                "payments": [
                    {
                        "paymentForm": "1",
                        "paymentMethod": "ZZZ",
                        "paymentDueDate": "2025-02-26",
                    }
                ],
            }
        )
        debit_note = self.client.debit_notes.create(debit_note_data)
        self.assertIsNotNone(debit_note.id)
