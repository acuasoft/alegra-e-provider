import asyncio
import json

import pytest
import vcr
from pydantic import TypeAdapter, ValidationError
from vcr.unittest import VCRTestCase

from alegra.client import ApiClient
from alegra.config import ApiConfig
from alegra.exceptions import AlegraResponseParseError
from alegra.models.invoice import (
    AnyInvoiceResponse,
    FailedInvoiceResponse,
    InvoiceResponse,
    RegisteredInvoiceResponse,
    SentInvoiceResponse,
    WaitingInvoiceResponse,
)
from tests.invoice_payloads import (
    CUFE,
    ISSUED_FIELDS,
    VERDICT_FIELDS,
    _invoice_payload,
    build_invoice,
)


class TestInvoiceResource(VCRTestCase):
    def setUp(self):
        self.config = ApiConfig(api_key="REDACTED", environment="sandbox")
        self.client = ApiClient(self.config)

    @vcr.use_cassette(
        "tests/fixtures/vcr_cassettes/test_create_invoice.yaml",
        filter_headers=["authorization"],
    )
    def test_create_invoice(self):
        invoice = self.client.invoices.create(build_invoice())
        self.assertIsNotNone(invoice.id)
        self.assertIsInstance(invoice, SentInvoiceResponse)


def _parse(payload):
    return TypeAdapter(AnyInvoiceResponse).validate_python(payload)


class TestInvoiceResponseByStatus:
    def test_registered_carries_only_the_fixed_fields(self):
        invoice = _parse(_invoice_payload("REGISTERED"))

        assert isinstance(invoice, RegisteredInvoiceResponse)
        assert invoice.id == "01JMZ1SMYJW51VAC1G2W38PJVR"
        assert invoice.cufe is None
        assert invoice.legalStatus is None

    def test_waiting_response_carries_cufe_and_files_but_no_verdict(self):
        invoice = _parse(_invoice_payload("WAITING_RESPONSE", **ISSUED_FIELDS))

        assert isinstance(invoice, WaitingInvoiceResponse)
        assert invoice.cufe == CUFE
        assert invoice.zipFileName == ISSUED_FIELDS["zipFileName"]
        assert invoice.legalStatus is None
        assert invoice.governmentResponse is None

    def test_sent_carries_the_files_and_the_verdict(self):
        invoice = _parse(_invoice_payload("SENT", **ISSUED_FIELDS, **VERDICT_FIELDS))

        assert isinstance(invoice, SentInvoiceResponse)
        assert invoice.legalStatus == "ACCEPTED"
        assert invoice.governmentResponse.code == "00"
        assert invoice.cufe == CUFE

    def test_sent_may_have_been_rejected(self):
        verdict = {
            "legalStatus": "REJECTED",
            "governmentResponse": {
                "code": "99",
                "message": "Validación contiene errores en campos mandatorios.",
                "errorMessages": ["Regla: FAU02, Rechazo: ..."],
            },
        }

        invoice = _parse(_invoice_payload("SENT", **ISSUED_FIELDS, **verdict))

        assert invoice.legalStatus == "REJECTED"
        assert invoice.governmentResponse.errorMessages == [
            "Regla: FAU02, Rechazo: ..."
        ]

    def test_failed_carries_the_errors(self):
        invoice = _parse(
            _invoice_payload(
                "FAILED",
                errors=[
                    {
                        "code": "EPR504",
                        "message": "Resend Error. Signature date is different from shipping date.",
                    },
                    {"message": "No code"},
                ],
            )
        )

        assert isinstance(invoice, FailedInvoiceResponse)
        assert invoice.errors[0].code == "EPR504"
        assert invoice.errors[0].message == (
            "Resend Error. Signature date is different from shipping date."
        )
        assert invoice.errors[1].code is None
        assert invoice.cufe is None

    def test_failed_keeps_whatever_was_generated_before_the_failure(self):
        invoice = _parse(_invoice_payload("FAILED", cufe=CUFE))

        assert invoice.cufe == CUFE
        assert invoice.errors is None

    @pytest.mark.parametrize("missing", list(ISSUED_FIELDS))
    def test_waiting_response_requires_each_issued_field(self, missing):
        fields = {k: v for k, v in ISSUED_FIELDS.items() if k != missing}

        payload = _invoice_payload("WAITING_RESPONSE", **fields)

        with pytest.raises(ValidationError) as exc_info:
            _parse(payload)

        assert exc_info.value.errors()[0]["loc"] == ("WAITING_RESPONSE", missing)

    @pytest.mark.parametrize("missing", list(VERDICT_FIELDS))
    def test_sent_requires_the_verdict(self, missing):
        verdict = {k: v for k, v in VERDICT_FIELDS.items() if k != missing}

        payload = _invoice_payload("SENT", **ISSUED_FIELDS, **verdict)

        with pytest.raises(ValidationError) as exc_info:
            _parse(payload)

        assert exc_info.value.errors()[0]["loc"] == ("SENT", missing)

    @pytest.mark.parametrize("status", ["PENDING", "", None, 123])
    def test_unknown_status_is_rejected(self, status):
        payload = _invoice_payload(status)

        with pytest.raises(ValidationError) as exc_info:
            _parse(payload)

        assert exc_info.value.errors()[0]["type"] == "union_tag_invalid"

    def test_missing_status_is_rejected(self):
        payload = _invoice_payload("REGISTERED")
        del payload["status"]

        with pytest.raises(ValidationError) as exc_info:
            _parse(payload)

        assert exc_info.value.errors()[0]["type"] == "union_tag_not_found"

    def test_json_input_builds_the_variant(self):
        payload = _invoice_payload("WAITING_RESPONSE", **ISSUED_FIELDS)

        invoice = TypeAdapter(AnyInvoiceResponse).validate_json(json.dumps(payload))

        assert isinstance(invoice, WaitingInvoiceResponse)

    @pytest.mark.parametrize(
        "payload",
        [
            _invoice_payload("REGISTERED"),
            _invoice_payload("WAITING_RESPONSE", **ISSUED_FIELDS),
            _invoice_payload("SENT", **ISSUED_FIELDS, **VERDICT_FIELDS),
            _invoice_payload("FAILED"),
        ],
    )
    def test_every_variant_is_an_invoice_response(self, payload):
        assert isinstance(_parse(payload), InvoiceResponse)

    def test_base_rejects_an_unknown_status(self):
        payload = _invoice_payload("PENDING")

        with pytest.raises(ValidationError):
            InvoiceResponse.model_validate(payload)

    def test_unknown_fields_are_ignored(self):
        invoice = _parse(
            _invoice_payload("SENT", **ISSUED_FIELDS, **VERDICT_FIELDS, newField=1)
        )

        assert isinstance(invoice, SentInvoiceResponse)


def _client_returning(response, async_mode=False):
    client = ApiClient(
        ApiConfig(api_key="key", environment="sandbox"), async_mode=async_mode
    )
    if async_mode:

        async def stub(method, endpoint, **kwargs):
            return response

    else:

        def stub(method, endpoint, **kwargs):
            return response

    client.invoices.resource.request_method = stub
    return client


class TestInvoicesThroughClient:
    def test_get_returns_the_invoice_while_waiting_on_the_dian(self):
        waiting = _invoice_payload("WAITING_RESPONSE", **ISSUED_FIELDS)
        client = _client_returning({"invoice": waiting})

        invoice = client.invoices.get(waiting["id"])

        assert isinstance(invoice, WaitingInvoiceResponse)
        assert invoice.id == waiting["id"]

    def test_list_builds_the_variant_of_each_invoice(self):
        client = _client_returning(
            {
                "invoices": [
                    _invoice_payload("WAITING_RESPONSE", **ISSUED_FIELDS),
                    _invoice_payload("REGISTERED"),
                ]
            }
        )

        invoices = client.invoices.list()

        assert [type(invoice) for invoice in invoices] == [
            WaitingInvoiceResponse,
            RegisteredInvoiceResponse,
        ]

    def test_create_builds_the_variant(self):
        sent = _invoice_payload("SENT", **ISSUED_FIELDS, **VERDICT_FIELDS)
        client = _client_returning({"invoice": sent})

        invoice = client.invoices.create(build_invoice())

        assert isinstance(invoice, SentInvoiceResponse)

    def test_async_create_builds_the_variant(self):
        waiting = _invoice_payload("WAITING_RESPONSE", **ISSUED_FIELDS)
        client = _client_returning({"invoice": waiting}, async_mode=True)

        invoice = asyncio.run(client.invoices.create(build_invoice()))

        assert isinstance(invoice, WaitingInvoiceResponse)

    def test_get_wraps_an_unknown_status_in_a_parse_error(self):
        response = {"invoice": _invoice_payload("PENDING")}
        client = _client_returning(response)

        with pytest.raises(AlegraResponseParseError) as exc_info:
            client.invoices.get("any-id")

        assert exc_info.value.response == response
