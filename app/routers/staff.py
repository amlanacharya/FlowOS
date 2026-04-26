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
from app.schemas.staff_shift import StaffShiftCreate, StaffShiftUpdate, StaffShiftResponse, ShiftComparisonResponse
from app.services.auth_service import AuthService
from app.services.staff_attendance_service import StaffAttendanceService
from app.services.staff_shift_service import StaffShiftService

router = APIRouter(prefix="/api/v1/staff", tags=["staff"])


def _to_response(staff: Staff, user: User) -> StaffResponse:
    return StaffResponse(
        id=staff.id,
        user_id=staff.user_id,
        organization_id=staff.organization_id,
        branch_id=staff.branch_id,
        role=staff.role,
        is_active=staff.is_active,
        joined_at=staff.joined_at,
        full_name=user.full_name,
        email=user.email,
    )


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
    return _to_response(staff, user)


@router.get("", response_model=List[StaffResponse])
async def list_staff(
    org_id: UUID = Query(...),
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> List[StaffResponse]:
    result = await session.execute(
        select(Staff, User).join(User, User.id == Staff.user_id).where(Staff.organization_id == org_id)
    )
    return [_to_response(staff, user) for staff, user in result.all()]


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


# Shift Management endpoints
@router.post("/shifts", response_model=StaffShiftResponse)
async def create_shift(
    staff_id: UUID = Query(...),
    shift: StaffShiftCreate = None,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> StaffShiftResponse:
    """Create a new staff shift."""
    from app.models import StaffShift

    service = StaffShiftService(session)
    try:
        created = await service.create_shift(
            branch_id=branch_id,
            staff_id=staff_id,
            shift_date=shift.shift_date,
            shift_start=shift.shift_start,
            shift_end=shift.shift_end,
            shift_type=shift.shift_type,
            notes=shift.notes,
        )
        return StaffShiftResponse(**created.dict())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/shifts", response_model=dict)
async def list_shifts(
    staff_id: UUID = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """List staff shifts."""
    from datetime import datetime

    date_from_obj = datetime.fromisoformat(date_from) if date_from else None
    date_to_obj = datetime.fromisoformat(date_to) if date_to else None

    service = StaffShiftService(session)
    shifts, total = await service.list_shifts(
        branch_id=branch_id,
        staff_id=staff_id,
        date_from=date_from_obj,
        date_to=date_to_obj,
        skip=skip,
        limit=limit,
    )

    return {
        "items": [StaffShiftResponse(**s.dict()) for s in shifts],
        "total": total,
    }


@router.get("/shifts/{staff_id}/comparison", response_model=ShiftComparisonResponse)
async def compare_shifts(
    staff_id: UUID,
    date_from: str = Query(None),
    date_to: str = Query(None),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> ShiftComparisonResponse:
    """Compare scheduled vs actual hours."""
    from datetime import datetime

    date_from_obj = datetime.fromisoformat(date_from) if date_from else None
    date_to_obj = datetime.fromisoformat(date_to) if date_to else None

    service = StaffShiftService(session)
    result = await service.compare_shifts(
        branch_id=branch_id,
        staff_id=staff_id,
        date_from=date_from_obj,
        date_to=date_to_obj,
    )

    return ShiftComparisonResponse(**result)


@router.get("/shifts/{shift_id}", response_model=StaffShiftResponse)
async def get_shift(
    shift_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> StaffShiftResponse:
    """Get shift details."""
    service = StaffShiftService(session)
    shift = await service.get_shift(shift_id)
    if not shift:
        raise ResourceNotFoundException()
    return StaffShiftResponse(**shift.dict())


@router.patch("/shifts/{shift_id}", response_model=StaffShiftResponse)
async def update_shift(
    shift_id: UUID,
    update: StaffShiftUpdate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> StaffShiftResponse:
    """Update shift details."""
    service = StaffShiftService(session)
    try:
        shift = await service.update_shift(
            shift_id=shift_id,
            shift_start=update.shift_start,
            shift_end=update.shift_end,
            shift_type=update.shift_type,
            notes=update.notes,
        )
        if not shift:
            raise ResourceNotFoundException()
        return StaffShiftResponse(**shift.dict())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/shifts/{shift_id}")
async def delete_shift(
    shift_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a shift."""
    service = StaffShiftService(session)
    success = await service.delete_shift(shift_id)
    if not success:
        raise ResourceNotFoundException()
    return {"message": "Shift deleted"}


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:
    result = await session.execute(
        select(Staff, User).join(User, User.id == Staff.user_id).where(Staff.id == staff_id)
    )
    row = result.first()
    if not row:
        raise ResourceNotFoundException()
    return _to_response(row[0], row[1])


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    staff_update: StaffCreate,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> StaffResponse:
    result = await session.execute(
        select(Staff, User).join(User, User.id == Staff.user_id).where(Staff.id == staff_id)
    )
    row = result.first()
    if not row:
        raise ResourceNotFoundException()
    staff, user = row
    for key, value in staff_update.dict(exclude_unset=True).items():
        if key not in ["email", "password"]:
            setattr(staff, key, value)
    staff.updated_at = datetime.utcnow()
    session.add(staff)
    await session.commit()
    await session.refresh(staff)
    return _to_response(staff, user)


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
