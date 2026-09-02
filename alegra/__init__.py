from . import _version
from .exceptions import (
    AlegraApiError,
    AlegraConfigurationError,
    AlegraHttpError,
    AlegraResponseParseError,
)

__version__ = _version.get_versions()["version"]

__all__ = [
    "AlegraApiError",
    "AlegraConfigurationError",
    "AlegraHttpError",
    "AlegraResponseParseError",
]
