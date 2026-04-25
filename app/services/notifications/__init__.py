import os
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NotificationLog

from .base import BaseNotificationProvider
from .stub import StubProvider
from .whatsapp import WhatsAppProvider


def get_provider() -> BaseNotificationProvider:
    """Get notification provider based on environment variable."""
    provider_name = os.environ.get("NOTIFICATION_PROVIDER", "stub").lower()

    if provider_name == "whatsapp":
        return WhatsAppProvider()
    else:
        return StubProvider()


async def dispatch_notification(
    session: AsyncSession,
    branch_id: UUID,
    recipient_type: str,
    recipient_id: UUID,
    to_phone: str,
    channel: str,
    event_type: str,
    template_name: str,
    params: dict,
) -> None:
    """
    Dispatch notification through configured provider.

    Creates NotificationLog entry and sends via provider.
    On failure, creates log entry with error and queues retry.

    Args:
        session: Database session
        branch_id: Branch UUID
        recipient_type: Type of recipient ('member', 'staff', etc.)
        recipient_id: UUID of recipient
        to_phone: Phone number in E.164 format
        channel: Notification channel (e.g., 'whatsapp', 'web_push')
        event_type: Event that triggered notification
        template_name: Template to use for message
        params: Parameters for template substitution
    """
    provider = get_provider()

    try:
        # Send notification
        provider_ref = await provider.send(to_phone, template_name, params)

        # Log success
        log = NotificationLog(
            branch_id=branch_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel,
            event_type=event_type,
            payload=params,
            status="sent",
            provider_ref=provider_ref,
            retry_count=0,
        )
        session.add(log)
        await session.commit()

    except Exception as e:
        # Log failure
        log = NotificationLog(
            branch_id=branch_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel,
            event_type=event_type,
            payload=params,
            status="failed",
            error_message=str(e),
            retry_count=1,
        )
        session.add(log)
        await session.commit()

        # TODO: Queue retry task via ARQ if retry_count < 3
        print(f"[NOTIFICATION FAILED] {event_type} to {to_phone}: {str(e)}")


__all__ = ["get_provider", "dispatch_notification", "BaseNotificationProvider"]
