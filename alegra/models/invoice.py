from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field

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


class ApiError(BaseModel):
    code: str | None = None
    message: str


class InvoiceResponse(BaseModel):
    """Fields common to every invoice response.

    The variant for a given status is chosen by `AnyInvoiceResponse`; validating
    through this base class returns the base, not a variant.
    """

    id: str
    companyIdentification: str
    customerIdentification: str
    type: str
    date: datetime
    prefix: str | None = None
    number: int
    fullNumber: str
    status: Literal["REGISTERED", "WAITING_RESPONSE", "SENT", "FAILED"]
    cufe: str | None = None
    qrCodeContent: str | None = None
    xmlFileName: str | None = None
    zipFileName: str | None = None
    legalStatus: str | None = None
    governmentResponse: GovernmentResponse | None = None
    errors: list[ApiError] | None = None


class RegisteredInvoiceResponse(InvoiceResponse):
    status: Literal["REGISTERED"]


class _IssuedInvoiceResponse(InvoiceResponse):
    cufe: str
    qrCodeContent: str
    xmlFileName: str
    zipFileName: str


class WaitingInvoiceResponse(_IssuedInvoiceResponse):
    status: Literal["WAITING_RESPONSE"]


class SentInvoiceResponse(_IssuedInvoiceResponse):
    status: Literal["SENT"]
    legalStatus: str
    governmentResponse: GovernmentResponse


class FailedInvoiceResponse(InvoiceResponse):
    status: Literal["FAILED"]


AnyInvoiceResponse = Annotated[
    Union[
        RegisteredInvoiceResponse,
        WaitingInvoiceResponse,
        SentInvoiceResponse,
        FailedInvoiceResponse,
    ],
    Field(discriminator="status"),
]


class FileResponse(BaseModel):
    content: str
