from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from alegra.models.customer import Customer


class Resolution(BaseModel):
    resolutionNumber: str
    prefix: str | None = None
    minNumber: int
    maxNumber: int
    startDate: str
    endDate: str
    technicalKey: str


class Taxes(BaseModel):
    taxCode: str
    taxAmount: float
    taxPercentage: str
    taxableAmount: float


class Item(BaseModel):
    code: str
    description: str
    price: float
    quantity: int
    unitCode: str
    note: Optional[str] = ""
    subtotal: float
    taxAmount: float
    total: float
    discount: float
    discountAmount: float
    taxes: List[Taxes] = []


class Payment(BaseModel):
    paymentForm: str
    paymentMethod: str
    paymentDueDate: str


class DiscountOrCharge(BaseModel):
    isCharge: bool
    reason: str
    reasonCode: str
    percentageAmount: float
    amount: float
    baseAmount: float


class TotalAmounts(BaseModel):
    grossTotal: float
    taxableTotal: float
    taxTotal: float
    discountTotal: float
    chargeTotal: float
    advanceTotal: float
    payableTotal: float
    currencyCode: str


class CompanyID(BaseModel):
    id: str


class Invoice(BaseModel):
    documentType: str
    resolution: Resolution
    company: CompanyID
    customer: Customer
    number: int
    note: Optional[str]
    items: List[Item]
    payments: List[Payment]
    discountsAndCharges: List[DiscountOrCharge] = []
    totalAmounts: TotalAmounts


class GovernmentResponse(BaseModel):
    code: str
    message: str
    errorMessages: List[str]


class InvoiceResponse(BaseModel):
    """Response for a created/fetched invoice.

    While status is "WAITING_RESPONSE", the DIAN hasn't ruled on the
    document yet and legalStatus and the fields derived from that ruling
    (cufe, governmentResponse, xmlFileName, zipFileName, qrCodeContent)
    are not yet available.
    """

    id: str
    companyIdentification: str
    customerIdentification: str
    type: str
    cufe: str | None = None
    date: datetime
    prefix: str | None = None
    number: int
    fullNumber: str
    status: str
    legalStatus: str | None = None
    governmentResponse: GovernmentResponse | None = None
    xmlFileName: str | None = None
    zipFileName: str | None = None
    qrCodeContent: str | None = None


class FileResponse(BaseModel):
    content: str
