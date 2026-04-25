from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Member


def optional_filters(*conditions: Any) -> list[Any]:
    return [condition for condition in conditions if condition is not None]


def branch_conditions(model: Any, branch_id: UUID, *conditions: Any) -> list[Any]:
    return [model.branch_id == branch_id, *optional_filters(*conditions)]


async def require_branch_member(session: AsyncSession, branch_id: UUID, member_id: UUID) -> Member:
    member = await session.get(Member, member_id)
    if not member or member.branch_id != branch_id:
        raise ValueError("Member not found in this branch")
    return member


def apply_pagination(statement: Any, skip: int, limit: int) -> Any:
    return statement.offset(skip).limit(limit)
