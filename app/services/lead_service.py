from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import LeadStatusEnum
from app.models import Lead, Member
from app.schemas.lead import LeadCreate, LeadUpdate


class LeadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_lead(self, branch_id: UUID, data: LeadCreate) -> Lead:
        lead = Lead(branch_id=branch_id, **data.dict())
        self.session.add(lead)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def get_lead(self, lead_id: UUID) -> Optional[Lead]:
        return await self.session.get(Lead, lead_id)

    async def list_leads(
        self,
        branch_id: UUID,
        status: Optional[LeadStatusEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Lead]:
        query = select(Lead).where(Lead.branch_id == branch_id)
        if status:
            query = query.where(Lead.status == status)
        result = await self.session.exec(query.offset(skip).limit(limit))
        return result.all()

    async def update_lead(self, lead_id: UUID, data: LeadUpdate) -> Optional[Lead]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        for key, value in data.dict(exclude_unset=True).items():
            setattr(lead, key, value)
        lead.updated_at = datetime.utcnow()
        self.session.add(lead)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def schedule_trial(
        self, lead_id: UUID, trial_datetime: datetime
    ) -> Optional[Lead]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        lead.trial_scheduled_at = trial_datetime
        lead.status = LeadStatusEnum.TRIAL_SCHEDULED
        self.session.add(lead)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def transition_status(
        self, lead_id: UUID, new_status: LeadStatusEnum
    ) -> Optional[Lead]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None

        valid_transitions = {
            LeadStatusEnum.NEW: [LeadStatusEnum.CONTACTED, LeadStatusEnum.LOST],
            LeadStatusEnum.CONTACTED: [LeadStatusEnum.TRIAL_SCHEDULED, LeadStatusEnum.LOST],
            LeadStatusEnum.TRIAL_SCHEDULED: [LeadStatusEnum.TRIAL_ATTENDED, LeadStatusEnum.LOST],
            LeadStatusEnum.TRIAL_ATTENDED: [LeadStatusEnum.CONVERTED, LeadStatusEnum.LOST],
            LeadStatusEnum.CONVERTED: [],
            LeadStatusEnum.LOST: [LeadStatusEnum.CONTACTED],
        }

        if new_status not in valid_transitions.get(lead.status, []):
            raise ValueError(f"Invalid transition from {lead.status} to {new_status}")

        lead.status = new_status
        lead.updated_at = datetime.utcnow()
        self.session.add(lead)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead

    async def convert_to_member(
        self, lead_id: UUID, member: Member
    ) -> Optional[Lead]:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        lead.converted_member_id = member.id
        lead.status = LeadStatusEnum.CONVERTED
        self.session.add(lead)
        await self.session.commit()
        await self.session.refresh(lead)
        return lead
