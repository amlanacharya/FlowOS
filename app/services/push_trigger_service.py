"""Service to trigger push notifications for member events."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Member
from app.services.notifications import dispatch_notification


async def notify_subscription_renewed(
    session: AsyncSession,
    branch_id: UUID,
    member_id: UUID,
    end_date: str,
) -> None:
    """Notify member of subscription renewal."""
    member = await session.get(Member, member_id)
    if not member or not member.push_opted_in or not member.push_token:
        return

    await dispatch_notification(
        session=session,
        branch_id=branch_id,
        recipient_type="member",
        recipient_id=member_id,
        to_phone=member.push_token,
        channel="web_push",
        event_type="subscription_renewed",
        template_name="subscription_renewed",
        params={"expiry_date": end_date},
    )


async def notify_payment_confirmed(
    session: AsyncSession,
    branch_id: UUID,
    member_id: UUID,
    amount: float,
) -> None:
    """Notify member of payment confirmation."""
    member = await session.get(Member, member_id)
    if not member or not member.push_opted_in or not member.push_token:
        return

    await dispatch_notification(
        session=session,
        branch_id=branch_id,
        recipient_type="member",
        recipient_id=member_id,
        to_phone=member.push_token,
        channel="web_push",
        event_type="payment_confirmed",
        template_name="payment_confirmed",
        params={"amount": f"₹{amount:.2f}"},
    )


async def notify_trial_expiring(
    session: AsyncSession,
    branch_id: UUID,
    member_id: UUID,
    days_remaining: int,
) -> None:
    """Notify member that trial is expiring soon."""
    member = await session.get(Member, member_id)
    if not member or not member.push_opted_in or not member.push_token:
        return

    await dispatch_notification(
        session=session,
        branch_id=branch_id,
        recipient_type="member",
        recipient_id=member_id,
        to_phone=member.push_token,
        channel="web_push",
        event_type="trial_expiring",
        template_name="trial_expiring",
        params={"days": days_remaining},
    )


async def notify_dues_overdue(
    session: AsyncSession,
    branch_id: UUID,
    member_id: UUID,
    amount_due: float,
) -> None:
    """Notify member of overdue dues."""
    member = await session.get(Member, member_id)
    if not member or not member.push_opted_in or not member.push_token:
        return

    await dispatch_notification(
        session=session,
        branch_id=branch_id,
        recipient_type="member",
        recipient_id=member_id,
        to_phone=member.push_token,
        channel="web_push",
        event_type="dues_overdue",
        template_name="dues_overdue",
        params={"amount": f"₹{amount_due:.2f}"},
    )


async def notify_class_enrolled(
    session: AsyncSession,
    branch_id: UUID,
    member_id: UUID,
    class_name: str,
) -> None:
    """Notify member of class enrollment."""
    member = await session.get(Member, member_id)
    if not member or not member.push_opted_in or not member.push_token:
        return

    await dispatch_notification(
        session=session,
        branch_id=branch_id,
        recipient_type="member",
        recipient_id=member_id,
        to_phone=member.push_token,
        channel="web_push",
        event_type="class_enrollment",
        template_name="class_enrollment",
        params={"class_name": class_name},
    )
