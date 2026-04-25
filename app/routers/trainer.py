from datetime import date, datetime, time
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.models import ClassEnrollment, ClassSession, Member, Staff
from app.schemas.trainer import TrainerEnrollmentMember, TrainerSessionResponse

router = APIRouter(prefix="/api/v1/trainer", tags=["trainer"])


async def _current_staff(claims: dict, session: AsyncSession) -> Staff:
    staff_id = claims.get("staff_id")
    if not staff_id:
        raise HTTPException(status_code=404, detail="Staff profile not found")
    staff = await session.get(Staff, UUID(staff_id))
    if not staff:
        raise HTTPException(status_code=404, detail="Staff profile not found")
    return staff


@router.get("/today", response_model=List[TrainerSessionResponse])
async def trainer_today(
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[TrainerSessionResponse]:
    staff = await _current_staff(claims, session)
    day_start = datetime.combine(date.today(), time.min)
    day_end = datetime.combine(date.today(), time.max)

    result = await session.execute(
        select(ClassSession)
        .where(
            ClassSession.branch_id == branch_id,
            ClassSession.trainer_staff_id == staff.id,
            ClassSession.scheduled_at >= day_start,
            ClassSession.scheduled_at <= day_end,
            ClassSession.is_cancelled == False,
        )
        .order_by(ClassSession.scheduled_at)
    )

    responses: list[TrainerSessionResponse] = []
    for class_session in result.scalars().all():
        enrollment_result = await session.execute(
            select(ClassEnrollment, Member)
            .join(Member, Member.id == ClassEnrollment.member_id)
            .where(ClassEnrollment.session_id == class_session.id)
            .order_by(Member.full_name)
        )
        members = [
            TrainerEnrollmentMember(
                enrollment_id=enrollment.id,
                member_id=member.id,
                member_name=member.full_name,
                attended=enrollment.attended,
                cancelled=enrollment.cancelled,
            )
            for enrollment, member in enrollment_result.all()
        ]
        responses.append(
            TrainerSessionResponse(
                session_id=class_session.id,
                class_type_id=class_session.class_type_id,
                scheduled_at=class_session.scheduled_at,
                duration_minutes=class_session.duration_minutes,
                capacity=class_session.capacity,
                enrolled_count=class_session.enrolled_count,
                members=members,
            )
        )
    return responses


@router.post("/enrollments/{enrollment_id}/attendance", response_model=TrainerEnrollmentMember)
async def mark_member_attendance(
    enrollment_id: UUID,
    attended: bool,
    claims: dict = Depends(require_roles(RoleEnum.TRAINER, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> TrainerEnrollmentMember:
    staff = await _current_staff(claims, session)
    enrollment = await session.get(ClassEnrollment, enrollment_id)
    if not enrollment or enrollment.branch_id != branch_id:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    class_session = await session.get(ClassSession, enrollment.session_id)
    if not class_session or class_session.trainer_staff_id != staff.id:
        raise HTTPException(status_code=403, detail="Enrollment is not assigned to this trainer")

    member = await session.get(Member, enrollment.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    enrollment.attended = attended
    session.add(enrollment)
    await session.commit()
    await session.refresh(enrollment)
    return TrainerEnrollmentMember(
        enrollment_id=enrollment.id,
        member_id=member.id,
        member_name=member.full_name,
        attended=enrollment.attended,
        cancelled=enrollment.cancelled,
    )
