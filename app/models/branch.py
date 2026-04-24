from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .lead import Lead
    from .member import Member
    from .member_subscription import MemberSubscription
    from .membership_plan import MembershipPlan
    from .organization import Organization
    from .staff import Staff


class Branch(SQLModel, table=True):
    __tablename__ = "branches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organization_id: UUID = Field(foreign_key="organizations.id", index=True)
    name: str = Field(max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Optional["Organization"] = Relationship(back_populates="branches")
    staff: List["Staff"] = Relationship(back_populates="branch")
    leads: List["Lead"] = Relationship(back_populates="branch")
    members: List["Member"] = Relationship(back_populates="branch")
    membership_plans: List["MembershipPlan"] = Relationship(back_populates="branch")
    member_subscriptions: List["MemberSubscription"] = Relationship(back_populates="branch")
