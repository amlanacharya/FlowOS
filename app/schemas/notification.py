from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class NotificationLogResponse(SQLModel):
    id: UUID
    branch_id: UUID
    recipient_type: str
    channel: str
    event_type: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None


class SendNotificationRequest(SQLModel):
    recipient_type: str
    recipient_id: UUID
    channel: str
    event_type: str
    payload: Optional[dict] = None
