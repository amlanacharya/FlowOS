from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class WorkoutLog(SQLModel, table=True):
    __tablename__ = "workout_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    workout_date: date_type = Field(default_factory=date_type.today, index=True)
    exercise_name: str = Field(max_length=255)
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[Decimal] = Field(default=None, max_digits=6, decimal_places=2)
    notes: Optional[str] = None
    logged_by_staff_id: Optional[UUID] = Field(default=None, foreign_key="staff.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
