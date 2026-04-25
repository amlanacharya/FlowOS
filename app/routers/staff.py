from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.core.security import hash_password
from app.database import get_session
from app.deps import get_branch_scope, require_roles, get_current_user
from app.models import Staff, User
from app.schemas.staff import StaffCreate, StaffResponse
from app.schemas.staff_attendance import (
    StaffCheckinRequest,
    StaffCheckinResponse,
    StaffAttendanceListResponse,
)
from app.services.auth_service import AuthService
from app.services.staff_attendance_service import StaffAttendanceService

router = APIRouter(prefix="/api/v1/staff", tags=["staff"])


@router.post("", response_model=StaffResponse)
async def create_staff(
    staff_data: StaffCreate,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:
    service = AuthService(session)
    user = await service.create_user(
        email=staff_data.email,
        hashed_password=hash_password(staff_data.password),
        full_name=staff_data.full_name,
        phone=staff_data.phone,
    )
    staff = Staff(
        user_id=user.id,
        organization_id=staff_data.organization_id,
        branch_id=staff_data.branch_id,
        role=staff_data.role,
        employee_code=staff_data.employee_code,
        specialization=staff_data.specialization,
    )
    session.add(staff)
    await session.commit()
    await session.refresh(staff)
    return staff


@router.get("", response_model=List[StaffResponse])
async def list_staff(
    org_id: UUID = Query(...),
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> List[StaffResponse]:
    statement = select(Staff).where(Staff.organization_id == org_id)
    result = await session.execute(statement)
    staff_list = result.scalars().all()
    return staff_list


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:
    staff = await session.get(Staff, staff_id)
    if not staff:
        raise ResourceNotFoundException()
    return staff


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    staff_update: StaffCreate,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:
    staff = await session.get(Staff, staff_id)
    if not staff:
        raise ResourceNotFoundException()
    for key, value in staff_update.dict(exclude_unset=True).items():
        if key not in ["email", "password"]:
            setattr(staff, key, value)
    staff.updated_at = datetime.utcnow()
    session.add(staff)
    await session.commit()
    await session.refresh(staff)
    return staff


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    staff = await session.get(Staff, staff_id)
    if not staff:
        raise ResourceNotFoundException()
    staff.is_active = False
    session.add(staff)
    await session.commit()
    return {"message": "Staff deactivated"}


# Attendance endpoints
@router.post("/checkin", response_model=StaffCheckinResponse)
async def staff_checkin(
    data: StaffCheckinRequest,
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StaffCheckinResponse:
    """Record staff check-in."""
    # Get staff_id from user
    statement = select(Staff).where(Staff.user_id == user.id)
    result = await session.execute(statement)
    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found for this user")

    service = StaffAttendanceService(session)
    try:
        attendance = await service.checkin(branch_id, staff.id, data.notes)
        return StaffCheckinResponse(**attendance.dict())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/checkout", response_model=StaffCheckinResponse)
async def staff_checkout(
    data: StaffCheckinRequest,
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StaffCheckinResponse:
    """Record staff check-out."""
    statement = select(Staff).where(Staff.user_id == user.id)
    result = await session.execute(statement)
    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found for this user")

    service = StaffAttendanceService(session)
    attendance = await service.checkout(staff.id, data.notes)

    if not attendance:
        raise HTTPException(status_code=400, detail="No active check-in found")

    return StaffCheckinResponse(**attendance.dict())


@router.get("/attendance", response_model=StaffAttendanceListResponse)
async def list_staff_attendance(
    staff_id: UUID = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> StaffAttendanceListResponse:
    """List staff attendance records."""
    from datetime import date

    date_from_obj = date.fromisoformat(date_from) if date_from else None
    date_to_obj = date.fromisoformat(date_to) if date_to else None

    service = StaffAttendanceService(session)
    records, total = await service.list_attendance(
        branch_id=branch_id,
        staff_id=staff_id,
        date_from=date_from_obj,
        date_to=date_to_obj,
        skip=skip,
        limit=limit,
    )

    return StaffAttendanceListResponse(
        items=[StaffCheckinResponse(**r.dict()) for r in records],
        total=total,
    )
