from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.reminder import ReminderChecklistItem
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/api/v1/reminders", tags=["reminders"])


@router.get("/checklist", response_model=List[ReminderChecklistItem])
async def list_reminder_checklist(
    claims: dict = Depends(
        require_roles(RoleEnum.FRONT_DESK, RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)
    ),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> List[ReminderChecklistItem]:
    service = ReminderService(session)
    return await service.list_checklist(branch_id)
