from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
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
        conditions = [StaffAttendance.branch_id == branch_id]

        if staff_id:
            conditions.append(StaffAttendance.staff_id == staff_id)

        if date_from:
            conditions.append(StaffAttendance.attendance_date >= date_from)

        if date_to:
            conditions.append(StaffAttendance.attendance_date <= date_to)

        count_result = await self.session.execute(
            select(func.count()).select_from(StaffAttendance).where(*conditions)
        )
        total = count_result.scalar() or 0

        statement = select(StaffAttendance).where(*conditions).order_by(StaffAttendance.checked_in_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all(), total

    async def get_summary(self, branch_id: UUID) -> dict:
        """Get staff attendance summary for today."""
        today = date.today()

        present_result = await self.session.execute(
            select(func.count()).select_from(StaffAttendance).where(
                StaffAttendance.branch_id == branch_id,
                StaffAttendance.attendance_date == today,
            )
        )
        present_count = present_result.scalar() or 0

        checked_in_result = await self.session.execute(
            select(func.count()).select_from(StaffAttendance).where(
                StaffAttendance.branch_id == branch_id,
                StaffAttendance.attendance_date == today,
                StaffAttendance.checked_out_at == None,
            )
        )
        checked_in_count = checked_in_result.scalar() or 0

        total_staff_result = await self.session.execute(
            select(func.count()).select_from(Staff).where(Staff.branch_id == branch_id)
        )
        total_staff = total_staff_result.scalar() or 0

        return {
            "present_today": present_count,
            "absent_today": total_staff - present_count,
            "checked_in_now": checked_in_count,
        }
