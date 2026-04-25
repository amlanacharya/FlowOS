from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LeadStatusEnum, RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.models import Lead, Member
from app.schemas.lead import CampaignAnalytics, LeadCreate, LeadResponse, LeadUpdate
from app.schemas.member import MemberCreate
from app.services.lead_service import LeadService
from app.services.member_service import MemberService

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


@router.post("", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> LeadResponse:
    service = LeadService(session)
    return await service.create_lead(branch_id, lead)


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[LeadResponse]:
    service = LeadService(session)
    return await service.list_leads(branch_id, status, skip, limit)


@router.get("/campaigns/summary", response_model=List[CampaignAnalytics])
async def lead_campaigns(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[CampaignAnalytics]:
    service = LeadService(session)
    return await service.campaign_analytics(branch_id)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> LeadResponse:
    service = LeadService(session)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise ResourceNotFoundException()
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    lead_update: LeadUpdate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> LeadResponse:
    service = LeadService(session)
    lead = await service.update_lead(lead_id, lead_update)
    if not lead:
        raise ResourceNotFoundException()
    return lead


@router.post("/{lead_id}/status")
async def update_status(
    lead_id: UUID,
    new_status: LeadStatusEnum,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    service = LeadService(session)
    try:
        lead = await service.transition_status(lead_id, new_status)
        return lead
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{lead_id}/schedule-trial")
async def schedule_trial(
    lead_id: UUID,
    trial_datetime: datetime,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
):
    service = LeadService(session)
    lead = await service.schedule_trial(lead_id, trial_datetime)
    if not lead:
        raise ResourceNotFoundException()
    return lead


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: UUID,
    member_data: MemberCreate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
):
    lead_service = LeadService(session)
    member_service = MemberService(session)

    lead = await lead_service.get_lead(lead_id)
    if not lead:
        raise ResourceNotFoundException()

    member = await member_service.create_member(branch_id, member_data)
    await lead_service.convert_to_member(lead_id, member)

    return {"lead_id": str(lead_id), "member_id": str(member.id)}
