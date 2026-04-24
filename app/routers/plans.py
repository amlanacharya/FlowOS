from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.models import MembershipPlan
from app.schemas.membership_plan import PlanCreate, PlanResponse, PlanUpdate

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


@router.post("", response_model=PlanResponse)
async def create_plan(
    plan: PlanCreate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> PlanResponse:
    db_plan = MembershipPlan(branch_id=branch_id, **plan.dict())
    session.add(db_plan)
    await session.commit()
    await session.refresh(db_plan)
    return db_plan


@router.get("", response_model=List[PlanResponse])
async def list_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER, RoleEnum.FRONT_DESK, RoleEnum.TRAINER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[PlanResponse]:
    statement = (
        select(MembershipPlan)
        .where(MembershipPlan.branch_id == branch_id)
        .where(MembershipPlan.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    return result.all()


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER, RoleEnum.FRONT_DESK, RoleEnum.TRAINER)),
    session: AsyncSession = Depends(get_session),
) -> PlanResponse:
    plan = await session.get(MembershipPlan, plan_id)
    if not plan:
        raise ResourceNotFoundException()
    return plan


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    plan_update: PlanUpdate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> PlanResponse:
    plan = await session.get(MembershipPlan, plan_id)
    if not plan:
        raise ResourceNotFoundException()

    from datetime import datetime

    for key, value in plan_update.dict(exclude_unset=True).items():
        setattr(plan, key, value)
    plan.updated_at = datetime.utcnow()
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    plan = await session.get(MembershipPlan, plan_id)
    if not plan:
        raise ResourceNotFoundException()
    plan.is_active = False
    session.add(plan)
    await session.commit()
    return {"message": "Plan deactivated"}
