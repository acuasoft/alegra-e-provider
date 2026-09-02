import asyncio
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
from alegra.resources.base import ApiResource


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
