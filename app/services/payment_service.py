from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select

from app.models import MemberSubscription, Payment
from app.schemas.payment import PaymentCreate
from app.core.enums import SubscriptionStatusEnum


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_payment(self, branch_id: UUID, data: PaymentCreate, staff_id: UUID) -> Payment:
        """Record a payment and update subscription amounts."""
        payment = Payment(
            branch_id=branch_id,
            received_by_staff_id=staff_id,
            **data.dict(exclude_unset=True)
        )
        self.session.add(payment)

        # Update subscription amount_due and amount_paid atomically
        if data.subscription_id:
            sub = await self.session.get(MemberSubscription, data.subscription_id)
            if sub:
                sub.amount_paid = sub.amount_paid + data.amount
                sub.amount_due = max(Decimal("0.00"), sub.total_amount - sub.amount_paid)
                self.session.add(sub)

        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        """Retrieve a payment by ID."""
        return await self.session.get(Payment, payment_id)

    async def list_payments(self, branch_id: UUID, skip: int = 0, limit: int = 100) -> List[Payment]:
        """List all payments for a branch."""
        statement = (
            select(Payment)
            .where(Payment.branch_id == branch_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_member_payments(self, member_id: UUID, skip: int = 0, limit: int = 100) -> List[Payment]:
        """List all payments for a member."""
        statement = (
            select(Payment)
            .where(Payment.member_id == member_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_summary(self, branch_id: UUID) -> dict:
        """Get payment summary for today and outstanding dues."""
        today = date.today()

        # Get today's collection
        statement = (
            select(func.sum(Payment.amount))
            .where(Payment.branch_id == branch_id)
            .where(Payment.payment_date == today)
        )
        result = await self.session.execute(statement)
        today_collection = result.scalar() or Decimal("0.00")

        # Get outstanding dues
        statement = (
            select(func.sum(MemberSubscription.amount_due))
            .where(MemberSubscription.branch_id == branch_id)
            .where(MemberSubscription.status != SubscriptionStatusEnum.EXPIRED)
        )
        result = await self.session.execute(statement)
        outstanding_dues = result.scalar() or Decimal("0.00")

        return {
            "today_collection": float(today_collection),
            "outstanding_dues": float(outstanding_dues),
        }
