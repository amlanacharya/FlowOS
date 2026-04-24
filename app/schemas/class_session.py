from datetime import datetime
from uuid import UUID

from sqlmodel import SQLModel


class ClassSessionCreate(SQLModel):
    class_type_id: UUID
    trainer_staff_id: UUID
    scheduled_at: datetime
    capacity: int = 20
    duration_minutes: int = 60


class ClassSessionResponse(SQLModel):
    id: UUID
    branch_id: UUID
    class_type_id: UUID
    trainer_staff_id: UUID
    scheduled_at: datetime
    capacity: int
    enrolled_count: int
    is_cancelled: bool
    created_at: datetime


class ClassSessionEnrollRequest(SQLModel):
    member_id: UUID
