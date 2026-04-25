from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel


class MemberFeedbackCreate(SQLModel):
    member_id: UUID
    rating: int
    comment: Optional[str] = None


class MemberFeedbackResponse(SQLModel):
    id: UUID
    member_id: UUID
    branch_id: UUID
    rating: int
    comment: Optional[str]
    submitted_at: datetime


class FeedbackSummary(SQLModel):
    average_rating: float
    total: int
    recent: List[MemberFeedbackResponse]


class FeedbackListResponse(SQLModel):
    items: List[MemberFeedbackResponse]
    total: int
