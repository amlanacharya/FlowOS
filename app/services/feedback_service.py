from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import MemberFeedback
from app.schemas.feedback import FeedbackListResponse, FeedbackSummary, MemberFeedbackCreate
from app.services.common import apply_pagination, branch_conditions, require_branch_member


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def submit_feedback(self, branch_id: UUID, data: MemberFeedbackCreate) -> MemberFeedback:
        await require_branch_member(self.session, branch_id, data.member_id)
        if data.rating < 1 or data.rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        feedback = MemberFeedback(
            member_id=data.member_id,
            branch_id=branch_id,
            rating=data.rating,
            comment=data.comment,
        )
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback

    async def list_feedback(
        self,
        branch_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_rating: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> FeedbackListResponse:
        conditions = branch_conditions(
            MemberFeedback,
            branch_id,
            MemberFeedback.submitted_at >= date_from if date_from else None,
            MemberFeedback.submitted_at <= date_to if date_to else None,
            MemberFeedback.rating >= min_rating if min_rating else None,
        )

        count_result = await self.session.execute(
            select(func.count()).select_from(MemberFeedback).where(*conditions)
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(apply_pagination(
            select(MemberFeedback)
            .where(*conditions)
            .order_by(MemberFeedback.submitted_at.desc()),
            skip,
            limit,
        ))
        return FeedbackListResponse(items=list(result.scalars().all()), total=total)

    async def summary(self, branch_id: UUID) -> FeedbackSummary:
        since = datetime.utcnow() - timedelta(days=30)
        summary_result = await self.session.execute(
            select(func.avg(MemberFeedback.rating), func.count(MemberFeedback.id)).where(
                MemberFeedback.branch_id == branch_id,
                MemberFeedback.submitted_at >= since,
            )
        )
        average, total = summary_result.one()

        recent_result = await self.session.execute(
            select(MemberFeedback)
            .where(MemberFeedback.branch_id == branch_id)
            .order_by(MemberFeedback.submitted_at.desc())
            .limit(3)
        )
        recent = list(recent_result.scalars().all())
        return FeedbackSummary(
            average_rating=round(float(average or 0), 2),
            total=int(total or 0),
            recent=recent,
        )
