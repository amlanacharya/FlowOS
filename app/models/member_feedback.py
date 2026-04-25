from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class MemberFeedback(SQLModel, table=True):
    __tablename__ = "member_feedback"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    member_id: UUID = Field(foreign_key="members.id", index=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow, index=True)
