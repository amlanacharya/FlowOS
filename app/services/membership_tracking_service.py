from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import (
    Member,
    MemberSubscription,
    SubscriptionAdjustment,
    SubscriptionPauseHistory,
)
from app.schemas.membership_tracking import (
    MembershipTrackingItem,
    PauseHistoryResponse,
    SubscriptionAdjustmentCreate,
    SubscriptionAdjustmentResponse,
)


class MembershipTrackingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_membership_tracking(
        self, branch_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[MembershipTrackingItem]:
        sub_statement = (
            select(MemberSubscription)
            .where(MemberSubscription.branch_id == branch_id)
            .order_by(MemberSubscription.end_date.asc())
            .offset(skip)
            .limit(limit)
        )
        sub_result = await self.session.execute(sub_statement)
        subscriptions = sub_result.scalars().all()

        if not subscriptions:
            return []

        member_ids = {sub.member_id for sub in subscriptions}
        member_statement = select(Member).where(Member.id.in_(member_ids))
        member_result = await self.session.execute(member_statement)
        members_by_id = {member.id: member for member in member_result.scalars().all()}

        today = date.today()
        items: List[MembershipTrackingItem] = []
        for sub in subscriptions:
            member = members_by_id.get(sub.member_id)
            if not member:
                continue
            items.append(
                MembershipTrackingItem(
                    subscription_id=sub.id,
                    member_id=member.id,
                    member_name=member.full_name,
                    member_phone=member.phone,
                    plan_id=sub.plan_id,
                    start_date=sub.start_date,
                    end_date=sub.end_date,
                    status=sub.status,
                    amount_due=float(sub.amount_due),
                    total_pause_days=sub.total_pause_days,
                    renewal_due_in_days=(sub.end_date - today).days,
                )
            )

        return items

    async def list_pause_history(self, subscription_id: UUID) -> List[PauseHistoryResponse]:
        statement = (
            select(SubscriptionPauseHistory)
            .where(SubscriptionPauseHistory.subscription_id == subscription_id)
            .order_by(SubscriptionPauseHistory.pause_date.desc())
        )
        result = await self.session.execute(statement)
        rows = result.scalars().all()

        return [
            PauseHistoryResponse(
                id=row.id,
                subscription_id=row.subscription_id,
                pause_date=row.pause_date,
                resume_date=row.resume_date,
                pause_days=row.pause_days,
                reason=row.reason,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def list_adjustments(self, subscription_id: UUID) -> List[SubscriptionAdjustmentResponse]:
        statement = (
            select(SubscriptionAdjustment)
            .where(SubscriptionAdjustment.subscription_id == subscription_id)
            .order_by(SubscriptionAdjustment.created_at.desc())
        )
        result = await self.session.execute(statement)
        rows = result.scalars().all()
        return [
            SubscriptionAdjustmentResponse(
                id=row.id,
                subscription_id=row.subscription_id,
                days_delta=row.days_delta,
                reason=row.reason,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def create_adjustment(
        self,
        branch_id: UUID,
        subscription_id: UUID,
        staff_id: UUID,
        payload: SubscriptionAdjustmentCreate,
    ) -> Optional[SubscriptionAdjustmentResponse]:
        subscription = await self.session.get(MemberSubscription, subscription_id)
        if not subscription or subscription.branch_id != branch_id:
            return None

        next_end_date = subscription.end_date + timedelta(days=payload.days_delta)
        if next_end_date < subscription.start_date:
            raise ValueError("Adjustment would make end date earlier than start date")

        subscription.end_date = next_end_date
        subscription.updated_at = datetime.utcnow()
        adjustment = SubscriptionAdjustment(
            branch_id=subscription.branch_id,
            member_id=subscription.member_id,
            subscription_id=subscription.id,
            days_delta=payload.days_delta,
            reason=payload.reason,
            created_by_staff_id=staff_id,
        )
        self.session.add(subscription)
        self.session.add(adjustment)
        await self.session.commit()
        await self.session.refresh(adjustment)
        return SubscriptionAdjustmentResponse(
            id=adjustment.id,
            subscription_id=adjustment.subscription_id,
            days_delta=adjustment.days_delta,
            reason=adjustment.reason,
            created_at=adjustment.created_at,
        )
