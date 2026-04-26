from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import MemberStatusEnum, RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, get_current_user, require_roles
from app.models import Member, Staff, User
from app.schemas.member import MemberCreate, MemberDetailResponse, MemberResponse, MemberUpdate
from app.services.member_service import MemberService

router = APIRouter(prefix="/api/v1/members", tags=["members"])


@router.post("", response_model=MemberResponse)
async def create_member(
    member: MemberCreate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
    staff_result = await session.execute(select(Staff).where(Staff.user_id == user.id))
    staff = staff_result.scalars().first()
    if not staff:
        raise ResourceNotFoundException("Staff profile not found")

    service = MemberService(session)
    try:
        return await service.create_member(branch_id, member, staff.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=List[MemberResponse])
async def list_members(
    status: Optional[MemberStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[MemberResponse]:
    service = MemberService(session)
    return await service.list_members(branch_id, status, skip, limit)


@router.get("/{member_id}", response_model=MemberDetailResponse)
async def get_member(
    member_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> MemberDetailResponse:
    service = MemberService(session)
    member = await service.get_member(member_id)
    if not member:
        raise ResourceNotFoundException()
    return member


@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    member_update: MemberUpdate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
    service = MemberService(session)
    member = await service.update_member(member_id, member_update)
    if not member:
        raise ResourceNotFoundException()
    return member


@router.post("/{member_id}/pause")
async def pause_member(
    member_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    service = MemberService(session)
    member = await service.pause_member(member_id)
    if not member:
        raise ResourceNotFoundException()
    return member


@router.post("/{member_id}/activate")
async def activate_member(
    member_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    service = MemberService(session)
    member = await service.activate_member(member_id)
    if not member:
        raise ResourceNotFoundException()
    return member


# Push Notification endpoints
@router.post("/{member_id}/push-subscribe")
async def push_subscribe(
    member_id: UUID,
    data: dict,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Subscribe member to web push notifications."""
    from datetime import datetime
    from sqlmodel import select

    member = await session.get(Member, member_id)
    if not member:
        raise ResourceNotFoundException()

    member.push_token = str(data.get("token"))
    member.push_opted_in = True
    member.push_token_updated_at = datetime.utcnow()
    session.add(member)
    await session.commit()

    return {"status": "subscribed", "member_id": str(member_id)}


@router.post("/{member_id}/push-unsubscribe")
async def push_unsubscribe(
    member_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Unsubscribe member from web push notifications."""
    member = await session.get(Member, member_id)
    if not member:
        raise ResourceNotFoundException()

    member.push_token = None
    member.push_opted_in = False
    session.add(member)
    await session.commit()

    return {"status": "unsubscribed", "member_id": str(member_id)}


@router.get("/{member_id}/push-status")
async def push_status(
    member_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get member push notification status."""
    member = await session.get(Member, member_id)
    if not member:
        raise ResourceNotFoundException()

    return {
        "opted_in": member.push_opted_in,
        "token_valid": bool(member.push_token),
        "last_updated": member.push_token_updated_at,
    }
