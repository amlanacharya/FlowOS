from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MemberStatusEnum, RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.member import MemberCreate, MemberDetailResponse, MemberResponse, MemberUpdate
from app.services.member_service import MemberService

router = APIRouter(prefix="/api/v1/members", tags=["members"])


@router.post("", response_model=MemberResponse)
async def create_member(
    member: MemberCreate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> MemberResponse:
    service = MemberService(session)
    return await service.create_member(branch_id, member)


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
