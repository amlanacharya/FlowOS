from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.dashboard import (
    AttendanceTrend,
    DashboardSummary,
    DuesReport,
    LeadFunnel,
    RevenueBreakdown,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> DashboardSummary:
    """Get dashboard summary metrics."""
    service = DashboardService(session)
    return await service.get_summary(branch_id)


@router.get("/revenue", response_model=List[RevenueBreakdown])
async def get_revenue(
    days: int = Query(30, ge=1, le=365),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[RevenueBreakdown]:
    """Get revenue breakdown report."""
    service = DashboardService(session)
    return await service.get_revenue_report(branch_id, days)


@router.get("/dues", response_model=List[DuesReport])
async def get_dues(
    claims: dict = Depends(
        require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)
    ),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[DuesReport]:
    """Get outstanding dues report."""
    service = DashboardService(session)
    return await service.get_dues_report(branch_id)


@router.get("/lead-funnel", response_model=LeadFunnel)
async def get_lead_funnel(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> LeadFunnel:
    """Get lead funnel metrics."""
    service = DashboardService(session)
    return await service.get_lead_funnel(branch_id)


@router.get("/attendance-trends", response_model=List[AttendanceTrend])
async def get_attendance_trends(
    days: int = Query(30, ge=1, le=365),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[AttendanceTrend]:
    """Get attendance trends."""
    service = DashboardService(session)
    return await service.get_attendance_trends(branch_id, days)
