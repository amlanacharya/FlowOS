from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import (
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, User


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        phone: Optional[str] = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            phone=phone,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        user.last_login = datetime.utcnow()
        self.session.add(user)
        await self.session.commit()
        return user

    def create_refresh_token(self, user_id: UUID) -> tuple[str, str]:
        return create_refresh_token(user_id)

    async def validate_refresh_token(self, token: str) -> Optional[UUID]:
        try:
            claims = decode_token(token)
            if claims.get("type") != "refresh":
                return None
            statement = (
                select(RefreshToken)
                .where(RefreshToken.jti == claims.get("jti"))
                .where(RefreshToken.revoked == False)
            )
            result = await self.session.execute(statement)
            rt = result.scalars().first()
            if not rt or rt.expires_at < datetime.utcnow():
                return None
            return UUID(claims["user_id"])
        except (ValueError, KeyError, AttributeError):
            return None

    async def revoke_refresh_token(self, token: str) -> bool:
        try:
            claims = decode_token(token)
            statement = select(RefreshToken).where(
                RefreshToken.jti == claims.get("jti")
            )
            result = await self.session.execute(statement)
            rt = result.scalars().first()
            if rt:
                rt.revoked = True
                self.session.add(rt)
                await self.session.commit()
                return True
        except (ValueError, KeyError, AttributeError):
            return False
        return False
