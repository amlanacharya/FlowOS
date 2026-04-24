from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class OrganizationCreate(SQLModel):
    name: str
    slug: str
    owner_email: str
    phone: Optional[str] = None


class OrganizationResponse(SQLModel):
    id: UUID
    name: str
    slug: str
    owner_email: str
    is_active: bool
    created_at: datetime
