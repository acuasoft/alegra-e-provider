class AlegraApiError(Exception):
    """Base class for every error this library raises intentionally."""


class AlegraConfigurationError(AlegraApiError):
    """Raised when an ApiConfig is constructed with invalid values."""


class AlegraHttpError(AlegraApiError):
    """Raised for an HTTP error response, or a network/transport failure.

    status_code is None for network-level failures (no response was received).
    """

    def __init__(self, message, status_code=None, url=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.response = response


class AlegraResponseParseError(AlegraApiError):
    """Raised when a successful response doesn't match what was expected:
    the configured response key is missing, or the data fails model validation.
    """
