from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import SubscriptionStatusEnum

if TYPE_CHECKING:
    from .branch import Branch
    from .member import Member
    from .staff import Staff


class MemberSubscription(SQLModel, table=True):
    __tablename__ = "member_subscriptions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    plan_id: UUID = Field(foreign_key="membership_plans.id")
    start_date: date
    end_date: date
    status: SubscriptionStatusEnum = Field(
        default=SubscriptionStatusEnum.ACTIVE,
        sa_column=Column(Enum(SubscriptionStatusEnum, native_enum=False), nullable=False)
    )
    total_amount: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    amount_paid: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    amount_due: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    freeze_days_used: int = Field(default=0)
    freeze_start: Optional[date] = None
    total_pause_days: int = Field(default=0)
    last_pause_date: Optional[date] = None
    last_resume_date: Optional[date] = None
    notes: Optional[str] = None
    created_by_staff_id: UUID = Field(foreign_key="staff.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    member: Optional["Member"] = Relationship(back_populates="subscriptions")
    branch: Optional["Branch"] = Relationship(back_populates="member_subscriptions")
    created_by_staff: Optional["Staff"] = Relationship(back_populates="subscriptions_created")
