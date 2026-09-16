import vcr
from vcr.unittest import VCRTestCase

from alegra.client import ApiClient
from alegra.config import ApiConfig
from alegra.models.invoice import Invoice, InvoiceResponse


class TestInvoiceResource(VCRTestCase):
    def setUp(self):
        self.config = ApiConfig(api_key="REDACTED", environment="sandbox")
        self.client = ApiClient(self.config)

    @vcr.use_cassette(
        "tests/fixtures/vcr_cassettes/test_create_invoice.yaml",
        filter_headers=["authorization"],
    )
    def test_create_invoice(self):
        invoice_data = Invoice(
            **{
                "documentType": "01",
                "resolution": {
                    "resolutionNumber": "18760000001",
                    "prefix": "SETP",
                    "minNumber": 990000000,
                    "maxNumber": 995000000,
                    "startDate": "2019-01-19",
                    "endDate": "2030-01-19",
                    "technicalKey": "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c",
                },
                "company": {
                    "id": "01HTJ3D9NZA79Z6BRNHB19C6Z0",
                },
                "customer": {
                    "address": {
                        "address": "Cra. 13 #12-12 Edificio A & A",
                        "city": "11001",
                        "department": "11",
                        "country": "CO",
                    },
                    "name": "Customer Name",
                    "taxCode": {"id": "01"},
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
                "number": 990015000,
                "note": "Nota relativa al documento",
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
                        "paymentMethod": "10",
                        "paymentDueDate": "2021-08-30",
                    }
                ],
            }
        )
        invoice = self.client.invoices.create(invoice_data)
        self.assertIsNotNone(invoice.id)


def _waiting_response_payload():
    return {
        "id": "01JMZ1SMYJW51VAC1G2W38PJVR",
        "companyIdentification": "1144145424",
        "customerIdentification": "222222222222",
        "type": "STANDARD",
        "date": "2025-02-25T12:17:11-05:00",
        "prefix": "SETP",
        "number": 990015000,
        "fullNumber": "SETP990015000",
        "status": "WAITING_RESPONSE",
    }


class TestInvoiceResponseWaitingOnDian:
    """While status is WAITING_RESPONSE, the DIAN hasn't ruled yet, so
    legalStatus and the fields derived from that ruling are absent."""

    def test_parses_without_the_dian_dependent_fields(self):
        invoice = InvoiceResponse.model_validate(_waiting_response_payload())

        assert invoice.id == "01JMZ1SMYJW51VAC1G2W38PJVR"
        assert invoice.status == "WAITING_RESPONSE"
        assert invoice.legalStatus is None
        assert invoice.cufe is None
        assert invoice.governmentResponse is None
        assert invoice.xmlFileName is None
        assert invoice.zipFileName is None
        assert invoice.qrCodeContent is None

    def test_still_parses_a_fully_resolved_response(self):
        payload = _waiting_response_payload()
        payload.update(
            {
                "status": "SENT",
                "legalStatus": "REJECTED",
                "cufe": "d31239c3e9629734229b5c2e7fc212af8aa585600bbf2927a8066419e624d0",
                "governmentResponse": {
                    "code": "99",
                    "message": "Validación contiene errores en campos mandatorios.",
                    "errorMessages": [],
                },
                "xmlFileName": "fv11441454240852500000023.xml",
                "zipFileName": "z11441454240852500000024.zip",
                "qrCodeContent": "NumFac: SETP990015000",
            }
        )

        invoice = InvoiceResponse.model_validate(payload)

        assert invoice.legalStatus == "REJECTED"
        assert invoice.cufe == payload["cufe"]
        assert invoice.governmentResponse.code == "99"
