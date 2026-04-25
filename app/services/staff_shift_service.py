from datetime import datetime, timedelta
from typing import List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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
        """Create a new shift. Checks for overlaps."""
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
        statement = select(StaffShift).where(StaffShift.branch_id == branch_id)

        if staff_id:
            statement = statement.where(StaffShift.staff_id == staff_id)
        if date_from:
            statement = statement.where(StaffShift.shift_date >= date_from)
        if date_to:
            statement = statement.where(StaffShift.shift_date <= date_to)

        count_statement = select(StaffShift).where(StaffShift.branch_id == branch_id)
        if staff_id:
            count_statement = count_statement.where(StaffShift.staff_id == staff_id)
        if date_from:
            count_statement = count_statement.where(StaffShift.shift_date >= date_from)
        if date_to:
            count_statement = count_statement.where(StaffShift.shift_date <= date_to)

        count_result = await self.session.execute(count_statement)
        total = len(count_result.scalars().all())

        statement = statement.order_by(StaffShift.shift_date.desc()).offset(skip).limit(limit)
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
        shifts, _ = await self.list_shifts(branch_id, staff_id, date_from, date_to, limit=1000)
        attendance_statement = select(StaffAttendance).where(
            StaffAttendance.staff_id == staff_id,
            StaffAttendance.branch_id == branch_id,
        )
        if date_from:
            attendance_statement = attendance_statement.where(
                StaffAttendance.attendance_date >= date_from.date()
            )
        if date_to:
            attendance_statement = attendance_statement.where(
                StaffAttendance.attendance_date <= date_to.date()
            )

        attendance_result = await self.session.execute(attendance_statement)
        attendances = attendance_result.scalars().all()

        scheduled_hours = sum(
            (shift.shift_end - shift.shift_start).total_seconds() / 3600 for shift in shifts
        )

        actual_hours = sum(
            (att.checked_out_at - att.checked_in_at).total_seconds() / 3600
            if att.checked_out_at
            else 0
            for att in attendances
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
