from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.exceptions import InvalidCredentialsException
from app.core.security import create_access_token, hash_password
from app.database import get_session
from app.deps import get_current_user, get_current_user_claims
from app.models import RefreshToken, Staff, User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    service = AuthService(session)
    user = await service.authenticate(request.email, request.password)
    if not user:
        raise InvalidCredentialsException()

    statement = select(Staff).where(Staff.user_id == user.id)
    result = await session.execute(statement)
    staff = result.scalars().first()
    if not staff:
        raise InvalidCredentialsException("Staff profile not found")

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": staff.role.value,
            "org_id": str(staff.organization_id),
            "branch_id": str(staff.branch_id),
            "staff_id": str(staff.id),
        }
    )
    token_str, jti = service.create_refresh_token(user.id)
    rt = RefreshToken(
        jti=jti,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    session.add(rt)
    await session.commit()
    return TokenResponse(access_token=access_token, refresh_token=token_str)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    service = AuthService(session)
    user_id = await service.validate_refresh_token(request.refresh_token)
    if not user_id:
        raise InvalidCredentialsException()

    user = await session.get(User, user_id)
    if not user:
        raise InvalidCredentialsException()

    statement = select(Staff).where(Staff.user_id == user_id)
    result = await session.execute(statement)
    staff = result.scalars().first()
    if not staff:
        raise InvalidCredentialsException("Staff profile not found")

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": staff.role.value,
            "org_id": str(staff.organization_id),
            "branch_id": str(staff.branch_id),
            "staff_id": str(staff.id),
        }
    )
    return TokenResponse(access_token=access_token, refresh_token=request.refresh_token)


@router.post("/logout")
async def logout(
    request: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    service = AuthService(session)
    await service.revoke_refresh_token(request.refresh_token)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    claims: dict = Depends(get_current_user_claims),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserProfileResponse:
    statement = select(Staff).where(Staff.user_id == user.id)
    result = await session.execute(statement)
    staff = result.scalars().first()
    if not staff:
        raise InvalidCredentialsException("Staff profile not found")

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=staff.role,
        branch_id=staff.branch_id,
        org_id=staff.organization_id,
        staff_id=staff.id,
    )


@router.patch("/me/password")
async def change_password(
    old_password: str,
    new_password: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from app.core.security import verify_password

    if not verify_password(old_password, user.hashed_password):
        raise InvalidCredentialsException()
    user.hashed_password = hash_password(new_password)
    session.add(user)
    await session.commit()
    return {"message": "Password changed"}
