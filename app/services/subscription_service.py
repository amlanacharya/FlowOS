from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import SubscriptionStatusEnum
from app.models import MembershipPlan, MemberSubscription
from app.schemas.member_subscription import SubscriptionCreate


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_subscription(
        self,
        branch_id: UUID,
        member_id: UUID,
        plan_id: UUID,
        staff_id: UUID,
        start_date: Optional[date] = None,
    ) -> MemberSubscription:
        plan = await self.session.get(MembershipPlan, plan_id)
        if not plan:
            raise ValueError("Plan not found")

        start = start_date or date.today()
        end = start + timedelta(days=plan.duration_days)

        sub = MemberSubscription(
            member_id=member_id,
            branch_id=branch_id,
            plan_id=plan_id,
            start_date=start,
            end_date=end,
            total_amount=plan.price,
            amount_due=plan.price,
            created_by_staff_id=staff_id,
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def get_subscription(self, sub_id: UUID) -> Optional[MemberSubscription]:
        return await self.session.get(MemberSubscription, sub_id)

    async def list_subscriptions(
        self,
        branch_id: UUID,
        status: Optional[SubscriptionStatusEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MemberSubscription]:
        query = select(MemberSubscription).where(
            MemberSubscription.branch_id == branch_id
        )
        if status:
            query = query.where(MemberSubscription.status == status)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def pause_subscription(
        self, sub_id: UUID, freeze_days: int = 30
    ) -> Optional[MemberSubscription]:
        sub = await self.get_subscription(sub_id)
        if not sub:
            return None
        sub.status = SubscriptionStatusEnum.PAUSED
        sub.freeze_start = date.today()
        sub.freeze_days_used += freeze_days
        sub.end_date = sub.end_date + timedelta(days=freeze_days)
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def resume_subscription(self, sub_id: UUID) -> Optional[MemberSubscription]:
        sub = await self.get_subscription(sub_id)
        if not sub:
            return None
        sub.status = SubscriptionStatusEnum.ACTIVE
        sub.freeze_start = None
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def renew_subscription(
        self, sub_id: UUID, staff_id: UUID
    ) -> Optional[MemberSubscription]:
        old_sub = await self.get_subscription(sub_id)
        if not old_sub:
            return None
        plan = await self.session.get(MembershipPlan, old_sub.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        new_sub = MemberSubscription(
            member_id=old_sub.member_id,
            branch_id=old_sub.branch_id,
            plan_id=old_sub.plan_id,
            start_date=old_sub.end_date + timedelta(days=1),
            end_date=old_sub.end_date + timedelta(days=plan.duration_days + 1),
            total_amount=plan.price,
            amount_due=plan.price,
            created_by_staff_id=staff_id,
        )
        self.session.add(new_sub)
        await self.session.commit()
        await self.session.refresh(new_sub)
        return new_sub
