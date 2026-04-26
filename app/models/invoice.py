from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum, Numeric
from sqlmodel import Field, SQLModel

from app.core.enums import InvoiceStatusEnum, InvoiceTypeEnum


class Invoice(SQLModel, table=True):
    __tablename__ = "invoices"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    invoice_no: str = Field(max_length=50, unique=True, index=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    subscription_id: Optional[UUID] = Field(default=None, foreign_key="member_subscriptions.id", index=True)
    invoice_type: InvoiceTypeEnum = Field(
        default=InvoiceTypeEnum.NEW_JOIN,
        sa_column=Column(
            Enum(
                InvoiceTypeEnum,
                native_enum=False,
                values_callable=lambda enum_cls: [item.value for item in enum_cls],
            ),
            nullable=False,
        ),
    )
    status: InvoiceStatusEnum = Field(
        default=InvoiceStatusEnum.ISSUED,
        sa_column=Column(
            Enum(
                InvoiceStatusEnum,
                native_enum=False,
                values_callable=lambda enum_cls: [item.value for item in enum_cls],
            ),
            nullable=False,
        ),
    )
    subtotal: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    registration_fee: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    discount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    tax: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    total_amount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    amount_paid: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    amount_due: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    due_date: date = Field(default_factory=date.today)
    notes: Optional[str] = None
    created_by_staff_id: UUID = Field(foreign_key="staff.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
