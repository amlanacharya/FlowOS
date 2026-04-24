from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.core.security import hash_password
from app.database import get_session
from app.deps import require_roles
from app.models import Staff, User
from app.schemas.staff import StaffCreate, StaffResponse
from app.services.auth_service import AuthService

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
