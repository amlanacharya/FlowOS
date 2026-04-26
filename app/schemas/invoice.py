from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import InvoiceStatusEnum, InvoiceTypeEnum


class InvoiceCreate(SQLModel):
    member_id: UUID
    subscription_id: Optional[UUID] = None
    invoice_type: InvoiceTypeEnum = InvoiceTypeEnum.NEW_JOIN
    subtotal: Decimal
    registration_fee: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(SQLModel):
    id: UUID
    invoice_no: str
    branch_id: UUID
    member_id: UUID
    subscription_id: Optional[UUID]
    invoice_type: InvoiceTypeEnum
    status: InvoiceStatusEnum
    subtotal: Decimal
    registration_fee: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    due_date: date
    notes: Optional[str]
    created_at: datetime
