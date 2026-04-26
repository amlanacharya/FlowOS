from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, get_current_user, require_roles
from app.models import Staff, User
from app.schemas.membership_tracking import (
    MembershipTrackingItem,
    PauseHistoryResponse,
    SubscriptionAdjustmentCreate,
    SubscriptionAdjustmentResponse,
)
from app.services.membership_tracking_service import MembershipTrackingService

router = APIRouter(prefix="/api/v1/membership-tracking", tags=["membership-tracking"])


@router.get("", response_model=List[MembershipTrackingItem])
async def list_membership_tracking(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(
        require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)
    ),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[MembershipTrackingItem]:
    service = MembershipTrackingService(session)
    return await service.list_membership_tracking(branch_id, skip, limit)


@router.get("/{subscription_id}/pause-history", response_model=List[PauseHistoryResponse])
async def list_pause_history(
    subscription_id: UUID,
    claims: dict = Depends(
        require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)
    ),
    session: AsyncSession = Depends(get_session),
) -> List[PauseHistoryResponse]:
    service = MembershipTrackingService(session)
    return await service.list_pause_history(subscription_id)


@router.get("/{subscription_id}/adjustments", response_model=List[SubscriptionAdjustmentResponse])
async def list_adjustments(
    subscription_id: UUID,
    claims: dict = Depends(
        require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)
    ),
    session: AsyncSession = Depends(get_session),
) -> List[SubscriptionAdjustmentResponse]:
    service = MembershipTrackingService(session)
    return await service.list_adjustments(subscription_id)


@router.post("/{subscription_id}/adjustments", response_model=SubscriptionAdjustmentResponse)
async def create_adjustment(
    subscription_id: UUID,
    payload: SubscriptionAdjustmentCreate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionAdjustmentResponse:
    result = await session.execute(select(Staff).where(Staff.user_id == user.id))
    staff = result.scalars().first()
    if not staff:
        raise ResourceNotFoundException("Staff profile not found")

    service = MembershipTrackingService(session)
    try:
        adjustment = await service.create_adjustment(branch_id, subscription_id, staff.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not adjustment:
        raise ResourceNotFoundException("Subscription not found for this branch")
    return adjustment
