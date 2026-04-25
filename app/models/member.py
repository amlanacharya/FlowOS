from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship, SQLModel

from app.core.enums import MemberStatusEnum

if TYPE_CHECKING:
    from .branch import Branch
    from .lead import Lead
    from .member_subscription import MemberSubscription


class Member(SQLModel, table=True):
    __tablename__ = "members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    full_name: str = Field(max_length=255)
    phone: str = Field(max_length=20, index=True)
    email: Optional[str] = Field(default=None, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=20)
    emergency_contact: Optional[str] = Field(default=None, max_length=255)
    member_code: str = Field(max_length=50, unique=True, index=True)
    status: MemberStatusEnum = Field(
        default=MemberStatusEnum.INACTIVE,
        sa_column=Column(Enum(MemberStatusEnum, native_enum=False), nullable=False)
    )
    joined_at: date = Field(default_factory=date.today)
    profile_photo_url: Optional[str] = None
    notes: Optional[str] = None
    push_token: Optional[str] = Field(default=None, max_length=500)
    push_opted_in: bool = Field(default=False)
    push_token_updated_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    branch: Optional["Branch"] = Relationship(back_populates="members")
    subscriptions: List["MemberSubscription"] = Relationship(back_populates="member")
    lead: Optional["Lead"] = Relationship(back_populates="converted_member")
