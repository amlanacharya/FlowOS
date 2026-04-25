from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel


class StaffCheckinRequest(SQLModel):
    notes: Optional[str] = None


class StaffCheckoutRequest(SQLModel):
    notes: Optional[str] = None


class StaffCheckinResponse(SQLModel):
    id: UUID
    staff_id: UUID
    branch_id: UUID
    check_in: datetime
    check_out: Optional[datetime]
    date: date
    notes: Optional[str]


class StaffAttendanceListResponse(SQLModel):
    items: List[StaffCheckinResponse]
    total: int


class StaffAttendanceSummary(SQLModel):
    present_today: int
    absent_today: int
    checked_in_now: int
