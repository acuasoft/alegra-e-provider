from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

from alegra.models.customer import Customer
from alegra.models.invoice import (
    CompanyID,
    DiscountOrCharge,
    GovernmentResponse,
    Item,
    Payment,
    TotalAmounts,
)


class AssociatedDocuments(BaseModel):
    date: str
    documentType: str
    number: int
    prefix: str
    uuid: str


class BaseNote(BaseModel):
    associatedDocuments: AssociatedDocuments
    company: CompanyID
    customer: Customer
    prefix: str
    number: int
    note: Optional[str]
    items: List[Item]
    payments: List[Payment]
    discountsAndCharges: List[DiscountOrCharge] = []
    totalAmounts: TotalAmounts


class CreditNote(BaseNote):
    class CreditNoteType(str, Enum):
        STANDARD = "91"
        STANDARD_NO_REFERENCE = "91-22"
        EXPORT = "02"

    class CreditNoteConcept(str, Enum):
        PARTIAL_RETURN = "1"
        CANCELLATION = "2"
        DISCOUNT = "3"
        PRICE_ADJUSTMENT = "4"
        OTHER = "5"

    documentType: CreditNoteType
    conceptCode: CreditNoteConcept


class DebitNote(BaseNote):
    class DebitNoteConcept(Enum):
        INTEREST = "1"
        BILLABLE_EXPENSES = "2"
        VALUE_CHANGE = "3"
        OTHER = "4"

    conceptCode: DebitNoteConcept


class NoteResponse(BaseModel):
    id: str
    companyIdentification: str
    customerIdentification: Optional[str]
    type: str
    cude: str
    date: datetime
    prefix: str
    number: int
    fullNumber: str
    status: str
    legalStatus: str
    governmentResponse: GovernmentResponse
    xmlFileName: str
    zipFileName: str
    qrCodeContent: str
