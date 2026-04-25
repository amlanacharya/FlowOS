from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import ActionTypeEnum, TriggerEventEnum


class AutomationRuleCreate(SQLModel):
    name: str
    trigger_event: TriggerEventEnum
    threshold_days: int = 7
    threshold_amount: Optional[Decimal] = None
    action: ActionTypeEnum


class AutomationRuleUpdate(SQLModel):
    name: Optional[str] = None
    threshold_days: Optional[int] = None
    threshold_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None


class AutomationRuleResponse(SQLModel):
    id: UUID
    branch_id: UUID
    name: str
    trigger_event: TriggerEventEnum
    threshold_days: int
    threshold_amount: Optional[Decimal]
    action: ActionTypeEnum
    is_active: bool
    created_at: datetime


class AutomationRuleList(SQLModel):
    items: List[AutomationRuleResponse]
    total: int
