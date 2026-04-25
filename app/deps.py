from typing import TypeVar
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RoleEnum
from app.core.exceptions import InsufficientPermissionsException, InvalidCredentialsException, ResourceNotFoundException
from app.core.security import decode_token
from app.database import get_session
from app.models import User

T = TypeVar('T')


bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


async def get_token_from_header(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise InvalidCredentialsException()
    return credentials.credentials


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


def check_found(item: T | None) -> T:
    """Raise ResourceNotFoundException if item is None, otherwise return item."""
    if not item:
        raise ResourceNotFoundException()
    return item
