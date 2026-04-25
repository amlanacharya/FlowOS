from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class WorkoutLogCreate(SQLModel):
    member_id: UUID
    date: Optional[date] = None
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[Decimal] = None
    notes: Optional[str] = None


class WorkoutLogResponse(SQLModel):
    id: UUID
    member_id: UUID
    branch_id: UUID
    workout_date: date
    exercise_name: str
    sets: Optional[int]
    reps: Optional[int]
    weight_kg: Optional[Decimal]
    notes: Optional[str]
    logged_by_staff_id: Optional[UUID]
    created_at: datetime


class WorkoutProgressPoint(SQLModel):
    workout_date: date
    sessions: int
    max_weight_kg: Optional[Decimal]
