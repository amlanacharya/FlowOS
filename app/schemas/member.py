from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import MemberStatusEnum


class MemberCreate(SQLModel):
    full_name: str
    phone: str
    plan_id: UUID
    email: Optional[str] = None
    aadhaar_no: Optional[str] = None
    pan_no: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[MemberStatusEnum] = MemberStatusEnum.ACTIVE


class MemberUpdate(SQLModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    aadhaar_no: Optional[str] = None
    pan_no: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[MemberStatusEnum] = None


class MemberResponse(SQLModel):
    id: UUID
    branch_id: UUID
    full_name: str
    phone: str
    member_code: str
    status: MemberStatusEnum
    joined_at: date
    created_at: datetime


class MemberDetailResponse(MemberResponse):
    email: Optional[str]
    aadhaar_no: Optional[str]
    pan_no: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    emergency_contact: Optional[str]
    notes: Optional[str]
