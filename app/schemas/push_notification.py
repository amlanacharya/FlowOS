from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class PushSubscriptionRequest(SQLModel):
    token: str


class PushSubscriptionResponse(SQLModel):
    status: str
    member_id: str


class PushStatusResponse(SQLModel):
    opted_in: bool
    token_valid: bool
    last_updated: Optional[str]
