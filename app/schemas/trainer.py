from datetime import datetime
from typing import List
from uuid import UUID

from sqlmodel import SQLModel


class TrainerEnrollmentMember(SQLModel):
    enrollment_id: UUID
    member_id: UUID
    member_name: str
    attended: bool
    cancelled: bool


class TrainerSessionResponse(SQLModel):
    session_id: UUID
    class_type_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    capacity: int
    enrolled_count: int
    members: List[TrainerEnrollmentMember]
