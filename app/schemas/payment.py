from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import PaymentModeEnum


class PaymentCreate(SQLModel):
    member_id: UUID
    subscription_id: Optional[UUID] = None
    amount: Decimal
    mode: PaymentModeEnum
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    payment_date: Optional[date] = None


class PaymentResponse(SQLModel):
    id: UUID
    branch_id: UUID
    member_id: UUID
    subscription_id: Optional[UUID]
    amount: Decimal
    mode: PaymentModeEnum
    payment_date: date
    created_at: datetime
