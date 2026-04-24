from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.notification_log import NotificationLog


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_notification(
        self,
        branch_id: UUID,
        recipient_type: str,
        recipient_id: UUID,
        channel: str,
        event_type: str,
        payload: Optional[dict] = None,
    ) -> NotificationLog:
        """Log a notification event."""
        log = NotificationLog(
            branch_id=branch_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel,
            event_type=event_type,
            payload=payload,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def mark_sent(self, log_id: UUID) -> Optional[NotificationLog]:
        """Mark a notification as successfully sent."""
        log = await self.session.get(NotificationLog, log_id)
        if log:
            log.status = "sent"
            log.sent_at = datetime.utcnow()
            self.session.add(log)
            await self.session.commit()
            await self.session.refresh(log)
        return log

    async def mark_failed(self, log_id: UUID, error: str) -> Optional[NotificationLog]:
        """Mark a notification as failed."""
        log = await self.session.get(NotificationLog, log_id)
        if log:
            log.status = "failed"
            log.error_message = error
            self.session.add(log)
            await self.session.commit()
            await self.session.refresh(log)
        return log

    async def list_logs(
        self, branch_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[NotificationLog]:
        """List notification logs for a branch."""
        result = await self.session.exec(
            select(NotificationLog)
            .where(NotificationLog.branch_id == branch_id)
            .order_by(NotificationLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.all()
