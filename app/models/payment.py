from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum, Numeric
from sqlmodel import Field, SQLModel

from app.core.enums import PaymentModeEnum

if TYPE_CHECKING:
    from .branch import Branch
    from .member import Member
    from .member_subscription import MemberSubscription
    from .staff import Staff


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    subscription_id: Optional[UUID] = Field(default=None, foreign_key="member_subscriptions.id")
    invoice_id: Optional[UUID] = Field(default=None, foreign_key="invoices.id", index=True)
    amount: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    mode: PaymentModeEnum = Field(sa_column=Column(Enum(PaymentModeEnum, native_enum=False), nullable=False))
    transaction_reference: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
    received_by_staff_id: UUID = Field(foreign_key="staff.id")
    payment_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.utcnow)
