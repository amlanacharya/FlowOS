from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import RoleEnum

if TYPE_CHECKING:
    from .branch import Branch
    from .lead import Lead
    from .member_subscription import MemberSubscription
    from .user import User


class Staff(SQLModel, table=True):
    __tablename__ = "staff"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True, index=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    role: RoleEnum = Field(
        sa_column=Column(Enum(RoleEnum, native_enum=False), nullable=False)
    )
    employee_code: Optional[str] = Field(default=None, max_length=50)
    specialization: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    joined_at: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship(back_populates="staff_profile")
    branch: Optional["Branch"] = Relationship(back_populates="staff")
    leads: List["Lead"] = Relationship(back_populates="assigned_to_staff")
    subscriptions_created: List["MemberSubscription"] = Relationship(back_populates="created_by_staff")
