from typing import Callable, Dict

from pydantic import BaseModel, ValidationError

from alegra.exceptions import AlegraApiError, AlegraResponseParseError


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
        """Parse API response and return validated model instance."""
        try:
            # Get the expected response key from configuration
            response_key = self.actions_config[action].get("response_key")

            if response_key:
                # Check if expected response key exists in response
                if response_key not in response:
                    # Provide detailed error information
                    error_details = []
                    if response.get("message"):
                        error_details.append(f"API message: {response.get('message')}")
                    if response.get("errors"):
                        error_details.append(f"API errors: {response.get('errors')}")
                    if response.get("error"):
                        error_details.append(f"API error: {response.get('error')}")

                    error_msg = f"Expected response key '{response_key}' not found in API response for action '{action}' on endpoint '{self.endpoint}'"
                    if error_details:
                        error_msg += f". {'. '.join(error_details)}"
                    else:
                        error_msg += f". Available keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}"

                    raise AlegraApiError(error_msg, response=response)

                response_data = response.get(response_key)
            else:
                response_data = response

            # Get the model class for validation
            model_class = self.actions_config[action].get("response_model")
            if not model_class:
                # If no response model is configured, return raw data
                return response_data

            # Validate response data against the model
            try:
                return model_class.model_validate(response_data)
            except ValidationError as e:
                error_msg = f"Failed to validate response data for action '{action}' on endpoint '{self.endpoint}'"
                error_msg += f". Validation errors: {e.errors()}"
                raise AlegraResponseParseError(error_msg, str(response_data), e)

        except (KeyError, AttributeError) as e:
            error_msg = f"Configuration error for action '{action}' on endpoint '{self.endpoint}': {str(e)}"
            raise AlegraApiError(error_msg, response=response)

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

        # Handle different success status codes for DELETE
        if hasattr(response, "status_code"):
            return response.status_code in [200, 204]
        elif isinstance(response, dict) and "status_code" in response:
            return response["status_code"] in [200, 204]
        else:
            # If we get here, it means the request was successful (no exception raised)
            return True

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
