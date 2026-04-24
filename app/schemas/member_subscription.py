from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import SubscriptionStatusEnum


class SubscriptionCreate(SQLModel):
    member_id: UUID
    plan_id: UUID
    start_date: Optional[date] = None


class SubscriptionUpdate(SQLModel):
    notes: Optional[str] = None


class SubscriptionResponse(SQLModel):
    id: UUID
    member_id: UUID
    plan_id: UUID
    start_date: date
    end_date: date
    status: SubscriptionStatusEnum
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    created_at: datetime
