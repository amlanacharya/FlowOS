from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.attendance import AttendanceCheckinRequest, AttendanceResponse
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])


@router.post("/checkin", response_model=AttendanceResponse)
async def checkin(
    data: AttendanceCheckinRequest,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.TRAINER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> AttendanceResponse:
    """Record a member check-in."""
    service = AttendanceService(session)
    try:
        return await service.checkin(branch_id, data.member_id, data.member_code, data.notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/checkout", response_model=AttendanceResponse)
async def checkout(
    member_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> AttendanceResponse:
    """Record a member check-out."""
    service = AttendanceService(session)
    attendance = await service.checkout(member_id)
    if not attendance:
        raise ResourceNotFoundException()
    return attendance


@router.get("", response_model=List[AttendanceResponse])
async def list_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[AttendanceResponse]:
    """List all attendance records for a branch."""
    service = AttendanceService(session)
    return await service.list_attendance(branch_id, skip, limit)


@router.get("/today")
async def list_today_checkins(
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[AttendanceResponse]:
    """List all check-ins for today."""
    service = AttendanceService(session)
    return await service.list_today_checkins(branch_id)
