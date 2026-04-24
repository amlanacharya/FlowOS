from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class PlanCreate(SQLModel):
    name: str
    duration_days: int
    price: Decimal
    max_freezes_allowed: int = 0
    includes_classes: bool = False
    max_class_sessions: Optional[int] = None
    description: Optional[str] = None


class PlanUpdate(SQLModel):
    name: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[Decimal] = None
    max_freezes_allowed: Optional[int] = None
    includes_classes: Optional[bool] = None
    max_class_sessions: Optional[int] = None
    description: Optional[str] = None


class PlanResponse(SQLModel):
    id: UUID
    branch_id: UUID
    name: str
    duration_days: int
    price: Decimal
    is_active: bool
    created_at: datetime
