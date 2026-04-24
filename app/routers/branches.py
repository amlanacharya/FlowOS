from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.enums import RoleEnum
from app.core.exceptions import ResourceNotFoundException
from app.database import get_session
from app.deps import require_roles
from app.models import Branch
from app.schemas.branch import BranchCreate, BranchResponse

router = APIRouter(prefix="/api/v1/branches", tags=["branches"])


@router.post("", response_model=BranchResponse)
async def create_branch(
    branch: BranchCreate,
    org_id: UUID = Query(...),
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> BranchResponse:
    db_branch = Branch(**branch.dict(), organization_id=org_id)
    session.add(db_branch)
    await session.commit()
    await session.refresh(db_branch)
    return db_branch


@router.get("", response_model=List[BranchResponse])
async def list_branches(
    org_id: UUID = Query(...),
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> List[BranchResponse]:
    statement = select(Branch).where(Branch.organization_id == org_id)
    result = await session.execute(statement)
    branches = result.scalars().all()
    return branches


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER, RoleEnum.BRANCH_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> BranchResponse:
    branch = await session.get(Branch, branch_id)
    if not branch:
        raise ResourceNotFoundException()
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    branch_update: BranchCreate,
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> BranchResponse:
    branch = await session.get(Branch, branch_id)
    if not branch:
        raise ResourceNotFoundException()
    for key, value in branch_update.dict(exclude_unset=True).items():
        setattr(branch, key, value)
    branch.updated_at = datetime.utcnow()
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


@router.delete("/{branch_id}")
async def delete_branch(
    branch_id: UUID,
    claims: dict = Depends(require_roles(RoleEnum.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> dict:
    branch = await session.get(Branch, branch_id)
    if not branch:
        raise ResourceNotFoundException()
    branch.is_active = False
    session.add(branch)
    await session.commit()
    return {"message": "Branch deactivated"}
