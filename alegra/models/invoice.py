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
    id: str
    companyIdentification: str
    customerIdentification: str
    type: str
    cufe: str
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


class FileResponse(BaseModel):
    content: str
