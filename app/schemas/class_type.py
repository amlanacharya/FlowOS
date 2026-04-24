from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class ClassTypeCreate(SQLModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = 60


class ClassTypeResponse(SQLModel):
    id: UUID
    branch_id: UUID
    name: str
    description: Optional[str] = None
    duration_minutes: int
    is_active: bool
    created_at: datetime
