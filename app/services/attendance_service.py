from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Attendance, Member, MemberSubscription
from app.core.enums import AttendanceTypeEnum, MemberStatusEnum, SubscriptionStatusEnum


class AttendanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def checkin(
        self,
        branch_id: UUID,
        member_id: Optional[UUID] = None,
        member_code: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Attendance]:
        """Record a member check-in."""
        # Resolve member ID if only code provided
        if member_code and not member_id:
            statement = select(Member).where(Member.member_code == member_code)
            result = await self.session.execute(statement)
            member = result.scalars().first()
            if member:
                member_id = member.id

        if not member_id:
            raise ValueError("Member not found")

        # Check for duplicate checkin today
        today_start = datetime.combine(date.today(), datetime.min.time())
        statement = (
            select(Attendance)
            .where(Attendance.member_id == member_id)
            .where(Attendance.attendance_type == AttendanceTypeEnum.GYM_CHECKIN)
            .where(Attendance.checked_in_at >= today_start)
        )
        result = await self.session.execute(statement)
        existing = result.scalars().first()

        if existing and not existing.checked_out_at:
            raise ValueError("Member already checked in today")

        attendance = Attendance(
            branch_id=branch_id,
            member_id=member_id,
            attendance_type=AttendanceTypeEnum.GYM_CHECKIN,
            notes=notes,
        )
        self.session.add(attendance)
        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance

    async def checkout(self, member_id: UUID) -> Optional[Attendance]:
        """Record a member check-out."""
        today_start = datetime.combine(date.today(), datetime.min.time())
        statement = (
            select(Attendance)
            .where(Attendance.member_id == member_id)
            .where(Attendance.checked_out_at == None)
            .where(Attendance.checked_in_at >= today_start)
            .order_by(Attendance.checked_in_at.desc())
        )
        result = await self.session.execute(statement)
        attendance = result.scalars().first()

        if not attendance:
            return None

        attendance.checked_out_at = datetime.utcnow()
        self.session.add(attendance)
        await self.session.commit()
        await self.session.refresh(attendance)
        return attendance

    async def list_attendance(self, branch_id: UUID, skip: int = 0, limit: int = 100) -> List[Attendance]:
        """List all attendance records for a branch."""
        statement = (
            select(Attendance)
            .where(Attendance.branch_id == branch_id)
            .order_by(Attendance.checked_in_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_today_checkins(self, branch_id: UUID) -> List[Attendance]:
        """List all check-ins for today."""
        today_start = datetime.combine(date.today(), datetime.min.time())
        statement = (
            select(Attendance)
            .where(Attendance.branch_id == branch_id)
            .where(Attendance.attendance_type == AttendanceTypeEnum.GYM_CHECKIN)
            .where(Attendance.checked_in_at >= today_start)
            .order_by(Attendance.checked_in_at.desc())
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def qr_checkin(
        self,
        branch_id: UUID,
        member_code: str,
        notes: Optional[str] = None,
    ) -> dict:
        """QR code check-in with member and subscription details."""
        # 1. Find member by code and branch
        statement = (
            select(Member)
            .where(Member.member_code == member_code)
            .where(Member.branch_id == branch_id)
        )
        result = await self.session.execute(statement)
        member = result.scalars().first()

        if not member:
            raise ValueError("member_code not found")

        # 2. Check member status
        if member.status in (MemberStatusEnum.EXPIRED, MemberStatusEnum.INACTIVE):
            raise ValueError(f"Member {member.full_name} status is {member.status.value}")

        # 3. Check for duplicate checkin today
        today_start = datetime.combine(date.today(), datetime.min.time())
        statement = (
            select(Attendance)
            .where(Attendance.member_id == member.id)
            .where(Attendance.attendance_type == AttendanceTypeEnum.GYM_CHECKIN)
            .where(Attendance.checked_in_at >= today_start)
        )
        result = await self.session.execute(statement)
        existing = result.scalars().first()

        if existing and not existing.checked_out_at:
            raise ValueError("Member already checked in today")

        # 4. Create attendance record
        attendance = Attendance(
            branch_id=branch_id,
            member_id=member.id,
            attendance_type=AttendanceTypeEnum.GYM_CHECKIN,
            notes=notes,
        )
        self.session.add(attendance)
        await self.session.commit()
        await self.session.refresh(attendance)

        # 5. Get first active subscription
        statement = (
            select(MemberSubscription)
            .where(MemberSubscription.member_id == member.id)
            .where(MemberSubscription.status == SubscriptionStatusEnum.ACTIVE)
            .order_by(MemberSubscription.end_date.desc())
        )
        result = await self.session.execute(statement)
        subscription = result.scalars().first()

        # 6. Build response
        return {
            "attendance_id": attendance.id,
            "member_id": member.id,
            "member_name": member.full_name,
            "subscription_end_date": subscription.end_date if subscription else None,
            "amount_due": subscription.amount_due if subscription else Decimal("0.00"),
            "checked_in_at": attendance.checked_in_at,
        }
