from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
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


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def daily_sales(self, branch_id: UUID, report_date: date) -> DailySalesReport:
        payments = await self.session.execute(
            select(Payment.mode, func.sum(Payment.amount))
            .where(Payment.branch_id == branch_id, Payment.payment_date == report_date)
            .group_by(Payment.mode)
        )
        collection_by_mode = {mode.value if hasattr(mode, "value") else str(mode): amount or Decimal("0") for mode, amount in payments.all()}
        total_collection = sum(collection_by_mode.values(), Decimal("0"))

        start = datetime.combine(report_date, datetime.min.time())
        end = datetime.combine(report_date, datetime.max.time())
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
        at_risk: list[AtRiskMember] = []
        today = date.today()
        for subscription, member in expired_rows:
            renewed_result = await self.session.execute(
                select(func.count(MemberSubscription.id)).where(
                    MemberSubscription.member_id == subscription.member_id,
                    MemberSubscription.start_date > subscription.end_date,
                    MemberSubscription.start_date <= subscription.end_date + timedelta(days=30),
                )
            )
            if (renewed_result.scalar() or 0) == 0:
                at_risk.append(
                    AtRiskMember(
                        member_id=member.id,
                        full_name=member.full_name,
                        expiry_date=subscription.end_date,
                        days_since_expiry=max((today - subscription.end_date).days, 0),
                    )
                )
        total_expired = len(expired_rows)
        return RetentionReport(
            total_expired=total_expired,
            not_renewed_within_30d=len(at_risk),
            churn_rate=round((len(at_risk) / total_expired) * 100, 2) if total_expired else 0,
            at_risk_members=at_risk,
        )

    async def trainer_performance(self, branch_id: UUID, date_from: date, date_to: date) -> list[TrainerPerformanceRow]:
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        result = await self.session.execute(
            select(ClassSession, Staff, User)
            .join(Staff, Staff.id == ClassSession.trainer_staff_id)
            .join(User, User.id == Staff.user_id)
            .where(ClassSession.branch_id == branch_id, ClassSession.scheduled_at >= start, ClassSession.scheduled_at <= end)
        )
        grouped: dict[UUID, dict] = {}
        for session, staff, user in result.all():
            bucket = grouped.setdefault(staff.id, {"name": user.full_name, "sessions": 0, "fill": 0.0, "member_hours": 0.0})
            bucket["sessions"] += 1
            bucket["fill"] += (session.enrolled_count / session.capacity) * 100 if session.capacity else 0
            bucket["member_hours"] += session.enrolled_count * (session.duration_minutes / 60)

        return [
            TrainerPerformanceRow(
                staff_id=staff_id,
                trainer_name=data["name"],
                sessions_delivered=data["sessions"],
                avg_fill_rate=round(data["fill"] / data["sessions"], 2) if data["sessions"] else 0,
                total_member_hours=round(data["member_hours"], 2),
            )
            for staff_id, data in grouped.items()
        ]

    async def revenue_forecast(self, branch_id: UUID) -> RevenueForecast:
        today = date.today()
        return RevenueForecast(
            next_30_days=await self._renewal_window(branch_id, today, today + timedelta(days=30)),
            next_60_days=await self._renewal_window(branch_id, today, today + timedelta(days=60)),
            next_90_days=await self._renewal_window(branch_id, today, today + timedelta(days=90)),
        )

    async def peak_hours(self, branch_id: UUID, date_from: date, date_to: date) -> list[PeakHourBucket]:
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
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
        rows = await self.session.execute(select(Payment).where(Payment.branch_id == branch_id, Payment.payment_date >= start))
        buckets: dict[str, dict[str, Decimal | int]] = {}
        for payment in rows.scalars().all():
            month = payment.payment_date.strftime("%Y-%m")
            bucket = buckets.setdefault(month, {"total": Decimal("0"), "count": 0})
            bucket["total"] = bucket["total"] + payment.amount
            bucket["count"] = int(bucket["count"]) + 1
        return [
            MonthlyRevenue(month=month, total_revenue=data["total"], payment_count=int(data["count"]))
            for month, data in sorted(buckets.items())
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
