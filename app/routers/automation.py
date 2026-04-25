from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import get_branch_scope, require_roles
from app.schemas.automation import AutomationRuleCreate, AutomationRuleList, AutomationRuleResponse, AutomationRuleUpdate
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/api/v1/automation/rules", tags=["automation"])


@router.post("", response_model=AutomationRuleResponse)
async def create_rule(
    data: AutomationRuleCreate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> AutomationRuleResponse:
    return await AutomationService(session).create_rule(branch_id, data)


@router.get("", response_model=AutomationRuleList)
async def list_rules(
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> AutomationRuleList:
    return await AutomationService(session).list_rules(branch_id)


@router.patch("/{rule_id}", response_model=AutomationRuleResponse)
async def update_rule(
    rule_id: UUID,
    data: AutomationRuleUpdate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> AutomationRuleResponse:
    rule = await AutomationService(session).update_rule(branch_id, rule_id, data)
    if not rule:
        raise ResourceNotFoundException()
    return rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id=Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not await AutomationService(session).delete_rule(branch_id, rule_id):
        raise ResourceNotFoundException()
    return {"message": "Automation rule deleted"}
