from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import MemberStatusEnum
from app.core.enums import InvoiceTypeEnum
from app.models import Member, MemberSubscription, MembershipPlan
from app.schemas.member import MemberCreate, MemberUpdate
from app.services.invoice_service import InvoiceService


class MemberService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_member_code(self, branch_id: UUID) -> str:
        """Generate unique member code for a branch."""
        result = await self.session.execute(
            select(Member)
            .where(Member.branch_id == branch_id)
            .order_by(Member.created_at.desc())
        )
        last_member = result.scalars().first()

        branch_prefix = f"BR{branch_id.hex[:6].upper()}"
        count = 1001

        if last_member:
            parts = last_member.member_code.split("-")
            if len(parts) == 2:
                branch_prefix = parts[0] or branch_prefix
                try:
                    count = int(parts[1]) + 1
                except ValueError:
                    pass

        return f"{branch_prefix}-{count:04d}"

    async def create_member(self, branch_id: UUID, data: MemberCreate, staff_id: UUID) -> Member:
        plan = await self.session.get(MembershipPlan, data.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if plan.branch_id != branch_id:
            raise ValueError("Plan does not belong to this branch")

        member = Member(
            branch_id=branch_id,
            member_code=await self.generate_member_code(branch_id),
            full_name=data.full_name,
            phone=data.phone,
            email=data.email,
            aadhaar_no=data.aadhaar_no,
            pan_no=data.pan_no,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            emergency_contact=data.emergency_contact,
            notes=data.notes,
            status=data.status or MemberStatusEnum.ACTIVE,
        )
        self.session.add(member)
        await self.session.flush()

        start_date = date.today()
        sub = MemberSubscription(
            member_id=member.id,
            branch_id=branch_id,
            plan_id=plan.id,
            start_date=start_date,
            end_date=start_date + timedelta(days=plan.duration_days),
            total_amount=plan.price,
            amount_due=plan.price,
            created_by_staff_id=staff_id,
        )
        self.session.add(sub)
        await self.session.flush()

        invoice_service = InvoiceService(self.session)
        await invoice_service.create_subscription_invoice(
            branch_id=branch_id,
            member_id=member.id,
            subscription_id=sub.id,
            plan=plan,
            created_by_staff_id=staff_id,
            invoice_type=InvoiceTypeEnum.NEW_JOIN,
        )

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
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

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
