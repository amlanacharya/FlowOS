from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import MemberStatusEnum
from app.models import Member
from app.schemas.member import MemberCreate, MemberUpdate


class MemberService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_member_code(self, branch_id: UUID) -> str:
        """Generate unique member code for a branch."""
        result = await self.session.exec(
            select(Member)
            .where(Member.branch_id == branch_id)
            .order_by(Member.created_at.desc())
        )
        last_member = result.first()

        branch_prefix = "BR01"
        count = 1

        if last_member:
            parts = last_member.member_code.split("-")
            if len(parts) == 2:
                try:
                    count = int(parts[1]) + 1
                except ValueError:
                    pass

        return f"{branch_prefix}-{count:04d}"

    async def create_member(self, branch_id: UUID, data: MemberCreate) -> Member:
        member = Member(
            branch_id=branch_id,
            member_code=await self.generate_member_code(branch_id),
            **data.dict(),
        )
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_member(self, member_id: UUID) -> Optional[Member]:
        return await self.session.get(Member, member_id)

    async def list_members(
        self,
        branch_id: UUID,
        status: Optional[MemberStatusEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Member]:
        query = select(Member).where(Member.branch_id == branch_id)
        if status:
            query = query.where(Member.status == status)
        result = await self.session.exec(query.offset(skip).limit(limit))
        return result.all()

    async def update_member(
        self, member_id: UUID, data: MemberUpdate
    ) -> Optional[Member]:
        member = await self.get_member(member_id)
        if not member:
            return None
        for key, value in data.dict(exclude_unset=True).items():
            setattr(member, key, value)
        member.updated_at = datetime.utcnow()
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def pause_member(self, member_id: UUID) -> Optional[Member]:
        member = await self.get_member(member_id)
        if not member:
            return None
        member.status = MemberStatusEnum.PAUSED
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def activate_member(self, member_id: UUID) -> Optional[Member]:
        member = await self.get_member(member_id)
        if not member:
            return None
        member.status = MemberStatusEnum.ACTIVE
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member
