from datetime import date
from uuid import UUID

from sqlmodel import SQLModel


class ReminderChecklistItem(SQLModel):
    subscription_id: UUID
    member_id: UUID
    member_name: str
    member_phone: str
    end_date: date
    checkpoint_day: int
    checkpoint_label: str
    amount_due: float
