from datetime import datetime, timedelta
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import ShiftTypeEnum
from app.models import StaffShift, StaffAttendance


class StaffShiftService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_shift(
        self,
        branch_id: UUID,
        staff_id: UUID,
        shift_date: datetime,
        shift_start: datetime,
        shift_end: datetime,
        shift_type: str = "regular",
        notes: str = None,
    ) -> StaffShift:
        """Create a new shift with overlap detection."""
        if shift_end <= shift_start:
            raise ValueError("Shift end must be after shift start")
        await self._check_overlap(staff_id, shift_start, shift_end)

        shift = StaffShift(
            branch_id=branch_id,
            staff_id=staff_id,
            shift_date=shift_date,
            shift_start=shift_start,
            shift_end=shift_end,
            shift_type=shift_type,
            notes=notes,
        )
        self.session.add(shift)
        await self.session.commit()
        await self.session.refresh(shift)
        return shift

    async def get_shift(self, shift_id: UUID) -> StaffShift:
        """Get shift by ID."""
        return await self.session.get(StaffShift, shift_id)

    async def update_shift(
        self,
        shift_id: UUID,
        shift_start: datetime = None,
        shift_end: datetime = None,
        shift_type: str = None,
        notes: str = None,
    ) -> StaffShift:
        """Update shift details."""
        shift = await self.session.get(StaffShift, shift_id)
        if not shift:
            return None

        if shift_start and shift_end:
            await self._check_overlap(shift.staff_id, shift_start, shift_end, exclude_id=shift_id)
            shift.shift_start = shift_start
            shift.shift_end = shift_end

        if shift_type:
            shift.shift_type = shift_type
        if notes is not None:
            shift.notes = notes

        shift.updated_at = datetime.utcnow()
        self.session.add(shift)
        await self.session.commit()
        await self.session.refresh(shift)
        return shift

    async def delete_shift(self, shift_id: UUID) -> bool:
        """Delete shift."""
        shift = await self.session.get(StaffShift, shift_id)
        if not shift:
            return False
        await self.session.delete(shift)
        await self.session.commit()
        return True

    async def list_shifts(
        self,
        branch_id: UUID,
        staff_id: UUID = None,
        date_from: datetime = None,
        date_to: datetime = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[StaffShift], int]:
        """List shifts with filtering."""
        conditions = [StaffShift.branch_id == branch_id]
        if staff_id:
            conditions.append(StaffShift.staff_id == staff_id)
        if date_from:
            conditions.append(StaffShift.shift_date >= date_from)
        if date_to:
            conditions.append(StaffShift.shift_date <= date_to)

        count_stmt = select(func.count()).select_from(StaffShift).where(*conditions)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        statement = select(StaffShift).where(*conditions).order_by(StaffShift.shift_date.desc()).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all(), total

    async def compare_shifts(
        self,
        branch_id: UUID,
        staff_id: UUID,
        date_from: datetime = None,
        date_to: datetime = None,
    ) -> dict:
        """Compare scheduled vs actual hours."""
        shift_conditions = [StaffShift.branch_id == branch_id, StaffShift.staff_id == staff_id]
        if date_from:
            shift_conditions.append(StaffShift.shift_date >= date_from)
        if date_to:
            shift_conditions.append(StaffShift.shift_date <= date_to)

        shift_stmt = select(StaffShift).where(*shift_conditions)
        shift_result = await self.session.execute(shift_stmt)
        shifts = shift_result.scalars().all()

        att_conditions = [StaffAttendance.staff_id == staff_id, StaffAttendance.branch_id == branch_id]
        if date_from:
            att_conditions.append(StaffAttendance.attendance_date >= date_from.date())
        if date_to:
            att_conditions.append(StaffAttendance.attendance_date <= date_to.date())

        att_result = await self.session.execute(select(StaffAttendance).where(*att_conditions))
        attendances = att_result.scalars().all()

        scheduled_hours = sum((s.shift_end - s.shift_start).total_seconds() / 3600 for s in shifts)
        actual_hours = sum(
            (a.checked_out_at - a.checked_in_at).total_seconds() / 3600
            if a.checked_out_at else 0
            for a in attendances
        )

        return {
            "staff_id": str(staff_id),
            "scheduled_hours": round(scheduled_hours, 2),
            "actual_hours": round(actual_hours, 2),
            "difference": round(scheduled_hours - actual_hours, 2),
            "attendance_count": len(attendances),
        }

    async def _check_overlap(
        self,
        staff_id: UUID,
        start: datetime,
        end: datetime,
        exclude_id: UUID = None,
    ) -> None:
        """Check if shift overlaps with existing shifts."""
        statement = select(StaffShift).where(
            StaffShift.staff_id == staff_id,
            StaffShift.shift_start < end,
            StaffShift.shift_end > start,
        )
        if exclude_id:
            statement = statement.where(StaffShift.id != exclude_id)

        result = await self.session.execute(statement)
        overlapping = result.scalars().first()

        if overlapping:
            raise ValueError("Shift overlaps with existing shift")
