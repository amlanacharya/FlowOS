from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import SubscriptionStatusEnum


class PauseHistoryResponse(SQLModel):
    id: UUID
    subscription_id: UUID
    pause_date: date
    resume_date: Optional[date]
    pause_days: int
    reason: Optional[str]
    created_at: datetime


class MembershipTrackingItem(SQLModel):
    subscription_id: UUID
    member_id: UUID
    member_name: str
    member_phone: str
    plan_id: UUID
    start_date: date
    end_date: date
    status: SubscriptionStatusEnum
    amount_due: float
    total_pause_days: int
    renewal_due_in_days: int


class SubscriptionAdjustmentCreate(SQLModel):
    days_delta: int
    reason: Optional[str] = None


class SubscriptionAdjustmentResponse(SQLModel):
    id: UUID
    subscription_id: UUID
    days_delta: int
    reason: Optional[str]
    created_at: datetime
