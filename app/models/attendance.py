from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum
from sqlmodel import Field, SQLModel

from app.core.enums import AttendanceTypeEnum

if TYPE_CHECKING:
    from .branch import Branch
    from .class_session import ClassSession
    from .lead import Lead
    from .member import Member
    from .staff import Staff


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    attendance_type: AttendanceTypeEnum = Field(sa_column=Column(Enum(AttendanceTypeEnum, native_enum=False), nullable=False))
    checked_in_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    checked_out_at: Optional[datetime] = None
    class_session_id: Optional[UUID] = Field(default=None, foreign_key="class_sessions.id")
    lead_id: Optional[UUID] = Field(default=None, foreign_key="leads.id")
    notes: Optional[str] = None
    recorded_by_staff_id: Optional[UUID] = Field(default=None, foreign_key="staff.id")
