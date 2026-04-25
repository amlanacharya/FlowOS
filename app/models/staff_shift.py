from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class StaffShift(SQLModel, table=True):
    __tablename__ = "staff_shifts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    staff_id: UUID = Field(foreign_key="staff.id", index=True)
    shift_date: datetime = Field(index=True)
    shift_start: datetime
    shift_end: datetime
    shift_type: str = Field(max_length=50, default="regular")
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
