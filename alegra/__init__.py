from . import _version

__version__ = _version.get_versions()["version"]

# Export main classes
from .client import ApiClient
from .config import ApiConfig

# Export exception classes
from .exceptions import (
    AlegraApiError,
    AlegraAuthenticationError,
    AlegraAuthorizationError,
    AlegraConfigurationError,
    AlegraHttpError,
    AlegraNotFoundError,
    AlegraRateLimitError,
    AlegraResponseParseError,
    AlegraServerError,
    AlegraValidationError,
)

# Export commonly used models
from .models.company import Company
from .models.customer import Customer
from .models.invoice import FileResponse, Invoice, InvoiceResponse
from .models.note import CreditNote, DebitNote, NoteResponse
from .models.payroll import Payroll
from .models.test_set import TestSet

__all__ = [
    "ApiClient",
    "ApiConfig",
    "AlegraApiError",
    "AlegraHttpError",
    "AlegraAuthenticationError",
    "AlegraAuthorizationError",
    "AlegraNotFoundError",
    "AlegraValidationError",
    "AlegraRateLimitError",
    "AlegraServerError",
    "AlegraResponseParseError",
    "AlegraConfigurationError",
    "Company",
    "Invoice",
    "InvoiceResponse",
    "FileResponse",
    "CreditNote",
    "DebitNote",
    "NoteResponse",
    "Payroll",
    "Customer",
    "TestSet",
]
