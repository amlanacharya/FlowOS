from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.routers.common import bad_request_on_value_error
from app.schemas.workout import WorkoutLogCreate, WorkoutLogResponse, WorkoutProgressPoint
from app.services.workout_service import WorkoutService

router = APIRouter(prefix="/api/v1/workouts", tags=["workouts"])


@router.post("", response_model=WorkoutLogResponse)
async def create_workout(
    data: WorkoutLogCreate,
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER, RoleEnum.MEMBER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> WorkoutLogResponse:
    service = WorkoutService(session)
    logged_by_staff_id = UUID(claims["staff_id"]) if claims.get("staff_id") else None
    return await bad_request_on_value_error(
        lambda: service.log_workout(branch_id, data, logged_by_staff_id)
    )


@router.get("/{member_id}", response_model=List[WorkoutLogResponse])
async def list_workouts(
    member_id: UUID,
    exercise_name: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER, RoleEnum.MEMBER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[WorkoutLogResponse]:
    service = WorkoutService(session)
    return await service.list_workouts(branch_id, member_id, exercise_name, date_from, date_to, skip, limit)


@router.get("/{member_id}/progress", response_model=List[WorkoutProgressPoint])
async def workout_progress(
    member_id: UUID,
    exercise_name: Optional[str] = None,
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER, RoleEnum.MEMBER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[WorkoutProgressPoint]:
    service = WorkoutService(session)
    return await service.progress(branch_id, member_id, exercise_name)
