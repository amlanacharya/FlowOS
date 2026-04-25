from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class PublicLeadCreate(SQLModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    branch_slug: str


class PublicLeadResponse(SQLModel):
    id: UUID
    message: str
