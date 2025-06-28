from pydantic import BaseModel, validator

from alegra.exceptions import AlegraConfigurationError


class ApiConfig(BaseModel):
    api_key: str
    environment: str

    @validator("api_key")
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise AlegraConfigurationError("API key cannot be empty")
        return v.strip()

    @validator("environment")
    def validate_environment(cls, v):
        valid_environments = ["sandbox", "production"]
        if v not in valid_environments:
            raise AlegraConfigurationError(
                f"Invalid environment '{v}'. Must be one of: {', '.join(valid_environments)}"
            )
        return v

    def get_base_url(self):
        if self.environment == "sandbox":
            return "https://sandbox-api.alegra.com/e-provider/col/v1"
        elif self.environment == "production":
            return "https://api.alegra.com/e-provider/col/v1"
        else:
            # This should never happen due to the validator, but keeping for safety
            raise AlegraConfigurationError(
                f"Invalid environment '{self.environment}'. Choose 'sandbox' or 'production'."
            )
