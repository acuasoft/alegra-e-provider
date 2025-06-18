"""Custom exceptions for the Alegra API client."""

import json
from typing import Optional


class AlegraApiError(Exception):
    """Base exception for all Alegra API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class AlegraHttpError(AlegraApiError):
    """Exception raised for HTTP errors from the Alegra API."""

    def __init__(
        self, message: str, status_code: int, response_text: str, url: str = None
    ):
        self.url = url
        self.response_text = response_text

        # Try to parse JSON response for more details
        response_data = None
        try:
            response_data = json.loads(response_text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Create a more descriptive message
        detailed_message = f"HTTP {status_code} error"
        if url:
            detailed_message += f" for {url}"
        detailed_message += f": {message}"

        if response_data:
            if isinstance(response_data, dict):
                if "message" in response_data:
                    detailed_message += f" - API message: {response_data['message']}"
                elif "errors" in response_data:
                    detailed_message += f" - API errors: {response_data['errors']}"

        super().__init__(detailed_message, status_code, response_data)


class AlegraAuthenticationError(AlegraHttpError):
    """Exception raised for authentication errors (401)."""

    pass


class AlegraAuthorizationError(AlegraHttpError):
    """Exception raised for authorization errors (403)."""

    pass


class AlegraNotFoundError(AlegraHttpError):
    """Exception raised for not found errors (404)."""

    pass


class AlegraValidationError(AlegraApiError):
    """Exception raised for validation errors (422)."""

    pass


class AlegraRateLimitError(AlegraHttpError):
    """Exception raised for rate limit errors (429)."""

    pass


class AlegraServerError(AlegraHttpError):
    """Exception raised for server errors (5xx)."""

    pass


class AlegraResponseParseError(AlegraApiError):
    """Exception raised when unable to parse API response."""

    def __init__(
        self, message: str, response_text: str, original_error: Exception = None
    ):
        self.response_text = response_text
        self.original_error = original_error

        detailed_message = f"Failed to parse API response: {message}"
        if original_error:
            detailed_message += f" (Original error: {str(original_error)})"

        super().__init__(detailed_message)


class AlegraConfigurationError(AlegraApiError):
    """Exception raised for configuration errors."""

    pass
