from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel

from app.core.enums import AttendanceTypeEnum


class AttendanceCheckinRequest(SQLModel):
    member_id: Optional[UUID] = None
    member_code: Optional[str] = None
    notes: Optional[str] = None


class AttendanceMarkRequest(SQLModel):
    member_id: UUID
    notes: Optional[str] = None


class AttendanceResponse(SQLModel):
    id: UUID
    branch_id: UUID
    member_id: UUID
    attendance_type: AttendanceTypeEnum
    checked_in_at: datetime
    checked_out_at: Optional[datetime]
    created_at: datetime = None


class QrCheckinRequest(SQLModel):
    member_code: str
    notes: Optional[str] = None


class QrCheckinResponse(SQLModel):
    attendance_id: UUID
    member_id: UUID
    member_name: str
    subscription_end_date: Optional[date]
    amount_due: Decimal
    checked_in_at: datetime
