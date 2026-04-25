from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import WorkoutLog
from app.schemas.workout import WorkoutLogCreate, WorkoutProgressPoint
from app.services.common import apply_pagination, branch_conditions, require_branch_member


class WorkoutService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_workout(
        self,
        branch_id: UUID,
        data: WorkoutLogCreate,
        logged_by_staff_id: Optional[UUID],
    ) -> WorkoutLog:
        await require_branch_member(self.session, branch_id, data.member_id)

        workout = WorkoutLog(
            branch_id=branch_id,
            member_id=data.member_id,
            workout_date=data.date or date.today(),
            exercise_name=data.exercise_name,
            sets=data.sets,
            reps=data.reps,
            weight_kg=data.weight_kg,
            notes=data.notes,
            logged_by_staff_id=logged_by_staff_id,
        )
        self.session.add(workout)
        await self.session.commit()
        await self.session.refresh(workout)
        return workout

    async def list_workouts(
        self,
        branch_id: UUID,
        member_id: UUID,
        exercise_name: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkoutLog]:
        conditions = branch_conditions(
            WorkoutLog,
            branch_id,
            WorkoutLog.member_id == member_id,
            WorkoutLog.exercise_name.ilike(f"%{exercise_name}%") if exercise_name else None,
            WorkoutLog.workout_date >= date_from if date_from else None,
            WorkoutLog.workout_date <= date_to if date_to else None,
        )

        statement = apply_pagination(
            select(WorkoutLog)
            .where(*conditions)
            .order_by(WorkoutLog.workout_date.desc(), WorkoutLog.created_at.desc()),
            skip,
            limit,
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def progress(
        self,
        branch_id: UUID,
        member_id: UUID,
        exercise_name: Optional[str] = None,
    ) -> list[WorkoutProgressPoint]:
        conditions = branch_conditions(
            WorkoutLog,
            branch_id,
            WorkoutLog.member_id == member_id,
            WorkoutLog.exercise_name.ilike(f"%{exercise_name}%") if exercise_name else None,
        )

        statement = (
            select(
                WorkoutLog.workout_date,
                func.count(WorkoutLog.id).label("sessions"),
                func.max(WorkoutLog.weight_kg).label("max_weight_kg"),
            )
            .where(*conditions)
            .group_by(WorkoutLog.workout_date)
            .order_by(WorkoutLog.workout_date)
        )
        result = await self.session.execute(statement)
        return [
            WorkoutProgressPoint(
                workout_date=row.workout_date,
                sessions=row.sessions,
                max_weight_kg=row.max_weight_kg,
            )
            for row in result.all()
        ]
