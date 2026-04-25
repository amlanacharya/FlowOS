from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum, Numeric
from sqlmodel import Field, SQLModel

from app.core.enums import ActionTypeEnum, TriggerEventEnum


class AutomationRule(SQLModel, table=True):
    __tablename__ = "automation_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    name: str = Field(max_length=255)
    trigger_event: TriggerEventEnum = Field(sa_column=Column(Enum(TriggerEventEnum, native_enum=False), nullable=False))
    threshold_days: int = Field(default=7)
    threshold_amount: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(10, 2), nullable=True))
    action: ActionTypeEnum = Field(sa_column=Column(Enum(ActionTypeEnum, native_enum=False), nullable=False))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
