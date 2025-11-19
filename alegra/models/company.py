import re
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from .address import Address

IDENTIFICATION_TYPES = [
    "11",
    "12",
    "13",
    "21",
    "22",
    "31",
    "41",
    "42",
    "47",
    "48",
    "50",
    "91",
]


class Webhook(BaseModel):
    url: str = ""
    headers: Dict[str, str] = {}
    status: str = ""


class Webhooks(BaseModel):
    general: Dict[str, Webhook] = {}
    payrolls: Dict[str, Webhook] = {}


class Certificate(BaseModel):
    name: str = ""
    extension: str = ""
    content: str = ""
    password: str = ""
    issuerName: str = ""
    startDate: str = ""
    endDate: str = ""
    serialNumber: str = ""


class GovernmentStatus(BaseModel):
    payrolls: str = ""


class NotificationByEmail(BaseModel):
    enabled: bool = False


class TaxCode(BaseModel):
    class TaxType(str, Enum):
        IVA = "01"
        INC = "04"
        IVA_AND_INC = "ZA"
        NOT_APPLICABLE = "ZZ"

    id: TaxType


class Company(BaseModel):
    id: Optional[str] = None
    name: str
    tradeName: Optional[str] = None
    identification: str
    dv: str
    useAlegraCertificate: bool
    organizationType: int
    identificationType: str
    regimeCode: str = ""
    taxCode: TaxCode
    email: EmailStr
    phone: Optional[str] = ""
    address: Address
    governmentStatus: Optional[GovernmentStatus] = None
    certificate: Optional[Certificate] = None
    webhooks: Optional[Webhooks] = None
    notificationByEmail: Optional[NotificationByEmail] = None

    @field_validator("dv")
    def validate_dv(cls, v):
        if not re.match(r"^([0-9]{1})$", v):
            raise ValueError("dv must be a single digit")
        return v

    @field_validator("identificationType")
    def validate_identificationType(cls, v):
        if len(v) > 2:
            raise ValueError("identificationType must have a maximum length of 2")
        if v not in IDENTIFICATION_TYPES:
            raise ValueError(
                f"identificationType must be one of the allowed values: {', '.join(IDENTIFICATION_TYPES)}"
            )
        return v

    @field_validator("organizationType")
    def validate_organizationType(cls, v):
        if v not in [1, 2]:
            raise ValueError("organizationType must be 1 or 2")
        return v

    @model_validator(mode="before")
    def check_certificate(cls, values):
        use_alegra_certificate = values.get("useAlegraCertificate")
        if use_alegra_certificate:
            return values

        certificate = values.get("certificate")
        if not use_alegra_certificate and not certificate:
            raise ValueError(
                "certificate is required when useAlegraCertificate is False"
            )
        return values
