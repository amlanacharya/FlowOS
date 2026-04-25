from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.routers.common import bad_request_on_value_error
from app.schemas.feedback import FeedbackListResponse, FeedbackSummary, MemberFeedbackCreate, MemberFeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("", response_model=MemberFeedbackResponse)
async def submit_feedback(
    data: MemberFeedbackCreate,
    claims: dict = Depends(require_roles(RoleEnum.MEMBER, RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> MemberFeedbackResponse:
    service = FeedbackService(session)
    return await bad_request_on_value_error(lambda: service.submit_feedback(branch_id, data))


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> FeedbackListResponse:
    service = FeedbackService(session)
    return await service.list_feedback(branch_id, date_from, date_to, min_rating, skip, limit)


@router.get("/summary", response_model=FeedbackSummary)
async def feedback_summary(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> FeedbackSummary:
    service = FeedbackService(session)
    return await service.summary(branch_id)
