from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import PlanTypeEnum


class PlanCreate(SQLModel):
    name: str
    plan_type: PlanTypeEnum = PlanTypeEnum.MONTHLY
    duration_days: int
    price: Decimal
    registration_fee: Decimal = Decimal("0.00")
    max_freezes_allowed: int = 0
    includes_classes: bool = False
    max_class_sessions: Optional[int] = None
    description: Optional[str] = None


class PlanUpdate(SQLModel):
    name: Optional[str] = None
    plan_type: Optional[PlanTypeEnum] = None
    duration_days: Optional[int] = None
    price: Optional[Decimal] = None
    registration_fee: Optional[Decimal] = None
    max_freezes_allowed: Optional[int] = None
    includes_classes: Optional[bool] = None
    max_class_sessions: Optional[int] = None
    description: Optional[str] = None


class PlanResponse(SQLModel):
    id: UUID
    branch_id: UUID
    name: str
    plan_type: PlanTypeEnum
    duration_days: int
    price: Decimal
    registration_fee: Decimal
    is_active: bool
    created_at: datetime
