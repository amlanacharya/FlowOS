from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class StaffAttendance(SQLModel, table=True):
    __tablename__ = "staff_attendance"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    staff_id: UUID = Field(foreign_key="staff.id", index=True)
    checked_in_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    checked_out_at: Optional[datetime] = None
    attendance_date: date = Field(default_factory=date.today, index=True)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
