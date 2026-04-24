from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import RoleEnum


class LoginRequest(SQLModel):
    email: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(SQLModel):
    refresh_token: str


class UserProfileResponse(SQLModel):
    id: UUID
    email: str
    full_name: str
    role: RoleEnum
    branch_id: UUID
    org_id: UUID
    staff_id: UUID
