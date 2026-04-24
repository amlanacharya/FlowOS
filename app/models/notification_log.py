from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from .branch import Branch


class NotificationLog(SQLModel, table=True):
    __tablename__ = "notification_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    branch_id: UUID = Field(foreign_key="branches.id", index=True)
    recipient_type: str = Field(max_length=50)
    recipient_id: UUID
    channel: str = Field(max_length=50)
    event_type: str = Field(max_length=100)
    payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(max_length=50, default="pending")
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
