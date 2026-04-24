from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import ClassType
from app.schemas.class_type import ClassTypeCreate, ClassTypeResponse
from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import require_roles, get_branch_scope
from datetime import datetime

router = APIRouter(prefix="/api/v1/class-types", tags=["class-types"])


@router.post("", response_model=ClassTypeResponse)
async def create_class_type(
    class_type: ClassTypeCreate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
):
    db_class_type = ClassType(branch_id=branch_id, **class_type.dict())
    session.add(db_class_type)
    await session.commit()
    await session.refresh(db_class_type)
    return db_class_type


@router.get("", response_model=List[ClassTypeResponse])
async def list_class_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER, RoleEnum.FRONT_DESK, RoleEnum.TRAINER)),
    branch_id: UUID = Depends(get_branch_scope),
    session: AsyncSession = Depends(get_session),
):
    statement = (
        select(ClassType)
        .where(ClassType.branch_id == branch_id)
        .where(ClassType.is_active)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/{class_type_id}", response_model=ClassTypeResponse)
async def get_class_type(
    class_type_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER, RoleEnum.FRONT_DESK, RoleEnum.TRAINER)),
    session: AsyncSession = Depends(get_session),
):
    class_type = await session.get(ClassType, class_type_id)
    if not class_type:
        raise ResourceNotFoundException()
    return class_type


@router.patch("/{class_type_id}", response_model=ClassTypeResponse)
async def update_class_type(
    class_type_id: UUID,
    class_type_update: ClassTypeCreate,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    class_type = await session.get(ClassType, class_type_id)
    if not class_type:
        raise ResourceNotFoundException()
    for key, value in class_type_update.dict(exclude_unset=True).items():
        setattr(class_type, key, value)
    class_type.updated_at = datetime.utcnow()
    session.add(class_type)
    await session.commit()
    await session.refresh(class_type)
    return class_type


@router.delete("/{class_type_id}")
async def delete_class_type(
    class_type_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.BRANCH_MANAGER, RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    class_type = await session.get(ClassType, class_type_id)
    if not class_type:
        raise ResourceNotFoundException()
    class_type.is_active = False
    session.add(class_type)
    await session.commit()
    return {"message": "Class type deactivated"}
