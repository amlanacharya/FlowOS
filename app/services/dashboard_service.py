from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import (
    AttendanceTypeEnum,
    LeadStatusEnum,
    MemberStatusEnum,
    SubscriptionStatusEnum,
)
from app.models import Attendance, ClassSession, Lead, Member, MemberSubscription, Payment
from app.schemas.dashboard import (
    AttendanceTrend,
    DashboardSummary,
    DuesReport,
    LeadFunnel,
    RevenueBreakdown,
)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self, branch_id: UUID) -> DashboardSummary:
        """Get dashboard summary metrics for a branch."""
        # Active members
        active_result = await self.session.exec(
            select(func.count(Member.id)).where(
                (Member.branch_id == branch_id)
                & (Member.status == MemberStatusEnum.ACTIVE)
            )
        )
        active_members = active_result.first() or 0

        # Revenue MTD
        first_day_month = date.today().replace(day=1)
        revenue_result = await self.session.exec(
            select(func.sum(Payment.amount)).where(
                (Payment.branch_id == branch_id) & (Payment.payment_date >= first_day_month)
            )
        )
        revenue_mtd = revenue_result.first() or Decimal("0.00")

        # Leads this week
        week_ago = date.today() - timedelta(days=7)
        leads_result = await self.session.exec(
            select(func.count(Lead.id)).where(
                (Lead.branch_id == branch_id) & (Lead.created_at >= week_ago)
            )
        )
        leads_this_week = leads_result.first() or 0

        # Trials scheduled
        trials_scheduled_result = await self.session.exec(
            select(func.count(Lead.id)).where(
                (Lead.branch_id == branch_id)
                & (Lead.status == LeadStatusEnum.TRIAL_SCHEDULED)
            )
        )
        trials_scheduled = trials_scheduled_result.first() or 0

        # Trials converted
        trials_converted_result = await self.session.exec(
            select(func.count(Lead.id)).where(
                (Lead.branch_id == branch_id) & (Lead.status == LeadStatusEnum.CONVERTED)
            )
        )
        trials_converted = trials_converted_result.first() or 0

        # Renewals due in 7 days
        today = date.today()
        due_date = today + timedelta(days=7)
        renewals_result = await self.session.exec(
            select(func.count(MemberSubscription.id)).where(
                (MemberSubscription.branch_id == branch_id)
                & (MemberSubscription.end_date <= due_date)
                & (MemberSubscription.end_date >= today)
                & (MemberSubscription.status == SubscriptionStatusEnum.ACTIVE)
            )
        )
        renewals_due_7_days = renewals_result.first() or 0

        # Collections today
        today_collections_result = await self.session.exec(
            select(func.sum(Payment.amount)).where(
                (Payment.branch_id == branch_id) & (Payment.payment_date == today)
            )
        )
        collections_today = today_collections_result.first() or Decimal("0.00")

        # Outstanding dues
        outstanding_result = await self.session.exec(
            select(func.sum(MemberSubscription.amount_due)).where(
                (MemberSubscription.branch_id == branch_id)
                & (MemberSubscription.status != SubscriptionStatusEnum.EXPIRED)
            )
        )
        outstanding_dues = outstanding_result.first() or Decimal("0.00")

        # Classes today
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        classes_today_result = await self.session.exec(
            select(func.count(ClassSession.id)).where(
                (ClassSession.branch_id == branch_id)
                & (ClassSession.scheduled_at >= today_start)
                & (ClassSession.scheduled_at <= today_end)
                & (ClassSession.is_cancelled == False)
            )
        )
        classes_today = classes_today_result.first() or 0

        # Class fill rate
        sessions_result = await self.session.exec(
            select(ClassSession).where(
                (ClassSession.branch_id == branch_id) & (ClassSession.is_cancelled == False)
            )
        )
        all_sessions = sessions_result.all()
        fill_rate = 0.0
        if all_sessions:
            total_capacity = sum(s.capacity for s in all_sessions)
            total_enrolled = sum(s.enrolled_count for s in all_sessions)
            if total_capacity > 0:
                fill_rate = (total_enrolled / total_capacity) * 100

        # Inactive members
        inactive_result = await self.session.exec(
            select(func.count(Member.id)).where(
                (Member.branch_id == branch_id)
                & (Member.status == MemberStatusEnum.INACTIVE)
            )
        )
        inactive_members = inactive_result.first() or 0

        return DashboardSummary(
            active_members=active_members,
            total_revenue_mtd=float(revenue_mtd),
            leads_this_week=leads_this_week,
            trials_scheduled=trials_scheduled,
            trials_converted=trials_converted,
            renewals_due_7_days=renewals_due_7_days,
            collections_today=float(collections_today),
            outstanding_dues=float(outstanding_dues),
            classes_today=classes_today,
            class_fill_rate=fill_rate,
            inactive_members=inactive_members,
        )

    async def get_revenue_report(
        self, branch_id: UUID, days: int = 30
    ) -> List[RevenueBreakdown]:
        """Get revenue breakdown for specified number of days."""
        start_date = date.today() - timedelta(days=days)
        results = await self.session.exec(
            select(
                Payment.payment_date,
                func.sum(Payment.amount).label("total_amount"),
                func.count(Payment.id).label("count"),
            )
            .where((Payment.branch_id == branch_id) & (Payment.payment_date >= start_date))
            .group_by(Payment.payment_date)
            .order_by(Payment.payment_date)
        )
        rows = results.all()
        return [
            RevenueBreakdown(date=row[0], amount=row[1], count=row[2]) for row in rows
        ]

    async def get_dues_report(self, branch_id: UUID) -> List[DuesReport]:
        """Get outstanding dues report."""
        today = date.today()
        subs_result = await self.session.exec(
            select(MemberSubscription, Member)
            .join(Member)
            .where(
                (MemberSubscription.branch_id == branch_id)
                & (MemberSubscription.amount_due > 0)
            )
            .order_by(MemberSubscription.end_date)
        )
        subs = subs_result.all()

        result: List[DuesReport] = []
        for sub, member in subs:
            days_overdue = (today - sub.end_date).days if sub.end_date < today else 0
            result.append(
                DuesReport(
                    member_id=member.id,
                    full_name=member.full_name,
                    amount_due=float(sub.amount_due),
                    days_overdue=days_overdue,
                )
            )
        return result

    async def get_lead_funnel(self, branch_id: UUID) -> LeadFunnel:
        """Get lead funnel metrics."""
        funnel: dict = {}
        for status in LeadStatusEnum:
            count_result = await self.session.exec(
                select(func.count(Lead.id)).where(
                    (Lead.branch_id == branch_id) & (Lead.status == status)
                )
            )
            count = count_result.first() or 0
            funnel[status.value] = count

        return LeadFunnel(
            new=funnel.get(LeadStatusEnum.NEW.value, 0),
            contacted=funnel.get(LeadStatusEnum.CONTACTED.value, 0),
            trial_scheduled=funnel.get(LeadStatusEnum.TRIAL_SCHEDULED.value, 0),
            trial_attended=funnel.get(LeadStatusEnum.TRIAL_ATTENDED.value, 0),
            converted=funnel.get(LeadStatusEnum.CONVERTED.value, 0),
            lost=funnel.get(LeadStatusEnum.LOST.value, 0),
        )

    async def get_attendance_trends(
        self, branch_id: UUID, days: int = 30
    ) -> List[AttendanceTrend]:
        """Get attendance trends for specified number of days."""
        start_date = date.today() - timedelta(days=days)
        results = await self.session.exec(
            select(
                func.date(Attendance.checked_in_at).label("attendance_date"),
                func.count(Attendance.id).label("checkin_count"),
            )
            .where(
                (Attendance.branch_id == branch_id)
                & (Attendance.attendance_type == AttendanceTypeEnum.GYM_CHECKIN)
                & (Attendance.checked_in_at >= start_date)
            )
            .group_by(func.date(Attendance.checked_in_at))
            .order_by(func.date(Attendance.checked_in_at))
        )
        rows = results.all()

        return [
            AttendanceTrend(date=row[0], checkin_count=row[1], checkout_count=0)
            for row in rows
        ]
