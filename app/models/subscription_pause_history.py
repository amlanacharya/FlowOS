from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SubscriptionPauseHistory(SQLModel, table=True):
    __tablename__ = "subscription_pause_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    subscription_id: UUID = Field(foreign_key="member_subscriptions.id", index=True)
    pause_date: date
    resume_date: Optional[date] = None
    pause_days: int = 0
    reason: Optional[str] = None
    created_by_staff_id: UUID = Field(foreign_key="staff.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
