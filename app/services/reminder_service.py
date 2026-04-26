from datetime import date
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Member, MemberSubscription
from app.schemas.reminder import ReminderChecklistItem


class ReminderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_checklist(self, branch_id: UUID) -> List[ReminderChecklistItem]:
        today = date.today()
        statement = (
            select(MemberSubscription, Member)
            .join(Member, Member.id == MemberSubscription.member_id)
            .where(MemberSubscription.branch_id == branch_id)
        )
        result = await self.session.execute(statement)
        rows = result.all()

        allowed_checkpoints = {-3, -2, -1, 0, 1}
        checklist: List[ReminderChecklistItem] = []
        for sub, member in rows:
            checkpoint = (sub.end_date - today).days
            mapped = -checkpoint
            if mapped not in allowed_checkpoints:
                continue
            checklist.append(
                ReminderChecklistItem(
                    subscription_id=sub.id,
                    member_id=member.id,
                    member_name=member.full_name,
                    member_phone=member.phone,
                    end_date=sub.end_date,
                    checkpoint_day=mapped,
                    checkpoint_label=f"T{mapped:+d}".replace("+", "+"),
                    amount_due=float(sub.amount_due),
                )
            )

        checklist.sort(key=lambda item: item.checkpoint_day, reverse=True)
        return checklist
