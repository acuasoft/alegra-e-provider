from pydantic import BaseModel, field_validator

from alegra.exceptions import AlegraConfigurationError

BASE_URLS = {
    "sandbox": "https://sandbox-api.alegra.com/e-provider/col/v1",
    "production": "https://api.alegra.com/e-provider/col/v1",
}


class ApiConfig(BaseModel):
    api_key: str
    environment: str

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        if not v.strip():
            raise AlegraConfigurationError("api_key cannot be blank.")
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        if v not in BASE_URLS:
            raise AlegraConfigurationError(
                f"Invalid environment '{v}'. Choose one of: {', '.join(BASE_URLS)}."
            )
        return v

    def get_base_url(self):
        return BASE_URLS[self.environment]
