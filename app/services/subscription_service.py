from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import InvoiceTypeEnum, SubscriptionStatusEnum
from app.models import MembershipPlan, MemberSubscription, SubscriptionPauseHistory
from app.services.invoice_service import InvoiceService


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
        create_invoice: bool = True,
        invoice_type: InvoiceTypeEnum = InvoiceTypeEnum.NEW_JOIN,
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
        await self.session.flush()

        if create_invoice:
            invoice_service = InvoiceService(self.session)
            await invoice_service.create_subscription_invoice(
                branch_id=branch_id,
                member_id=member_id,
                subscription_id=sub.id,
                plan=plan,
                created_by_staff_id=staff_id,
                invoice_type=invoice_type,
            )

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
        self,
        sub_id: UUID,
        staff_id: UUID,
        pause_date: date,
        reason: Optional[str] = None,
    ) -> Optional[MemberSubscription]:
        sub = await self.get_subscription(sub_id)
        if not sub:
            return None

        open_pause_statement = (
            select(SubscriptionPauseHistory)
            .where(SubscriptionPauseHistory.subscription_id == sub.id)
            .where(SubscriptionPauseHistory.resume_date.is_(None))
            .order_by(SubscriptionPauseHistory.created_at.desc())
            .limit(1)
        )
        open_pause_result = await self.session.execute(open_pause_statement)
        if open_pause_result.scalars().first():
            raise ValueError("Subscription already paused and waiting for resume date")

        sub.status = SubscriptionStatusEnum.PAUSED
        sub.freeze_start = pause_date
        sub.last_pause_date = pause_date

        pause_event = SubscriptionPauseHistory(
            branch_id=sub.branch_id,
            member_id=sub.member_id,
            subscription_id=sub.id,
            pause_date=pause_date,
            reason=reason,
            created_by_staff_id=staff_id,
        )
        self.session.add(pause_event)
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def resume_subscription(
        self, sub_id: UUID, resume_date: date
    ) -> Optional[MemberSubscription]:
        sub = await self.get_subscription(sub_id)
        if not sub:
            return None

        open_pause_statement = (
            select(SubscriptionPauseHistory)
            .where(SubscriptionPauseHistory.subscription_id == sub.id)
            .where(SubscriptionPauseHistory.resume_date.is_(None))
            .order_by(SubscriptionPauseHistory.created_at.desc())
            .limit(1)
        )
        open_pause_result = await self.session.execute(open_pause_statement)
        pause_event = open_pause_result.scalars().first()
        if not pause_event:
            raise ValueError("No active pause entry found for this subscription")
        if resume_date < pause_event.pause_date:
            raise ValueError("Resume date cannot be before pause date")

        pause_days = (resume_date - pause_event.pause_date).days
        pause_event.resume_date = resume_date
        pause_event.pause_days = max(0, pause_days)
        pause_event.updated_at = datetime.utcnow()

        extension_days = max(0, pause_days)
        if extension_days > 0:
            sub.end_date = sub.end_date + timedelta(days=extension_days)
        sub.total_pause_days += extension_days
        sub.freeze_days_used += extension_days
        sub.status = SubscriptionStatusEnum.ACTIVE
        sub.freeze_start = None
        sub.last_resume_date = resume_date
        sub.updated_at = datetime.utcnow()
        self.session.add(pause_event)
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def renew_subscription(
        self, sub_id: UUID, staff_id: UUID, plan_id: Optional[UUID] = None
    ) -> Optional[MemberSubscription]:
        old_sub = await self.get_subscription(sub_id)
        if not old_sub:
            return None
        selected_plan_id = plan_id or old_sub.plan_id
        plan = await self.session.get(MembershipPlan, selected_plan_id)
        if not plan:
            raise ValueError("Plan not found")

        new_sub = MemberSubscription(
            member_id=old_sub.member_id,
            branch_id=old_sub.branch_id,
            plan_id=selected_plan_id,
            start_date=old_sub.end_date + timedelta(days=1),
            end_date=old_sub.end_date + timedelta(days=plan.duration_days + 1),
            total_amount=plan.price,
            amount_due=plan.price,
            created_by_staff_id=staff_id,
        )
        self.session.add(new_sub)
        await self.session.flush()

        invoice_service = InvoiceService(self.session)
        await invoice_service.create_subscription_invoice(
            branch_id=old_sub.branch_id,
            member_id=old_sub.member_id,
            subscription_id=new_sub.id,
            plan=plan,
            created_by_staff_id=staff_id,
            invoice_type=InvoiceTypeEnum.RENEWAL,
        )

        await self.session.commit()
        await self.session.refresh(new_sub)
        return new_sub
