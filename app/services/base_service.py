from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Member


async def validate_member_in_branch(session: AsyncSession, member_id: UUID, branch_id: UUID) -> Member:
    """Validate that a member exists in the specified branch."""
    member = await session.get(Member, member_id)
    if not member or member.branch_id != branch_id:
        raise ValueError("Member not found in this branch")
    return member
