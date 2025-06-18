import json

import httpx
import requests

from alegra.config import ApiConfig
from alegra.exceptions import (
    AlegraAuthenticationError,
    AlegraAuthorizationError,
    AlegraHttpError,
    AlegraNotFoundError,
    AlegraRateLimitError,
    AlegraResponseParseError,
    AlegraServerError,
    AlegraValidationError,
)
from alegra.models.company import Company
from alegra.models.dian import DianResource
from alegra.models.invoice import FileResponse, Invoice, InvoiceResponse
from alegra.models.note import CreditNote, DebitNote, NoteResponse
from alegra.models.payroll import Payroll
from alegra.models.test_set import TestSet
from alegra.resources.factory import ResourceFactory


class ApiClient:
    def __init__(self, config: ApiConfig, async_mode=False):
        self.config = config
        self.base_url = self.config.get_base_url()
        self.async_mode = async_mode
        self._initialize_resources()

    def _handle_response(self, response, url: str = None):
        """Handle HTTP response and raise appropriate exceptions for errors."""
        status_code = response.status_code

        # Check for HTTP errors
        if status_code >= 400:
            response_text = response.text

            # Create specific exception based on status code
            if status_code == 401:
                raise AlegraAuthenticationError(
                    "Authentication failed. Please check your API key.",
                    status_code,
                    response_text,
                    url,
                )
            elif status_code == 403:
                raise AlegraAuthorizationError(
                    "Access forbidden. You don't have permission to access this resource.",
                    status_code,
                    response_text,
                    url,
                )
            elif status_code == 404:
                raise AlegraNotFoundError(
                    "Resource not found.", status_code, response_text, url
                )
            elif status_code == 422:
                raise AlegraValidationError(
                    "Validation error. Please check your request data.",
                    status_code,
                    response_text,
                )
            elif status_code == 429:
                raise AlegraRateLimitError(
                    "Rate limit exceeded. Please try again later.",
                    status_code,
                    response_text,
                    url,
                )
            elif status_code >= 500:
                raise AlegraServerError(
                    "Server error occurred. Please try again later.",
                    status_code,
                    response_text,
                    url,
                )
            else:
                raise AlegraHttpError(
                    "HTTP error occurred", status_code, response_text, url
                )

        # Try to parse JSON response
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as e:
            # For successful responses that aren't JSON (like 204 No Content)
            if status_code < 400:
                return {"status_code": status_code}
            else:
                raise AlegraResponseParseError(
                    "Unable to parse response as JSON", response.text, e
                )

    async def _async_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.config.api_key}"}, timeout=30.0
        ) as client:
            try:
                response = await client.request(method, url, **kwargs)
                return self._handle_response(response, url)
            except httpx.RequestError as e:
                raise AlegraHttpError(
                    f"Network error occurred: {str(e)}", None, str(e), url
                )

    def _sync_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint}"
        with requests.Session() as session:
            session.headers.update(
                {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Accept": "application/json",
                }
            )
            try:
                response = session.request(method, url, **kwargs)
                return self._handle_response(response, url)
            except requests.RequestException as e:
                raise AlegraHttpError(
                    f"Network error occurred: {str(e)}", None, str(e), url
                )

    def _request(self, method, endpoint, **kwargs):
        if self.async_mode:
            return self._async_request(method, endpoint, **kwargs)
        else:
            return self._sync_request(method, endpoint, **kwargs)

    def _initialize_resources(self):
        self.company = ResourceFactory(
            self,
            "company",
            self._request,
            {
                "get": {
                    "model": Company,
                    "response_model": Company,
                    "response_key": "company",
                },
                "update": {
                    "model": Company,
                    "response_model": Company,
                    "response_key": "company",
                },
            },
        )
        self.companies = ResourceFactory(
            self,
            "companies",
            self._request,
            {
                "create": {
                    "model": Company,
                    "response_model": Company,
                    "response_key": "company",
                },
                "get": {
                    "model": Company,
                    "response_model": Company,
                    "response_key": "company",
                },
                "update": {
                    "model": Company,
                    "response_model": Company,
                    "response_key": "company",
                },
                "list": {
                    "model": Company,
                    "response_model": Company,
                    "response_key": "companies",
                },
            },
        )
        self.payrolls = ResourceFactory(
            self,
            "payrolls",
            self._request,
            {
                "create": {"model": Payroll, "response_key": "payroll"},
                "get": {"model": Payroll, "response_key": "payroll"},
                "update": {"model": Payroll, "response_key": "payroll"},
                "list": {"model": Payroll, "response_key": "payrolls"},
                "perform__replace": {"model": Payroll, "response_key": "payroll"},
                "perform__cancel": {"model": Payroll, "response_key": "payroll"},
            },
        )
        self.dian = ResourceFactory(
            self,
            "dian",
            self._request,
            {"list": {"model": DianResource, "response_key": "dian"}},
        )
        self.test_sets = ResourceFactory(
            self,
            "test-sets",
            self._request,
            {
                "create": {"model": TestSet, "response_key": "test_set"},
                "get": {"model": TestSet, "response_key": "test_set"},
            },
        )
        self.invoices = ResourceFactory(
            self,
            "invoices",
            self._request,
            {
                "create": {
                    "model": Invoice,
                    "response_model": InvoiceResponse,
                    "response_key": "invoice",
                },
                "get": {
                    "model": Invoice,
                    "response_model": InvoiceResponse,
                    "response_key": "invoice",
                },
                "perform__file_xml": {
                    "model": FileResponse,
                    "endpoint_suffix": "files/XML",
                    "response_model": FileResponse,
                    "response_key": "file",
                },
                "list": {
                    "model": InvoiceResponse,
                    "response_model": InvoiceResponse,
                    "response_key": "invoices",
                },
            },
        )
        self.credit_notes = ResourceFactory(
            self,
            "credit-notes",
            self._request,
            {
                "create": {
                    "model": CreditNote,
                    "response_model": NoteResponse,
                    "response_key": "creditNote",
                },
                "get": {
                    "model": CreditNote,
                    "response_model": NoteResponse,
                    "response_key": "creditNote",
                },
                "perform__file_xml": {
                    "model": FileResponse,
                    "endpoint_suffix": "files/XML",
                    "response_model": FileResponse,
                    "response_key": "file",
                },
                "list": {
                    "model": NoteResponse,
                    "response_model": NoteResponse,
                    "response_key": "creditNotes",
                },
            },
        )
        self.debit_notes = ResourceFactory(
            self,
            "debit-notes",
            self._request,
            {
                "create": {
                    "model": DebitNote,
                    "response_model": NoteResponse,
                    "response_key": "debitNote",
                },
                "get": {
                    "model": DebitNote,
                    "response_model": NoteResponse,
                    "response_key": "debitNote",
                },
                "perform__file_xml": {
                    "model": FileResponse,
                    "endpoint_suffix": "files/XML",
                    "response_model": FileResponse,
                    "response_key": "file",
                },
                "list": {
                    "model": NoteResponse,
                    "response_model": NoteResponse,
                    "response_key": "debitNotes",
                },
            },
        )
