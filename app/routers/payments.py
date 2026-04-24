from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, get_current_user, require_roles
from app.models import Staff, User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse)
async def record_payment(
    payment: PaymentCreate,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaymentResponse:
    """Record a new payment for a member."""
    statement = select(Staff).where(Staff.user_id == user.id)
    result = await session.execute(statement)
    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff profile not found")

    service = PaymentService(session)
    return await service.record_payment(branch_id, payment, staff.id)


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[PaymentResponse]:
    """List all payments for a branch."""
    service = PaymentService(session)
    return await service.list_payments(branch_id, skip, limit)


@router.get("/member/{member_id}", response_model=List[PaymentResponse])
async def list_member_payments(
    member_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> List[PaymentResponse]:
    """List all payments for a specific member."""
    service = PaymentService(session)
    return await service.list_member_payments(member_id, skip, limit)


@router.get("/summary")
async def get_summary(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get payment summary for today and outstanding dues."""
    service = PaymentService(session)
    return await service.get_summary(branch_id)
