from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, PgEnum
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import LeadStatusEnum

if TYPE_CHECKING:
    from .branch import Branch
    from .staff import Staff
    from .member import Member


class Lead(SQLModel, table=True):
    __tablename__ = "leads"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    full_name: str = Field(max_length=255)
    phone: str = Field(max_length=20, index=True)
    email: Optional[str] = Field(default=None, max_length=255)
    source: Optional[str] = Field(default=None, max_length=100)
    status: LeadStatusEnum = Field(
        default=LeadStatusEnum.NEW,
        sa_column=Column(PgEnum(LeadStatusEnum, native_enum=False), nullable=False)
    )
    assigned_to_staff_id: Optional[UUID] = Field(default=None, foreign_key="staff.id")
    trial_scheduled_at: Optional[datetime] = None
    trial_attended_at: Optional[datetime] = None
    notes: Optional[str] = None
    converted_member_id: Optional[UUID] = Field(default=None, foreign_key="members.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    branch: Optional["Branch"] = Relationship(back_populates="leads")
    assigned_to_staff: Optional["Staff"] = Relationship(back_populates="leads")
    converted_member: Optional["Member"] = Relationship(back_populates="lead")
