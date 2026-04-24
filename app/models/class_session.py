from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .branch import Branch
    from .class_enrollment import ClassEnrollment
    from .class_type import ClassType
    from .staff import Staff


class ClassSession(SQLModel, table=True):
    __tablename__ = "class_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    class_type_id: UUID = Field(foreign_key="class_types.id", index=True)
    trainer_staff_id: UUID = Field(foreign_key="staff.id", index=True)
    scheduled_at: datetime = Field(index=True)
    duration_minutes: int = Field(default=60)
    capacity: int = Field(default=20)
    enrolled_count: int = Field(default=0)
    is_cancelled: bool = Field(default=False)
    cancellation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    enrollments: List["ClassEnrollment"] = Relationship(back_populates="session")
