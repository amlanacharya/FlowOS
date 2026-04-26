from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import PlanTypeEnum

if TYPE_CHECKING:
    from .branch import Branch


class MembershipPlan(SQLModel, table=True):
    __tablename__ = "membership_plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    name: str = Field(max_length=255)
    plan_type: PlanTypeEnum = Field(
        default=PlanTypeEnum.MONTHLY,
        sa_column=Column(
            Enum(
                PlanTypeEnum,
                native_enum=False,
                values_callable=lambda enum_cls: [item.value for item in enum_cls],
            ),
            nullable=False,
        ),
    )
    duration_days: int
    price: Decimal = Field(sa_column=Column(Numeric(10, 2)))
    registration_fee: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    max_freezes_allowed: int = Field(default=0)
    includes_classes: bool = Field(default=False)
    max_class_sessions: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    branch: Optional["Branch"] = Relationship(back_populates="membership_plans")
