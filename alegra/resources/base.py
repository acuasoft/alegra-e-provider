import re
from functools import lru_cache
from typing import Any, Callable, Dict, List

from pydantic import BaseModel, TypeAdapter, ValidationError

from alegra.exceptions import AlegraResponseParseError


@lru_cache(maxsize=None)
def _adapter(tp):
    return TypeAdapter(tp)


_MAX_ERRORS = 5
_MAX_KEYS = 10
_MAX_KEY_LENGTH = 64
_MAX_MESSAGE_LENGTH = 200
_STATUS_PATTERN = re.compile(r"[A-Z_]{1,32}")
_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}")


def _more(total: int, shown: int):
    return f" (+{total - shown} more)" if total > shown else ""


def _describe_error(error: dict):
    location = ".".join(str(part) for part in error["loc"])
    if error["type"] == "union_tag_invalid":
        ctx = error["ctx"]
        discriminator = str(ctx["discriminator"]).strip("'\"")
        message = f"{discriminator}: not one of {ctx['expected_tags']}"
        return f"{location}.{message}" if location else message
    message = error["msg"]
    if error["type"] == "value_error":
        message = message.split(": ", 1)[0]
    message = message[:_MAX_MESSAGE_LENGTH]
    return f"{location}: {message}" if location else message


def _describe_keys(keys: List[str], shown: List[str]):
    if not keys:
        return "no keys"
    return f"keys: {', '.join(shown)}{_more(len(keys), len(shown))}"


def _describe_subject(data: Any):
    if not isinstance(data, dict):
        return ""
    status, resource_id = data.get("status"), data.get("id")
    parts = []
    if isinstance(status, str) and _STATUS_PATTERN.fullmatch(status):
        parts.append(f"status={status}")
    if isinstance(resource_id, str) and _ID_PATTERN.fullmatch(resource_id):
        parts.append(f"id={resource_id}")
    return f" ({', '.join(parts)})" if parts else ""


def _model_mismatch_error(
    action: str,
    endpoint: str,
    error: ValidationError,
    data: Any,
    response: Any,
):
    """Builds the parse error for data that failed model validation.

    The message names the failing fields and never includes values from the
    response; pydantic's own text is not used because it echoes the input.

    Args:
        action: The resource action being parsed.
        endpoint: The resource endpoint.
        error: The validation error raised for the data.
        data: The data that was validated.
        response: The full decoded response body, kept on the exception.

    Returns:
        The exception to raise.
    """
    errors = error.errors(include_url=False, include_input=False)
    shown = errors[:_MAX_ERRORS]
    details = "; ".join(_describe_error(e) for e in shown) + _more(
        len(errors), len(shown)
    )
    return AlegraResponseParseError(
        f"Response for '{action}' on '{endpoint}' didn't match the expected shape"
        f"{_describe_subject(data)}: {details}",
        response=response,
    )


class ApiResource:
    def __init__(
        self,
        client,
        endpoint: str,
        request_method: Callable,
        actions_config: Dict[str, Dict[str, str]],
    ):
        self.client = client
        self.endpoint = endpoint
        self.request_method = request_method
        self.actions_config = actions_config

    def _is_action_allowed(self, action: str):
        return action in self.actions_config

    def _extract(self, response, action: str):
        response_key = self.actions_config[action].get("response_key")
        if not response_key:
            return response
        if not isinstance(response, dict):
            raise AlegraResponseParseError(
                f"Expected a JSON object in response for action '{action}' "
                f"on '{self.endpoint}', got {type(response).__name__}",
                response=response,
            )
        if response_key not in response:
            keys = sorted(str(key) for key in response)
            shown = [key[:_MAX_KEY_LENGTH] for key in keys[:_MAX_KEYS]]
            raise AlegraResponseParseError(
                f"Expected key '{response_key}' in response for action '{action}' "
                f"on '{self.endpoint}'; got {_describe_keys(keys, shown)}",
                response=response,
            )
        return response[response_key]

    def _validate(self, model, data, action: str, response):
        try:
            return _adapter(model).validate_python(data)
        except ValidationError as e:
            raise _model_mismatch_error(
                action, self.endpoint, e, data, response
            ) from None

    def _parse_response(self, response, action: str):
        data = self._extract(response, action)
        model = self.actions_config[action]["response_model"]
        return self._validate(model, data, action, response)

    def _prepare_data(self, data: BaseModel):
        if data is None:
            return {}
        data = data.model_dump()
        if "customer" in data:
            customer_data = data["customer"]
            if customer_data["dv"] is None:
                del customer_data["dv"]

        if "resolution" in data:
            resolution_data = data["resolution"]
            if resolution_data.get("prefix") is None:
                del resolution_data["prefix"]

        return {k: v for k, v in data.items() if v is not None}

    def get(self, resource_id: str):
        action = "get"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The action 'get' is not allowed for {self.endpoint}"
            )
        endpoint = f"{self.endpoint}/{resource_id}"
        response = self.request_method("GET", endpoint)
        return self._parse_response(response, action)

    def create(self, data: BaseModel):
        if self.client.async_mode:
            return self.create_async(data)
        else:
            action = "create"
            if not self._is_action_allowed(action):
                raise NotImplementedError(
                    f"The action 'create' is not allowed for {self.endpoint}"
                )
            response = self.request_method(
                "POST", self.endpoint, json=self._prepare_data(data)
            )
            return self._parse_response(response, action)

    async def create_async(self, data: BaseModel):
        action = "create"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The action 'create' is not allowed for {self.endpoint}"
            )
        response = await self.request_method(
            "POST", self.endpoint, json=self._prepare_data(data)
        )
        return self._parse_response(response, action)

    def update(self, resource_id: str, data: BaseModel):
        action = "update"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The action 'update' is not allowed for {self.endpoint}"
            )
        endpoint = f"{self.endpoint}/{resource_id}"
        response = self.request_method("PATCH", endpoint, json=self._prepare_data(data))
        return self._parse_response(response, action)

    def delete(self, resource_id: str):
        action = "delete"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The action 'delete' is not allowed for {self.endpoint}"
            )
        endpoint = f"{self.endpoint}/{resource_id}"
        self.request_method("DELETE", endpoint)
        return True

    def list(self, params=None):
        action = "list"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The action 'list' is not allowed for {self.endpoint}"
            )
        response = self.request_method("GET", self.endpoint, params=params)
        config = self.actions_config[action]
        model = config.get("response_model") or config["model"]
        items = self._extract(response, action)
        return self._validate(List[model], items, action, response)

    def perform_subaction(
        self, resource_id: str, subaction: str, data: BaseModel = None
    ):
        action = f"perform__{subaction}"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The subaction '{subaction}' is not allowed for {self.endpoint}"
            )
        endpoint_suffix = self.actions_config[action].get("endpoint_suffix", subaction)
        endpoint = f"{self.endpoint}/{resource_id}/{endpoint_suffix}"

        kwargs = {}
        if data:
            kwargs["json"] = self._prepare_data(data)

        response = self.request_method(
            self._request_method_for_subaction(subaction), endpoint, **kwargs
        )
        return self._parse_response(response, action)

    @staticmethod
    def _request_method_for_subaction(subaction: str):
        return "POST" if subaction in ["replace", "cancel"] else "GET"
