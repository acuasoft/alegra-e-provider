import asyncio
import traceback
from unittest.mock import patch

import httpx
import pytest
import requests
from pydantic import BaseModel

from alegra.client import ApiClient
from alegra.config import ApiConfig
from alegra.exceptions import (
    AlegraApiError,
    AlegraConfigurationError,
    AlegraHttpError,
    AlegraResponseParseError,
)
from alegra.models.company import Company
from alegra.models.invoice import AnyInvoiceResponse
from alegra.resources.base import ApiResource
from tests.invoice_payloads import ISSUED_FIELDS, _invoice_payload


class Widget(BaseModel):
    id: str


class TestApiConfigValidation:
    def test_invalid_environment_raises_configuration_error(self):
        with pytest.raises(AlegraConfigurationError):
            ApiConfig(api_key="some-key", environment="staging")

    def test_blank_api_key_raises_configuration_error(self):
        with pytest.raises(AlegraConfigurationError):
            ApiConfig(api_key="   ", environment="sandbox")


class TestSyncRequestErrorHandling:
    def setup_method(self):
        self.client = ApiClient(ApiConfig(api_key="key", environment="sandbox"))

    def test_error_response_raises_http_error_with_status_code(self):
        fake_response = requests.Response()
        fake_response.status_code = 404
        fake_response._content = b'{"message": "not found"}'

        with patch.object(requests.Session, "request", return_value=fake_response):
            with pytest.raises(AlegraHttpError) as exc_info:
                self.client._request("GET", "invoices/missing")

        assert exc_info.value.status_code == 404

    def test_connection_error_raises_http_error_with_no_status_code(self):
        with patch.object(
            requests.Session,
            "request",
            side_effect=requests.ConnectionError("boom"),
        ):
            with pytest.raises(AlegraHttpError) as exc_info:
                self.client._request("GET", "invoices/missing")

        assert exc_info.value.status_code is None


class TestAsyncRequestErrorHandling:
    def setup_method(self):
        self.client = ApiClient(
            ApiConfig(api_key="key", environment="sandbox"), async_mode=True
        )

    def test_error_response_raises_http_error_with_status_code(self):
        fake_response = httpx.Response(404, json={"message": "not found"})

        async def fake_request(*args, **kwargs):
            return fake_response

        async def run():
            return await self.client._request("GET", "invoices/missing")

        with patch.object(httpx.AsyncClient, "request", fake_request):
            with pytest.raises(AlegraHttpError) as exc_info:
                asyncio.run(run())

        assert exc_info.value.status_code == 404

    def test_connection_error_raises_http_error_with_no_status_code(self):
        async def fake_request(*args, **kwargs):
            raise httpx.ConnectError("boom")

        async def run():
            return await self.client._request("GET", "invoices/missing")

        with patch.object(httpx.AsyncClient, "request", fake_request):
            with pytest.raises(AlegraHttpError) as exc_info:
                asyncio.run(run())

        assert exc_info.value.status_code is None


class TestParseResponse:
    def setup_method(self):
        self.resource = ApiResource(
            client=None,
            endpoint="widgets",
            request_method=None,
            actions_config={
                "get": {"response_key": "widget", "response_model": Widget},
            },
        )

    def test_missing_response_key_raises_parse_error(self):
        with pytest.raises(AlegraResponseParseError):
            self.resource._parse_response({"unexpected": "shape"}, "get")

    def test_failed_model_validation_raises_parse_error(self):
        with pytest.raises(AlegraResponseParseError):
            self.resource._parse_response({"widget": {"id": 123, "extra": True}}, "get")

    def test_list_accepts_the_model_key(self):
        resource = ApiResource(
            client=None,
            endpoint="widgets",
            request_method=lambda method, endpoint, **kwargs: {
                "widgets": [{"id": "a"}]
            },
            actions_config={"list": {"response_key": "widgets", "model": Widget}},
        )

        assert resource.list() == [Widget(id="a")]


class TestParseErrorsCarryNoResponseData:
    def setup_method(self):
        self.resource = ApiResource(
            client=None,
            endpoint="invoices",
            request_method=None,
            actions_config={
                "get": {"response_key": "invoice", "response_model": AnyInvoiceResponse}
            },
        )

    def _parse_error(self, response):
        with pytest.raises(AlegraResponseParseError) as exc_info:
            self.resource._parse_response(response, "get")
        return exc_info.value

    def test_message_names_status_id_and_field(self):
        response = {"invoice": _invoice_payload("WAITING_RESPONSE")}

        message = str(self._parse_error(response))

        assert "status=WAITING_RESPONSE" in message
        assert "id=01JMZ1SMYJW51VAC1G2W38PJVR" in message
        assert "WAITING_RESPONSE.cufe: Field required" in message
        assert "222222222222" not in message
        assert "NumFac" not in message

    def test_values_never_reach_the_traceback(self):
        payload = _invoice_payload(
            "WAITING_RESPONSE", **ISSUED_FIELDS, customerIdentification=123456789
        )
        response = {"invoice": payload}

        exc = self._parse_error(response)

        assert "123456789" not in "".join(traceback.format_exception(exc))
        assert exc.__cause__ is None
        assert exc.__suppress_context__ is True

    @pytest.mark.parametrize("status", ["SECRET-222222222222", "x" * 5000])
    def test_unknown_status_is_not_echoed(self, status):
        response = {"invoice": _invoice_payload(status)}

        message = str(self._parse_error(response))

        assert (
            "status: not one of 'REGISTERED', 'WAITING_RESPONSE', 'SENT', 'FAILED'"
            in message
        )
        assert "222222222222" not in message
        assert "x" * 20 not in message

    def test_errors_are_capped_at_five(self):
        payload = _invoice_payload("REGISTERED")
        for field in (
            "id",
            "companyIdentification",
            "customerIdentification",
            "type",
            "date",
            "number",
            "fullNumber",
        ):
            del payload[field]
        response = {"invoice": payload}

        message = str(self._parse_error(response))

        assert message.endswith("(+2 more)")

    def test_missing_key_names_keys_not_values(self):
        response = {"errors": [{"message": "Invoice 900123456 not found"}]}

        message = str(self._parse_error(response))

        assert "errors" in message
        assert "900123456" not in message

    def test_missing_key_message_is_bounded(self):
        response = {f"{i:0100d}": i for i in range(200)}

        message = str(self._parse_error(response))

        assert len(message) < 1500
        assert message.endswith("(+190 more)")

    @pytest.mark.parametrize("response", [["x"], None, "invoice", ["invoice"]])
    def test_non_object_response_raises_parse_error(self, response):
        with pytest.raises(AlegraResponseParseError):
            self.resource._parse_response(response, "get")

    def test_empty_response_says_there_are_no_keys(self):
        message = str(self._parse_error({}))

        assert message.endswith("; got no keys")

    def test_list_error_keeps_the_item_index(self):
        registered = _invoice_payload("REGISTERED")
        bad_payload = _invoice_payload("SECRET-999")
        client = ApiClient(ApiConfig(api_key="key", environment="sandbox"))
        client.invoices.resource.request_method = lambda method, endpoint, **kw: {
            "invoices": [registered, bad_payload]
        }

        with pytest.raises(AlegraResponseParseError) as exc_info:
            client.invoices.list()

        message = str(exc_info.value)
        assert "1.status: not one of" in message
        assert "SECRET-999" not in message

    def test_email_validation_reason_is_not_echoed(self):
        payload = {
            "name": "Acme",
            "identification": "900123456",
            "dv": "1",
            "useAlegraCertificate": True,
            "organizationType": 1,
            "identificationType": "31",
            "taxCode": {"id": "01"},
            "email": "a@[1.2.3]",
            "address": {},
        }
        resource = ApiResource(
            client=None,
            endpoint="companies",
            request_method=lambda method, endpoint, **kw: {"company": payload},
            actions_config={
                "get": {"response_key": "company", "response_model": Company}
            },
        )

        with pytest.raises(AlegraResponseParseError) as exc_info:
            resource.get("1")

        message = str(exc_info.value)
        assert "email: value is not a valid email address" in message
        assert "1.2.3" not in message

    def test_body_is_kept_on_the_exception(self):
        response = {"invoice": _invoice_payload("WAITING_RESPONSE")}

        assert self._parse_error(response).response == response

    def test_odd_status_or_id_is_left_out(self):
        payload = _invoice_payload("WAITING_RESPONSE", id="x" * 100)
        response = {"invoice": payload}

        assert "id=" not in str(self._parse_error(response))


class TestListExtraction:
    def _resource(self, response, **config):
        return ApiResource(
            client=None,
            endpoint="widgets",
            request_method=lambda method, endpoint, **kwargs: response,
            actions_config={"list": {"model": Widget, **config}},
        )

    def test_missing_key_raises_parse_error(self):
        resource = self._resource({"other": []}, response_key="widgets")

        with pytest.raises(AlegraResponseParseError):
            resource.list()

    def test_without_response_key_the_whole_response_is_the_list(self):
        resource = self._resource([{"id": "a"}])

        assert resource.list() == [Widget(id="a")]

    def test_null_list_raises_parse_error_without_empty_location(self):
        resource = self._resource({"widgets": None}, response_key="widgets")

        with pytest.raises(AlegraResponseParseError) as exc_info:
            resource.list()

        assert '": : "' not in str(exc_info.value)

    def test_invalid_item_is_located_by_index(self):
        resource = self._resource(
            {"widgets": [{"id": "a"}, {}]}, response_key="widgets"
        )

        with pytest.raises(AlegraResponseParseError) as exc_info:
            resource.list()

        assert "1.id: Field required" in str(exc_info.value)


class TestDelete:
    def setup_method(self):
        self.client = ApiClient(ApiConfig(api_key="key", environment="sandbox"))
        self.resource = ApiResource(
            client=self.client,
            endpoint="widgets",
            request_method=self.client._request,
            actions_config={"delete": {}},
        )

    def test_delete_returns_true_on_success(self):
        fake_response = requests.Response()
        fake_response.status_code = 204
        fake_response._content = b""

        with patch.object(requests.Session, "request", return_value=fake_response):
            assert self.resource.delete("some-id") is True

    def test_delete_raises_http_error_on_failure(self):
        fake_response = requests.Response()
        fake_response.status_code = 404
        fake_response._content = b'{"message": "not found"}'

        with patch.object(requests.Session, "request", return_value=fake_response):
            with pytest.raises(AlegraHttpError):
                self.resource.delete("some-id")


class TestPackageExports:
    def test_exceptions_are_importable_from_top_level_package(self):
        import alegra

        assert alegra.AlegraApiError is AlegraApiError
        assert alegra.AlegraConfigurationError is AlegraConfigurationError
        assert alegra.AlegraHttpError is AlegraHttpError
        assert alegra.AlegraResponseParseError is AlegraResponseParseError
