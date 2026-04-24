from datetime import date
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import RoleEnum


class StaffCreate(SQLModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    role: RoleEnum
    organization_id: UUID
    branch_id: UUID
    employee_code: Optional[str] = None
    specialization: Optional[str] = None


class StaffResponse(SQLModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    branch_id: UUID
    role: RoleEnum
    full_name: str
    email: str
    is_active: bool
    joined_at: date
