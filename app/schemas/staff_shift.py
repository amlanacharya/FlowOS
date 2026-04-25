from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class StaffShiftCreate(SQLModel):
    shift_date: datetime
    shift_start: datetime
    shift_end: datetime
    shift_type: str = "regular"
    notes: Optional[str] = None


class StaffShiftUpdate(SQLModel):
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    shift_type: Optional[str] = None
    notes: Optional[str] = None


class StaffShiftResponse(SQLModel):
    id: UUID
    branch_id: UUID
    staff_id: UUID
    shift_date: datetime
    shift_start: datetime
    shift_end: datetime
    shift_type: str
    notes: Optional[str]
    created_at: datetime


class ShiftComparisonResponse(SQLModel):
    staff_id: UUID
    scheduled_hours: float
    actual_hours: float
    difference: float
    attendance_count: int
