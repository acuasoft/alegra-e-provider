from typing import Callable, Dict

from pydantic import BaseModel


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

    def _parse_response(self, response, action: str):
        response_key = self.actions_config[action].get("response_key")
        if response_key:
            if response_key not in response:
                if response.get("message"):
                    raise ValueError(response.get("message"))
                if response.get("errors"):
                    raise ValueError(response.get("errors"))
                raise ValueError(f"Response key '{response_key}' not found in response")
            response_data = response.get(response_key, response)
        else:
            response_data = response
        model = self.actions_config[action]["response_model"]
        return model.model_validate(response_data)

    def _prepare_data(self, data: BaseModel):
        if data is None:
            return {}
        data = data.model_dump()
        if "customer" in data:
            customer_data = data["customer"]
            if customer_data["dv"] is None:
                del customer_data["dv"]
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
        response = self.request_method("DELETE", endpoint)
        return response.status_code == 204

    def list(self, params=None):
        action = "list"
        if not self._is_action_allowed(action):
            raise NotImplementedError(
                f"The action 'list' is not allowed for {self.endpoint}"
            )
        response = self.request_method("GET", self.endpoint, params=params)
        return [
            self.actions_config[action]["model"].model_validate(item)
            for item in response.get(
                self.actions_config[action].get("response_key", [])
            )
        ]

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
