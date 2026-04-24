from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class BranchCreate(SQLModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None


class BranchResponse(SQLModel):
    id: UUID
    organization_id: UUID
    name: str
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
