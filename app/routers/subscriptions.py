from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum, SubscriptionStatusEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, get_current_user, require_roles
from app.models import Staff, User
from app.schemas.member_subscription import (
    PauseSubscriptionRequest,
    ResumeSubscriptionRequest,
    SubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    member_id: UUID,
    plan_id: UUID,
    start_date: Optional[date] = None,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionResponse:
    result = await session.execute(select(Staff).where(Staff.user_id == user.id))
    staff = result.scalars().first()
    if not staff:
        raise ResourceNotFoundException("Staff profile not found")

    service = SubscriptionService(session)
    return await service.create_subscription(branch_id, member_id, plan_id, staff.id, start_date)


@router.get("", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    status: Optional[SubscriptionStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[SubscriptionResponse]:
    service = SubscriptionService(session)
    return await service.list_subscriptions(branch_id, status, skip, limit)


@router.get("/{sub_id}", response_model=SubscriptionResponse)
async def get_subscription(
    sub_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionResponse:
    service = SubscriptionService(session)
    sub = await service.get_subscription(sub_id)
    if not sub:
        raise ResourceNotFoundException()
    return sub


@router.post("/{sub_id}/pause")
async def pause_subscription(
    sub_id: UUID,
    payload: PauseSubscriptionRequest,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Staff).where(Staff.user_id == user.id))
    staff = result.scalars().first()
    if not staff:
        raise ResourceNotFoundException("Staff profile not found")

    service = SubscriptionService(session)
    try:
        sub = await service.pause_subscription(sub_id, staff.id, payload.pause_date, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not sub:
        raise ResourceNotFoundException()
    return sub


@router.post("/{sub_id}/resume")
async def resume_subscription(
    sub_id: UUID,
    payload: ResumeSubscriptionRequest,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    service = SubscriptionService(session)
    try:
        sub = await service.resume_subscription(sub_id, payload.resume_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not sub:
        raise ResourceNotFoundException()
    return sub


@router.post("/{sub_id}/renew")
async def renew_subscription(
    sub_id: UUID,
    plan_id: Optional[UUID] = None,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER)),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Staff).where(Staff.user_id == user.id))
    staff = result.scalars().first()
    if not staff:
        raise ResourceNotFoundException("Staff profile not found")

    service = SubscriptionService(session)
    try:
        new_sub = await service.renew_subscription(sub_id, staff.id, plan_id=plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not new_sub:
        raise ResourceNotFoundException()
    return new_sub
