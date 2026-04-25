from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Staff, StaffAttendance


class StaffAttendanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def checkin(
        self,
        branch_id: UUID,
        staff_id: UUID,
        notes: Optional[str] = None,
    ) -> StaffAttendance:
        """Record staff check-in."""
        today_start = datetime.combine(date.today(), datetime.min.time())

        # Check if already checked in today
        statement = (
            select(StaffAttendance)
            .where(StaffAttendance.staff_id == staff_id)
            .where(StaffAttendance.attendance_date == date.today())
            .where(StaffAttendance.checked_out_at == None)
        )
        result = await self.session.execute(statement)
        existing = result.scalars().first()

        if existing:
            raise ValueError("Staff already checked in today")

        attendance = StaffAttendance(
            branch_id=branch_id,
            staff_id=staff_id,
            date=date.today(),
            notes=notes,
        )
        self.session.add(attendance)
        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance

    async def checkout(
        self,
        staff_id: UUID,
        notes: Optional[str] = None,
    ) -> Optional[StaffAttendance]:
        """Record staff check-out."""
        statement = (
            select(StaffAttendance)
            .where(StaffAttendance.staff_id == staff_id)
            .where(StaffAttendance.attendance_date == date.today())
            .where(StaffAttendance.checked_out_at == None)
        )
        result = await self.session.execute(statement)
        attendance = result.scalars().first()

        if not attendance:
            return None

        attendance.checked_out_at = datetime.utcnow()
        if notes:
            attendance.notes = notes
        self.session.add(attendance)
        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance

    async def list_attendance(
        self,
        branch_id: UUID,
        staff_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[StaffAttendance], int]:
        """List staff attendance records."""
        statement = select(StaffAttendance).where(
            StaffAttendance.branch_id == branch_id
        )

        if staff_id:
            statement = statement.where(StaffAttendance.staff_id == staff_id)

        if date_from:
            statement = statement.where(StaffAttendance.attendance_date >= date_from)

        if date_to:
            statement = statement.where(StaffAttendance.attendance_date <= date_to)

        # Get total count
        count_statement = select(StaffAttendance).where(
            StaffAttendance.branch_id == branch_id
        )
        if staff_id:
            count_statement = count_statement.where(StaffAttendance.staff_id == staff_id)
        if date_from:
            count_statement = count_statement.where(StaffAttendance.attendance_date >= date_from)
        if date_to:
            count_statement = count_statement.where(StaffAttendance.attendance_date <= date_to)

        count_result = await self.session.execute(count_statement)
        total = len(count_result.scalars().all())

        statement = statement.order_by(StaffAttendance.checked_in_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all(), total

    async def get_summary(self, branch_id: UUID) -> dict:
        """Get staff attendance summary for today."""
        today = date.today()

        # Present today (has check_in record for today)
        present_statement = (
            select(StaffAttendance)
            .where(StaffAttendance.branch_id == branch_id)
            .where(StaffAttendance.attendance_date == today)
        )
        present_result = await self.session.execute(present_statement)
        present_count = len(present_result.scalars().all())

        # Currently checked in (no check_out)
        checked_in_statement = (
            select(StaffAttendance)
            .where(StaffAttendance.branch_id == branch_id)
            .where(StaffAttendance.attendance_date == today)
            .where(StaffAttendance.checked_out_at == None)
        )
        checked_in_result = await self.session.execute(checked_in_statement)
        checked_in_count = len(checked_in_result.scalars().all())

        # Staff count for this branch
        staff_statement = select(Staff).where(Staff.branch_id == branch_id)
        staff_result = await self.session.execute(staff_statement)
        total_staff = len(staff_result.scalars().all())

        return {
            "present_today": present_count,
            "absent_today": total_staff - present_count,
            "checked_in_now": checked_in_count,
        }
