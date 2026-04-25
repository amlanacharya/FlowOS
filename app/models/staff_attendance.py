from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .branch import Branch
    from .staff import Staff


class StaffAttendance(SQLModel, table=True):
    __tablename__ = "staff_attendance"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    staff_id: UUID = Field(foreign_key="staff.id", index=True)
    check_in: datetime = Field(default_factory=datetime.utcnow, index=True)
    check_out: Optional[datetime] = None
    date: date = Field(default_factory=date.today, index=True)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    branch: Optional["Branch"] = Relationship(back_populates="staff_attendance")
    staff: Optional["Staff"] = Relationship(back_populates="attendance")
