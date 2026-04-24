from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.models import ClassEnrollment
from app.schemas.class_session import ClassSessionCreate, ClassSessionEnrollRequest, ClassSessionResponse
from app.services.class_service import ClassService

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=ClassSessionResponse)
async def create_session(
    data: ClassSessionCreate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> ClassSessionResponse:
    """Create a new class session."""
    service = ClassService(session)
    return await service.create_session(branch_id, data)


@router.get("", response_model=List[ClassSessionResponse])
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER, RoleEnum.FRONT_DESK, RoleEnum.TRAINER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[ClassSessionResponse]:
    """List all active class sessions for a branch."""
    service = ClassService(session)
    return await service.list_sessions(branch_id, skip, limit)


@router.get("/{session_id}", response_model=ClassSessionResponse)
async def get_session(
    session_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER, RoleEnum.FRONT_DESK, RoleEnum.TRAINER)),
    session: AsyncSession = Depends(get_session),
) -> ClassSessionResponse:
    """Get details of a specific class session."""
    service = ClassService(session)
    cs = await service.get_session(session_id)
    if not cs:
        raise ResourceNotFoundException()
    return cs


@router.post("/{session_id}/enroll", response_model=dict)
async def enroll_member(
    session_id: UUID,
    data: ClassSessionEnrollRequest,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Enroll a member in a class session."""
    service = ClassService(session)
    try:
        enrollment = await service.enroll_member(session_id, data.member_id, branch_id)
        if not enrollment:
            raise ResourceNotFoundException()
        return {"enrollment_id": str(enrollment.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{session_id}/enroll/{member_id}")
async def cancel_enrollment(
    session_id: UUID,
    member_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Cancel a member's enrollment in a class session."""
    statement = (
        select(ClassEnrollment)
        .where(ClassEnrollment.session_id == session_id)
        .where(ClassEnrollment.member_id == member_id)
    )
    result = await session.execute(statement)
    enrollment = result.scalars().first()

    if not enrollment:
        raise ResourceNotFoundException()

    service = ClassService(session)
    await service.cancel_enrollment(enrollment.id)
    return {"message": "Enrollment cancelled"}


@router.post("/{session_id}/cancel")
async def cancel_session(
    session_id: UUID,
    reason: Optional[str] = None,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> ClassSessionResponse:
    """Cancel a class session."""
    service = ClassService(session)
    cs = await service.cancel_session(session_id, reason)
    if not cs:
        raise ResourceNotFoundException()
    return cs
