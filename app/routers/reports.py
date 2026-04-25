from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.report import (
    DailySalesReport,
    MonthlyRevenue,
    PeakHourBucket,
    RetentionReport,
    RevenueForecast,
    TrainerPerformanceRow,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/daily-sales", response_model=DailySalesReport)
async def daily_sales(
    report_date: date = Query(default_factory=date.today, alias="date"),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> DailySalesReport:
    return await ReportService(session).daily_sales(branch_id, report_date)


@router.get("/retention", response_model=RetentionReport)
async def retention(
    date_from: date = Query(default_factory=lambda: date.today().replace(day=1)),
    date_to: date = Query(default_factory=date.today),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> RetentionReport:
    return await ReportService(session).retention(branch_id, date_from, date_to)


@router.get("/trainer-performance", response_model=List[TrainerPerformanceRow])
async def trainer_performance(
    date_from: date = Query(default_factory=lambda: date.today().replace(day=1)),
    date_to: date = Query(default_factory=date.today),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[TrainerPerformanceRow]:
    return await ReportService(session).trainer_performance(branch_id, date_from, date_to)


@router.get("/revenue-forecast", response_model=RevenueForecast)
async def revenue_forecast(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> RevenueForecast:
    return await ReportService(session).revenue_forecast(branch_id)


@router.get("/peak-hours", response_model=List[PeakHourBucket])
async def peak_hours(
    date_from: date = Query(default_factory=lambda: date.today().replace(day=1)),
    date_to: date = Query(default_factory=date.today),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[PeakHourBucket]:
    return await ReportService(session).peak_hours(branch_id, date_from, date_to)


@router.get("/monthly-revenue", response_model=List[MonthlyRevenue])
async def monthly_revenue(
    months: int = Query(12, ge=1, le=36),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[MonthlyRevenue]:
    return await ReportService(session).monthly_revenue(branch_id, months)
