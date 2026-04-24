from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .branch import Branch
    from .class_session import ClassSession
    from .member import Member


class ClassEnrollment(SQLModel, table=True):
    __tablename__ = "class_enrollments"
    __table_args__ = (UniqueConstraint("session_id", "member_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="class_sessions.id", index=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    attended: bool = Field(default=False)
    cancelled: bool = Field(default=False)

    session: Optional["ClassSession"] = Relationship(back_populates="enrollments")
