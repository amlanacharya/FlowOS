from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import AutomationRule
from app.schemas.automation import AutomationRuleCreate, AutomationRuleList, AutomationRuleUpdate


class AutomationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_rule(self, branch_id: UUID, data: AutomationRuleCreate) -> AutomationRule:
        rule = AutomationRule(branch_id=branch_id, **data.model_dump())
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def list_rules(self, branch_id: UUID, skip: int = 0, limit: int = 100) -> AutomationRuleList:
        count_result = await self.session.execute(select(func.count()).select_from(AutomationRule).where(AutomationRule.branch_id == branch_id))
        result = await self.session.execute(
            select(AutomationRule)
            .where(AutomationRule.branch_id == branch_id)
            .order_by(AutomationRule.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return AutomationRuleList(items=list(result.scalars().all()), total=count_result.scalar() or 0)

    async def update_rule(self, branch_id: UUID, rule_id: UUID, data: AutomationRuleUpdate) -> Optional[AutomationRule]:
        rule = await self.session.get(AutomationRule, rule_id)
        if not rule or rule.branch_id != branch_id:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        rule.updated_at = datetime.utcnow()
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, branch_id: UUID, rule_id: UUID) -> bool:
        rule = await self.session.get(AutomationRule, rule_id)
        if not rule or rule.branch_id != branch_id:
            return False
        await self.session.delete(rule)
        await self.session.commit()
        return True
