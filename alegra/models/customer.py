from typing import Optional

from pydantic import BaseModel, EmailStr

from alegra.models.address import Address
from alegra.models.company import TaxCode


class Customer(BaseModel):
    name: str
    taxCode: TaxCode
    organizationType: int
    identificationType: str
    identificationNumber: Optional[str]
    dv: Optional[str]
    email: Optional[EmailStr] = ""
    address: Optional[Address] = None
    phone: str = ""
