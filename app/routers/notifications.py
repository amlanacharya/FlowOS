from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.notification import NotificationLogResponse, SendNotificationRequest
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationLogResponse])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[NotificationLogResponse]:
    """List notification logs."""
    service = NotificationService(session)
    return await service.list_logs(branch_id, skip, limit)


@router.post("", response_model=NotificationLogResponse)
async def send_notification(
    data: SendNotificationRequest,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> NotificationLogResponse:
    """Send a notification and log it."""
    service = NotificationService(session)
    log = await service.log_notification(
        branch_id,
        data.recipient_type,
        data.recipient_id,
        data.channel,
        data.event_type,
        data.payload,
    )
    # In POC, just log it. Later integrate with actual notification providers
    await service.mark_sent(log.id)
    return log
