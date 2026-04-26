import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, literal_column, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import AttendanceTypeEnum, LeadStatusEnum, SubscriptionStatusEnum
from app.models import Attendance, ClassSession, Lead, Member, MemberSubscription, Payment, Staff, User
from app.schemas.report import (
    AtRiskMember,
    DailySalesReport,
    MonthlyRevenue,
    PeakHourBucket,
    RetentionReport,
    RevenueForecast,
    RevenueWindow,
    TrainerPerformanceRow,
)


@dataclass
class TrainerPerformanceBucket:
    """Bucket for aggregating trainer performance metrics."""
    staff_id: UUID
    name: str
    sessions: int = 0
    fill: float = 0.0
    member_hours: float = 0.0


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _date_to_datetime_range(self, from_date: date, to_date: date = None) -> tuple[datetime, datetime]:
        """Convert date range to datetime range (start of day to end of day)."""
        if to_date is None:
            to_date = from_date
        start = datetime.combine(from_date, datetime.min.time())
        end = datetime.combine(to_date, datetime.max.time())
        return start, end

    async def daily_sales(self, branch_id: UUID, report_date: date) -> DailySalesReport:
        payments = await self.session.execute(
            select(Payment.mode, func.sum(Payment.amount))
            .where(Payment.branch_id == branch_id, Payment.payment_date == report_date)
            .group_by(Payment.mode)
        )
        collection_by_mode = {mode.value if hasattr(mode, "value") else str(mode): amount or Decimal("0") for mode, amount in payments.all()}
        total_collection = sum(collection_by_mode.values(), Decimal("0"))

        start, end = self._date_to_datetime_range(report_date)
        new_members = await self._count(Member.id, Member.branch_id == branch_id, Member.created_at >= start, Member.created_at <= end)
        renewals = await self._count(MemberSubscription.id, MemberSubscription.branch_id == branch_id, MemberSubscription.created_at >= start, MemberSubscription.created_at <= end)
        converted = await self._count(Lead.id, Lead.branch_id == branch_id, Lead.status == LeadStatusEnum.CONVERTED, Lead.updated_at >= start, Lead.updated_at <= end)

        return DailySalesReport(
            date=report_date,
            total_collection=total_collection,
            collection_by_mode=collection_by_mode,
            new_members=new_members,
            renewals=renewals,
            leads_converted=converted,
        )

    async def retention(self, branch_id: UUID, date_from: date, date_to: date) -> RetentionReport:
        expired_result = await self.session.execute(
            select(MemberSubscription, Member)
            .join(Member, Member.id == MemberSubscription.member_id)
            .where(
                MemberSubscription.branch_id == branch_id,
                MemberSubscription.end_date >= date_from,
                MemberSubscription.end_date <= date_to,
            )
        )
        expired_rows = expired_result.all()
        total_expired = len(expired_rows)

        if total_expired == 0:
            return RetentionReport(
                total_expired=0,
                not_renewed_within_30d=0,
                churn_rate=0.0,
                at_risk_members=[],
            )

        at_risk: list[AtRiskMember] = []
        today = date.today()

        for subscription, member in expired_rows:
            renewed_count = await self._count(
                MemberSubscription.id,
                MemberSubscription.member_id == subscription.member_id,
                MemberSubscription.start_date > subscription.end_date,
                MemberSubscription.start_date <= subscription.end_date + timedelta(days=30),
            )
            if renewed_count == 0:
                at_risk.append(
                    AtRiskMember(
                        member_id=member.id,
                        full_name=member.full_name,
                        expiry_date=subscription.end_date,
                        days_since_expiry=max((today - subscription.end_date).days, 0),
                    )
                )

        return RetentionReport(
            total_expired=total_expired,
            not_renewed_within_30d=len(at_risk),
            churn_rate=round((len(at_risk) / total_expired) * 100, 2) if total_expired else 0,
            at_risk_members=at_risk,
        )

    async def trainer_performance(self, branch_id: UUID, date_from: date, date_to: date) -> list[TrainerPerformanceRow]:
        start, end = self._date_to_datetime_range(date_from, date_to)
        result = await self.session.execute(
            select(ClassSession, Staff, User)
            .join(Staff, Staff.id == ClassSession.trainer_staff_id)
            .join(User, User.id == Staff.user_id)
            .where(ClassSession.branch_id == branch_id, ClassSession.scheduled_at >= start, ClassSession.scheduled_at <= end)
        )
        grouped: dict[UUID, TrainerPerformanceBucket] = {}
        for session, staff, user in result.all():
            if staff.id not in grouped:
                grouped[staff.id] = TrainerPerformanceBucket(staff_id=staff.id, name=user.full_name)
            bucket = grouped[staff.id]
            bucket.sessions += 1
            bucket.fill += (session.enrolled_count / session.capacity) * 100 if session.capacity else 0
            bucket.member_hours += session.enrolled_count * (session.duration_minutes / 60)

        return [
            TrainerPerformanceRow(
                staff_id=bucket.staff_id,
                trainer_name=bucket.name,
                sessions_delivered=bucket.sessions,
                avg_fill_rate=round(bucket.fill / bucket.sessions, 2) if bucket.sessions else 0,
                total_member_hours=round(bucket.member_hours, 2),
            )
            for bucket in grouped.values()
        ]

    async def revenue_forecast(self, branch_id: UUID) -> RevenueForecast:
        today = date.today()
        next_30, next_60, next_90 = await asyncio.gather(
            self._renewal_window(branch_id, today, today + timedelta(days=30)),
            self._renewal_window(branch_id, today, today + timedelta(days=60)),
            self._renewal_window(branch_id, today, today + timedelta(days=90)),
        )
        return RevenueForecast(
            next_30_days=next_30,
            next_60_days=next_60,
            next_90_days=next_90,
        )

    async def peak_hours(self, branch_id: UUID, date_from: date, date_to: date) -> list[PeakHourBucket]:
        start, end = self._date_to_datetime_range(date_from, date_to)
        rows = await self.session.execute(
            select(func.extract("hour", Attendance.checked_in_at), func.count(Attendance.id))
            .where(
                Attendance.branch_id == branch_id,
                Attendance.attendance_type == AttendanceTypeEnum.GYM_CHECKIN,
                Attendance.checked_in_at >= start,
                Attendance.checked_in_at <= end,
            )
            .group_by(func.extract("hour", Attendance.checked_in_at))
        )
        counts = {int(hour): int(count) for hour, count in rows.all()}
        return [PeakHourBucket(hour=hour, checkin_count=counts.get(hour, 0)) for hour in range(24)]

    async def monthly_revenue(self, branch_id: UUID, months: int = 12) -> list[MonthlyRevenue]:
        start = date.today().replace(day=1) - timedelta(days=31 * max(months - 1, 0))
        month_expr = literal_column("date_trunc('month', payments.payment_date)")
        rows = await self.session.execute(
            select(
                month_expr.label("month"),
                func.sum(Payment.amount).label("total"),
                func.count(Payment.id).label("count"),
            )
            .where(Payment.branch_id == branch_id, Payment.payment_date >= start)
            .group_by(month_expr)
            .order_by(month_expr)
        )
        return [
            MonthlyRevenue(
                month=month.strftime("%Y-%m"),
                total_revenue=total or Decimal("0"),
                payment_count=int(count or 0),
            )
            for month, total, count in rows.all()
        ]

    async def _renewal_window(self, branch_id: UUID, start: date, end: date) -> RevenueWindow:
        result = await self.session.execute(
            select(func.count(MemberSubscription.id), func.sum(MemberSubscription.total_amount)).where(
                MemberSubscription.branch_id == branch_id,
                MemberSubscription.status == SubscriptionStatusEnum.ACTIVE,
                MemberSubscription.end_date >= start,
                MemberSubscription.end_date <= end,
            )
        )
        count, amount = result.one()
        return RevenueWindow(count=count or 0, projected_amount=amount or Decimal("0"))

    async def _count(self, column, *conditions) -> int:
        result = await self.session.execute(select(func.count(column)).where(*conditions))
        return result.scalar() or 0
