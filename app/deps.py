from typing import List
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import InsufficientPermissionsException, InvalidCredentialsException
from app.core.security import decode_token
from app.database import get_session
from app.models import Staff, User


async def get_token_from_header(authorization: str = Header(...)) -> str:
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidCredentialsException()
    return parts[1]


async def get_current_user_claims(
    token: str = Depends(get_token_from_header),
) -> dict:
    return decode_token(token)


async def get_current_user(
    claims: dict = Depends(get_current_user_claims),
    session: AsyncSession = Depends(get_session),
) -> User:
    user_id = UUID(claims["sub"])
    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise InvalidCredentialsException()
    return user


def require_roles(*allowed_roles: RoleEnum):
    async def _check(
        claims: dict = Depends(get_current_user_claims),
    ) -> dict:
        role = RoleEnum(claims["role"])
        if role not in allowed_roles:
            raise InsufficientPermissionsException()
        return claims

    return _check


async def get_branch_scope(
    claims: dict = Depends(get_current_user_claims),
    request: Request = None,
) -> UUID:
    role = RoleEnum(claims["role"])
    if role == RoleEnum.OWNER:
        if request:
            branch_id = request.query_params.get("branch_id")
            if branch_id:
                return UUID(branch_id)
    return UUID(claims["branch_id"])
